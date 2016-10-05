from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

def ClosestPointsOnTwoLines( linePoint1, lineVec1, linePoint2, lineVec2):

    closestPointLine1 = FreeCAD.Vector(0,0,0)
    closestPointLine2 = FreeCAD.Vector(0,0,0)

    a = lineVec1.dot( lineVec1 )
    b = lineVec1.dot( lineVec2 )
    e = lineVec2.dot( lineVec2 )

    d = a*e - b*b

    #lines are not parallel
    if (d != 0):

        r = linePoint1 - linePoint2
        c = lineVec1.dot( r )
        f = lineVec2.dot( r )

        s = (b*f - c*e) / d
        t = (a*f - c*b) / d

        closestPointLine1 = linePoint1 + lineVec1.multiply(s)
        closestPointLine2 = linePoint2 + lineVec2.multiply(t)

        ret = [closestPointLine1,closestPointLine2]

        return ret;

    else:
        return False;

def IntersectionPoint( Pt1, Pt2, Pt3, Pt4):
        
    pt = ClosestPointsOnTwoLines( Pt1, Pt2-Pt1, Pt3, Pt4-Pt3 )

    v = pt[1].sub(pt[0])
    #l = v.Length
    #v.normalize()
    v.multiply(0.5)
    
    return ( pt[0].add(v) )


class BlendCurve:
    def __init__(self, obj , edges):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nBlendCurve class Init\n")
        
        obj.addProperty("App::PropertyBool","AddCurves","BlendCurve","Add input curves to result").AddCurves = False
        obj.addProperty("App::PropertyBool","ShowPoints","BlendCurve","Show ontrol polygon").ShowPoints = False
        
        obj.addProperty("App::PropertyLinkSub","Edge1","BlendCurve","Edge 1").Edge1 = edges[0]
        obj.addProperty("App::PropertyLinkSub","Edge2","BlendCurve","Edge 2").Edge2 = edges[1]
        
        obj.addProperty("App::PropertyBool","Reverse1","BlendCurve","Reverse curve direction").Reverse1 = False
        obj.addProperty("App::PropertyFloatConstraint","Parameter1","BlendCurve","Location of blend curve")
        obj.addProperty("App::PropertyFloatConstraint","Scale1","BlendCurve","Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration","Continuity1","BlendCurve","Continuity").Continuity1=["C0","G1","G2"]
        
        obj.addProperty("App::PropertyBool","Reverse2","BlendCurve","Reverse curve direction").Reverse2 = False
        obj.addProperty("App::PropertyFloatConstraint","Parameter2","BlendCurve","Location of blend curve")
        obj.addProperty("App::PropertyFloatConstraint","Scale2","BlendCurve","Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration","Continuity2","BlendCurve","Continuity").Continuity2=["C0","G1","G2"]
        
        obj.addProperty("Part::PropertyPartShape","Shape","BlendCurve", "Shape of the blend curve")
        
        obj.Scale1 = (10.,0.1,100.,0.5)
        obj.Scale2 = (10.,0.1,100.,0.5)
        self.scale1 = obj.Scale1 / 10.
        self.scale2 = obj.Scale2 / 10.
        
        self.cont1 = 0
        self.cont2 = 0

        self.reverse1 = obj.Reverse1
        self.reverse2 = obj.Reverse2
        self.blendDegree = 1 + self.cont1 + self.cont2
        
        self.initEdges(obj)
        
        obj.Parameter1 = ( self.edge1.LastParameter * 100, self.edge1.FirstParameter * 100, self.edge1.LastParameter * 100, 0.5 )
        obj.Parameter2 = ( self.edge2.LastParameter * 100, self.edge2.FirstParameter * 100, self.edge2.LastParameter * 100, 0.5 )
        self.param1 = self.edge1.LastParameter
        self.param2 = self.edge2.LastParameter
        
        obj.Proxy = self
        self.execute(obj)

    def initEdges(self, fp):
        n1 = eval(fp.Edge1[1][0].lstrip('Edge'))
        if (not fp.Edge1[0].Shape.Edges) and (not fp.Edge2[0].Shape.Edges):
            return
        if self.reverse1:
            self.curve1 = fp.Edge1[0].Shape.Edges[n1-1].Curve.copy()
            poles = self.curve1.getPoles()
            self.curve1.setPoles(poles[::-1])
        else:
            self.curve1 = fp.Edge1[0].Shape.Edges[n1-1].Curve
        self.edge1 = self.curve1.toShape()
        
        n2 = eval(fp.Edge2[1][0].lstrip('Edge'))
        if self.reverse2:
            self.curve2 = fp.Edge2[0].Shape.Edges[n2-1].Curve.copy()
            poles = self.curve2.getPoles()
            self.curve2.setPoles(poles[::-1])
        else:
            self.curve2 = fp.Edge2[0].Shape.Edges[n2-1].Curve
        self.edge2 = self.curve2.toShape()
        
        #fp.Parameter1 = ( self.edge1.LastParameter * 100, self.edge1.FirstParameter * 100, self.edge1.LastParameter * 100, 0.5 )
        #fp.Parameter2 = ( self.edge2.LastParameter * 100, self.edge2.FirstParameter * 100, self.edge2.LastParameter * 100, 0.5 )
        #self.param1 = self.edge1.LastParameter
        #self.param2 = self.edge1.LastParameter
        
    def computePoles(self):
        poles = [self.edge1.valueAt(self.param1)] * (self.cont1 + 1) + [self.edge2.valueAt(self.param2)] * (self.cont2 + 1)
        #poles[0]  = self.edge1.valueAt(self.param1)
        #poles[-1] = self.edge2.valueAt(self.param2)
        polese1 = self.curve1.getPoles()
        polese2 = self.curve2.getPoles()
        p = IntersectionPoint(polese1[-1],polese1[-2],polese2[-1],polese1[-2])
        chordLength = p.sub(polese1[-1]).Length + p.sub(polese2[-1]).Length
        #chord = poles[-1].sub(poles[0])
        segmentLength = chordLength * 1.0 / self.blendDegree
        
        if self.cont1 > 0:
            e1d1 = self.edge1.derivative1At(self.param1)
            e1d1.normalize().multiply( segmentLength * self.scale1 )
            poles[1]  = poles[0].add(e1d1)
            #remaining = poles[1].sub(poles[-1]).Length
            #segmentLength = remaining * 1.0 / ( self.blendDegree -1 )
        if self.cont2 > 0:
            e2d1 = self.edge2.derivative1At(self.param2)
            e2d1.normalize().multiply( segmentLength * self.scale2 )
            poles[-2] = poles[-1].add(e2d1)
            #remaining = poles[-2].sub(poles[self.cont1]).Length
            #segmentLength = remaining * 1.0 / ( self.blendDegree -2 )
        
        if self.cont1 > 1:
            curvature1 = self.edge1.curvatureAt(self.param1)
            radius = curvature1 * self.blendDegree * pow(e1d1.Length,2) / (self.blendDegree -1)
            opp = math.sqrt(pow(segmentLength * self.scale1,2)-pow(radius,2))
            c = Part.Circle()
            c.Axis = e1d1
            v = FreeCAD.Vector(e1d1)
            v.normalize().multiply(e1d1.Length+opp)
            c.Center = poles[0].add(v)
            c.Radius = radius
            poles[2] = c.value(c.parameter(poles[-1-self.cont2]))
            #remaining = poles[-1-self.cont2].sub(poles[2]).Length
            #segmentLength = remaining * 1.0 / ( 2 )
            
        if self.cont2 > 1:
            curvature2 = self.edge2.curvatureAt(self.param2)
            radius = curvature2 * self.blendDegree * pow(e2d1.Length,2) / (self.blendDegree -1)
            opp = math.sqrt(pow(segmentLength * self.scale2,2)-pow(radius,2))
            c = Part.Circle()
            c.Axis = e2d1
            v = FreeCAD.Vector(e2d1)
            v.normalize().multiply(e2d1.Length+opp)
            c.Center = poles[-1].add(v)
            c.Radius = radius
            poles[-3] = c.value(c.parameter(poles[self.cont1]))
            #remaining = poles[-3].sub(poles[self.cont1]).Length
            #segmentLength = remaining * 1.0 / ( 1 )
        
        return poles
        
        
    def execute(self, fp):
        
        self.blendPoles = self.computePoles() #[self.edge1.valueAt(self.param1),self.edge2.valueAt(self.param2)]
        
        self.blendCurve = Part.BezierCurve()
        self.blendCurve.increase(self.blendDegree)
        self.blendCurve.setPoles(self.blendPoles)
        
        b  = self.blendCurve.toShape()
        edges = [b]
        
        if fp.AddCurves:
            c1 = self.curve1.copy()
            c1.segment(c1.FirstParameter,self.param1)
            e1 = c1.toShape()
            c2 = self.curve2.copy()
            c2.segment(c2.FirstParameter,self.param2)
            e2 = c2.toShape()
            edges += [e1,e2]
            
        if fp.ShowPoints:
            poly = []
            for e in edges:
                poly.append(Part.makePolygon(e.Curve.getPoles()))
            edges += poly
        fp.Shape  = Part.Wire(edges)
        #else:
            
            #fp.Shape = self.blendCurve.toShape()


    def onChanged(self, fp, prop):

        if prop == "Edge1" or prop == "Edge2":
            self.initEdges(fp)
        elif prop == "Scale1":
            self.scale1 = fp.Scale1 / 10.
        elif prop == "Scale2":
            self.scale2 = fp.Scale2 / 10.
        elif prop == "Parameter1":
            self.param1 = fp.Parameter1 / 100
        elif prop == "Parameter2":
            self.param2 = fp.Parameter2 / 100
        elif prop == "Continuity1":
            self.cont1 = self.getContinuity(fp.Continuity1)
            self.blendDegree = 1 + self.cont1 + self.cont2
        elif prop == "Continuity2":
            self.cont2 = self.getContinuity(fp.Continuity2)
            self.blendDegree = 1 + self.cont1 + self.cont2
        elif prop == "Reverse1":
            FreeCAD.Console.PrintMessage("\nReverse1 changed\n")
            self.reverse1 = fp.Reverse1
            self.initEdges(fp)
        elif prop == "Reverse2":
            FreeCAD.Console.PrintMessage("\nReverse2 changed\n")
            self.reverse2 = fp.Reverse2
            self.initEdges(fp)
        else:
            return
        self.execute(fp)

    def getContinuity(self, cont):
        if cont == "C0":
            return 0
        elif cont == "G1":
            return 1
        else:
            return 2

class ParametricBlendCurve:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj),Part.Edge):
                        res.append([obj.Object,obj.SubElementNames[i]])
                    i += 1
            else:
                i = 0
                for e in obj.Object.Shape.Edges:
                    n = "Edge"+str(i)
                    res.append([obj.Object,n])
                    i += 1
        return res
    
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = self.parseSel(s)
        print str(edges)
        obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Blend Curve") #add object to document
        BlendCurve(obj,edges[0:2])
        obj.ViewObject.Proxy = 0
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/blend.svg', 'MenuText': 'ParametricBlendCurve', 'ToolTip': 'Creates a parametric blend curve'}

FreeCADGui.addCommand('ParametricBlendCurve', ParametricBlendCurve())




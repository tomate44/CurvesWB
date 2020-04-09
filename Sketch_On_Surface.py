# -*- coding: utf-8 -*-

__title__ = "Sketch on surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Map a sketch on a surface"

import FreeCAD
import FreeCADGui
import Part
import Sketcher
from FreeCAD import Base
import _utils

TOOL_ICON = _utils.iconsPath() + '/sketch_surf.svg'
#debug = _utils.debug
debug = _utils.doNothing
vec = FreeCAD.Vector


# DEPRECATED

#def Points2D(pts):
    #if isinstance(pts,FreeCAD.Vector):
        #return Base.Vector2d(pts.x,pts.y)
    #elif isinstance(pts,(list,tuple)):
        #l = [Points2D(p) for p in pts]
        #return l
    #else:
        #App.Console.PrintError("Failed to convert points to 2D\n")
        #return None

#def toShape(curves2d,surf, Approx = 32):
    #edges = []
    #for c in curves2d:
        #if Approx:
            #pts = c.toShape(surf).discretize(QuasiNumber = Approx)
            #bs = Part.BSplineCurve()
            #bs.approximate(pts)
            #edges.append(bs.toShape())
        #else:
            #edges.append(c.toShape(surf))
    #com = Part.Compound(edges)
    #return com

#def to2D(geom):
    #if isinstance(geom,list):
        #r = []
        #for e in geom:
            #if isinstance(e,Part.Line):
                #ls = Part.LineSegment(e.valueAt(e.FirstParameter),e.valueAt(e.LastParameter))
                #r.append(to2D(ls))
            #else:
                #r.append(to2D(e))
        #return r
    #if isinstance(geom,Part.ArcOfCircle):
        #debug('Arc Of Circle')
        
        #circle2D = Part.Geom2d.Circle2d( Points2D(geom.Circle.Center), geom.Circle.Radius)
        #curve2D = Part.Geom2d.ArcOfCircle2d( circle2D, geom.FirstParameter, geom.LastParameter)
        
    ##elif isinstance(geom,Part.ArcOfConic):
        ##print('Arc Of Conic')
    #elif isinstance(geom,Part.ArcOfEllipse):
        #debug('Arc Of Ellipse')
    #elif isinstance(geom,Part.ArcOfHyperbola):
        #debug('Arc Of Hyperbola')
    #elif isinstance(geom,Part.ArcOfParabola):
        #debug('Arc Of Parabola')
    #elif isinstance(geom,Part.BSplineCurve):
        #debug('BSpline Curve')

        #poles3D = geom.getPoles()
        #weights = geom.getWeights()
        #knots =   geom.getKnots()
        #mults =   geom.getMultiplicities()
        #degree =  geom.Degree
        #periodic  = geom.isPeriodic()

        #poles2D = Points2D(poles3D)
        #curve2D = Part.Geom2d.BSplineCurve2d()
        ## buildFromPolesMultsKnots arguments: poles (sequence of Base.Vector), [mults , knots, periodic, degree, weights (sequence of float), CheckRational]
        #curve2D.buildFromPolesMultsKnots( poles2D, mults, knots, periodic, degree, weights)

    #elif isinstance(geom,Part.BezierCurve):
        #debug('Bezier Curve')
        
        #poles3D = geom.getPoles()
        #weights = geom.getWeights()
        #degree =  geom.Degree
        #periodic  = geom.isPeriodic()

        #poles2D = Points2D(poles3D)
        #curve2D = Part.Geom2d.BezierCurve2d()
        #curve2D.increase(degree)
        #for i in range(geom.NbPoles):
            #curve2D.setPole(i+1,poles2D[i])
            #curve2D.setWeight(i+1,weights[i])
        
    #elif isinstance(geom,Part.Circle):
        #debug('Circle')
        
        #curve2D = Part.Geom2d.Circle2d( Points2D(geom.Center), geom.Radius)
        
    ##elif isinstance(geom,Part.Conic):
        ##print('Conic')
    #elif isinstance(geom,Part.Ellipse):
        #debug('Ellipse')
        
        #curve2D = Part.Geom2d.Ellipse2d( Points2D(geom.Center), geom.MajorRadius, geom.MinorRadius)
        
    #elif isinstance(geom,Part.Hyperbola):
        #debug('Hyperbola')
    #elif isinstance(geom,Part.Parabola):
        #debug('Parabola')
    #elif isinstance(geom,Part.Line):
        #debug('Line')
    #elif isinstance(geom,Part.LineSegment):
        #debug('LineSegment')
        
        #p0 = geom.StartPoint
        #p1 = geom.EndPoint
        #Pts2D = Points2D([p0,p1])
        #curve2D = Part.Geom2d.Line2dSegment(Pts2D[0],Pts2D[1])

    ##print(curve2D)
    #return curve2D

def stretched_plane(geom_range=[0,1,0,1], param_range=[0,2,0,2]):
    u0, u1, v0, v1 = geom_range
    s0, s1, t0, t1 = param_range
    bs = Part.BSplineSurface()
    poles = [[FreeCAD.Vector(u0,v0,0), FreeCAD.Vector(u0,v1,0)],
                [FreeCAD.Vector(u1,v0,0), FreeCAD.Vector(u1,v1,0)]]
    umults = [2, 2]
    vmults = [2, 2]
    uknots = [s0, s1]
    vknots = [t0, t1]
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots, False, False, 1, 1)
    return bs

class BoundarySorter:
    def __init__(self, wires):
        self.wires = []
        self.parents = []
        self.sorted_wires = []
        for w in wires:
            self.wires.append(w)
            self.parents.append([])
            self.sorted_wires.append([])
        self.done = False
    def check_inside(self):
        for i, w1 in enumerate(self.wires):
            for j, w2 in enumerate(self.wires):
                if not i == j:
                    if w2.BoundBox.isInside(w1.BoundBox):
                        self.parents[i].append(j)
    def sort_pass(self):
        to_remove = []
        for i,p in enumerate(self.parents):
            if (p is not None) and p == []:
                to_remove.append(i)
                self.sorted_wires[i].append(self.wires[i])
                self.parents[i] = None
        #print("Removing parents : {}".format(to_remove))
        for i,p in enumerate(self.parents):
            if (p is not None) and len(p) == 1:
                to_remove.append(i)
                self.sorted_wires[p[0]].append(self.wires[i])
                self.parents[i] = None
        #print("Removing full : {}".format(to_remove))
        if len(to_remove) > 0:
            for i,p in enumerate(self.parents):
                if (p is not None):
                    for r in to_remove:
                        if r in p:
                            p.remove(r)
        else:
            self.done = True
    def sort(self):
        self.check_inside()
        #print(self.parents)
        while not self.done:
            #print("Pass {}".format(i))
            self.sort_pass()
        result = []
        for w in self.sorted_wires:
            if w:
                result.append(w)
        return result

class sketchOnSurface:
    "This feature object maps a sketch on a surface"
    def __init__(self, obj):
        obj.addProperty("App::PropertyLink",    "Sketch", "SketchOnSurface", "Input Sketch")
        obj.addProperty("App::PropertyBool",    "FillFaces",     "Settings", "Make faces from closed wires").FillFaces = True
        obj.addProperty("App::PropertyBool",    "FillExtrusion", "Settings", "Add extrusion faces").FillExtrusion = True
        obj.addProperty("App::PropertyFloat",   "Offset",   "Settings", "Offset distance of mapped sketch").Offset = 0.0
        obj.addProperty("App::PropertyFloat",   "Thickness","Settings", "Extrusion thickness").Thickness = 1.0
        obj.addProperty("App::PropertyBool",    "ReverseU", "Touchup", "Reverse U direction").ReverseU = False
        obj.addProperty("App::PropertyBool",    "ReverseV", "Touchup", "Reverse V direction").ReverseV = False
        obj.addProperty("App::PropertyBool",    "ConstructionBounds", "Touchup", "include construction geometry in sketch bounds").ConstructionBounds = True
        obj.Proxy = self

    def build_faces(self, wl, surf):
        faces = []
        bs = BoundarySorter(wl)
        for wirelist in bs.sort():
            #print(wirelist)
            f = Part.Face(surf, wirelist[0])
            f.validate()
            if len(wirelist) > 1:
                f.cutHoles(wirelist[1:])
                f.validate()
            faces.append(f)
        return faces

    def mapping(self, obj, quad, face):
        proj = quad.project(obj.Sketch.Shape.Edges)
        new_edges = []
        for e in proj.Edges:
            try:
                c2d, fp, lp = quad.curveOnSurface(e)
                ne = c2d.toShape(face.Surface, fp, lp)
                new_edges.append(ne)
            except TypeError:
                debug("Failed to get 2D curve")
        sorted_edges = Part.sortEdges(new_edges)
        wirelist = [Part.Wire(el) for el in sorted_edges]
        if obj.FillFaces:
            return self.build_faces(wirelist, face.Surface)
        else:
            return wirelist

    def execute(self, obj):
        def error(msg):
            func_name = "{} (Sketch_On_Surface)  : ".format(obj.Label)
            FreeCAD.Console.PrintError(func_name + msg + "\n")
        if not obj.Sketch:
            error("No Sketch attached")
            return
        skedges = []
        for i in obj.Sketch.Geometry:
            if i.Construction and not obj.ConstructionBounds:
                continue
            try:
                skedges.append(i.toShape())
            except:
                debug("toShape() error, ignoring geometry")
        comp = Part.Compound(skedges)

        bb = comp.BoundBox
        u0, u1, v0, v1 = (bb.XMin,bb.XMax,bb.YMin,bb.YMax)
        debug("Sketch bounds = {}".format((u0, u1, v0, v1)))
        
        try:
            n = eval(obj.Sketch.Support[0][1][0].lstrip('Face'))
            face = obj.Sketch.Support[0][0].Shape.Faces[n-1]
            face.Placement = obj.Sketch.Support[0][0].getGlobalPlacement()
        except (IndexError, AttributeError, SyntaxError) as e:
            error("Failed to get the face support of the sketch\n")
            return
        debug("Target face bounds = {}".format(face.ParameterRange))
        
        if obj.ReverseU:
            u0, u1 = u1, u0
        if obj.ReverseV:
            v0, v1 = v1, v0
        bs = stretched_plane(geom_range=[u0, u1, v0, v1], param_range=face.ParameterRange)
        quad = bs.toShape()
        quad.Placement = obj.Sketch.getGlobalPlacement()
        shapes_1 = []
        shapes_2 = []
        if (obj.Offset == 0):
            shapes_1 = self.mapping(obj, quad, face)
        else:
            f1 = face.makeOffsetShape(obj.Offset, 1e-3)
            shapes_1 = self.mapping(obj, quad, f1.Face1)
        if (obj.Thickness == 0) and shapes_1:
            obj.Shape = Part.Compound(shapes_1)
            return
        else:
            f2 = face.makeOffsetShape(obj.Offset+obj.Thickness, 1e-3)
            shapes_2 = self.mapping(obj, quad, f2.Face1)
            if not obj.FillExtrusion:
                if shapes_1 or shapes_2:
                    obj.Shape = Part.Compound(shapes_1 + shapes_2)
                    return
            else:
                shapes = []
                for i in range(len(shapes_1)):
                    if isinstance(shapes_1[i], Part.Face):
                        faces = shapes_1[i].Faces + shapes_2[i].Faces
                        for j in range(len(shapes_1[i].Wires)):
                            loft = Part.makeLoft([shapes_1[i].Wires[j], shapes_2[i].Wires[j]], False, True)
                            faces.extend(loft.Faces)
                        try:
                            shell = Part.Shell(faces)
                            solid = Part.Solid(shell)
                            shapes.append(solid)
                        except Part.OCCError:
                            FreeCAD.Console.PrintWarning("Sketch on surface : failed to create solid #{}.\n".format(i+1))
                            shapes.extend(faces)
                    else:
                        loft = Part.makeLoft([shapes_1[i].Wires[0], shapes_2[i].Wires[0]], obj.FillFaces, True)
                        shapes.append(loft)
                if shapes:
                    obj.Shape = Part.Compound(shapes)


class sosVP:
    def __init__(self,vobj):
        vobj.Proxy = self
        self.children = []
       
    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        #self.ViewObject = vobj
        self.Object = vobj.Object
        #if self.Object.Sketch:
            #self.children = [self.Object.Sketch]
        #else:
            #self.children = []
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        return [self.Object.Sketch]
        
def addFaceWireToSketch(fa, w, sk):
    curves = list()
    const = list()
    pl = Part.Plane()
    for idx in range(len(w.Edges)):
        e = fa.curveOnSurface(w.Edges[idx])
        e3d = e[0].toShape(pl)
        tc = e3d.Curve.trim(e[1],e[2])
        curves.append(tc)
    o = int(sk.GeometryCount)
    sk.addGeometry(curves,False)
    
    for idx in range(len(curves)):
        const.append(Sketcher.Constraint('Block',o+idx))
    sk.addConstraint(const)

def addFaceBoundsToSketch(para_range, sk):
    geoList = list()
    conList = list()
    u0,u1,v0,v1 = para_range
    geoList.append(Part.LineSegment(vec(u0,v0,0),vec(u1,v0,0)))
    geoList.append(Part.LineSegment(vec(u1,v0,0),vec(u1,v1,0)))
    geoList.append(Part.LineSegment(vec(u1,v1,0),vec(u0,v1,0)))
    geoList.append(Part.LineSegment(vec(u0,v1,0),vec(u0,v0,0)))
    o = int(sk.GeometryCount)
    sk.addGeometry(geoList,False)
    
    conList.append(Sketcher.Constraint('Coincident',o+0,2,o+1,1))
    conList.append(Sketcher.Constraint('Coincident',o+1,2,o+2,1))
    conList.append(Sketcher.Constraint('Coincident',o+2,2,o+3,1))
    conList.append(Sketcher.Constraint('Coincident',o+3,2,o+0,1))
    conList.append(Sketcher.Constraint('Horizontal',o+0))
    conList.append(Sketcher.Constraint('Horizontal',o+2))
    conList.append(Sketcher.Constraint('Vertical',o+1))
    conList.append(Sketcher.Constraint('Vertical',o+3))
    conList.append(Sketcher.Constraint('DistanceX',o+2,2,o+2,1,u1-u0))
    conList.append(Sketcher.Constraint('DistanceY',o+1,1,o+1,2,v1-v0))
    conList.append(Sketcher.Constraint('DistanceX',o+0,1,-1,1,-u0)) 
    conList.append(Sketcher.Constraint('DistanceY',o+0,1,-1,1,-v0)) 
    sk.addConstraint(conList)

def build_sketch(sk, fa):
    # add the bounding box of the face to the sketch
    u0,u1,v0,v1 = fa.ParameterRange
    if isinstance(fa.Surface, Part.Cylinder):
        u1 *= fa.Surface.Radius
        addFaceBoundsToSketch([u0,u1,v0,v1], sk)
    elif isinstance(fa.Surface, Part.Cone):
        u1 = 0.5 * (fa.Edge1.Length + fa.Edge3.Length)
        addFaceBoundsToSketch([u0,u1,v0,v1], sk)
    elif len(fa.Edges) == 4:
        u1 = 0.5 * (fa.Edge1.Length + fa.Edge3.Length)
        v1 = 0.5 * (fa.Edge2.Length + fa.Edge4.Length)
        addFaceBoundsToSketch([0,u1,0,v1], sk)
    else:
        for w in fa.Wires:
            addFaceWireToSketch(fa, w, sk)
    
    for i in range(int(sk.GeometryCount)):
        sk.toggleConstruction(i)

class SoS:
    def get_selection(self):
        sketch = None
        face_link = []
        sel = FreeCADGui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.Object.TypeId == 'Sketcher::SketchObject':
                sketch = selobj.Object
            elif selobj.HasSubObjects:
                if issubclass(type(selobj.SubObjects[0]),Part.Face):
                    face_link = (selobj.Object,[selobj.SubElementNames[0]])
        return sketch, face_link

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sketch, face_link = self.get_selection()
        if not sketch and not face_link:
            FreeCAD.Console.PrintMessage("Please select a face (in the 3D view) or a sketch\n")
            return
        if not sketch:
            sketch = doc.addObject('Sketcher::SketchObject','Mapped_Sketch')
            sketch.Support = face_link
            n = eval(face_link[1][0].lstrip('Face'))
            fa = face_link[0].Shape.Faces[n-1]
            build_sketch(sketch, fa)
            doc.recompute()
        sos = doc.addObject("Part::FeaturePython","Sketch On Surface")
        sketchOnSurface(sos)
        sos.Sketch = sketch
        sosVP(sos.ViewObject)
        doc.recompute()
        sketch.ViewObject.Visibility = False

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('SoS', SoS())
        


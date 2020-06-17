from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


def linkSubList_convertToOldStyle(references):
    """("input: [(obj1, (sub1, sub2)), (obj2, (sub1, sub2))]\n"
    "output: [(obj1, sub1), (obj1, sub2), (obj2, sub1), (obj2, sub2)]")"""
    result = []
    for tup in references:
        if type(tup[1]) is tuple or type(tup[1]) is list:
            for subname in tup[1]:
                result.append((tup[0], subname))
            if len(tup[1]) == 0:
                result.append((tup[0], ''))
        elif isinstance(tup[1],basestring):
            # old style references, no conversion required
            result.append(tup)
    return result

class sw2r:
    def __init__(self, obj):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nsw2r class init\n")
        obj.addProperty("App::PropertyLinkSubList","Rails","sw2r","List of rails")
        obj.addProperty("App::PropertyLinkSubList","Profiles","sw2r","List of profiles")
        obj.addProperty("App::PropertyIntegerConstraint","RailPoints","sw2r","Number of rail samples")
        obj.addProperty("App::PropertyIntegerConstraint","ProfilePoints","sw2r","Number of profile samples")
        obj.addProperty("App::PropertyIntegerConstraint","Degree","sw2r","Surface degree")
        obj.addProperty("App::PropertyIntegerConstraint","Iterations","sw2r","Number of iterations")
        obj.addProperty("App::PropertyIntegerConstraint","Segments","sw2r","Number of surface segments")
        obj.addProperty("App::PropertyFloat","MaxError","sw2r","Max error")
        #obj.addProperty("Part::PropertyPartShape","Shape","sw2r", "Shape of surface")
        obj.Proxy = self

        obj.Degree = (3,1,25,1)
        obj.Iterations = (1,1,12,1)
        obj.ProfilePoints = (16,3,100,1)
        obj.RailPoints = (32,3,100,1)
        obj.Segments = (3,1,50,1)

    def getShape(self, link):
        if 'Edge' in link[1]:
            n = eval(link[1].lstrip('Edge'))
            r = link[0].Shape.Edges[n-1]
            print(r)
            return (r)
        elif link[1] == '':
            if link[0].Shape.Wires:
                return (link[0].Shape.Wires[0])
            elif link[0].Shape.Edges:
                return (link[0].Shape.Edges[0])
            

    def execute(self, obj):
        r1 = self.getShape(linkSubList_convertToOldStyle(obj.Rails)[0]).discretize(Number = obj.RailPoints)
        r2 = self.getShape(linkSubList_convertToOldStyle(obj.Rails)[1]).discretize(Number = obj.RailPoints) #[::-1]
        d1 = Part.LineSegment(r1[0],r2[0]).toShape()
        d2 = Part.LineSegment(r1[-1],r2[-1]).toShape()
        d3 = Part.LineSegment(r1[0],r2[-1]).toShape()
        d4 = Part.LineSegment(r1[-1],r2[0]).toShape()
        distToShape1 = abs(d1.distToShape(d2)[0])
        distToShape2 = abs(d3.distToShape(d4)[0])
        if distToShape1 < distToShape2:
            r2 = r2[::-1]
        bs1 = Part.BSplineCurve()
        bs2 = Part.BSplineCurve()
        bs1.approximate( Points = r1, DegMin = 1, DegMax = 5, Continuity = 'C1') #, LengthWeight = 1.0, CurvatureWeight = 1.0 )
        bs2.approximate( Points = r2, DegMin = 1, DegMax = 5, Continuity = 'C1') #, LengthWeight = 1.0, CurvatureWeight = 1.0 )
        Surf = bs1.makeRuledSurface(bs2)
        Surf.increaseDegree(5,5)
        #Part.show(Surf.toShape())
        #RuledSurface = FreeCAD.ActiveDocument.addObject('Part::RuledSurface', 'Ruled Surface')
        #RuledSurface.Curve1=(obj.Rails[0])
        #RuledSurface.Curve2=(obj.Rails[1])
        #App.ActiveDocument.recompute()
        #Surf = RuledSurface.Shape.Surface
        #return
        pts = []
        pts += r1
        pts += r2

        for pro in linkSubList_convertToOldStyle(obj.Profiles):
            sh = self.getShape(pro)
            if sh.Orientation == 'Reversed':
                pts += sh.discretize(Number = obj.ProfilePoints) #[::-1]
            else:
                pts += sh.discretize(Number = obj.ProfilePoints)

        cleanpts = []
        for p in pts:
            if not p in cleanpts:
                cleanpts.append(p)

    #static char* kwds_Parameter[] = {"Surface","Points","Curves","Degree",
        #"NbPtsOnCur","NbIter","Tol2d","Tol3d","TolAng","TolCurv","Anisotropie",NULL};

    #PyObject* surface = 0;
    #PyObject* points = 0;
    #PyObject* curves = 0;
    #int Degree = 3;
    #int NbPtsOnCur = 10;
    #int NbIter = 3;
    #double Tol2d = 0.00001;
    #double Tol3d = 0.0001;
    #double TolAng = 0.01;
    #double TolCurv = 0.1;
    #PyObject* Anisotropie = Py_False;


        plate = Part.PlateSurface( Surface = Surf, Points = cleanpts, Degree = 3, NbIter = obj.Iterations)
        #"Tol3d","MaxSegments","MaxDegree","MaxDistance","CritOrder","Continuity","EnlargeCoeff"
        su = plate.makeApprox(MaxSegments = obj.Segments, MaxDegree = obj.Degree, EnlargeCoeff = 1.0) #Continuity = 'C2',
        sh = su.toShape()
        obj.Shape = sh

        #App.ActiveDocument.removeObject(RuledSurface.Name)

        errors = []
        for p in cleanpts:
            errors.append(sh.distToShape(Part.Vertex(p))[0])
        maxError = max(errors)
        print("\n\nMax Error : "+str(maxError))
        obj.MaxError = maxError

        #App.ActiveDocument.recompute()

        return

    def onChanged(self, fp, prop):
        FreeCAD.Console.PrintMessage("\n"+str(prop)+" changed")
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None


class sweep2R:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj),Part.Edge):
                        res.append((obj.Object,[obj.SubElementNames[i]]))
                        #res.append(obj.SubElementNames[i])
                    i += 1
            else:
                res.append((obj.Object,['']))
        return res

    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        rails = self.parseSel(selection)[0:2]
        profiles = self.parseSel(selection)[2:]
        print(rails)
        print(profiles)

        obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Sweep2Rails")
        sw2r(obj)
        #sw2rVP(obj.ViewObject)
        obj.ViewObject.Proxy=0
        obj.setEditorMode("MaxError", 1)

        obj.Rails = rails
        obj.Profiles = profiles

        FreeCAD.ActiveDocument.recompute()


    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/sw2r.svg', 'MenuText': 'Sweep 2 rails', 'ToolTip': 'Sweep profiles on 2 rails'}

FreeCADGui.addCommand('sw2r2', sweep2R())

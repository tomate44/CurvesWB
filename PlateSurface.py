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
        debug("\nsw2r class init\n")
        
        # List of constraint objects
        obj.addProperty("App::PropertyLinkList",           "Objects",      "PlateSurface", "List of constraint objects")
        
        # Arguments of the PlateSurface algorithm
        obj.addProperty("App::PropertyIntegerConstraint",  "PlateDegree",  "Plate",        "Plate degree")
        obj.addProperty("App::PropertyIntegerConstraint",  "Iterations",   "Plate",        "Number of iterations")
        obj.addProperty("App::PropertyFloat",              "Tol2d",        "Plate",        "2D Tolerance").Tol2d = 0.00001
        obj.addProperty("App::PropertyFloat",              "Tol3d",        "Plate",        "3D Tolerance").Tol3d = 0.0001
        obj.addProperty("App::PropertyFloat",              "TolAngular",   "Plate",        "Angular Tolerance").TolAngular = 0.01
        obj.addProperty("App::PropertyFloat",              "TolCurvature", "Plate",        "Curvature Tolerance").TolCurvature = 0.1
        obj.addProperty("App::PropertyBool",               "Anisotropie",  "Plate",        "Anisotropie").Anisotropie = False
        
        # Arguments of the BSpline approximation
        obj.addProperty("App::PropertyIntegerConstraint",  "MaxDegree",    "Bspline",      "Max degree of Bspline approximation")
        obj.addProperty("App::PropertyIntegerConstraint",  "MaxSegments",  "Bspline",      "Max Number of surface segments")
        obj.addProperty("App::PropertyFloat",              "MaxDistance",  "Bspline",      "Max Distance to plate surface").MaxDistance = 0.0001
        obj.addProperty("App::PropertyFloat",              "Tolerance",    "Bspline",      "3D Tolerance of Bspline approximation").Tolerance = 0.01
        obj.addProperty("App::PropertyIntegerConstraint",  "CritOrder",    "Bspline",      "Criterion Order")
        obj.addProperty("App::PropertyEnumeration",        "Continuity",   "Bspline",      "Desired continuity of the surface").Continuity=["C0","C1","G1","C2","G2","C3","CN"]
        obj.addProperty("App::PropertyFloat",              "EnlargeCoeff", "Bspline",      "Enlarge Coefficient").EnlargeCoeff = 1.1

        obj.Proxy = self
        obj.PlateDegree = ( 3, 3, 25, 1)
        obj.Iterations  = ( 1, 1, 12, 1)
        obj.MaxDegree   = ( 3, 3, 25, 1)
        obj.MaxSegments = ( 3, 1, 50, 1)
        obj.CritOrder   = (-1,-1,  1, 1)
        

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
            

    def getSurface(self, obj):
        for l in obj.Objects:
            if l.Shape.Faces:
                return(l.Shape.Faces[0])
        return(None)

    def getPoints(self, obj):
        pts = []
        for l in obj.Objects:
            try:
                pts += l.Points
            except:
                pts += [v.Point for v in obj.Shape.Vertexes]
        return(pts)

    def execute(self, obj):
        Surf = self.getSurface(obj)
        pts =  self.getPoints(obj)

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

        if Surf:
            plate = Part.PlateSurface( Surface = Surf, Points = cleanpts, Degree = obj.PlateDegree, NbIter = obj.Iterations, Tol2d = obj.Tol2d, Tol3d = obj.Tol3d, TolAng = obj.TolAngular, TolCurv = obj.TolCurvature, Anisotropie = obj.Anisotropie)
        else:
            plate = Part.PlateSurface( Points = cleanpts, Degree = obj.PlateDegree, NbIter = obj.Iterations, Tol2d = obj.Tol2d, Tol3d = obj.Tol3d, TolAng = obj.TolAngular, TolCurv = obj.TolCurvature, Anisotropie = obj.Anisotropie)
        #"Tol3d","MaxSegments","MaxDegree","MaxDistance","CritOrder","Continuity","EnlargeCoeff"
        su = plate.makeApprox( Tol3d = obj.Tolerance, MaxSegments = obj.MaxSegments, MaxDegree = obj.MaxDegree, MaxDistance = obj.MaxDistance, CritOrder = obj.CritOrder, Continuity = obj.Continuity, EnlargeCoeff = obj.EnlargeCoeff)
        sh = su.toShape()
        obj.Shape = sh

        return

    def onChanged(self, fp, prop):
        debug("\n"+str(prop)+" changed")
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

FreeCADGui.addCommand('sw2r', sweep2R())


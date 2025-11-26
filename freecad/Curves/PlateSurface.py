# SPDX-License-Identifier: LGPL-2.1-or-later

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

class plateSurfFP:
    def __init__(self, obj):
        ''' Add the properties '''
        debug("\nplateSurfFP class init\n")
        
        # List of constraint objects
        obj.addProperty("App::PropertyLinkList",           "Objects",      "Plate", "List of constraint objects")
        
        # Arguments of the PlateSurface algorithm
        obj.addProperty("App::PropertyIntegerConstraint",  "PlateDegree",  "Plate",        "Plate degree")
        obj.addProperty("App::PropertyIntegerConstraint",  "Iterations",   "Plate",        "Number of iterations")
        obj.addProperty("App::PropertyFloat",              "Tol2d",        "Plate",        "2D Tolerance")
        obj.addProperty("App::PropertyFloat",              "Tol3d",        "Plate",        "3D Tolerance")
        obj.addProperty("App::PropertyFloat",              "TolAngular",   "Plate",        "Angular Tolerance").TolAngular = 0.1
        obj.addProperty("App::PropertyFloat",              "TolCurvature", "Plate",        "Curvature Tolerance").TolCurvature = 0.1
        obj.addProperty("App::PropertyBool",               "Anisotropie",  "Plate",        "Anisotropie").Anisotropie = False
        
        # Arguments of the BSpline approximation
        obj.addProperty("App::PropertyIntegerConstraint",  "MaxDegree",    "SurfaceApproximation",      "Max degree of Bspline approximation")
        obj.addProperty("App::PropertyIntegerConstraint",  "MaxSegments",  "SurfaceApproximation",      "Max Number of surface segments")
        obj.addProperty("App::PropertyFloat",              "MaxDistance",  "SurfaceApproximation",      "Max Distance to plate surface").MaxDistance = 0.001
        obj.addProperty("App::PropertyFloat",              "Tolerance",    "SurfaceApproximation",      "3D Tolerance of Bspline approximation").Tolerance = 0.01
        obj.addProperty("App::PropertyIntegerConstraint",  "CritOrder",    "SurfaceApproximation",      "Criterion Order")
        obj.addProperty("App::PropertyEnumeration",        "Continuity",   "SurfaceApproximation",      "Desired continuity of the surface").Continuity=["C0","C1","C2"]
        obj.addProperty("App::PropertyFloat",              "EnlargeCoeff", "SurfaceApproximation",      "Enlarge Coefficient").EnlargeCoeff = 1.1

        obj.Proxy = self
        obj.PlateDegree = ( 3, 3, 25, 1)
        obj.Iterations  = ( 1, 1, 12, 1)
        obj.MaxDegree   = ( 3, 3, 25, 1)
        obj.MaxSegments = ( 3, 1, 50, 1)
        obj.CritOrder   = ( 0,-1,  1, 1)
        obj.Continuity  = "C1"
        obj.Tol2d = 0.00001
        obj.Tol3d = 0.0001
        

    def getSurface(self, obj):
        for l in obj.Objects:
            if l.Shape.Faces:
                return(l.Shape.Faces[0].Surface)
        return(None)

    def getPoints(self, obj):
        pts = []
        for l in obj.Objects:
            try:
                pts += l.Points
            except:
                pts += [v.Point for v in l.Shape.Vertexes]
        debug("Found %d points"%(len(pts)))
        return(pts)

    def execute(self, obj):
        self.Surf = self.getSurface(obj)
        pts =  self.getPoints(obj)

        self.cleanpts = []
        for p in pts:
            if not p in self.cleanpts:
                self.cleanpts.append(p)

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

        if self.Surf:
            debug("Found surface : %s"%str(self.Surf))
            self.plate = Part.PlateSurface( Surface = self.Surf, Points = self.cleanpts, Degree = obj.PlateDegree, NbIter = obj.Iterations, Tol2d = obj.Tol2d, Tol3d = obj.Tol3d)# TolAng = obj.TolAngular, TolCurv = obj.TolCurvature, Anisotropie = obj.Anisotropie
            #self.plate = Part.PlateSurface( Surface = self.Surf, Points = self.cleanpts)
        elif self.cleanpts:
            debug("No surface")
            self.plate = Part.PlateSurface( Points = self.cleanpts, Degree = obj.PlateDegree, NbIter = obj.Iterations) #, Tol2d = obj.Tol2d) #, Tol3d = obj.Tol3d) #, TolAng = obj.TolAngular, TolCurv = obj.TolCurvature, Anisotropie = obj.Anisotropie)
        #"Tol3d","MaxSegments","MaxDegree","MaxDistance","CritOrder","Continuity","EnlargeCoeff"
        debug("makeApprox")
        self.su = self.plate.makeApprox( Tol3d = obj.Tolerance, MaxSegments = obj.MaxSegments, MaxDegree = obj.MaxDegree, MaxDistance = obj.MaxDistance, CritOrder = obj.CritOrder, Continuity = obj.Continuity, EnlargeCoeff = obj.EnlargeCoeff)
        sh = self.su.toShape()
        obj.Shape = sh

        return

    def onChanged(self, fp, prop):
        debug("%s changed"%(str(prop)))
        if prop == "Continuity":
            debug(fp.Continuity)
            if (fp.Continuity == "C2") and (fp.MaxDegree < 5):
                fp.MaxDegree = 5
        if prop == "Tol3d":
            if fp.Tol3d > 0.002:
                fp.Tol3d = 0.002

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return None

        def loads(self, state):
            return None

    else:
        def __getstate__(self):
            return None

        def __setstate__(self, state):
            return None


class Plate:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            res.append(obj)
        return res

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        objs = self.parseSel(selection)

        obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Plate Surface")
        plateSurfFP(obj)
        obj.Objects = objs
        obj.ViewObject.Proxy=0
        #obj.setEditorMode("MaxError", 1)

        #FreeCAD.ActiveDocument.recompute()


    def GetResources(self):
        return {'Pixmap': path_curvesWB_icons+'/sw2r.svg',
                'MenuText': 'Plate Surface',
                'ToolTip': 'Plate Surface'}

FreeCADGui.addCommand('Plate', Plate())


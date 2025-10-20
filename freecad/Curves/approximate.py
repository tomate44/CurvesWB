# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Approximate"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Approximate a set of points."

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'approximate.svg')
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

# ********************************************************
# **** Part.BSplineCurve.approximate() documentation *****
# ********************************************************

# Replaces this B-Spline curve by approximating a set of points.
# The function accepts keywords as arguments.

# approximate2(Points = list_of_points)

# Optional arguments :

# DegMin = integer (3) : Minimum degree of the curve.
# DegMax = integer (8) : Maximum degree of the curve.
# Tolerance = float (1e-3) : approximating tolerance.
# Continuity = string ('C2') : Desired continuity of the curve.
# Possible values : 'C0','G1','C1','G2','C2','C3','CN'

# LengthWeight = float, CurvatureWeight = float, TorsionWeight = float
# If one of these arguments is not null, the functions approximates the
# points using variational smoothing algorithm, which tries to minimize
# additional criterium:
# LengthWeight*CurveLength + CurvatureWeight*Curvature + TorsionWeight*Torsion
# Continuity must be C0, C1 or C2, else defaults to C2.

# Parameters = list of floats : knot sequence of the approximated points.
# This argument is only used if the weights above are all null.

# ParamType = string ('Uniform','Centripetal' or 'ChordLength')
# Parameterization type. Only used if weights and Parameters above aren't specified.

# Note : Continuity of the spline defaults to C2. However, it may not be applied if
# it conflicts with other parameters ( especially DegMax ).    parametrization


class Approximate:
    def __init__(self, obj, source):
        ''' Add the properties '''
        debug("\nApproximate class Init\n")
        obj.addProperty("App::PropertyLink", "PointObject", "Approximate",
                        "Object containing the points to approximate").PointObject = source
        obj.addProperty("App::PropertyBool", "ClampEnds", "General",
                        "Clamp endpoints").ClampEnds = False
        obj.addProperty("App::PropertyBool", "Closed", "General",
                        "Force a closed curve").Closed = False
        obj.addProperty("App::PropertyInteger", "DegreeMin", "General",
                        "Minimum degree of the curve").DegreeMin = 3
        obj.addProperty("App::PropertyInteger", "DegreeMax", "General",
                        "Maximum degree of the curve").DegreeMax = 5
        obj.addProperty("App::PropertyFloat", "ApproxTolerance", "General",
                        "Approximation tolerance")
        obj.addProperty("App::PropertyEnumeration", "Continuity", "General",
                        "Desired continuity of the curve").Continuity = ["C0", "C1", "G1", "C2", "G2", "C3", "CN"]
        obj.addProperty("App::PropertyEnumeration", "Method", "General",
                        "Approximation method").Method = ["Parametrization", "Smoothing Algorithm"]
        obj.addProperty("App::PropertyEnumeration", "Parametrization", "Parameters",
                        "Parametrization type").Parametrization = ["ChordLength", "Centripetal", "Uniform", "Curvilinear"]
        obj.addProperty("App::PropertyFloatConstraint", "LengthWeight", "Parameters",
                        "Weight of curve length for smoothing algorithm").LengthWeight = 1.0
        obj.addProperty("App::PropertyFloatConstraint", "CurvatureWeight", "Parameters",
                        "Weight of curve curvature for smoothing algorithm").CurvatureWeight = 1.0
        obj.addProperty("App::PropertyFloatConstraint", "TorsionWeight", "Parameters",
                        "Weight of curve torsion for smoothing algorithm").TorsionWeight = 1.0
        obj.addProperty("App::PropertyInteger", "FirstIndex", "Range",
                        "Index of first point").FirstIndex = 0
        obj.addProperty("App::PropertyInteger", "LastIndex", "Range",
                        "Index of last point (-1 to ignore)")
        obj.addProperty("App::PropertyInteger", "StartOffset", "Range",
                        "For closed curves, allows to choose the location of the join point").StartOffset = 0
        # obj.addProperty("App::PropertyVectorList",   "Points",    "Approximate",   "Points")
        # obj.addProperty("Part::PropertyPartShape",   "Shape",     "Approximate",   "Shape")
        obj.Proxy = self
        self.obj = obj
        self.Points = []
        obj.LengthWeight = (1.0, 0.01, 10.0, 0.1)
        obj.CurvatureWeight = (1.0, 0.01, 10.0, 0.1)
        obj.TorsionWeight = (1.0, 0.01, 10.0, 0.1)
        obj.Method = "Parametrization"
        obj.Parametrization = "ChordLength"
        obj.Continuity = 'C2'
        obj.LastIndex = -1
        self.getPoints(obj)
        self.setTolerance(obj)
        # obj.ApproxTolerance = 0.05
        
        # self.execute(obj)

    def setTolerance(self, obj):
        try:
            le = obj.PointObject.Shape.BoundBox.DiagonalLength
            obj.ApproxTolerance = le / 10000.0
        except AttributeError:
            obj.ApproxTolerance = 0.001

    def getPoints(self, obj):
        if hasattr(obj.PointObject, 'Group'):
            a = []
            for o in obj.PointObject.Group:
                if hasattr(o, 'Points'):
                    a.append(o.Points)
                else:
                    a.append([v.Point for v in o.Shape.Vertexes])
            self.Points = a
        elif hasattr(obj.PointObject, 'ProfileSamples'):
            numVert = len(obj.PointObject.Shape.Vertexes)
            debug("Surface object detected")
            debug("%d points" % numVert)
            # n = numVert / obj.PointObject.ProfileSamples
            a = []
            r = []
            for i in range(numVert):
                r.append(obj.PointObject.Shape.Vertexes[i].Point)
                if (not i == 0) and ((i + 1) % obj.PointObject.ProfileSamples == 0):
                    a.append(r)
                    r = []
            # a.append(r)
            if not a == []:
                self.Points = a
                debug("Array : %d x %d" % (len(a), len(a[0])))
            else:
                self.Points = []
        elif hasattr(obj.PointObject, 'Points'):
            if isinstance(obj.PointObject.Points, (list, tuple)):
                self.Points = obj.PointObject.Points
            elif hasattr(obj.PointObject.Points, 'Points'):
                self.Points = obj.PointObject.Points.Points
        elif hasattr(obj.PointObject.Shape, 'OrderedVertexes'):
            self.Points = [v.Point for v in obj.PointObject.Shape.OrderedVertexes]
        else:
            self.Points = [v.Point for v in obj.PointObject.Shape.Vertexes]
        if obj.Closed:
            if not obj.StartOffset == 0:
                if self.Points[0] == self.Points[-1]:
                    self.Points = self.Points[:-1]
                self.Points = self.Points[obj.StartOffset:] + self.Points[:obj.StartOffset]
            if not self.Points[0] == self.Points[-1]:
                self.Points.append(self.Points[0])
        if (len(self.Points) < (obj.LastIndex + 1)) and obj.LastIndex >= 0:
            obj.LastIndex = len(self.Points) - 1
        debug("extracted {} point objects".format(len(self.Points)))

    def buildCurve(self, obj):
        if obj.LastIndex > 0:
            pts = self.Points[obj.FirstIndex:obj.LastIndex + 1]
        else:
            pts = self.Points[obj.FirstIndex:]
        bs = Part.BSplineCurve()
        if (obj.Method == "Parametrization") and (obj.Parametrization == "Curvilinear") and (hasattr(obj.PointObject, "Distance")):
            params = []
            try:
                dis = obj.PointObject.Distance
            except AttributeError:
                dis = 1.0
            for i in range(len(pts)):
                params.append(1.0 * i * dis)
            lv = pts[-1].sub(pts[-2])
            params[-1] = params[-2] + lv.Length
            bs.interpolate(Points=pts, Parameters=params, Tolerance=obj.ApproxTolerance)

        elif obj.Method == "Parametrization":
            bs.approximate(Points=pts, DegMin=obj.DegreeMin, DegMax=obj.DegreeMax, Tolerance=obj.ApproxTolerance, Continuity=obj.Continuity,
                           ParamType=obj.Parametrization)
        elif obj.Method == "Smoothing Algorithm":
            bs.approximate(Points=pts, DegMin=obj.DegreeMin, DegMax=obj.DegreeMax, Tolerance=obj.ApproxTolerance, Continuity=obj.Continuity,
                           LengthWeight=obj.LengthWeight, CurvatureWeight=obj.CurvatureWeight, TorsionWeight=obj.TorsionWeight)
        if obj.ClampEnds:
            bs.setPole(1, self.Points[0])
            bs.setPole(int(bs.NbPoles), self.Points[-1])
        self.curve = bs

    def buildSurf(self, obj):
        if obj.LastIndex > 0:
            pts = self.Points[obj.FirstIndex:obj.LastIndex + 1]
        else:
            pts = self.Points[obj.FirstIndex:]
        bs = Part.BSplineSurface()
        cont = 0
        if obj.Continuity == 'C1':
            cont = 1
        elif obj.Continuity == 'C2':
            cont = 2
        if obj.Method == "Parametrization":
            bs.approximate(Points=pts, DegMin=obj.DegreeMin, DegMax=obj.DegreeMax, Tolerance=obj.ApproxTolerance, Continuity=cont,
                           ParamType=obj.Parametrization)
        elif obj.Method == "Smoothing Algorithm":
            bs.approximate(Points=pts, DegMin=obj.DegreeMin, DegMax=obj.DegreeMax, Tolerance=obj.ApproxTolerance, Continuity=cont,
                           LengthWeight=obj.LengthWeight, CurvatureWeight=obj.CurvatureWeight, TorsionWeight=obj.TorsionWeight)
        self.curve = bs

    def execute(self, obj):
        debug("\n* Approximate : execute *\n")
        self.getPoints(obj)
        if isinstance(self.Points[0], list):
            self.buildSurf(obj)
        else:
            self.buildCurve(obj)
        obj.Shape = self.curve.toShape()

    def onChanged(self, fp, prop):
        if 'Restore' in fp.State:
            return
        if not fp.PointObject:
            return
        if prop == "PointObject":
            debug("Approximate : PointObject changed\n")
            self.getPoints(fp)

        if prop == "Parametrization":
            debug("Approximate : Parametrization changed\n")
            props = ["ClampEnds", "DegreeMin", "DegreeMax", "Continuity"]
            if fp.Parametrization == "Curvilinear":
                if hasattr(fp.PointObject, "Distance"):
                    for p in props:
                        fp.setEditorMode(p, 2)
                else:
                    fp.Parametrization == "ChordLength"
            else:
                for p in props:
                    fp.setEditorMode(p, 0)

        if prop == "Method":
            debug("Approximate : Method changed\n")
            if fp.Method == "Parametrization":
                fp.setEditorMode("Parametrization", 0)
                fp.setEditorMode("LengthWeight", 2)
                fp.setEditorMode("CurvatureWeight", 2)
                fp.setEditorMode("TorsionWeight", 2)
            elif fp.Method == "Smoothing Algorithm":
                fp.setEditorMode("Parametrization", 2)
                fp.setEditorMode("LengthWeight", 0)
                fp.setEditorMode("CurvatureWeight", 0)
                fp.setEditorMode("TorsionWeight", 0)
                if fp.Continuity in ["C3", "CN"]:
                    fp.Continuity = 'C2'

        if prop == "Continuity":
            if fp.Method == "Smoothing Algorithm":
                if fp.Continuity == 'C1':
                    if fp.DegreeMax < 3:
                        fp.DegreeMax = 3
                elif fp.Continuity in ['G1', 'G2', 'C2']:
                    if fp.DegreeMax < 5:
                        fp.DegreeMax = 5
            debug("Approximate : Continuity changed to " + str(fp.Continuity))

        if prop == "DegreeMin":
            if fp.DegreeMin < 1:
                fp.DegreeMin = 1
            elif fp.DegreeMin > fp.DegreeMax:
                fp.DegreeMin = fp.DegreeMax
            debug("Approximate : DegreeMin changed to " + str(fp.DegreeMin))
        if prop == "DegreeMax":
            if fp.DegreeMax < fp.DegreeMin:
                fp.DegreeMax = fp.DegreeMin
            elif fp.DegreeMax > 14:
                fp.DegreeMax = 14
            if fp.Method == "Smoothing Algorithm":
                if fp.Continuity in ['G1', 'G2', 'C2']:
                    if fp.DegreeMax < 5:
                        fp.DegreeMax = 5
                elif fp.Continuity == "C1":
                    if fp.DegreeMax < 3:
                        fp.DegreeMax = 3
            debug("Approximate : DegreeMax changed to " + str(fp.DegreeMax))
        if prop == "ApproxTolerance":
            if fp.ApproxTolerance < 1e-6:
                fp.ApproxTolerance = 1e-6
            elif fp.ApproxTolerance > 1000.0:
                fp.ApproxTolerance = 1000.0
            debug("Approximate : ApproxTolerance changed to " + str(fp.ApproxTolerance))

        if prop == "FirstIndex":
            if fp.FirstIndex < 0:
                fp.FirstIndex = 0
            elif fp.FirstIndex > fp.LastIndex - 1:
                fp.FirstIndex = fp.LastIndex - 1
            debug("Approximate : FirstIndex changed to " + str(fp.FirstIndex))
        if prop == "LastIndex":
            if (fp.LastIndex >= 0) and (fp.LastIndex < fp.FirstIndex + 1):
                fp.LastIndex = fp.FirstIndex + 1
            if hasattr(self, "Points") and fp.LastIndex > len(self.Points) - 1:
                fp.LastIndex = len(self.Points) - 1
            debug("Approximate : LastIndex changed to " + str(fp.LastIndex))
        if prop == "Closed":
            debug("Approximate : Closed changed\n")
            if fp.Closed:
                fp.setEditorMode("StartOffset", 0)
            else:
                fp.setEditorMode("StartOffset", 2)

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            self.Points = False
            return dict()

        def loads(self, state):
            return None

    else:
        def __getstate__(self):
            self.Points = False
            return dict()

        def __setstate__(self, state):
            return None


class ViewProviderApp:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def setEdit(self, vobj, mode):
        return False

    def unsetEdit(self, vobj, mode):
        return

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    def claimChildren(self):
        return [self.Object.PointObject]

    def onDelete(self, feature, subelements):
        try:
            self.Object.PointObject.ViewObject.Visibility = True
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: {0} \n".format(err))
        return True


class approx:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if hasattr(obj.Object, 'Group'):
                return obj.Object
            elif hasattr(obj.Object, "Shape") and len(obj.Object.Shape.Vertexes) > 1:
                res.append(obj.Object)
            elif hasattr(obj.Object, "Points"):
                res.append(obj.Object)
        if res:
            return res
        else:
            FreeCAD.Console.PrintMessage("\nPlease select an object that has at least 2 vertexes")
        return None

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        try:
            ordered = FreeCADGui.activeWorkbench().Selection
            if ordered:
                s = ordered
        except AttributeError:
            pass
        source = self.parseSel(s)
        if not source:
            return False
        if not isinstance(source, list):
            obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Approximation_Surface")
            Approximate(obj, source)
            ViewProviderApp(obj.ViewObject)
            # s.ViewObject.Visibility = False
        else:
            for s in source:
                obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Approximation_Curve")
                Approximate(obj, s)
                ViewProviderApp(obj.ViewObject)
                s.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Approximate',
                'ToolTip': 'Approximate points to NURBS curve or surface'}


FreeCADGui.addCommand('Approximate', approx())




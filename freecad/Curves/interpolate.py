# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Interpolate"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Interpolate a set of points."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'interpolate.svg')
# debug = _utils.debug
debug = _utils.doNothing


# ********************************************************
# **** Part.BSplineCurve.interpolate() documentation *****
# ********************************************************

# Replaces this B-Spline curve by interpolating a set of points.
# The function accepts keywords as arguments.

# interpolate(Points = list_of_points)

# Optional arguments :

# PeriodicFlag = bool (False) : Sets the curve closed or opened.
# Tolerance = float (1e-6) : interpolating tolerance

# Parameters : knot sequence of the interpolated points.
# If not supplied, the function defaults to chord-length parameterization.
# If PeriodicFlag == True, one extra parameter must be appended.

# EndPoint Tangent constraints :

# InitialTangent = vector, FinalTangent = vector
# specify tangent vectors for starting and ending points
# of the BSpline. Either none, or both must be specified.

# Full Tangent constraints :

# Tangents = list_of_vectors, TangentFlags = list_of_bools
# Both lists must have the same length as Points list.
# Tangents specifies the tangent vector of each point in Points list.
# TangentFlags (bool) activates or deactivates the corresponding tangent.
# These arguments will be ignored if EndPoint Tangents (above) are also defined.

# Note : Continuity of the spline defaults to C2. However, if periodic, or tangents
# are supplied, the continuity will drop to C1.


class Interpolate:
    def __init__(self, obj, source):
        ''' Add the properties '''
        debug("\nInterpolate class Init\n")
        obj.addProperty("App::PropertyLink",           "Source",         "General",    "Source object that provides points to interpolate")
        obj.addProperty("App::PropertyLinkSubList",    "PointList",      "General",    "Point list to interpolate")
        obj.addProperty("App::PropertyBool",           "Periodic",       "General",    "Set the curve closed").Periodic = False
        obj.addProperty("App::PropertyFloat",          "Tolerance",      "General",    "Interpolation tolerance").Tolerance = 1e-7
        obj.addProperty("App::PropertyBool",           "CustomTangents", "General",    "User specified tangents").CustomTangents = False
        obj.addProperty("App::PropertyBool",           "DetectAligned",  "General",    "interpolate 3 aligned points with a line").DetectAligned = False
        obj.addProperty("App::PropertyBool",           "Polygonal",      "General",    "interpolate with a degree 1 polygonal curve").Polygonal = False
        obj.addProperty("App::PropertyInteger",        "StartOffset",    "General",    "Offset the start index of the point list").StartOffset = 0
        obj.addProperty("App::PropertyBool",           "WireOutput",     "Parameters", "outputs a wire or a single edge").WireOutput = False
        obj.addProperty("App::PropertyFloatList",      "Parameters",     "Parameters", "Parameters of interpolated points")
        obj.addProperty("App::PropertyEnumeration",    "Parametrization","Parameters", "Parametrization type")
        obj.addProperty("App::PropertyVectorList",     "Tangents",       "General",    "Tangents at interpolated points")
        obj.addProperty("App::PropertyBoolList",       "TangentFlags",   "General",    "Activation flag of tangents")
        obj.addProperty("App::PropertyLinkSub", "FaceSupport", "Spiral", "Face support of the spiral")
        obj.addProperty("App::PropertyInteger", "UTurns", "Spiral", "Nb of turns between 2 points, in U direction").UTurns = 0
        obj.addProperty("App::PropertyInteger", "VTurns", "Spiral", "Nb of turns between 2 points, in V direction").VTurns = 0
        obj.Parametrization = ["ChordLength", "Centripetal", "Uniform", "Custom"]
        obj.Proxy = self
        if isinstance(source, (list, tuple)):
            obj.PointList = source
            obj.setEditorMode("Source", 2)
        else:
            obj.Source = source
            obj.setEditorMode("PointList", 2)
        obj.Parametrization = "ChordLength"
        # obj.setEditorMode("CustomTangents", 2)
        obj.setEditorMode("DetectAligned", 2)

    def getSupportface(self, obj):
        if len(obj.FaceSupport) == 2:
            surf = obj.FaceSupport[0].getSubObject(obj.FaceSupport[1][0])
            print(f"Surface detected : {surf}")
            return surf

    def getPoints(self, obj):
        vl = self.getVertexes(obj)
        if not isinstance(vl, (list, tuple)):
            return []
        pts = [v.Point for v in vl if isinstance(v, Part.Vertex)]
        off = 0
        if hasattr(obj, "StartOffset"):
            off = obj.StartOffset
        return pts[off:] + pts[:off]

    def getVertexes(self, obj):
        try:
            if obj.Source:
                if hasattr(obj.Source.Shape, "OrderedVertexes"):
                    return obj.Source.Shape.OrderedVertexes
                else:
                    return obj.Source.Shape.Vertexes
            elif obj.PointList:
                return _utils.getShape(obj, "PointList", "Vertex")
        except Exception as exc:
            print(str(exc))
            return []

    def detect_aligned_pts(self, fp, pts):
        tol = .99
        tans = fp.Tangents
        flags = [False] * len(pts)  # list(fp.TangentFlags)
        for i in range(len(pts) - 2):
            v1 = pts[i + 1] - pts[i]
            v2 = pts[i + 2] - pts[i + 1]
            l1 = v1.Length
            l2 = v2.Length
            v1.normalize()
            v2.normalize()
            if v1.dot(v2) > tol:
                debug("aligned points detected : {} - {} - {}".format(i, i + 1, i + 2))
                tans[i] = v1.multiply(l1 / 3.0)
                tans[i + 2] = v2.multiply(l2 / 3.0)
                tans[i + 1] = (v1 + v2).multiply(min(l1, l2) / 6.0)
                flags[i] = True
                flags[i + 1] = True
                flags[i + 2] = True
        fp.Tangents = tans
        fp.TangentFlags = flags

    def periodic_interpolate(self, pts, params, tol):
        nbp = len(pts)
        n = 1
        if nbp <= 4:
            n = 2
        npts = pts
        npts.extend(pts * (2 * n))
        period = params[-1] - params[0]
        nparams = []
        for p in params:
            for i in range(1, n + 1):
                nparams.append(p)
                nparams.append(p - i * period)
                nparams.append(p + i * period)
        npars = list(set(nparams))
        npars.sort()
        # interpolate the extended list of points
        bs = Part.BSplineCurve()
        bs.interpolate(Points=npts, Parameters=npars, PeriodicFlag=True)
        # extract a one turn BSpline curve in the middle
        offset = n * nbp
        npoles = bs.getPoles()[offset:-offset - 1]
        nmults = bs.getMultiplicities()[offset:-offset]
        nknots = bs.getKnots()[offset:-offset]
        nbs = Part.BSplineCurve()
        nbs.buildFromPolesMultsKnots(npoles, nmults, nknots, True, 3)
        return nbs

    def execute(self, obj):
        debug("* Interpolate : execute *")
        pts = self.getPoints(obj)
        if abs(obj.UTurns) + abs(obj.VTurns) > 0:
            f = self.getSupportface(obj)
            s = f.Surface
            if s is not None:
                u0, u1, v0, v1 = s.bounds()
                eps = 1e-3
                p2l = []
                for i in range(len(pts)):
                    s1, t1 = s.parameter(pts[i])
                    s2, t2 = s1, t1
                    if s.isUPeriodic():
                        if abs(u1 - s1) < eps:
                            s1 -= u1 - u0
                        s2 = s1 + (i + 1) * obj.UTurns * (u1 - u0)
                    if s.isVPeriodic():
                        if abs(v1 - t1) < eps:
                            t1 -= v1 - v0
                        t2 = t1 + (i + 1) * obj.VTurns * (v1 - v0)
                    if f.isPartOfDomain(s2, t2):
                        p2l.append(FreeCAD.Base.Vector2d(s2, t2))
                    #elif f.isPartOfDomain(s2, t1):
                        #p2l.append(FreeCAD.Base.Vector2d(s2, t1))
                    #elif f.isPartOfDomain(s1, t2):
                        #p2l.append(FreeCAD.Base.Vector2d(s1, t2))
                if len(p2l) > 1:
                    bs = Part.Geom2d.BSplineCurve2d()
                    bs.interpolate(p2l)
                    edges = [bs.toShape(s)]
                    obj.Shape = Part.Wire(edges)
                    return
        self.setParameters(obj)
        if obj.Polygonal:
            if obj.Periodic:
                pts.append(pts[0])
            poly = Part.makePolygon(pts)
            if obj.WireOutput:
                obj.Shape = poly
                return
            else:
                bs = poly.approximate(1e-8, obj.Tolerance, 999, 1)
        else:
            if obj.Periodic:
                bs = self.periodic_interpolate(pts, obj.Parameters, obj.Tolerance)
            else:
                bs = Part.BSplineCurve()
                bs.interpolate(Points=pts, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance, Parameters=obj.Parameters)
            if not (len(obj.Tangents) == len(pts) and len(obj.TangentFlags) == len(pts)):  # or obj.DetectAligned:
                if obj.Periodic:
                    obj.Tangents = [bs.tangent(p)[0] for p in obj.Parameters[0:-1]]
                else:
                    obj.Tangents = [bs.tangent(p)[0] for p in obj.Parameters]
                obj.TangentFlags = [True] * len(pts)
            if obj.CustomTangents:  # or obj.DetectAligned:
                # if obj.DetectAligned:
                # self.detect_aligned_pts(obj, pts)
                bs.interpolate(Points=pts, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance, Parameters=obj.Parameters,
                               Tangents=obj.Tangents, TangentFlags=obj.TangentFlags)  # Scale=False)
        obj.Shape = bs.toShape()

    def setParameters(self, obj):
        # Computes a knot Sequence for a set of points
        # fac (0-1) : parameterization factor
        # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        pts = self.getPoints(obj)
        val = 1.0  # Chord-length
        if obj.Parametrization == "Custom":
            return
        elif obj.Parametrization == "Centripetal":
            val = 0.5
        elif obj.Parametrization == "Uniform":
            val = 0.0
        if obj.Periodic and pts[0].distanceToPoint(pts[-1]) > 1e-7:  # we need to add the first point as the end point
            pts.append(pts[0])
        obj.Parameters = self.parametrization(pts, val)

    def parametrization(self, pts, val):
        params = [0]
        for i in range(1, len(pts)):
            p = pts[i].sub(pts[i - 1])
            pl = pow(p.Length, val)
            params.append(params[-1] + pl)
        m = float(max(params))
        return [p / m for p in params]

    def touch_parametrization(self, fp):
        p = fp.Parametrization
        fp.Parametrization = p

    def onChanged(self, fp, prop):
        if 'Restore' in fp.State:
            return
        pts = self.getPoints(fp)
        if not pts:
            return
        if prop in ("Parametrization", "Source", "PointList"):
            # debug("Approximate : Parametrization changed\n")
            if fp.Parametrization == "Custom":
                fp.setEditorMode("Parameters", 0)
            else:
                fp.setEditorMode("Parameters", 2)
                self.setParameters(fp)
        if prop == "Polygonal":
            group = ["CustomTangents", "DetectAligned", "Parameters", "Parametrization", "Tangents", "TangentFlags"]
            if fp.Polygonal:
                _utils.setEditorMode(fp, group, 2)
                fp.setEditorMode("WireOutput", 0)
            else:
                _utils.setEditorMode(fp, group, 0)
                fp.setEditorMode("WireOutput", 2)
        if prop in ["Periodic", "PointList"]:
            self.touch_parametrization(fp)
        if prop == "StartOffset":
            minidx = -len(pts)
            maxidx = len(pts) - 1
            if fp.StartOffset < minidx:
                fp.StartOffset = minidx
            if fp.StartOffset > maxidx:
                fp.StartOffset = maxidx

    def onDocumentRestored(self, fp):
        fp.setEditorMode("CustomTangents", 2)
        self.touch_parametrization(fp)
        if not hasattr(fp, "StartOffset"):
            fp.addProperty("App::PropertyInteger",
                           "StartOffset",
                           "General",
                           "Offset the start index of the point list").StartOffset = 0


class ViewProviderInterpolate:
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

    # def claimChildren(self):
        # return [self.Object.PointObject]

    # def onDelete(self, feature, subelements):
        # try:
            # self.Object.PointObject.ViewObject.Visibility=True
        # except Exception as err:
            # FreeCAD.Console.PrintError("Error in onDelete: {0} \n".format(err))
        # return True


class interpolate:
    def parseSel(self, selectionObject):
        verts = list()
        for obj in selectionObject:
            if obj.HasSubObjects:
                FreeCAD.Console.PrintMessage("object has subobjects {}\n".format(obj.SubElementNames))
                for n in obj.SubElementNames:
                    if 'Vertex' in n:
                        verts.append((obj.Object, [n]))
            else:
                # FreeCAD.Console.PrintMessage("object has no subobjects\n")
                verts = obj.Object
        if verts:
            return verts
        else:
            FreeCAD.Console.PrintMessage("\nPlease select an object that has at least 2 vertexes\n")
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
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Interpolation_Curve")
        Interpolate(obj, source)
        ViewProviderInterpolate(obj.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Interpolate', interpolate())

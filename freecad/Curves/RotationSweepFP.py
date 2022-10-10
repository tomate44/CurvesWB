# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import curves_to_surface as CTS
from freecad.Curves import SweepPath
from freecad.Curves import ICONPATH

err = FreeCAD.Console.PrintError
warn = FreeCAD.Console.PrintWarning
message = FreeCAD.Console.PrintMessage
TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')
# debug = _utils.debug
# debug = _utils.doNothing


"""Class BSplineFacade is a collection of functions
that work both on BSpline curves and BSpline surfaces.
The geom argument of the functions is either :
- a BSpline Curve
- U or V dimension of a BSpline Surface in the form (surf, 0 or 1)
"""


def getDegree(geom):
    "Returns the degree of the BSpline geom"
    if isinstance(geom, Part.BSplineCurve):
        return geom.Degree
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            return geom[0].UDegree
        elif geom[1] == 1:
            return geom[0].VDegree


def getKnots(geom):
    "Returns the knots of the BSpline geom"
    if isinstance(geom, Part.BSplineCurve):
        return geom.getKnots()
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            return geom[0].getUKnots()
        elif geom[1] == 1:
            return geom[0].getVKnots()


def getMults(geom):
    "Returns the multiplicities of the BSpline geom"
    if isinstance(geom, Part.BSplineCurve):
        return geom.getMultiplicities()
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            return geom[0].getUMultiplicities()
        elif geom[1] == 1:
            return geom[0].getVMultiplicities()


def incDegree(geom, d):
    """incDegree(geom, d)
    Raise the degree of the BSpline geom to d
    """
    if isinstance(geom, Part.BSplineCurve):
        geom.increaseDegree(d)
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            geom[0].increaseDegree(d, geom[0].VDegree)
        elif geom[1] == 1:
            geom[0].increaseDegree(geom[0].UDegree, d)


def insKnotsMults(geom, knots, mults, tol=1e-10, add=False):
    """insKnots(geom, knots, mults, tol=1e-10, add=False)
    Inserts the knots and mults into the BSpline geom
    """
    message(f"insKnotsMults: {geom}\n")
    # geom.scaleKnotsToBounds()
    # print(knots)
    # print(mults)
    # print(getKnots(geom))
    # print(getMults(geom))
    # print(geom.getPoles())
    if isinstance(geom, Part.BSplineCurve):
        geom.insertKnots(knots, mults, tol, add)
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            geom[0].insertUKnots(knots, mults, tol, add)
        elif geom[1] == 1:
            geom[0].insertVKnots(knots, mults, tol, add)
    # return geom


def syncDegree(geo1, geo2):
    """syncDegree(geo1, geo2)
    Raise the degree of one of the BSpline geoms
    to match the other one.
    """
    d1 = getDegree(geo1)
    d2 = getDegree(geo2)
    if d1 > d2:
        incDegree(geo2, d1)
    elif d2 > d1:
        incDegree(geo1, d2)


def syncAllDegrees(*geo_list):
    """syncAllDegrees(geo_list)
    Raise the degree of the BSpline geoms
    the highest one.
    """
    deg = max([getDegree(g) for g in geo_list])
    for geo in geo_list:
        incDegree(geo, deg)


def insKnots(geo1, geo2, tol=1e-10, add=False):
    """insKnots(geo1, geo2, tol=1e-10, add=False)
    Inserts the knots and mults of geo2 into the BSpline geo1
    """
    knots = getKnots(geo2)
    mults = getMults(geo2)
    # print(knots, mults)
    insKnotsMults(geo1, knots, mults, tol, add)


def syncKnots(geo1, geo2, tol=1e-10):
    """syncKnots(geo1, geo2, tol=1e-10)
    Mutual knots insertion (geo1 and geo2 are modified)
    to make the 2 BSpline geometries compatible.
    """
    # k = getKnots(geo1)
    # m = getMults(geo1)
    # k2 = getKnots(geo2)
    # m2 = getMults(geo2)
    geo3 = geo1
    insKnots(geo1, geo2, tol, False)
    insKnots(geo2, geo3, tol, False)


def syncAllKnots(geo_list, tol=1e-10):
    """syncAllKnots(geo_list, tol=1e-10)
    Knots insertion to make the BSpline geometries compatible.
    """
    for geo in geo_list[1:]:
        insKnots(geo_list[0], geo, tol, False)
    for geo in geo_list[1:]:
        insKnots(geo, geo_list[0], tol, False)


def normalize(geom):
    """normalize([bpline_objects, ...])
    Batch normalize knots of supplied bspline geometries.
    works on curves and surfaces.
    """
    for g in geom:
        g.scaleKnotsToBounds()


def contact_points(curve, pt1, pt2):
    """contact_points(bspline_curve, pt1, pt2)
    Trim or extend bspline_curve to contact points.
    The bspline_curve is also oriented from pt1 to pt2
    """
    p1 = curve.parameter(pt1)
    p2 = curve.parameter(pt2)
    fp = curve.FirstParameter
    lp = curve.LastParameter
    if p1 > p2:
        curve.reverse()
        contact_points(curve, pt1, pt2)
        return
    if p1 == fp:
        curve.setPole(1, pt1)
    if p2 == lp:
        curve.setPole(curve.NbPoles, pt2)
    try:
        curve.segment(p1, p2)
    except Part.OCCError:
        err(f"Failed to segment BSpline curve ({fp}, {lp})\n")
        err(f"between ({p1}, {p2})\n")
    curve.scaleKnotsToBounds()


def contact_shapes(bscurve, shape1, shape2):
    """contact_shapes(bspline_curve, shape1, shape2)
    Trim or extend bspline_curve to contact shapes.
    The bspline_curve is also oriented from shape1 to shape2
    """
    edge = bscurve.toShape()
    pt1 = edge.distToShape(shape1)[1][0][1]
    pt2 = edge.distToShape(shape2)[1][0][1]
    contact_points(bscurve, pt1, pt2)


class RotationSweep:
    def __init__(self, path, profiles, closed=False):
        self.path = path
        self.profiles = profiles
        self.closed = closed
        self.tol = 1e-7
        self.sort_profiles()
        self.trim_profiles()
        self.trim_path()

    def get_profile_parameters(self):
        pl = []
        for p in self.profiles:
            dist, pts, info = self.path.distToShape(p)
            pl.append(self.path.Curve.parameter(pts[0][0]))
        return pl

    def sort_profiles(self):
        def getParam(p):
            dist, pts, info = self.path.distToShape(p)
            return self.path.Curve.parameter(pts[0][0])
        self.profiles.sort(key=getParam)

    def getCenter(self):
        center = FreeCAD.Vector()
        if len(self.profiles) == 1:
            warn("RotationSweep: Only 1 profile provided.\n")
            warn("Choosing center opposite to path.\n")
            dist, pts, info = self.path.distToShape(self.profiles[0])
            par = self.profiles[0].Curve.parameter(pts[0][1])
            fp = self.profiles[0].FirstParameter
            lp = self.profiles[0].LastParameter
            if abs(par - fp) > abs(par - lp):
                center = self.profiles[0].valueAt(fp)
            else:
                center = self.profiles[0].valueAt(lp)
        else:
            for p in self.profiles[1:]:
                dist, pts, info = p.distToShape(self.profiles[0])
                center += pts[0][1]
            center = center / (len(self.profiles) - 1)
        message(f"Center found at {center}\n")
        return center

    def loftProfiles(self):
        cl = [c.Curve for c in self.profiles]
        cts = CTS.CurvesToSurface(cl)
        cts.match_degrees()
        # self.auto_orient()
        # self.auto_twist()
        cts.normalize_knots()
        # CTS.match_knots(cts.curves)
        syncAllKnots(cts.curves, 1e-8)
        cts.Parameters = self.get_profile_parameters()
        cts.interpolate()
        # wl = [Part.Wire([c]) for c in self.profiles]
        # loft = Part.makeLoft(wl, False, False, self.closed, 3)
        s = cts._surface
        s.scaleKnotsToBounds()
        return s  # loft.Face1.Surface

    def ruledToCenter(self, curve, center):
        bs = Part.BSplineSurface()
        # poles = [[center] * curve.NbPoles, curve.getPoles()]
        poles = [curve.getPoles(), [center] * curve.NbPoles]
        bs.buildFromPolesMultsKnots(poles,
                                    [2, 2], curve.getMultiplicities(),
                                    [0.0, 1.0], curve.getKnots(),
                                    False, curve.isPeriodic(),
                                    1, curve.Degree)
        return bs

    def trim_profiles(self):
        center = self.getCenter()
        edges = []
        for i, prof in enumerate(self.profiles):
            message(f"Connecting curve #{i}\n")
            c = prof.Curve
            contact_shapes(c, self.path, Part.Vertex(center))
            edges.append(c.toShape())
        self.profiles = edges

    def trim_path(self):
        c = self.path.Curve
        contact_shapes(c, self.profiles[0], self.profiles[-1])
        self.path = c.toShape()

    def insert_profiles(self, num=0):
        if num < 1:
            return
        rsp = SweepPath.RotationSweepPath(self.path, self.getCenter())
        rsp.add_profile(self.profiles)
        rsp.interpolate_local_profiles()
        profs = [c.toShape() for c in rsp.insert_profiles(num)]
        self.profiles = profs

    def compute(self):
        c = self.path.Curve
        # S1
        loft = self.loftProfiles()
        normalize([c, loft])
        syncDegree(c, [loft, 1])
        syncKnots(c, [loft, 1], 1e-7)
        # S2
        ruled = self.ruledToCenter(c, self.getCenter())
        syncDegree([ruled, 0], [loft, 0])
        insKnots([ruled, 0], [loft, 0], 1e-7)
        # S3
        pts_interp = CTS.U_linear_surface(loft)
        syncDegree([pts_interp, 0], [loft, 0])
        insKnots([pts_interp, 0], [loft, 0], 1e-7)
        # return loft, ruled, pts_interp
        gordon = CTS.Gordon(loft, ruled, pts_interp)
        return gordon.gordon()

    @property
    def Face(self):
        g = self.compute()
        return g.toShape()
        return Part.Compound([s.toShape() for s in g])


class RotsweepProxyFP:
    """Creates a ..."""

    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Profiles",
                        "InputShapes", "The list of profiles to sweep")
        obj.addProperty("App::PropertyLinkSub", "Path",
                        "InputShapes", "The sweep path")
        obj.addProperty("App::PropertyBool", "Closed",
                        "Settings", "Close the sweep shape")
        obj.addProperty("App::PropertyBool", "AddProfiles",
                        "Settings", "Add profiles to the sweep shape")
        obj.addProperty("App::PropertyInteger", "AddSamples",
                        "Settings", "Number of additional profiles")
        obj.setEditorMode("AddProfiles", 2)
        obj.Proxy = self

    def getCurve(self, lo):
        edges = []
        po, psn = lo
        # print(psn)
        for sn in psn:
            if "Edge" in sn:
                edges.append(po.getSubObject(sn))
        if len(edges) == 0:
            edges = po.Shape.Edges
        bsedges = []
        for e in edges:
            if isinstance(e.Curve, Part.BSplineCurve):
                bsedges.append(e)
            else:
                c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
                bsedges.append(c.toShape())
        return bsedges

    def getCurves(self, prop):
        edges = []
        for p in prop:
            edges.extend(self.getCurve(p))
        return edges

    def execute(self, obj):
        path = self.getCurve(obj.Path)[0]
        profiles = self.getCurves(obj.Profiles)
        rs = RotationSweep(path, profiles, obj.Closed)
        rs.insert_profiles(obj.AddSamples)
        if obj.AddProfiles:
            obj.Shape = Part.Compound([rs.Face] + rs.profiles)
        else:
            obj.Shape = rs.Face

    def onChanged(self, obj, prop):
        return False


class RotsweepProxyVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None


class RotsweepFPCommand:
    """Create a ... feature"""

    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                              "Rotation Sweep")
        RotsweepProxyFP(fp)
        fp.Path = sel[0]
        fp.Profiles = sel[1:]
        RotsweepProxyVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        links = []
        sel = FreeCADGui.Selection.getSelectionEx('', 0)
        for so in sel:
            if so.HasSubObjects:
                links.append((so.Object, so.SubElementNames))
            else:
                links.append((so.Object, [""]))
        if len(links) < 2:
            FreeCAD.Console.PrintError("Select Path and Profiles first !\n")
        else:
            self.makeFeature(links)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curves_RotationSweep', RotsweepFPCommand())

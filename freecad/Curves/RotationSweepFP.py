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
from freecad.Curves import ICONPATH

warn = FreeCAD.Console.PrintWarning
message = warn = FreeCAD.Console.PrintMessage
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
    if p1 > p2:
        curve.reverse()
        contact_points(curve, pt1, pt2)
        return
    if p1 == curve.FirstParameter:
        curve.setPole(1, pt1)
    if p2 == curve.LastParameter:
        curve.setPole(curve.NbPoles, pt2)
    curve.segment(p1, p2)
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
            par = self.profiles[0].parameter(pts[0][1])
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

    def insertknotsSC(self, surf, curve, direc=0, reciprocal=False):
        if direc == 1:
            surf.insertVKnots(curve.getKnots(), curve.getMultiplicities(), self.tol, False)
        else:
            surf.insertUKnots(curve.getKnots(), curve.getMultiplicities(), self.tol, False)
        if reciprocal:
            if direc == 1:
                curve.insertKnots(surf.getVKnots(), surf.getVMultiplicities(), self.tol, False)
            else:
                curve.insertKnots(surf.getUKnots(), surf.getUMultiplicities(), self.tol, False)

    def loftProfiles(self):
        wl = [Part.Wire([c]) for c in self.profiles]
        loft = Part.makeLoft(wl, False, False, self.closed, 3)
        return loft.Face1.Surface

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

    def trim_profiles(self, sh1, sh2):
        edges = []
        for prof in self.profiles:
            c = prof.Curve
            contact_shapes(c, sh1, sh2)
            edges.append(c.toShape())
        self.profiles = edges

    def compute(self):
        center = self.getCenter()
        self.trim_profiles(self.path, Part.Vertex(center))
        c = self.path.Curve
        contact_shapes(c, self.profiles[0], self.profiles[-1])
        self.path = c.toShape()
        loft = self.loftProfiles()
        # return loft
        c = self.path.Curve
        # c.scaleKnotsToBounds()
        # loft.scaleKnotsToBounds()
        # d = max(c.Degree, loft.VDegree)
        normalize([c, loft])
        syncDegree(c, [loft, 1])
        # loft.increaseDegree(loft.UDegree, d)
        # c.increaseDegree(d)
        syncKnots(c, [loft, 1], 1e-10)
        # self.insertknotsSC(loft, c, 1, True)
        # self.path = c.toShape()
        ruled = self.ruledToCenter(c, center)
        syncDegree([ruled, 0], [loft, 0])
        # normalize([ruled])
        # ruled.increaseDegree(loft.UDegree, d)
        insKnots([ruled, 0], [loft, 0], 1e-10)
        # self.insertknotsSC(ruled, loft.vIso(0.0), 0, False)
        # self.insertknotsSC(ruled, loft.uIso(0.0), 0, False)
        pts_interp = CTS.U_linear_surface(loft)
        # pts_interp.increaseDegree(loft.UDegree, d)
        syncDegree([pts_interp, 0], [loft, 0])
        # self.insertknotsSC(pts_interp, loft.vIso(0.0), 0, False)
        insKnots([pts_interp, 0], [loft, 0], 1e-10)
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
        obj.Proxy = self

    def getCurve(self, prop):
        edges = []
        po, psn = prop
        # print(psn)
        for sn in psn:
            if "Edge" in sn:
                edges.append(po.getSubObject(sn))
        if len(edges) == 0:
            edges = po.Shape.Edges
        if len(edges) == 1:
            return edges[0]
        soed = Part.sortEdges(edges)
        w = Part.Wire(soed[0])
        bs = w.approximate(1e-10, 1e-7, 10000, 3)
        # print(bs)
        return bs.toShape()

    def execute(self, obj):
        path = self.getCurve(obj.Path)
        profiles = [self.getCurve(li) for li in obj.Profiles]
        rs = RotationSweep(path, profiles, obj.Closed)
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
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Rotation Sweep")
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

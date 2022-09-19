# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
# from FreeCAD.Console import PrintError, PrintWarning, PrintMessage
import FreeCADGui
import Part
from freecad.Curves import curves_to_surface as CTS
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')
# debug = _utils.debug
# debug = _utils.doNothing


def insKnots(geom, knots, mults, tol=1e-10, add=False):
    if isinstance(geom, Part.BSplineCurve):
        geom.insertKnots(knots, mults, tol, add)
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            geom[0].insertUKnots(knots, mults, tol, add)
        elif geom[1] == 1:
            geom[0].insertVKnots(knots, mults, tol, add)

def getDegree(geom):
    if isinstance(geom, Part.BSplineCurve):
        return geom.Degree
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            return geom.UDegree
        elif geom[1] == 1:
            return geom.VDegree

def getKnots(geom):
    if isinstance(geom, Part.BSplineCurve):
        return geom.getKnots()
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            return geom.getUKnots()
        elif geom[1] == 1:
            return geom.getVKnots()

def getMults(geom):
    if isinstance(geom, Part.BSplineCurve):
        return geom.getMultiplicities()
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            return geom.getUMultiplicities()
        elif geom[1] == 1:
            return geom.getVMultiplicities()

def incDegree(geom, d):
    if isinstance(geom, Part.BSplineCurve):
        geom.increaseDegree(d)
    elif isinstance(geom, (list, tuple)):
        if geom[1] == 0:
            geom[0].increaseDegree(d, geom[0].VDegree)
        elif geom[1] == 1:
            geom[0].increaseDegree(geom[0].UDegree, d)

def syncDegree(geo1, geo2):
    d1 = geo1.getDegree()
    d2 = geo2.getDegree()
    if d1 > d2:
        incDegree(geo2, d1)
    elif d2 > d1:
        incDegree(geo1, d2)

def syncKnots(geo1, geo2, tol=1e-10):
    k = getKnots(geo1)
    m = getMults(geo1)
    insKnots(geo1, getKnots(geo2), getMults(geo2), tol, False)
    insKnots(geo2, k, m, tol, False)

def normalize(*geom):
    for g in geom:
        g.scaleKnotsToBounds()

def clamp(curve, pt1, pt2):
    p1 = curve.parameter(pt1)
    p2 = curve.parameter(pt2)
    if p1 > p2:
        curve.reverse()
        clamp(curve, pt1, pt2)
        return
    if p1 == curve.FirstParameter:
        curve.setPole(1, pt1)
    if p2 == curve.LastParameter:
        curve.setPole(curve.NbPoles, pt2)
    curve.segment(p1, p2)
    curve.scaleKnotsToBounds()

def trim_and_orient(curve, geo1, geo2):
    edge = curve.toShape()
    sh1 = geo1.toShape()
    sh2 = geo2.toShape()
    pt1 = edge.distToShape(sh1)[1][0][1]
    pt2 = edge.distToShape(sh2)[1][0][1]
    clamp(curve, pt1, pt2)




class RotationSweep:
    def __init__(self, path, profiles, closed=False):
        self.path = path
        self.profiles = profiles
        self.closed = closed
        self.tol = 1e-7

    def getCenter(self):
        if len(self.profiles) == 1:
            FreeCAD.Console.PrintWarning("RotationSweep: Only 1 profile provided. Choosing center opposite to path.\n")
            dist, pts, info = self.path.distToShape(self.profiles[0])
            par = self.profiles[0].parameter(pts[0][1])
            if abs(par - self.profiles[0].FirstParameter) > abs(par - self.profiles[0].LastParameter):
                return self.profiles[0].valueAt(self.profiles[0].FirstParameter)
            else:
                return self.profiles[0].valueAt(self.profiles[0].LastParameter)

        center = FreeCAD.Vector()
        for p in self.profiles[1:]:
            dist, pts, info = p.distToShape(self.profiles[0])
            center += pts[0][1]
        return center / (len(self.profiles) - 1)

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

    def compute(self):
        center = self.getCenter()
        loft = self.loftProfiles()
        # return loft
        c = self.path.Curve
        c.scaleKnotsToBounds()
        loft.scaleKnotsToBounds()
        d = max(c.Degree, loft.VDegree)
        loft.increaseDegree(loft.UDegree, d)
        c.increaseDegree(d)
        self.insertknotsSC(loft, c, 1, True)
        # self.path = c.toShape()
        ruled = self.ruledToCenter(c, center)
        ruled.increaseDegree(loft.UDegree, d)
        self.insertknotsSC(ruled, loft.vIso(0.0), 0, False)
        # self.insertknotsSC(ruled, loft.uIso(0.0), 0, False)
        pts_interp = CTS.U_linear_surface(loft)
        pts_interp.increaseDegree(loft.UDegree, d)
        self.insertknotsSC(pts_interp, loft.vIso(0.0), 0, False)
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

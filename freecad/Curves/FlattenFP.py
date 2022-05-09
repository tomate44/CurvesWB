# -*- coding: utf-8 -*-

__title__ = 'Flatten face'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
import Part
from math import pi
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')
vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d


def flat_cylinder(cyl, inPlace=True, size=100.0):
    """
    flat_face = flat_cylinder_surface(face, in_place=False)
    Creates a flat nurbs surface from input cylindrical face, with same parametrization.
    If in_place is True, the surface is located at the seam edge of the face.
    """
    u0, u1 = cyl.bounds()[0:2]
    prange = u1 - u0
    v0, v1 = -size, size
    c1 = cyl.uIso(u0)  # seam line
    e1 = c1.toShape(v0, v1)
    c2 = cyl.vIso(v1)  # circle
    e2 = c2.toShape(u0, u1)
    l2 = e2.Length
    if inPlace:
        t1 = c2.tangent(c2.FirstParameter)[0]
        e3 = e1.copy()
        e3.translate(t1 * l2)
        rs = Part.makeRuledSurface(e1, e3)
        bs = rs.Surface
        bs.exchangeUV()
    else:
        bs = Part.BSplineSurface()
        bs.setPole(1, 1, vec3(u0 - prange, -size, 0))
        bs.setPole(1, 2, vec3(u1 + prange, -size, 0))
        bs.setPole(2, 1, vec3(u0 - prange, size, 0))
        bs.setPole(2, 2, vec3(u1 + prange, size, 0))
    bs.setUKnots([u0 - prange, u1 + prange])
    bs.setVKnots([-size, size])
    return bs


def flat_cone(cone, inPlace=True, radius=0.0, scale=1.0, rational=False):
    ci = Part.Circle(cone.Center, cone.Axis, cone.Radius)
    cilen = ci.length()
    p1 = ci.value(ci.FirstParameter)
    ci.Radius = cone.Apex.distanceToPoint(p1)
    if radius > 1e-7:
        scale = radius / ci.Radius

    if inPlace:
        ci.Center = cone.Apex
    else:
        ci.Center = FreeCAD.Vector(0, 0, 0)
        ci.Axis = FreeCAD.Vector(0, 0, 1)

    if rational:
        bs = ci.toNurbs()  # 0.0, ci.parameterAtDistance(cilen))
    else:
        bs = ci.toBSpline()  # 0.0, ci.parameterAtDistance(cilen))
    fac = bs.length() / cilen
    bs.scale(ci.Center, scale)
    bs2 = bs.copy()
    bs2.mirror(ci.Center)
    rs = Part.makeRuledSurface(bs2.toShape(), bs.toShape()).Surface
    sign = 1.0
    if cone.parameter(cone.Apex)[1] > 0:
        sign = -1.0
    vk1 = -ci.Radius * (scale + sign)
    vk2 = ci.Radius * (scale - sign)
    rs.setVKnots([vk1, vk2])
    rs.setUKnot(2, 2 * pi * fac)
    if not rs.isUPeriodic():
        print("setting curve periodic")
        rs.setUPeriodic()
    return rs


def flatten(face, inPlace=False):
    """
    Flattens a face.
    Currently, this works only on conical and cylindrical faces.
    Returns the flat face, or a compound of wires, if face creation fails.
    """
    tol = 1e-7
    size = 1e12
    if isinstance(face.Surface, Part.Cone):
        flatsurf = flat_cone(face.Surface, inPlace, size)
    elif isinstance(face.Surface, Part.Cylinder):
        flatsurf = flat_cylinder(face.Surface, inPlace, size)
    else:
        raise TypeError("Face support must be a cone or a cylinder.")
    u0,u1,v0,v1 = face.Surface.bounds()
    seam = face.Surface.uIso(0)
    wires = []
    planeXY = Part.Plane()
    for w in face.Wires:
        edges = []
        additional_edges = []
        for e in w.Edges:
            c, fp, lp = face.curveOnSurface(e)
            edges.append(c.toShape(flatsurf, fp, lp))
            if e.isSeam(face):
                p1 = c.value(fp)
                p2 = c.value(lp)
                tr_vec = vec2(0, 0)
                if abs(p1.x-u0)+abs(p2.x-u0) < tol:
                    print("seam edge detected at u0")
                    tr_vec = vec2(u1-u0, 0)
                elif abs(p1.x-u1)+abs(p2.x-u1) < tol:
                    print("seam edge detected at u1")
                    tr_vec = vec2(u0-u1, 0)
                elif abs(p1.y-v0)+abs(p2.y-v0) < tol:
                    print("seam edge detected at v0")
                    tr_vec = vec2(0, v1-v0)
                elif abs(p1.y-v1)+abs(p2.y-v1) < tol:
                    print("seam edge detected at v1")
                    tr_vec = vec2(0, v0-v1)
                c.translate(tr_vec)
                re = c.toShape(flatsurf, fp, lp)
                re.reverse()
                edges.append(re)
        se = Part.sortEdges(edges)
        if len(se) > 1:
            print("multiple wires : trying to join them")
            se = Part.sortEdges(edges+additional_edges)
        if len(se) > 1:
            print("Failed to join wires ???")
            for el in se:
                w = Part.Wire(el)
                wires.append(w)
            return Part.Compound(wires)

        w = Part.Wire(se[0])
        if not w.isClosed():
            print("open wire")
            # w = wt.close(w)
        wires.append(w)
    f = Part.Face(wires)
    f.validate()
    if f.isValid():
        f.reverse()
        return f
    else:
        return Part.Compound(wires)



def flatten_face(face, inPlace=True):
    size = 1e2
    if isinstance(face.Surface, Part.Cone):
        flatsurf = flat_cone(face.Surface, inPlace, size)
    elif isinstance(face.Surface, Part.Cylinder):
        flatsurf = flat_cylinder(face.Surface, inPlace, size)
    else:
        raise TypeError("Face support must be a cone or a cylinder.")
    wl = []
    for w in face.Wires:
        el = []
        for e in w.OrderedEdges:
            c, fp, lp = face.curveOnSurface(e)
            el.append(c.toShape(flatsurf, fp, lp))
            if e.isSeam(face):
                e.reverse()
                c, fp, lp = face.curveOnSurface(e)
                el.append(c.toShape(flatsurf, fp, lp))
        se = Part.sortEdges(el)
        for sei in se:
            try:
                nw = Part.Wire(sei)
            except Part.OCCError:
                print("Part.Wire : Part.OCCError")
                continue
            if not nw.isValid():
                print("Wire isn't valid")
            if not nw.isClosed():
                print("Wire isn't closed")
            if w.isSame(face.OuterWire):
                print("Outerwire detected")
                wl.insert(0, nw)
            else:
                wl.append(nw)
    nf = Part.Face(flatsurf, wl)
    if not nf.isValid():
        print("Face isn't valid")
        nf.validate()
    return nf


class FlattenProxy:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Source",
                        "Source", "The conical face to flatten")
        obj.addProperty("App::PropertyBool", "InPlace",
                        "Settings", "Place the flatten face at the same location as the source face")
        obj.Proxy = self

    def get_face(self, fp):
        obj, subnames = fp.Source
        for n in subnames:
            f = obj.getSubObject(n)
            if isinstance(f, Part.Face):
                return f
        return obj.Shape.Face1

    def execute(self, obj):
        face = self.get_face(obj)
        flat_face = flatten_face(face, obj.InPlace)
        obj.Shape = flat_face

    def onChanged(self, obj, prop):
        return False


class FlattenViewProxy:
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


class Curves_Flatten_Face_Cmd:
    """Create a ... feature"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "")
        FlattenProxy(fp)
        FlattenViewProxy(fp.ViewObject)
        fp.Source = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select a conical face\n")
        for so in sel:
            for sn in so.SubElementNames:
                if "Face" in sn:
                    self.makeFeature((so.Object, sn))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curves_FlattenFace', Curves_Flatten_Face_Cmd())

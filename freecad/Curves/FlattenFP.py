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


def flat_cylinder(cyl, inPlace=True, scale=1.0):
    """
    flat_face = flat_cylinder_surface(face, in_place=False)
    Creates a flat nurbs surface from input cylindrical face, with same parametrization.
    If in_place is True, the surface is located at the seam edge of the face.
    """
    u0, u1, v0, v1 = cyl.bounds()
    c1 = cyl.uIso(u0)  # seam line
    e1 = c1.toShape(0.0, 1.0)
    c2 = cyl.vIso(v0)  # circle
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
        bs.setPole(1, 1, vec3(v0, 0, 0))
        bs.setPole(1, 2, vec3(v1, 0, 0))
        bs.setPole(2, 1, vec3(v0, l2, 0))
        bs.setPole(2, 2, vec3(v1, l2, 0))
    bs.setUKnots([0, 2 * pi])
    bs.setVKnots([v0, v1])
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
        bs = ci.toNurbs(0.0, ci.parameterAtDistance(cilen))
    else:
        bs = ci.toBSpline(0.0, ci.parameterAtDistance(cilen))

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
    rs.setUKnot(2, 2 * pi)
    return rs


def flatten_face(face, inPlace=True):
    if isinstance(face.Surface, Part.Cone):
        flatsurf = flat_cone(face.Surface, inPlace)
    elif isinstance(face.Surface, Part.Cylinder):
        flatsurf = flat_cylinder(face.Surface, inPlace)
    else:
        raise TypeError("Face support must be a cone or a cylinder.")
    el = []
    for e in face.Edges:
        c, fp, lp = face.curveOnSurface(e)
        el.append(c.toShape(flatsurf, fp, lp))
        if e.isSeam(face):
            e.reverse()
            c, fp, lp = face.curveOnSurface(e)
            el.append(c.toShape(flatsurf, fp, lp))

    wl = []
    for we in Part.sortEdges(el):
        wl.append(Part.Wire(we))
    return Part.Face(wl)


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

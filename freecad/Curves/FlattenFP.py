# -*- coding: utf-8 -*-

__title__ = 'Flatten face'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Creates a flat developed face from conical and cylindrical faces'
__usage__ = """You must select a conical or cylindrical face in the 3D View.
InPlace property puts the unrolled face tangent to the source face (InPlace = True)
or in the XY plane (InPlace = False)"""

import os
import FreeCAD
import FreeCADGui
import Part
from math import pi
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'flatten.svg')
vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d


def flat_cylinder_surface(cyl, inPlace=False, size=0.0):
    """Returns a BSpline surface that is a flat representation of the input Cylinder.

    Parameters
    ----------
    cyl : Surface of type Part.Cylinder
    InPlace (bool) : If True, the output surface will be placed so that it is
        tangent to the source cylinder, at the seam line.
        If False, the output surface will be in the default XY plane.
    size (float) : Sets the size of the square output surface to size.
        If size==0.0, size is set to twice the circumference of the input cylinder

    Returns
    -------
    a square BSpline surface that matches the parametric space of the input cylinder.
    """
    if size == 0.0:
        size = cyl.Radius * 4 * pi
    hs = size / 2
    bs = Part.BSplineSurface()
    bs.setPole(1, 1, vec3(-hs, -hs))
    bs.setPole(1, 2, vec3(-hs, hs))
    bs.setPole(2, 1, vec3(hs, -hs))
    bs.setPole(2, 2, vec3(hs, hs))
    bs.setUKnots([-hs / cyl.Radius, hs / cyl.Radius])
    bs.setVKnots([-hs, hs])
    if inPlace:
        origin = cyl.value(0, 0)
        x, y = cyl.tangent(0, 0)
        rot = FreeCAD.Rotation(x, y, x.cross(y), "XYZ")
        pl = FreeCAD.Placement(origin, rot)
        bs.transform(pl.Matrix)
    return bs


def flat_cone_surface(cone, inPlace=False, size=0.0):
    """Returns a BSpline surface that is a flat representation of the input Cone.

    Parameters
    ----------
    cone : Surface of type Part.Cone
    InPlace (bool) : If True, the output surface will be placed so that it is
        tangent to the source cone, at the seam line.
        If False, the output surface will be in the default XY plane.
    size (float) : Sets the radius of the circular output surface to size.
        If size==0.0, size is set to the cone radius.

    Returns
    -------
    a circular BSpline surface that matches the parametric space of the input cone.
    """
    if size == 0.0:
        size = cone.Radius
    fp = cone.value(0, 0)
    hyp = Part.LineSegment(fp, cone.Apex)
    axis = Part.Line(cone.Center, cone.Axis)
    if axis.parameter(cone.Apex) < 0:
        ci = Part.Circle(vec3(), vec3(0, 0, 1), size)
        cimir = ci.copy()
        cimir.mirror(cimir.Center)
        # print("Opening cone")
        rs = Part.makeRuledSurface(cimir.toShape(), ci.toShape()).Surface
        start = -size - hyp.length()
    else:
        ci = Part.Circle(vec3(), vec3(0, 0, -1), size)
        cimir = ci.copy()
        cimir.mirror(cimir.Center)
        # print("Closing cone")
        rs = Part.makeRuledSurface(ci.toShape(), cimir.toShape()).Surface
        start = -size + hyp.length()
    end = start + 2 * size
    # print(f"Setting V range [{start} - {end}]")
    rs.setVKnots([start, end])
    rs.setUKnot(2, 2 * pi * hyp.length() / cone.Radius)
    rs.setUPeriodic()
    if inPlace:
        origin = cone.Apex
        y, x = cone.tangent(0, 0)
        rot = FreeCAD.Rotation(x, y, x.cross(y), "XYZ")
        pl = FreeCAD.Placement(origin, rot)
        rs.transform(pl.Matrix)
    return rs


def flatten_face(face, inPlace=False, size=0.0):
    """Returns a face that is a flat representation of the input cone or cylinder face.

    Parameters
    ----------
    face : face of a cone or cylinder surface.
    InPlace (bool) : If True, the output surface will be placed so that it is
        tangent to the source face, at the seam line.
        If False, the output surface will be in the default XY plane.
    size (float) : Allows to specify the size of the computed surface.
        This has now influence on the shape of the output face.

    Returns
    -------
    a face that is the unrolled representation of the input cone or cylinder face.
    """
    if isinstance(face.Surface, Part.Cone):
        flatsurf = flat_cone_surface(face.Surface, inPlace, size)
    elif isinstance(face.Surface, Part.Cylinder):
        flatsurf = flat_cylinder_surface(face.Surface, inPlace, size)
    else:
        raise TypeError("Face support must be a cone or a cylinder.")
    wl = []
    ow = None
    for w in face.Wires:
        el = []
        for e in w.OrderedEdges:
            c, fp, lp = face.curveOnSurface(e)
            el.append(c.toShape(flatsurf, fp, lp))
        nw = Part.Wire(el)
        if w.Orientation == "Reversed":
            nw.reverse()
        if w.isPartner(face.OuterWire):
            ow = nw
        else:
            wl.append(nw)
    ff = Part.Face(flatsurf, ow)
    ff.validate()
    if wl:
        ff.cutHoles(wl)
    ff.validate()
    return ff


class FlattenProxy:
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Source",
                        "Source", "The conical face to flatten")
        obj.addProperty("App::PropertyBool", "InPlace",
                        "Settings", "Unroll the face in place")
        obj.addProperty("App::PropertyFloat", "Size",
                        "Settings", "Size of the underlying surface")
        obj.setEditorMode("Size", 2)
        obj.Size = 1.0
        obj.InPlace = True
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
        flat_face = flatten_face(face, obj.InPlace, obj.Size)
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
    """Create a flatten face feature"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Flatten")
        FlattenProxy(fp)
        FlattenViewProxy(fp.ViewObject)
        fp.Source = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))
        for so in sel:
            for sn in so.SubElementNames:
                subo = so.Object.getSubObject(sn)
                if hasattr(subo, "Surface") and isinstance(subo.Surface, (Part.Cylinder, Part.Cone)):
                    self.makeFeature((so.Object, sn))
                else:
                    FreeCAD.Console.PrintError("Bad input :{}-{}\n".format(so.Object.Label, sn))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('Curves_FlattenFace', Curves_Flatten_Face_Cmd())

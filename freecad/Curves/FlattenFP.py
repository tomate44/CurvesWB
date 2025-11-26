# SPDX-License-Identifier: LGPL-2.1-or-later

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
from freecad.Curves.nurbs_tools import KnotVector
from freecad.Curves.map_on_face import ShapeMapper

TOOL_ICON = os.path.join(ICONPATH, 'flatten.svg')
vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d

preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves")
if 'FlattenDefaultInPlace' not in preferences.GetBools():
    preferences.SetBool("FlattenDefaultInPlace", True)

"""
poles (sequence of sequence of Base.Vector), umults, vmults, [uknots, vknots, uperiodic, vperiodic, udegree, vdegree, weights (sequence of sequence of float)]
"""


def ruled_surface(curve1, curve2):
    bs1 = curve1.toBSpline()
    bs2 = curve2.toBSpline()
    surf = Part.BSplineSurface()
    poles = list(zip(bs1.getPoles(), bs2.getPoles()))
    mults = bs1.getMultiplicities()
    surf.buildFromPolesMultsKnots(poles, mults, [2, 2], bs1.getKnots(), [0, 1], False, False, bs1.Degree, 1)
    return surf


def arclength_approx(curve, num=100):
    """Returns an arc-length approximation BSpline of a curve or edge
    num (default 100) is the number of samples"""
    sh = curve
    if hasattr(curve, "toShape"):
        sh = curve.toShape()
    dist = sh.Length / num
    pts = sh.discretize(Distance=dist)
    params = [i * dist for i in range(len(pts) - 1)]
    params.append(sh.Length)
    bs = Part.BSplineCurve()
    bs.approximate(Points=pts, Parameters=params)
    return bs


def XY_Compound(face):
    fel = []
    for e in face.OuterWire.OrderedEdges:
        cos = face.curveOnSurface(e)
        fe = cos[0].toShape(cos[1], cos[2])
        fel.append(fe)
    comp = Part.Compound(fel)
    return comp


def parametric_bounds(shape):
    bb = shape.BoundBox
    return bb.XMin, bb.YMin, bb.XMax, bb.YMax


def seam_indices(shape):
    xi, yi, xa, ya = parametric_bounds(shape)
    left_seams = []
    right_seams = []
    for i, fe in enumerate(shape.Edges):
        bb = fe.BoundBox
        if bb.XLength < 1e-7:
            if abs(bb.XMin - xi) < 1e-7:
                left_seams.append(i)
            if abs(bb.XMax - xa) < 1e-7:
                right_seams.append(i)
    return left_seams, right_seams


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
        size = 1.1 * cyl.Radius * 4 * pi
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
    axis = Part.Line()
    axis.Location = cone.Center
    axis.Direction = cone.Axis
    if axis.parameter(cone.Apex) < 0:
        ci = Part.Circle(vec3(), vec3(0, 0, 1), size)
        cimir = ci.copy()
        cimir.mirror(cimir.Center)
        print("Opening cone")
        # rs = Part.makeRuledSurface(cimir.toShape(), ci.toShape()).Surface
        rs = ruled_surface(cimir, ci)
        start = -size - hyp.length()
    else:
        ci = Part.Circle(vec3(), vec3(0, 0, -1), size)
        cimir = ci.copy()
        cimir.mirror(cimir.Center)
        print("Closing cone")
        # rs = Part.makeRuledSurface(ci.toShape(), cimir.toShape()).Surface
        rs = ruled_surface(ci, cimir)
        start = -size + hyp.length()
    end = start + 2 * size
    u0, u1, v0, v1 = rs.bounds()
    if hasattr(rs, "scaleKnotsToBounds"):
        rs.scaleKnotsToBounds(u0, 2 * pi * hyp.length() / cone.Radius, start, end)
    else:
        rs.setVKnots([start, end])
        knots = rs.getUKnots()
        kv = KnotVector(knots)
        rs.setUKnots(kv.transpose(u0, 2 * pi * hyp.length() / cone.Radius))
    rs.setUPeriodic()
    if inPlace:
        origin = cone.Apex
        y, x = cone.tangent(0, 0)
        rot = FreeCAD.Rotation(x, y, x.cross(y), "XYZ")
        pl = FreeCAD.Placement(origin, rot)
        rs.transform(pl.Matrix)
    return rs


def flat_extrusion_surface(extr, inPlace=False, size=1e10):
    """Returns a BSpline surface that is a flat
    representation of the input Surface of Extrusion.

    Parameters
    ----------
    extr : Surface of type Part.SurfaceOfExtrusion
    InPlace (bool) : If True, the output surface will be placed so that it is
        tangent to the source surface, at the origin extrusion line.
        If False, the output surface will be in the default XY plane.
    size (float) : Sets the V size of the output surface to size.
        If size==0.0, size is set to twice the extrusion length

    Returns
    -------
    a square BSpline surface that matches the parametric space
    of the input Surface of Extrusion.
    """
    basc = extr.BasisCurve
    # if basc.isPeriodic():
    #     basc.setNotPeriodic()
    based = basc.toShape()
    # Part.show(based, "BasisCurve")

    pl = Part.Plane(basc.value(basc.FirstParameter), extr.Direction)
    plts = Part.RectangularTrimmedSurface(pl, -size, size, -size, size)
    plsh = plts.toShape()
    # Part.show(plsh)

    proj = plsh.project([based])  # , surf.Direction)

    # Part.show(proj, "BasisCurve Projection")

    if len(proj.Edges) > 1:
        w = Part.Wire(proj.Edges)
        pe = w.approximate(1e-10, 1e-7, 1000, 7)
        print("Projection : multiple edges approximated")
    else:
        pe = proj.Edge1.Curve

    alc = arclength_approx(pe)
    sof = Part.SurfaceOfExtrusion(alc, extr.Direction)
    # return sof
    u0, u1, v0, v1 = sof.bounds()
    nts = Part.RectangularTrimmedSurface(sof, u0, u1, -size, size)
    nface = nts.toShape()

    proj2 = nface.project([based])
    if not proj2.Edges:
        print("Flatten : Failed to create flat_extrusion_surface")
        return nts
    pe = proj2.Edge1
    cos, fp, lp = nface.curveOnSurface(pe)
    flatbasc = cos.toShape(fp, lp)
    sof2 = Part.SurfaceOfExtrusion(flatbasc.Curve, FreeCAD.Vector(0, 1, 0))
    u0, u1, v0, v1 = sof2.bounds()
    nts2 = Part.RectangularTrimmedSurface(sof2, u0, u1, -size, size)

    if inPlace:
        origin = basc.value(basc.FirstParameter)
        u, v = extr.parameter(origin)
        y = extr.Direction
        n = extr.normal(u, v)
        rot = FreeCAD.Rotation(y.cross(n), y, n, "XYZ")
        pl = FreeCAD.Placement(origin, rot)
        nts2.transform(pl.Matrix)
    return nts2


def intersection(lines, tol=1e-7):
    """
    If lines all intersect into one point.
    Returns this point, or None
    """
    interlist = []
    for i in range(len(lines) - 1):
        inter = lines[i].intersect(lines[i + 1])
        if len(inter) == 1:
            interlist.append(inter[0].toShape().Point)
    if len(interlist) == 0:
        return None
    for i in range(len(interlist) - 1):
        if interlist[i].distanceToPoint(interlist[i + 1]) > tol:
            return None
    point = FreeCAD.Vector()
    for pt in interlist:
        point += pt
    point /= len(interlist)
    return point



def flat_conical_surface(conic, inPlace=False, size=0.0):
    """Returns a BSpline surface that is a flat
    representation of the input conical Surface.

    Parameters
    ----------
    extr : Surface of type Part.SurfaceOfExtrusion
    InPlace (bool) : If True, the output surface will be placed so that it is
        tangent to the source surface, at the origin extrusion line.
        If False, the output surface will be in the default XY plane.
    size (float) : Sets the V size of the output surface to size.
        If size==0.0, size is set to twice the extrusion length

    Returns
    -------
    a square BSpline surface that matches the parametric space
    of the input Surface of Extrusion.
    """
    samples = 10
    size = 1e10
    u0, u1, v0, v1 = conic.bounds()
    urange = u1 - u0
    uparams = [u0 + i * urange / (samples) for i in range(samples)]
    ulines = []
    for u in uparams:
        print(u)
        iso = conic.uIso(u)
        pt = iso.value(v0)
        pt2 = iso.value(v1)
        # print(tan)
        line = Part.makeLine(pt, pt2)
        Part.show(line)
        ulines.append(line.Curve.toShape())
    center = FreeCAD.Vector()
    for i in range(len(ulines) - 1):
        center += ulines[i].distToShape(ulines[i + 1])[1][0][0]
    center = center / (samples - 1)
    print(center)

    sph = Part.Sphere()
    sph.Center = center
    sph.Radius = center.distanceToPoint(conic.uIso(u0).value(0.5 * (v0 + v1)))
    inter = sph.intersect(conic)
    print(inter)

    if len(inter) > 1:
        edges = [c.toShape() for c in inter]
        se = Part.sortEdges(edges)
        w = Part.Wire(se[0])
        pe = w.approximate(1e-10, 1e-7, 1000, 7)
        print("Projection : multiple edges approximated")
    else:
        pe = inter[0]

    Part.show(pe.toShape())

    # What's next ?

    # alc = arclength_approx(pe)
    # sof = Part.SurfaceOfExtrusion(alc, conic.Direction)
    # # return sof
    # u0, u1, v0, v1 = sof.bounds()
    # nts = Part.RectangularTrimmedSurface(sof, u0, u1, -size, size)
    # nface = nts.toShape()
    #
    # proj2 = nface.project([based])
    # if not proj2.Edges:
    #     print("Flatten : Failed to create flat_conicusion_surface")
    #     return nts
    # pe = proj2.Edge1
    # cos, fp, lp = nface.curveOnSurface(pe)
    # flatbasc = cos.toShape(fp, lp)
    # sof2 = Part.SurfaceOfExtrusion(flatbasc.Curve, FreeCAD.Vector(0, 1, 0))
    # u0, u1, v0, v1 = sof2.bounds()
    # nts2 = Part.RectangularTrimmedSurface(sof2, u0, u1, -size, size)
    #
    # if inPlace:
    #     origin = basc.value(basc.FirstParameter)
    #     u, v = conic.parameter(origin)
    #     y = conic.Direction
    #     n = conic.normal(u, v)
    #     rot = FreeCAD.Rotation(y.cross(n), y, n, "XYZ")
    #     pl = FreeCAD.Placement(origin, rot)
    #     nts2.transform(pl.Matrix)
    # return nts2


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
        if size <= 0.0:
            comp = XY_Compound(face)
            u, v = face.Surface.parameter(face.Surface.Apex)
            vert = Part.Vertex(FreeCAD.Vector(u, v, 0))
            comp.add(vert)
            size = 1.01 * max(abs(comp.BoundBox.YMax), abs(comp.BoundBox.YLength))
            # offset = face.Surface.parameter(face.Surface.Apex)
            # size = abs(face.ParameterRange[3] - offset[1])
            # print(size)
        flatsurf = flat_cone_surface(face.Surface, inPlace, size)
    elif isinstance(face.Surface, Part.Cylinder):
        flatsurf = flat_cylinder_surface(face.Surface, inPlace, size)
    elif isinstance(face.Surface, Part.SurfaceOfExtrusion):
        flatsurf = flat_extrusion_surface(face.Surface, inPlace, size)
    # elif isinstance(face.Surface, Part.BSplineSurface):
    #     flatsurf = flat_conical_surface(face.Surface, inPlace, size)
    else:
        raise TypeError(f"Flattening surface of type {face.Surface.TypeId} not implemented")
    wl = []
    ow = None
    build_face = True
    for i, w in enumerate(face.Wires):
        el = []
        for e in w.OrderedEdges:
            c, fp, lp = face.curveOnSurface(e)
            el.append(c.toShape(flatsurf, fp, lp))
        try:
            nw = Part.Wire(el)
            assert nw.isClosed() and nw.isValid()
            if w.Orientation == "Reversed":
                nw.reverse()
        except (Part.OCCError, AssertionError):
            FreeCAD.Console.PrintError(f"Wire{i + 1} is not valid. Switching to Compound output.\n")
            build_face = False
            nw = Part.Compound(el)
        if w.isPartner(face.OuterWire):
            ow = nw
        else:
            wl.append(nw)
    if not build_face:
        return Part.Compound([ow] + wl)
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
        obj.Size = 0.0
        preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves")
        obj.InPlace = preferences.GetBool("FlattenDefaultInPlace", True)
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
                if hasattr(subo, "Surface") and isinstance(subo.Surface, (Part.Cylinder,
                                                                        Part.Cone,
                                                                        Part.SurfaceOfExtrusion)):
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

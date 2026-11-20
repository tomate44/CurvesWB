import FreeCAD
# import FreeCADGui
import Part
from math import pi
from freecad.Curves.lib.precision import tol3d
from freecad.Curves.lib.surface_identifier import SurfaceIdentifier, canonical_face
from freecad.Curves.lib.logger import FCLogger
from freecad.Curves.nurbs_tools import KnotVector


vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d
err = FreeCAD.Console.PrintError


class PCurve:
    def __init__(self, *args):
        if isinstance(args[0], Part.Edge) and isinstance(args[1], Part.Face):
            self.curve2d, self.fp, self.lp = args[1].curveOnSurface(args[0])
        elif len(args) == 3:
            self.curve2d, self.fp, self.lp = args


class Wire2D:
    def __init__(self, pcurves):
        self.pcurves = pcurves


class FlattenedSurface:
    XY = Part.Plane().toShape()

    def __init__(self):
        self.Matrix = FreeCAD.Matrix()

    def mat2d(self):
        cells = ("A11", "A12", "A13", "A21", "A22", "A23")
        return [getattr(self.Matrix, cell) for cell in cells]

    def get_wire2d(self, wire):
        cosl = []
        trfwire = wire.transformGeometry(self.Matrix, True)
        for e in trfwire.Wire1.OrderedEdges:
            pc, fp, lp = FlattenedSurface.XY.curveOnSurface(e)
            # pc.transform(self.mat2d())
            cosl.append(PCurve(pc, fp, lp))
        return Wire2D(cosl)


class FlattenedCylinder(FlattenedSurface):
    def __init__(self, cylinder):
        super().__init__()
        self.BasisSurface = cylinder
        self.Matrix.scale(1 / cylinder.Radius, 1, 1)


class FlattenCylinder:
    def __init__(self, face):
        self.cylindricalFace = canonical_face(face)
        if not self.cylindricalFace.TypeId == 'Part.Cylinder':
            raise (ValueError, 'Face is not cylindrical')
        self.build_face()

    def __getattr__(self, name):
        return self.Face.__getattribute__(name)

    def build_face(self):
        u0, u1, v0, v1 = self.cylindricalFace.ParameterRange
        bs = Part.BSplineSurface()
        bs.setPole(1, 1, vec3(0, 0))
        bs.setPole(1, 2, vec3(0, v1 - v0))
        bs.setPole(2, 1, vec3(2 * pi, 0))
        bs.setPole(2, 2, vec3(2 * pi, v1 - v0))
        bs.setUKnots([0, 2 * pi])
        bs.setVKnots([v0, v1])
        return bs


class FlattenFace:
    "Flatten a face"

    def __init__(self, face):
        self.logger = FCLogger("Debug", "FlattenFace")
        self.face = face
        self.tol3d = tol3d
        self.bounds = 0, 1, 0, 1
        self.valid_surf_types = (Part.Cone,
                                 Part.Cylinder,
                                 Part.SurfaceOfExtrusion)

    def encompass(self, shape):
        "Sets the XY dimensions of the FlattenFace"
        bb = shape.BoundBox
        self.bounds = bb.XMin, bb.XMax, bb.YMin, bb.YMax

    def flat_cylinder(self, cyl):
        "Returns a BSpline surface that is a flat representation of the input Cylinder"
        hs = 2 * pi * cyl.Radius
        bs = Part.BSplineSurface()
        bs.setPole(1, 1, vec3(0, 0))
        bs.setPole(1, 2, vec3(0, 1))
        bs.setPole(2, 1, vec3(hs, 0))
        bs.setPole(2, 2, vec3(hs, 1))
        bs.setUKnots([0, 2 * pi])
        bs.setVKnots([0, 1])
        return bs

    @property
    def Face(self):
        sr = SurfaceIdentifier(self.face)
        surf = sr.get_surface()
        match surf.TypeId:
            case 'Part.Cone':
                pass
            case 'Part.Cylinder':
                flat_surf = self.flat_cylinder(surf)
            case 'Part.SurfaceOfExtrusion':
                pass
            case _:
                err(f"{self.face.Surface.TypeId} not supported\n")
                return
        return face


def ruled_surface(curve1, curve2):
    """
    Returns a ruled surface between curve1 and curve2
    The two curves are supposed to be compatible
    """
    bs1 = curve1.toBSpline()
    bs2 = curve2.toBSpline()
    surf = Part.BSplineSurface()
    poles = list(zip(bs1.getPoles(), bs2.getPoles()))
    mults = bs1.getMultiplicities()
    surf.buildFromPolesMultsKnots(poles, mults, [2, 2], bs1.getKnots(), [
                                  0, 1], False, False, bs1.Degree, 1)
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


def flat_outerwire(face):
    "returns a coumpound of the outerwire edges mapped on XY"
    fel = []
    for e in face.OuterWire.OrderedEdges:
        cos = face.curveOnSurface(e)
        fe = cos[0].toShape(cos[1], cos[2])
        fel.append(fe)
    comp = Part.Compound(fel)
    return comp


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
        rs.scaleKnotsToBounds(
            u0, 2 * pi * hyp.length() / cone.Radius, start, end)
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
            comp = flat_outerwire(face)
            u, v = face.Surface.parameter(face.Surface.Apex)
            vert = Part.Vertex(FreeCAD.Vector(u, v, 0))
            comp.add(vert)
            size = 1.01 * max(abs(comp.BoundBox.YMax),
                              abs(comp.BoundBox.YLength))
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
        raise TypeError(
            f"Flattening surface of type {face.Surface.TypeId} not implemented")
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
            FreeCAD.Console.PrintError(
                f"Wire{i + 1} is not valid. Switching to Compound output.\n")
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

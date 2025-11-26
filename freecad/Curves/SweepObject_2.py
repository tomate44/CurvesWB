# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part
vec2 = FreeCAD.Base.Vector2d
from freecad.Curves import curves_to_surface
from . import TOL3D


class SortedShape:
    tol3d = TOL3D
    def __init__(self, shape, tol=tol3d):
        self.BaseShape = shape
        self.Tol3d = tol
        self.Mapping = []
        if isinstance(shape, Part.Face):
            self._wires = [SortedShape(w) for w in shape.Wires]
        elif isinstance(shape, Part.Wire):
            self._edges = [SortedShape(e) for e in shape.Edges]
        elif isinstance(shape, Part.Edge):
            self._vertexes = [SortedShape(v) for w in shape.Wires]

    def __getattr__(self, attr):
        return getattr(self.BaseShape, attr)

    @property
    def Wires(self):
        if hasattr(self, "_wires") and (len(self._wires) == len(self.Mapping)):
            return [self._wires[self.Mapping[i]] for i in range(len(self._wires))]
        return self.BaseShape.Wires

    @property
    def Edges(self):
        if hasattr(self, "_edges") and (len(self._edges) == len(self.Mapping)):
            return [self._edges[self.Mapping[i]] for i in range(len(self._edges))]
        return []

    @property
    def Vertexes(self):
        if hasattr(self, "_vertexes") and (len(self._vertexes) == len(self.Mapping)):
            return [self._vertexes[self.Mapping[i]] for i in range(len(self._vertexes))]
        return []

    def average_normal(self):
        normal = FreeCAD.Vector()
        if self.BaseShape:
            pass


class ProfileShape(SortedShape):
    """Wrapper for shapes that will be used in a surfacing operation"""

    tol3d = FreeCAD.Base.Precision.confusion()
    def __init__(self, shape, tol=tol3d, rational=False):
        super().__init__(shape, tol)
        # self.BaseShape = shape
        # self.tol3d = tol
        self.full_bspline = None
        self.polygon = None
        self.BSplines = []
        self.compute_BSplines(rational)

    @property
    def NbWires(self):
        return len(self.BaseShape.Wires)

    @property
    def NbEdges(self):
        return len(self.BaseShape.Edges)

    @property
    def NbVertexes(self):
        return len(self.BaseShape.Vertexes)

    @property
    def NbCurves(self):
        return len(self.BSplines)

    # def get_max_edge_gap(self):
    #     maxgap = 0.0
    #     for i in range(self.NbEdges - 1):
    #         e = self.BaseShape.Edges[i]
    #         comp = Part.Compound(self.BaseShape.Edges[:i] + self.BaseShape.Edges[i + 1:])
    #         dist, pts, info = e.distToShape(comp)
    #         maxgap = max(maxgap, dist)
    #     return maxgap

    def end_points_2D(self):
        sp = FreeCAD.Vector()
        ep = FreeCAD.Vector()
        ma = -1e100
        mi = 1e100
        for v in self.BaseShape.Vertexes:
            if abs(v.Y) < self.tol3d:
                if v.X > ma:
                    ma = v.X
                    ep = v.Point
                if v.X < mi:
                    mi = v.X
                    sp = v.Point
        return sp, ep

    def end_points(self):
        ov = self.BaseShape.OrderedVertexes
        vl = (ov[0], ov[-1])
        return [v.Point for v in vl]

    def compute_BSplines(self, rational=False):
        self.BSplines = []
        # Shape is a single Vertex
        if (self.NbEdges == 0):
            bs = Part.BSplineCurve()
            bs.setPole(1, self.BaseShape.Vertex1.Point)
            bs.setPole(2, self.BaseShape.Vertex1.Point)
            self.BSplines.append(bs)
        # Shape is a single Edge
        if (self.NbEdges == 1):
            e = self.BaseShape.Edge1
            if rational:
                e = self.BaseShape.Edge1.toNurbs().Edge1
            c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
            self.BSplines.append(c)
        # Shape is a single Wire
        elif (self.NbWires == 1):
            shape = self.BaseShape.Wire1
            if rational:
                shape = self.BaseShape.Wire1.toNurbs().Wire1
            for e in shape.OrderedEdges:
                c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
                self.BSplines.append(c)
        c0 = self.BSplines[0].copy()
        if len(self.BSplines) > 1:
            for c in self.BSplines[1:]:
                c0.join(c)
        self.full_bspline = c0
        self.compute_uniform_polygon()
        return self.full_bspline

    def compute_uniform_polygon(self):
        p = self.full_bspline.FirstParameter
        pts = [self.full_bspline.value(p)]
        pars = [0.0]
        if len(self.BSplines) > 1:
            for i, v in enumerate(self.BaseShape.OrderedVertexes[1:-1]):
                print(i)
                p = self.full_bspline.parameter(v.Point)
                print(p)
                pts.append(self.full_bspline.value(p))
                pars.append(float(i + 1))
        p = self.full_bspline.LastParameter
        pts.append(self.full_bspline.value(p))
        pars.append(pars[-1] + 1)
        mults = [1] * (len(pars))
        mults[0] = 2
        mults[-1] = 2
        bs = Part.BSplineCurve()
        print(pts, mults, pars)
        bs.buildFromPolesMultsKnots(pts, mults, pars, False, 1)
        self.polygon = bs
        return self.polygon


class Path2Rails:
    def __init__(self, rail1, rail2, tol=1e-7):
        self.Rail1 = ProfileShape(rail1, tol)
        self.Rail2 = ProfileShape(rail2, tol)
        # self.Face1 = face1
        # self.Face2 = face2
        # self.TangentToFaces = False
        self.ReversedNormal = False
        ruled = Part.makeRuledSurface(self.Rail1.full_bspline.toShape(),
                                      self.Rail2.full_bspline.toShape())
        self.Surface = ruled.Surface
        self.Surface.scaleKnotsToBounds(0.0, 1.0)

    def origin(self, u):
        return self.Surface.value(u, 0.0)

    def XPoint(self, u):
        return self.Surface.value(u, 1.0)

    def get_transform_matrix(self, u1, u2=-1, position=0.0):
        # obj.Rail1Length = e1.Length
        # obj.Rail2Length = e2.Length
        # p1 = e1.getParameterByLength(obj.Position1 * e1.Length)
        if u2 < 0.0 or u2 > 1.0:
            u2 = u1
        par1 = (u1, 0.0)
        par2 = (u2, 1.0)
        origin = self.Surface.value(*par1)
        ptX = self.Surface.value(*par2)
        tangent = ptX - origin
        width = tangent.Length
        tangent.normalize()
        # tan1 = self.Surface.tangent(*par1)[0]
        # tan2 = self.Surface.tangent(*par2)[0]
        # tangent = (1.0 - position) * tan1 + position * tan2
        nor1 = self.Surface.normal(*par1)
        nor2 = self.Surface.normal(*par2)
        normal = (1.0 - position) * nor1 + position * nor2
        if self.ReversedNormal:
            normal = -normal
        bino = -normal.cross(tangent)
        # if obj.NormalReverse:
        #     bino = -bino
        m = FreeCAD.Matrix(tangent.x, normal.x, bino.x, origin.x,
                           tangent.y, normal.y, bino.y, origin.y,
                           tangent.z, normal.z, bino.z, origin.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        return m, width


class TopoSweep2Rails:
    """Sweep Topo Shapes on 2 rails"""

    def __init__(self, rails, profiles, tol=1e-7):
        # rl = [SweepObject(r) for r in rails]
        self.Profiles = [ProfileShape(p, tol) for p in profiles]
        self.Rails = [ProfileShape(r, tol) for r in rails]
        # self.Path = Path2Rails(*rails, tol)
        self.tol3d = tol

    def sweep(self):
        nb_curves_list = [p.NbCurves for p in self.Profiles]
        compat_prof = (len(set(nb_curves_list)) == 1)
        r1 = self.Rails[0].full_bspline
        r2 = self.Rails[1].full_bspline
        if compat_prof:
            nb_curves = self.Profiles[0].NbCurves
            poly_profs = [p.polygon for p in self.Profiles]
            poly_rails = [r1, r2]
            s2r = curves_to_surface.CurvesOn2Rails(poly_profs, poly_rails)
            s = s2r.build_surface()
            # return s.toShape()
            full_rails = [r1]
            for i in range(nb_curves - 1):
                p = s.uIso((i + 1) / nb_curves)
                full_rails.append(p)
            full_rails.append(r2)
            rail_shapes = [r.toShape() for r in full_rails]
            # return Part.Compound(rail_shapes)
            surfs = []
            for i in range(nb_curves):
                profs = [p.BSplines[i] for p in self.Profiles]
                rails = full_rails[i:i + 2]
                s2r = curves_to_surface.CurvesOn2Rails(profs, rails)
                surfs.append(s2r.build_surface())
            faces = [s.toShape() for s in surfs]
            shell = Part.Shell(faces)
            return shell
        profs = [p.full_bspline for p in self.Profiles]
        rails = [r1, r2]
        s2r = curves_to_surface.CurvesOn2Rails(profs, rails)
        s = s2r.build_surface()
        return s.toShape()


"""
sel = FreeCADGui.Selection.getSelection()
o = sel[0]
swob = ProfileShape(o.Shape)
# print(swob.get_max_edge_gap())
Part.show(swob.full_bspline.toShape())
Part.show(swob.polygon.toShape())
"""

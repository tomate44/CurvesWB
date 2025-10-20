# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part
from Part import Geom2d
from FreeCAD import Base
from freecad.Curves import _utils

# Find the minimum distance to another shape.
# distToShape(Shape s):  Returns a list of minimum distance and solution point pairs.
#
# Returned is a tuple of three: (dist, vectors, infos).
#
# dist is the minimum distance, in mm (float value).
#
# vectors is a list of pairs of App.Vector. Each pair corresponds to solution.
# Example: [(Vector (2.0, -1.0, 2.0), Vector (2.0, 0.0, 2.0)), (Vector (2.0,
# -1.0, 2.0), Vector (2.0, -1.0, 3.0))] First vector is a point on self, second
# vector is a point on s.
#
# infos contains additional info on the solutions. It is a list of tuples:
# (topo1, index1, params1, topo2, index2, params2)
#
#     topo1, topo2 are strings identifying type of BREP element: 'Vertex',
#     'Edge', or 'Face'.
#
#     index1, index2 are indexes of the elements (zero-based).
#
#     params1, params2 are parameters of internal space of the elements. For
#     vertices, params is None. For edges, params is one float, u. For faces,
#     params is a tuple (u,v).

debug = _utils.debug


def startPoint(c):
    return c.value(c.FirstParameter)


def endPoint(c):
    return c.value(c.LastParameter)


def distToCurve(c1, c2):
    pa1 = c1.parameter(startPoint(c2))
    pa2 = c1.parameter(endPoint(c2))
    pt1 = c1.value(pa1)
    pt2 = c1.value(pa2)
    d1 = pt1 - startPoint(c2)
    d2 = pt2 - endPoint(c2)
    if d1 > d2:
        return d2, pa2, c2.LastParameter
    else:
        return d1, pa1, c2.FirstParameter


def linearDeviation(edge, radius=1.0):
    sp = edge.valueAt(edge.FirstParameter)
    ep = edge.valueAt(edge.LastParameter)
    axis = ep - sp
    cyl = Part.makeCylinder(radius, axis.Length, sp, axis)
    d, pts, info = edge.distToShape(cyl.Face1)
    params = list()
    for i in info:
        if i[0] in ("Edge", b"Edge"):
            params.append(i[2])
        elif i[0] in ("Vertex", b"Vertex"):
            params.append(edge.parameterAt(edge.Vertexes[i[1]]))
    return (radius - d), params


def isLinear(edge, tol=1e-7):
    d, params = linearDeviation(edge)
    if d < tol:
        return True
    return False


def add2d(p1, p2):
    return Base.Vector2d(p1.x + p2.x, p1.y + p2.y)


def mul2d(vec, fac):
    return Base.Vector2d(vec.x * fac, vec.y * fac)


""" Doc of Part.Geom2d.BSplineCurve2d.buildFromPolesMultsKnots()

    Builds a B-Spline by a lists of Poles, Mults, Knots.
    arguments: poles (sequence of Base.Vector), [mults , knots, periodic, degree, weights (sequence of float), CheckRational]

    Examples:
    from FreeCAD import Base
    import Part
    V=Base.Vector
    poles=[V(-10,-10),V(10,-10),V(10,10),V(-10,10)]

    # non-periodic spline
    n=Part.BSplineCurve()
    n.buildFromPolesMultsKnots(poles,(3,1,3),(0,0.5,1),False,2)
    Part.show(n.toShape())

    # periodic spline
    p=Part.BSplineCurve()
    p.buildFromPolesMultsKnots(poles,(1,1,1,1,1),(0,0.25,0.5,0.75,1),True,2)
    Part.show(p.toShape())

    # periodic and rational spline
    r=Part.BSplineCurve()
    r.buildFromPolesMultsKnots(poles,(1,1,1,1,1),(0,0.25,0.5,0.75,1),True,2,(1,0.8,0.7,0.2))
    Part.show(r.toShape())
"""


def curve2d_extend(curve, start=0.5, end=0.5):
    """Extends a Geom2d curve at each extremity, by a linear tangent
    "start" and "end" parameters are factors of curve length.
    Returns a BSplineCurve."""
    bs = curve.toBSpline(curve.FirstParameter, curve.LastParameter)
    t1 = mul2d(bs.tangent(bs.FirstParameter), -1.0)
    t2 = bs.tangent(bs.LastParameter)
    poles = bs.getPoles()
    mults = bs.getMultiplicities()
    knots = bs.getKnots()

    pre = list()
    post = list()
    for i in range(bs.Degree):
        le = bs.length() * (bs.Degree - i) / bs.Degree
        pre.append(add2d(bs.value(bs.FirstParameter), mul2d(t1, start * le)))
        post.append(add2d(bs.value(bs.LastParameter), mul2d(t2, end * le)))
    newpoles = pre + poles + post

    mults.insert(1, bs.Degree)
    mults.insert(len(mults) - 2, bs.Degree)
    prange = bs.LastParameter - bs.FirstParameter
    knots.insert(0, bs.FirstParameter - prange * start)
    knots.append(bs.LastParameter + prange * end)
    try:
        bs.buildFromPolesMultsKnots(newpoles, mults, knots, bs.isPeriodic(), bs.Degree)
    except Part.OCCError:
        print(bs.Degree)
        print(len(newpoles))
        print(sum(mults))
        print(len(knots))
    return bs


def intersection2d(curve, c1, c2):
    inter11 = curve.intersectCC(c1)
    inter12 = curve.intersectCC(c2)
    if len(inter11) > 0 and len(inter12) > 0:
        return (curve, inter11[0], inter12[0])
    else:
        return False


def get_offset_curve(bc, c1, c2, dist=0.1):
    """computes the offsetcurve2d that is at distance dist from curve bc, that intersect c1 and c2.
    Returns the offset curve and the intersection points"""
    off1 = Part.Geom2d.OffsetCurve2d(bc, dist)
    intersec = intersection2d(off1, c1, c2)
    if intersec:
        return intersec

    off2 = Part.Geom2d.OffsetCurve2d(bc, -dist)
    intersec = intersection2d(off1, c1, c2)
    if intersec:
        return intersec

    ext1 = curve2d_extend(off1, 0.2, 0.2)
    intersec = intersection2d(ext1, c1, c2)
    if intersec:
        return intersec

    ext2 = curve2d_extend(off2, 0.2, 0.2)
    intersec = intersection2d(ext2, c1, c2)
    if intersec:
        return intersec


class curveOnSurface(object):

    def __init__(self, edge=None, face=None):
        self.face = face
        self.edge = edge
        self.curve2D = None
        self.edgeOnFace = None
        self.firstParameter = 0.0
        self.lastParameter = 1.0
        self.reverseTangent = False
        self.reverseNormal = False
        self.reverseBinormal = False
        self.isValid = False
        self._closed = False
        self._reversed = False
        self.validate()

    @property
    def closed(self):
        return self._closed

    @closed.setter
    def closed(self, c):
        self._closed = c
        self.validate()

    @property
    def reversed(self):
        return self._reversed

    @reversed.setter
    def reversed(self, b):
        if self._reversed is not bool(b):
            self.reverse()

    def reverse(self):
        if self.isValid:
            print("Curve on surface: reversing")
            print("{},{}".format(self.firstParameter, self.lastParameter))
            v1 = self.curve2D.value(self.firstParameter)
            v2 = self.curve2D.value(self.lastParameter)
            self.curve2D.reverse()
            self.firstParameter = self.curve2D.parameter(v2)
            self.lastParameter = self.curve2D.parameter(v1)
            self._reversed = not self._reversed
            print("{},{}".format(self.firstParameter, self.lastParameter))
            self.edgeOnFace = self.curve2D.toShape(self.face, self.firstParameter, self.lastParameter)
            # self.edgeOnFace.Placement = self.face.Placement
        else:
            print("Cannot reverse, invalid curve on surface")

    def setEdge(self, edge):
        self.edge = edge
        self.validate()

    def getEdge(self):
        return self.edgeOnFace.transformGeometry(self.face.Placement.toMatrix())

    def setFace(self, face):
        self.face = face
        self.validate()

    def validate(self):
        c2d = None
        if (self.edge is not None) and (self.face is not None):
            c2d = self.face.curveOnSurface(self.edge)
            if not isinstance(c2d, tuple):
                # print("curveOnSurface failed")
                try:
                    newface = self.face.Surface.toShape()
                    newedges = newface.project([self.edge]).Edges
                    e0 = newedges[0]
                    c2d = newface.curveOnSurface(e0)
                    # if projection created several edges,
                    # we need to join them into a single BSpline curve.
                    if len(newedges) > 1:
                        c = c2d[0].toBSpline(c2d[1], c2d[2])
                        for e in newedges[1:]:
                            c2d, fp, lp = newface.curveOnSurface(e)
                            bs = c2d.toBSpline(fp, lp)
                            c.join(bs)
                        c2d = [c, c.FirstParameter, c.LastParameter]
                    print("CurveOnSurface projection fallback : OK.")
                except (Part.OCCError, IndexError):
                    print("CurveOnSurface projection fallback : Failed.")
            if isinstance(c2d, tuple):
                self.curve2D = c2d[0]
                self.firstParameter = c2d[1]
                self.lastParameter = c2d[2]
                self.edgeOnFace = self.curve2D.toShape(self.face, self.firstParameter, self.lastParameter)

                if isinstance(self.edgeOnFace, Part.Edge):
                    self.isValid = True
                else:
                    self.isValid = False
                    self.edgeOnFace = Part.Edge(self.edge.Curve, self.firstParameter, self.lastParameter)
            else:
                # e = self.face.project([self.edge]).Edges[0]
                self.isValid = False
                self.firstParameter = self.edge.FirstParameter
                self.lastParameter = self.edge.LastParameter
                self.edgeOnFace = Part.Edge(self.edge.Curve, self.firstParameter, self.lastParameter)
            if self._closed:
                curve = self.edgeOnFace.Curve.copy()
                curve.setPeriodic()
                self.edgeOnFace = curve.toShape()
                print("edgeOnFace is periodic : {}".format(curve.isPeriodic()))
        # self.edgeOnFace.Placement = self.face.Placement
        return self.isValid

    def valueAt(self, t):
        if self.isValid:
            return self.edgeOnFace.valueAt(t)
        else:
            p = self.edge.valueAt(t)
            surf = self.face.Surface
            u, v = surf.parameter(p)
            return self.face.Surface.value(u, v)

    def tangentAt(self, t):
        if self.isValid:
            if self.reverseTangent:
                return self.edgeOnFace.tangentAt(t).negative().normalize()
            else:
                return self.edgeOnFace.tangentAt(t).normalize()
        else:
            if self.reverseTangent:
                return self.edge.tangentAt(t).negative().normalize()
            else:
                return self.edge.tangentAt(t).normalize()

    def normalAt(self, t):
        if self.isValid:
            vec = None
            p = self.curve2D.value(t)
            vec = self.face.normalAt(p.x, p.y)
            if self.reverseNormal:
                return vec.negative().normalize()
            else:
                return vec.normalize()
        else:
            p = self.edge.valueAt(t)
            surf = self.face.Surface
            u, v = surf.parameter(p)
            if self.reverseNormal:
                return self.face.Surface.normal(u, v).negative().normalize()
            else:
                return self.face.Surface.normal(u, v).normalize()

    def binormalAt(self, t):
        ta = self.tangentAt(t)
        n = self.normalAt(t)
        if (ta is not None) and (n is not None):
            if self.reverseBinormal:
                return ta.cross(n).negative().normalize()
            else:
                return ta.cross(n).normalize()
        else:
            return None

    def tangentTo(self, t, pt):
        v = self.valueAt(t)
        n = self.normalAt(t)
        tanPlane = Part.Plane(v, n)
        line = Part.Line(pt, pt.add(n))
        ptOnPlane = tanPlane.intersect(line)
        res = []
        if isinstance(ptOnPlane, tuple):
            for el in ptOnPlane:
                if isinstance(el, (tuple, list)):
                    for e in el:
                        if isinstance(e, Part.Point):
                            res.append(FreeCAD.Vector(e.X, e.Y, e.Z).sub(v))
        return res

    def build_param_list(self, num):
        if num < 2:
            num = 2
        ran = self.lastParameter - self.firstParameter
        self.param_list = list()
        for i in range(num):
            self.param_list.append(self.firstParameter + float(i) * ran / (num - 1))
        return True

    def dot(self, v1, v2):
        v13 = FreeCAD.Vector(v1.x, v1.y, 0.0)
        v23 = FreeCAD.Vector(v2.x, v2.y, 0.0)
        return v13.dot(v23)

    def cross(self, v1, v2):
        v13 = FreeCAD.Vector(v1.x, v1.y, 0.0)
        v23 = FreeCAD.Vector(v2.x, v2.y, 0.0)
        return v13.cross(v23)

    def orientation(self, v1, v2):
        v13 = FreeCAD.Vector(v1.x, v1.y, 0.0)
        v23 = FreeCAD.Vector(v2.x, v2.y, 0.0)
        cross3d = v13.cross(v23)
        z = FreeCAD.Vector(0.0, 0.0, 1.0)
        dot = z.dot(cross3d)
        print(dot)
        if dot < 0:
            return -1.0
        else:
            return 1.0

    def normal2D(self, v):
        v3 = FreeCAD.Vector(v.x, v.y, 0.0)
        if self.reverseNormal:
            z = FreeCAD.Vector(0.0, 0.0, -1.0)
        else:
            z = FreeCAD.Vector(0.0, 0.0, 1.0)
        cr = z.cross(v3)
        return Base.Vector2d(cr.x, cr.y)

    def get_cross_curves(self, num=10, scale=1.0, untwist=False):
        pl = self.edge.Placement
        if scale == 0:
            scale = 1.0
        self.build_param_list(num)
        if untwist:
            self.param_list.reverse()
        curves = list()
        for p in self.param_list:
            p0 = self.curve2D.value(p)
            ta = self.curve2D.tangent(p)
            no = self.normal2D(ta)
            fac = scale  # * self.orientation(ta,no)
            p1 = Base.Vector2d(p0.x + no.x * fac, p0.y + no.y * fac)
            ls1 = Geom2d.Line2dSegment(p0, p1)
            edge1 = ls1.toShape(self.face, ls1.FirstParameter, ls1.LastParameter)
            edge1.Placement = pl
            curves.append(edge1)
        return curves

    def get_offset_curve2d(self, dist=0.1):
        cos = list()
        idx = -1
        nbe = len(self.face.OuterWire.Edges)
        for n, e in enumerate(self.face.OuterWire.Edges):
            c = self.face.curveOnSurface(e)
            if len(c) == 3:
                cos.append(c[0].toBSpline(c[1], c[2]))
            else:
                FreeCAD.Console.PrintError("failed to extract 2D geometry")
            if e.isPartner(self.edge):
                idx = n

        # idx is the index of the curve to offset
        # get the index of the 2 neighbour curves
        id1 = idx - 1 if idx > 0 else nbe - 1
        id2 = idx + 1 if idx < nbe - 1 else 0

        # get offset curve
        off = get_offset_curve(cos[idx], cos[id1], cos[id2], dist)
        bs = None
        if off:
            p1 = off[0].parameter(off[1])
            p2 = off[0].parameter(off[2])
            if p1 < p2:
                bs = off[0].toBSpline(p1, p2)
            else:
                bs = off[0].toBSpline(p2, p1)
        return bs

    def get_cross_curve(self, off, u=0):
        """returns cross-curve from offsetCurve off to COS at param u"""
        if u < self.firstParameter or u > self.lastParameter:
            FreeCAD.Console.PrintError("Curve_on_surface.get_cross_curve : parameter out of range\n")
            FreeCAD.Console.PrintError("{} is not in [{},{}]\n".format(u, self.firstParameter, self.lastParameter))
        if u < self.firstParameter:
            u = self.firstParameter
        elif u > self.lastParameter:
            u = self.lastParameter
        fac = (u - self.firstParameter) / (self.lastParameter - self.firstParameter)
        v = off.FirstParameter + fac * (off.LastParameter - off.FirstParameter)
        p1 = off.value(v)
        p2 = self.curve2D.value(u)
        ls = Part.Geom2d.Line2dSegment(p1, p2)
        sh = ls.toShape(self.face.Surface)
        # sh = sh.transformGeometry(self.face.Placement.toMatrix()).Edges[0]
        FreeCAD.Console.PrintMessage(" {} - {}\n".format(self.edge.Curve, str(sh.distToShape(self.edge)[0])))
        # d,pts,info = sh.distToShape(self.edge)
        # if d > 1e-8:
        #     bs = sh.Edges[0].Curve.toBSpline()
        #     bs.setPole(bs.NbPoles,pts[0][1])
        #     return bs.toShape())
        return sh

    # def get_cross_curve_toward_point(self, param, pt, scale=1.0, untwist=False):
        # pl = self.edge.Placement
        # if scale == 0:
        #     scale = 1.0
        # edge_point = self.edgeOnFace.valueAt(param)
        # vec = edge_point.sub(pt)
        # vec.normalize()
        # vec.multiply(scale)
        # point = edge_point.add(vec)
        # u0,v0 = self.face.Surface.parameter(point)
        # u1,v1 = self.face.Surface.parameter(edge_point)
        # p0 = Base.Vector2d(u0,v0)
        # p1 = Base.Vector2d(u1,v1)
        # debug("%s - %s"%(p0,p1))
        # ls1 = Geom2d.Line2dSegment(p0, p1)
        # edge1 = ls1.toShape(self.face, ls1.FirstParameter, ls1.LastParameter)
        # edge1.Placement = pl
        # return edge1

    def normalFace(self, samp, dist, tol=1e-5, sym=False):
        face = None
        if sym:
            dist /= 2.0
        ran = self.lastParameter - self.firstParameter
        pts = list()
        pars = list()
        for i in range(samp):
            t = self.firstParameter + float(i) * ran / (samp - 1)
            pts.append(self.valueAt(t).add(self.normalAt(t) * float(dist)))
            pars.append(t)
        # if self._closed:
        #     pts = pts[:-1]
        bs = Part.BSplineCurve()
        # bs.interpolate(Points = pts, Parameters = pars, PeriodicFlag = self._closed)
        bs.approximate(Points=pts, Parameters=pars, DegMin=3, DegMax=7, Tolerance=tol)
        if sym:
            pts = list()
            pars = list()
            for i in range(samp):
                t = self.firstParameter + float(i) * ran / (samp - 1)
                pts.append(self.valueAt(t).sub(self.normalAt(t) * float(dist)))
                pars.append(t)
            # if self._closed:
            #     pts = pts[:-1]
            bs2 = Part.BSplineCurve()
            # bs2.interpolate(Points = pts, Parameters = pars, PeriodicFlag = self._closed)
            bs2.approximate(Points=pts, Parameters=pars, DegMin=3, DegMax=7, Tolerance=tol)
            face = Part.makeRuledSurface(bs2.toShape(), bs.toShape())
        else:
            face = Part.makeRuledSurface(self.edgeOnFace, bs.toShape())
        if self._closed:
            surf = face.Surface.copy()
            surf.setUPeriodic()
            face = surf.toShape()
        # face.Placement = self.face.Placement
        return face.transformGeometry(self.face.Placement.toMatrix())

    def binormalFace(self, samp, dist, tol=1e-5, sym=False):
        face = None
        if sym:
            dist /= 2.0
        ran = self.lastParameter - self.firstParameter
        pts = list()
        pars = list()
        for i in range(samp):
            t = self.firstParameter + float(i) * ran / (samp - 1)
            pts.append(self.valueAt(t).add(self.binormalAt(t) * float(dist)))
            pars.append(t)
        # if self._closed:
        #     pts = pts[:-1]
        bs = Part.BSplineCurve()
        bs.approximate(Points=pts, Parameters=pars, DegMin=3, DegMax=7, Tolerance=tol)
        if sym:
            pts = list()
            pars = list()
            for i in range(samp):
                t = self.firstParameter + float(i) * ran / (samp - 1)
                pts.append(self.valueAt(t).sub(self.binormalAt(t) * float(dist)))
                pars.append(t)
            # if self._closed:
            #     pts = pts[:-1]
            bs2 = Part.BSplineCurve()
            bs2.approximate(Points=pts, Parameters=pars, DegMin=3, DegMax=7, Tolerance=tol)
            face = Part.makeRuledSurface(bs2.toShape(), bs.toShape())
        else:
            face = Part.makeRuledSurface(self.edgeOnFace, bs.toShape())
        if self._closed:
            surf = face.Surface.copy()
            surf.setUPeriodic()
            face = surf.toShape()
        # nf = face.transformGeometry(self.face.Placement.toMatrix())
        return face.transformGeometry(self.face.Placement.toMatrix())

    def get_adjacent_edges(self):
        """returns the edges of Face that are connected to Edge"""
        e1 = None
        e2 = None
        for w in self.face.Wires:
            for e in w.Edges:
                if not e.isPartner(self.edge):
                    for v in e.Vertexes:
                        if v.isPartner(self.edge.Vertexes[0]):
                            e1 = e
                        elif v.isPartner(self.edge.Vertexes[1]):
                            e2 = e
        return [e1, e2]

    def get_adjacent_edges_tangents(self):
        """returns the tangents of edges of Face that are connected to Edge"""
        e1, e2 = self.get_adjacent_edges()
        pt1 = self.face.Surface.parameter(self.edge.Vertexes[0].Point)
        cos1 = self.face.curveOnSurface(e1)
        par1 = cos1[0].parameter(Base.Vector2d(pt1[0], pt1[1]))
        tan1 = cos1[0].tangent(par1)
        return tan1


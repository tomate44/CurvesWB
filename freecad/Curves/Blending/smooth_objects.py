# -*- coding: utf-8 -*-

__title__ = ""
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """"""

from time import time
from math import pi
from operator import itemgetter

import FreeCAD
import FreeCADGui
import Part
import numpy as np

from math import pi
from .. import _utils
from .. import curves_to_surface
from ..nurbs_tools import nurbs_quad


printError = FreeCAD.Console.PrintError


# Conversion between 2D and 3D vectors

def vec3(*arg):
    if (len(arg) == 1) and isinstance(arg[0], FreeCAD.Base.Vector2d):
        return FreeCAD.Vector(arg[0].x, arg[0].y)
    else:
        return FreeCAD.Vector(*arg)


def vec2(*arg):
    if (len(arg) == 1) and isinstance(arg[0], FreeCAD.Vector):
        return FreeCAD.Base.Vector2d(arg[0].x, arg[0].y)
    else:
        return FreeCAD.Base.Vector2d(*arg)


class SmoothPoint:
    """A group formed from a 3D point and some derivatives

    Attributes
    ----------
    continuity : int
        The continuity order of this SmoothPoint.
        This is equal to the number of derivatives
    point : FreeCAD.Vector
        The location in 3D space of this SmoothPoint (D0)
    tangent : FreeCAD.Vector
        The tangent of this SmoothPoint (D1)

    Methods
    -------
    tangent_edge(size=0)
        returns the edge representing the tangent, with given size
    value(size=0)
        Returns the scaled SmoothPoint vectors, so that the tangent has given size.

    If size == 0, returns the original unscaled vectors.
    """

    def __init__(self, vecs):
        self.raw_vectors = vecs

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.raw_vectors)

    def __str__(self):
        return "{}(C{} at {})".format(self.__class__.__name__, self.continuity, self.raw_vectors[0])

    @property
    def continuity(self):
        """The continuity order of this SmoothPoint"""

        return len(self.raw_vectors) - 1

    @property
    def point(self):
        """The location in 3D space of this SmoothPoint (D0)"""

        if self.continuity >= 0:
            return self.raw_vectors[0]

    @property
    def tangent(self):
        """The tangent of this SmoothPoint (D1)"""

        if self.continuity > 0:
            return self.raw_vectors[1]
        return FreeCAD.Vector(0, 0, 0)

    def tangent_edge(self, size=1.0):
        """Returns the edge representing the tangent

        Returns the edge representing the tangent
        scaled by the supplied factor

        Parameters
        ----------
        size : float
            The desired size of the tangent vector

        Returns
        -------
        FreeCAD vector
            The edge representing the tangent
        """

        return Part.makeLine(self.point, self.point + self.tangent.normalize() * size)

    def value(self, size=0):
        """Returns the scaled SmoothPoint vectors.

        Returns the scaled SmoothPoint vectors
        so that the tangent has given size,
        or the original unscaled vectors if size == 0

        Parameters
        ----------
        size : float
            The desired size of the tangent vector
            If size == 0, the original unscaled vectors are returned

        Returns
        -------
        List of FreeCAD vectors
            The scaled vectors of this SmoothPoint
        """

        if size == 0 or self.continuity <= 0:
            return self.raw_vectors
        else:
            scale = size / self.raw_vectors[1].Length
            return [self.raw_vectors[i] * pow(scale, i) for i in range(self.continuity + 1)]


class SurfaceDirectionalDerivatives:
    """Surface directional derivatives

    Computes the (order + 1) derivatives of the surface
    at given location, in a given direction, or toward a target point.
    
    Example
    -------
    mySDD = SurfaceDirectionalDerivatives(a_surface, 3)
    mySDD.getSmoothPoint((0.5,0.5), direction=(1.0, 1.0))

    Attributes
    ----------
    Surface : Part.Geometry.Surface (or Part.Face)
        The support surface that provides the derivatives
    Continuity : Int in [0, 1, 2, 3, 4]
        The order of the last derivative to compute

    Methods
    -------
    getSmoothPoint(location, order=-1, direction=(), target=None)
        Returns the SmoothPoint at location, in given direction, or toward target point.
    """

    def __init__(self, surface, continuity=0):
        self.Surface = surface
        self.Continuity = continuity

    @property
    def Surface(self):
        return self._surface

    @Surface.setter
    def Surface(self, surf):
        if isinstance(surf, Part.Face):
            self._surface = surf.Surface
        elif surf.isDerivedFrom("Part::GeomSurface"):
            self._surface = surf
        else:
            printError(f"{self.__class__.__name__}: {surf} is not a valid Surface")
            self._surface = None

    @property
    def Continuity(self):
        return self._continuity

    @Continuity.setter
    def Continuity(self, cont):
        if (cont >= 0) and (cont <= 4):
            self._continuity = cont
        else:
            printError(f"{self.__class__.__name__}: {cont} is not a valid continuity")
            self._continuity = 0

    def projection_coords(self, v1, v2, v3):
        """Returns the coordinates of v1
        in the (v2, v3) coordinate system.
        """
        m = FreeCAD.Matrix()
        m.A11 = v2.x
        m.A12 = v3.x
        m.A21 = v2.y
        m.A22 = v3.y
        m.A31 = v2.z
        m.A32 = v3.z
        im = m.inverse()
        nv1 = im.multVec(v1)
        return nv1

    def getSmoothPoint(self, location, direction=(), target=None, order=-1):
        """Returns the point and derivatives of the surface at given location

        location : tuple/list of 2 coordinates, or Vector2d
            The (u, v) coordinates defining the point on the surface
        direction : tuple/list of 2 coordinates, or Vector2d (optional)
            The (u, v) coordinates of the direction vector of the first derivative
        target : FreeCAD.Vector (optional)
            The 3D Point toward which the first derivative will be pointing
        order : Int in [0, 1, 2, 3, 4]
            The order of the last derivative to compute.
            if order is omitted, or out of valid range, Continuity attribute is used.

        Returns
        -------
        a SmoothPoint object containing the point and derivatives of the surface.
        If order > 0, a direction, or a target point must be supplied.
        """
        if isinstance(location, FreeCAD.Base.Vector2d):
            a, b = location.x, location.y
        elif len(location) == 2:
            a, b = location
        else:
            printError(f"{self.__class__.__name__}: {location} is not a valid location")

        if (order < 0) or (order > 4):
            cont = self._continuity
        else:
            cont = order

        # C0
        pt = self._surface.getD0(a, b)
        if cont == 0:
            return SmoothPoint([pt])

        # G1
        du = self._surface.getDN(a, b, 1, 0)
        dv = self._surface.getDN(a, b, 0, 1)
        if isinstance(direction, FreeCAD.Base.Vector2d):
            x, y = direction.x, direction.y
        elif len(direction) == 2:
            x, y = direction
        elif isinstance(target, FreeCAD.Vector):
            dirv = target - pt
            # dirx = Part.makeLine(vec3(0, 0, 0), du)
            # diry = Part.makeLine(vec3(0, 0, 0), dv)
            # x = dirx.Curve.parameter(dirv) / du.Length
            # y = diry.Curve.parameter(dirv) / dv.Length
            x, y, _ = self.projection_coords(dirv, du, dv)
        else:
            raise ValueError("You must specify a direction=(float, float) or a target=FreeCAD.Vector")
        d1 = x * du + y * dv
        if cont == 1:
            return SmoothPoint([pt, d1])

        # G2
        d2u = self._surface.getDN(a, b, 2, 0)
        d2v = self._surface.getDN(a, b, 0, 2)
        duv = self._surface.getDN(a, b, 1, 1)
        d2 = pow(x, 2) * d2u + 2 * x * y * duv + pow(y, 2) * d2v
        if cont == 2:
            return SmoothPoint([pt, d1, d2])

        # G3
        d3u = self._surface.getDN(a, b, 3, 0)
        d2uv = self._surface.getDN(a, b, 2, 1)
        du2v = self._surface.getDN(a, b, 1, 2)
        d3v = self._surface.getDN(a, b, 0, 3)
        d3 = pow(x, 3) * d3u + 3 * pow(x, 2) * y * d2uv + 3 * x * pow(y, 2) * du2v + pow(y, 3) * d3v
        if cont == 3:
            return SmoothPoint([pt, d1, d2, d3])

        # G4
        d4u = self._surface.getDN(a, b, 4, 0)
        d3uv = self._surface.getDN(a, b, 3, 1)
        d2u2v = self._surface.getDN(a, b, 2, 2)
        du3v = self._surface.getDN(a, b, 1, 3)
        d4v = self._surface.getDN(a, b, 0, 4)
        d4 = (pow(x, 4) * d4u) + (4 * pow(x, 3) * y * d3uv) + (4 * pow(x, 2) * pow(y, 2) * d2u2v) + (4 * x * pow(y, 3) * du3v) + (pow(y, 4) * d4v)
        return SmoothPoint([pt, d1, d2, d3, d4])


class ValueOnEdge:
    """Interpolates a float value along an edge.
    voe = ValueOnEdge(anEdge, value=None)"""
    def __init__(self, edge, value=None):
        self._edge = edge
        self._curve = Part.BSplineCurve()
        self._pts = []
        if value is not None:
            self.set(value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.values)

    @property
    def values(self):
        return [vec2(v.x, v.y) for v in self._pts]

    def set(self, val):
        "Set a constant value, or a list of regularly spaced values"
        self._pts = []
        if isinstance(val, (list, tuple)):
            if len(val) == 1:
                val *= 2
            params = np.linspace(self._edge.FirstParameter, self._edge.LastParameter, len(val))
            for i in range(len(val)):
                self.add(val[i], abs_par=params[i], recompute=False)
        elif isinstance(val, (int, float)):
            self.set([val, val])
        self._compute()

    def _get_real_param(self, abs_par=None, rel_par=None, dist_par=None, point=None):
        """return the real edge parameter from one of the parameter values in :
        * abs_par : the real parameter
        * rel_par : the normalized parameter in [0.0, 1.0]
        * dist_par : the distance from start (if positive) or end (if negative)
        * point : parameter nearest to point"""
        if abs_par is not None:
            # if abs_par >= self._edge.FirstParameter and abs_par <= self._edge.LastParameter:
            return abs_par
        elif rel_par is not None:
            # if rel_par >= 0.0 and rel_par <= 1.0:
            return self._edge.FirstParameter + rel_par * (self._edge.LastParameter - self._edge.FirstParameter)
        elif dist_par is not None:
            # if abs(dist_par) <= self._edge.Length:
            return self._edge.getParameterByLength(dist_par)
        elif point is not None:
            p = self._edge.Curve.parameter(point)
            if p < self._edge.FirstParameter:
                p += (self._edge.LastParameter - self._edge.FirstParameter)
            elif p > self._edge.LastParameter:
                p -= (self._edge.LastParameter - self._edge.FirstParameter)
            return p
        else:
            raise ValueError("No parameter")

    def add(self, val, abs_par=None, rel_par=None, dist_par=None, point=None, recompute=True):
        """Add a value on the edge at the given parameter.
        Input:
        - val : float value
        - one of the parameter values :
        * abs_par : the real parameter
        * rel_par : the normalized parameter in [0.0, 1.0]
        * dist_par : the distance from start (if positive) or end (if negative)
        * point : parameter nearest to point
        - recompute : if True(default), recompute the interpolating curve"""
        par = self._get_real_param(abs_par, rel_par, dist_par, point)
        self._pts.append(FreeCAD.Vector(val.x, val.y, par))
        if recompute:
            self._compute()

    def reset(self):
        self._pts = []

    def _compute(self):
        if len(self._pts) < 2:
            return
        self._pts = sorted(self._pts, key=itemgetter(2))
        par = [p.z for p in self._pts]
        if self._edge.isClosed() and self._edge.Curve.isPeriodic() and len(self._pts) > 2:
            self._curve.interpolate(Points=self._pts[:-1], Parameters=par, PeriodicFlag=True)
        else:
            self._curve.interpolate(Points=self._pts, Parameters=par, PeriodicFlag=False)

    def _value(self, pt):
        return vec2(pt.x, pt.y)

    def valueAt(self, abs_par=None, rel_par=None, dist_par=None, point=None):
        """Returns an interpolated value at the given parameter.
        Input:
        - one of the parameter values :
        * abs_par : the real parameter
        * rel_par : the normalized parameter in [0.0, 1.0]
        * dist_par : the distance from start (if positive) or end (if negative)
        * point : parameter nearest to point"""
        if len(self._pts) == 1:
            return self._value(self._pts[0])
        par = self._get_real_param(abs_par, rel_par, dist_par)
        return self._value(self._curve.value(par))


class SmoothEdge:
    """Defines an edge that can produce SmoothPoints.
    smed = SmoothEdge(myEdge, continuity=2)
    print(smed.valueAt(0.5))
    will return the point and the 2 derivatives
    located at parameter 0.5 on myEdge."""
    def __init__(self, edge, continuity=1):
        self.continuity = continuity
        self.edge = edge
        self._fp = self._edge.FirstParameter
        self._lp = self._edge.LastParameter

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__,
                                   self.edge, self.continuity)

    @property
    def edge(self):
        "The support edge"
        return self._edge

    @edge.setter
    def edge(self, edge):
        if isinstance(edge, Part.Wire):
            self._edge = edge.approximate(1e-10, 1e-7, 999, 25)
        elif edge.isDerivedFrom("Part::GeomCurve"):
            self._edge = edge.toShape()
        else:
            self._edge = edge

    def valueAt(self, par):
        res = [self._edge.Curve.getD0(par), ]
        if self._continuity > 0:
            res.extend([self._edge.Curve.getDN(par, i + 1) for i in range(self._continuity)])
        return SmoothPoint(res)


class SmoothEdgeOnFace(SmoothEdge):
    """Defines an smooth edge on a face.
    smedof = SmoothEdgeOnFace(myEdge, myFace, continuity=2)"""
    def __init__(self, edge, face, continuity=1):
        super().__init__(edge, continuity)
        self.face = face
        self.aux_curve = vec2(0, 1)
        self.sdd = SurfaceDirectionalDerivatives(face, continuity)

    def __repr__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__,
                                       self.edge, self.face, self.continuity)

    @property
    def face(self):
        "The support face of this SmoothEdge"
        return self._face

    @face.setter
    def face(self, face):
        if face.isDerivedFrom("Part::GeomSurface"):
            self._face = face.toShape()
        else:
            self._face = face

    def getOutside(self, par=0.5, eps=1e-3):
        c2d, fp, lp = self._face.curveOnSurface(self._edge)
        p = fp + par * (lp - fp)
        pt = c2d.value(p)
        t = c2d.tangent(p)
        pod1 = self._face.isPartOfDomain(pt.x + t.y * eps, pt.y - t.x * eps)
        pod2 = self._face.isPartOfDomain(pt.x - t.y * eps, pt.y + t.x * eps)
        if pod2 and (not pod1):
            return -1
        elif pod1 and (not pod2):
            return 1
        return False

    def setOutside(self, reverse=False, par=0.5, eps=1e-3):
        outs = self.getOutside(par, eps)
        if outs is not False:
            if reverse:
                self.aux_curve = vec2(0, -outs)
            else:
                self.aux_curve = vec2(0, outs)

    def fresnetPlaneAt(self, par):
        o = self._edge.valueAt(par)
        x = self._edge.tangentAt(par)
        n = self._face.normalAt(*self._face.Surface.parameter(o))
        y = n.cross(x)
        return Part.Plane(o, o + x, o + y)

    def getValue(self, curve, par):
        rp = (par - self._fp) / (self._lp - self._fp)
        np = curve.FirstParameter + rp * (curve.LastParameter - curve.FirstParameter)
        if hasattr(curve, "valueAt"):
            return curve.valueAt(np)
        elif hasattr(curve, "value"):
            return curve.value(np)

    def crossDirAt(self, par):
        fp = self.fresnetPlaneAt(par)
        if isinstance(self.aux_curve, FreeCAD.Base.Vector2d):
            pt = fp.value(self.aux_curve.x, self.aux_curve.y)
        elif isinstance(self.aux_curve, Part.Geom2d.Curve2d):
            pt2d = self.getValue(self.aux_curve, par)
            pt = fp.value(pt2d.x, pt2d.y)
        elif isinstance(self.aux_curve, FreeCAD.Vector):
            pt = self.aux_curve
        else:
            pt = self.getValue(self.aux_curve, par)
        # quad = self.D1QuadAt(par)
        # return quad.parameter(pt)
        return pt

    def valueAt(self, par):
        location = self._face.Surface.parameter(self._edge.valueAt(par))
        pt = self.crossDirAt(par)
        return self.sdd.getSmoothPoint(location, target=pt)

    def valueAtPoint(self, pt):
        # TODO Check valid range
        return self.valueAt(self._edge.Curve.parameter(pt))

    def shape(self, num=10, size=1.0):
        params = np.linspace(self._edge.FirstParameter, self._edge.LastParameter, num)
        edges = []
        for p in params:
            sp = self.valueAt(p).value(size)
            pts = [sp[0], sp[0] + sp[1], self.crossDirAt(p)]
            edges.append(Part.makePolygon(pts))
        return Part.Compound(edges)


"""
from importlib import reload
vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d
from freecad.Curves.Blending import smooth_objects
reload(smooth_objects)
o = smooth_objects.SmoothEdgeOnFace(e1, f1, 3)
o.setOutside()
o.aux_curve = v1.Point
Part.show(o.shape(30))


"""
























class BlendCurve:
    """BlendCurve generates a bezier curve that
    smoothly interpolates two PointOnEdge objects"""
    def __init__(self, point1, point2):
        self.min_method = 'Nelder-Mead'
        self.min_options = {"maxiter": 2000, "disp": False}
        self.point1 = point1
        self.point2 = point2
        self._curve = Part.BezierCurve()
        self.nb_samples = 32

    def __repr__(self):
        return "{}(Edge1({:3.3f}, G{}), Edge2({:3.3f}, G{}))".format(self.__class__.__name__,
                                                                     self.point1.parameter,
                                                                     self.point1.continuity,
                                                                     self.point2.parameter,
                                                                     self.point2.continuity)

    @staticmethod
    def can_minimize():
        try:
            from scipy.optimize import minimize
            return True
        except ImportError:
            return False

    @property
    def point1(self):
        "The PointOnEdge object that defines the start of the BlendCurve"
        return self._point1

    @point1.setter
    def point1(self, p):
        self._point1 = p

    @property
    def point2(self):
        "The PointOnEdge object that defines the end of the BlendCurve"
        return self._point2

    @point2.setter
    def point2(self, p):
        self._point2 = p

    @property
    def scale1(self):
        "The scale of the first PointOnEdge object"
        return self.point1.size / self.chord_length

    @scale1.setter
    def scale1(self, s):
        self.point1.size = s * self.chord_length

    @property
    def scale2(self):
        "The scale of the second PointOnEdge object"
        return self.point2.size / self.chord_length

    @scale2.setter
    def scale2(self, s):
        self.point2.size = s * self.chord_length

    @property
    def scales(self):
        "The scales of the two PointOnEdge objects"
        return self.scale1, self.scale2

    @scales.setter
    def scales(self, s):
        self.scale1 = s
        self.scale2 = s

    @property
    def chord_length(self):
        return max(1e-6, self.point1.point.distanceToPoint(self.point2.point))

    @property
    def curve(self):
        "Returns the Bezier curve that represent the BlendCurve"
        return self._curve

    @property
    def shape(self):
        "Returns the edge that represent the BlendCurve"
        return self._curve.toShape()

    def perform(self, vecs=None):
        "Generate the Bezier curve that interpolates the 2 points"
        if vecs is None:
            self._curve.interpolate([self.point1.vectors, self.point2.vectors])
        else:
            self._curve.interpolate(vecs)
        return self._curve

    def auto_orient(self, tol=1e-3):
        """Automatically orient the 2 point tangents
        blend_curve.auto_orient(tol=1e-3)
        Tolerance is used to detect parallel tangents"""
        line1 = self.point1.get_tangent_edge()
        line2 = self.point2.get_tangent_edge()
        p1 = line1.Curve.parameter(self.point2.point)
        p2 = line2.Curve.parameter(self.point1.point)
        if p1 < 0:
            self.scale1 = -self.scale1
        if p2 > 0:
            self.scale2 = -self.scale2

    def auto_scale(self, auto_orient=True):
        """Sets the scale of the 2 points proportional to chord length
        blend_curve.auto_scale(auto_orient=True)
        Can optionally start with an auto_orientation"""

        # nb = self.point1.continuity + self.point2.continuity + 1
        # chord_length = self.point1.point.distanceToPoint(self.point2.point)
        # print("Tan1 : {:3.3f}, Tan2 : {:3.3f}".format(self.point1.tangent.Length, self.point2.tangent.Length))
        self.scale1 = 1.0  # 0.5 / (1 + self.point1.continuity)
        self.scale2 = 1.0  # 0.5 / (1 + self.point2.continuity)
        if auto_orient:
            self.auto_orient()
        # print("Tan1 : {:3.3f}, Tan2 : {:3.3f}".format(self.point1.tangent.Length, self.point2.tangent.Length))

    # Curve evaluation methods
    def _curvature_regularity_score(self, scales):
        "Returns difference between max and min curvature along curve"
        self.scale1, self.scale2 = scales
        self.perform()
        curva_list = [self.curve.curvature(p / self.nb_samples) for p in range(self.nb_samples + 1)]
        return (max(curva_list) - min(curva_list))

    def _cp_regularity_score(self, scales):
        "Returns difference between max and min distance between consecutive poles"
        self.scale1, self.scale2 = scales
        self.perform()
        pts = self.curve.getPoles()
        vecs = []
        for i in range(1, self.curve.NbPoles):
            vecs.append(pts[i] - pts[i - 1])
        poly = Part.makePolygon(pts)
        llist = [v.Length for v in vecs]
        return poly.Length + (max(llist) - min(llist))

    def _total_cp_angular(self, scales):
        "Returns difference between max and min angle between consecutive poles"
        self.scale1, self.scale2 = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        angles = []
        for i in range(1, len(poly.Edges)):
            angles.append(poly.Edges[i - 1].Curve.Direction.getAngle(poly.Edges[i].Curve.Direction))
        return (max(angles) - min(angles))

    def set_regular_poles(self):
        """Iterative function that sets
        a regular distance between control points"""
        self.scales = 1.0
        self.auto_orient()
        minimize(self._cp_regularity_score,
                 [self.scale1, self.scale2],
                 method=self.min_method,
                 options=self.min_options)

    def minimize_curvature(self):
        """Iterative function that tries to minimize
        the curvature along the curve
        nb_samples controls the number of curvature samples"""
        self.scales = 1.0
        self.auto_orient()
        minimize(self._curvature_regularity_score,
                 [self.scale1, self.scale2],
                 method=self.min_method,
                 options=self.min_options)

    def minimize_angular_variation(self):
        """Iterative function that tries to minimize
        the angular deviation between consecutive control points"""
        self.scales = 1.0
        self.auto_orient()
        minimize(self._total_cp_angular,
                 [self.scale1, self.scale2],
                 method=self.min_method,
                 options=self.min_options)



def add2d(p1, p2):
    return vec2(p1.x + p2.x, p1.y + p2.y)


def mul2d(vec, fac):
    return vec2(vec.x * fac, vec.y * fac)


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


class EdgeOnFace:
    """Defines an edge located on a face.
    Provides derivative data to create smooth surface from this edge.
    The property 'continuity' defines the number of derivative vectors.
    """
    def __init__(self, edge, face, continuity=1):
        self._face = face
        self._edge = edge
        self._offset = None
        self._angle = ValueOnEdge(edge, 90.0)
        self._size = ValueOnEdge(edge, 1.0)
        self.continuity = continuity

    def __repr__(self):
        return "{} (Edge {}, Face {}, G{})".format(self.__class__.__name__,
                                                   hex(id(self._edge)),
                                                   hex(id(self._face)),
                                                   self.continuity)

    def _get_real_param(self, abs_par=None, rel_par=None, dist_par=None):
        """Check range and return the real edge parameter from:
        - the real parameter
        - the normalized parameter in [0.0, 1.0]
        - the distance from start (if positive) or end (if negative)"""
        if abs_par is not None:
            # if abs_par < self._edge.FirstParameter:
            #    abs_par = self._edge.FirstParameter
            # elif abs_par > self._edge.LastParameter:
            #    abs_par = self._edge.LastParameter
            return abs_par
        elif rel_par is not None:
            # if rel_par < 0.0:
            #   rel_par = 0.0
            # elif rel_par > 1.0:
            #   rel_par = 1.0
            return self._edge.FirstParameter + rel_par * (self._edge.LastParameter - self._edge.FirstParameter)
        elif dist_par is not None:
            # if dist_par < -self._edge.Length:
            #   dist_par = -self._edge.Length
            # elif dist_par > self._edge.Length:
            #   dist_par = self._edge.Length
            return self._edge.getParameterByLength(dist_par)
        else:
            raise ValueError("No parameter")

    def _relative_param(self, par):
        "returns relative parameter corresponding to given real parameter"
        return (par - self._edge.FirstParameter) / (self._edge.LastParameter - self._edge.FirstParameter)

    @property
    def continuity(self):
        "Defines the number of derivative vectors of this EdgeOnFace"
        return self._continuity

    @continuity.setter
    def continuity(self, val):
        if val < 0:
            self._continuity = 0
        elif val > 5:
            self._continuity = 5
        else:
            self._continuity = val

    @property
    def angle(self):
        "Returns the object that defines angle along the edge"
        return self._angle

    @angle.setter
    def angle(self, angle):
        self._angle.set(angle)

    @property
    def size(self):
        "Returns the object that defines size along the edge"
        return self._size

    @size.setter
    def size(self, size):
        self._size.set(size)

    def get_offset_curve2d(self, dist=0.1):
        cos = list()
        idx = -1
        nbe = len(self._face.OuterWire.OrderedEdges)
        for n, e in enumerate(self._face.OuterWire.OrderedEdges):
            c = self._face.curveOnSurface(e)
            if len(c) == 3:
                cos.append(c[0].toBSpline(c[1], c[2]))
            else:
                FreeCAD.Console.PrintError("failed to extract 2D geometry")
            if e.isPartner(self._edge):
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

    def curve_on_surface(self):
        cos = self._face.curveOnSurface(self._edge)
        if cos is None:
            proj = self._face.project([self._edge])
            cos = self._face.curveOnSurface(proj.Edge1)
        return cos

    def cross_curve(self, abs_par=None, rel_par=None, dist_par=None):
        par = self._get_real_param(abs_par, rel_par, dist_par)
        if self._offset is None:
            self._offset = self.get_offset_curve2d()
        cos, fp, lp = self.curve_on_surface()
        off_par = self._offset.FirstParameter + self._relative_param(par) * (self._offset.LastParameter - self._offset.FirstParameter)
        line = Part.Geom2d.Line2dSegment(self._offset.value(off_par), cos.value(par))
        line3d = line.toShape(self._face.Surface)
        # line3d.reverse()
        return line3d

    def valueAtPoint(self, pt):
        "Returns PointOnEdge object at given point"
        if isinstance(pt, FreeCAD.Vector):
            par = self._edge.Curve.parameter(pt)
            if par < self._edge.FirstParameter and self._edge.Curve.isClosed():
                par += self._edge.LastParameter - self._edge.FirstParameter
            return self.value(abs_par=par)

    def value(self, abs_par=None, rel_par=None, dist_par=None):
        """Returns PointOnEdge object at given parameter:
        - abs_par : the real parameter
        - rel_par : the normalized parameter in [0.0, 1.0]
        - dist_par : the distance from start (if positive) or end (if negative)"""
        par = self._get_real_param(abs_par, rel_par, dist_par)
        cc = self.cross_curve(abs_par=par)
        d, pts, info = cc.distToShape(self._edge)
        new_par = cc.Curve.parameter(pts[0][0])
        size = self.size.value(abs_par=par)
        if cc:
            poe = PointOnEdge(cc, new_par, self.continuity, size)
            return poe

    def discretize(self, num=10):
        "Returns a list of num PointOnEdge objects along edge"
        poe = []
        for i in np.linspace(0.0, 1.0, num):
            poe.append(self.value(rel_par=i))
        return poe

    def shape(self, num=10):
        "Returns a compound of num PointOnEdge objects along edge"
        return Part.Compound([poe.rear_segment() for poe in self.discretize(num)])


class BlendSurface:
    """BSpline surface that smoothly interpolates two EdgeOnFace objects"""
    def __init__(self, edge1, face1, edge2, face2):
        self.edge1 = SmoothEdgeOnFace(edge1, face1)
        self.edge2 = SmoothEdgeOnFace(edge2, face2)
        self._ruled_surface = None
        self._surface = None
        self._curves = []

    def __repr__(self):
        return "{}(Edge1({}, G{}), Edge2({}, G{}))".format(self.__class__.__name__,
                                                           hex(id(self.edge1)),
                                                           self.edge1.continuity,
                                                           hex(id(self.edge2)),
                                                           self.edge2.continuity)

    @property
    def continuity(self):
        "Returns the continuities of the BlendSurface"
        return [self.edge1.continuity, self.edge2.continuity]

    @continuity.setter
    def continuity(self, args):
        if isinstance(args, (int, float)):
            self.edge1.continuity = args
            self.edge2.continuity = args
        elif isinstance(args, (list, tuple)):
            self.edge1.continuity = args[0]
            self.edge2.continuity = args[1]

    @property
    def curves(self):
        "Returns the Blend curves that represent the BlendSurface"
        return self._curves

    @property
    def edges(self):
        "Returns the compound of edges that represent the BlendSurface"
        el = [c.toShape() for c in self._curves]
        return Part.Compound(el)

    @property
    def surface(self):
        "Returns the BSpline surface that represent the BlendSurface"
        # self.perform()
        guides = [bezier.toBSpline() for bezier in self._curves]
        # builder = GordonSurfaceBuilder(guides, self.rails, [0.0, 1.0], self._params)
        # s2r = curves_to_surface.CurvesOn2Rails(guides, self.rails)
        cts = curves_to_surface.CurvesToSurface(guides)
        # cts.set_parameters(1.0)
        cts.Parameters = self._params
        s1 = cts.interpolate()
        s2 = curves_to_surface.ruled_surface(self.rails[0].toShape(), self.rails[1].toShape(), True).Surface
        s2.exchangeUV()
        s3 = curves_to_surface.U_linear_surface(s1)
        gordon = curves_to_surface.Gordon(s1, s2, s3)
        self._surface = gordon.Surface
        return self._surface

    @property
    def face(self):
        "Returns the face that represent the BlendSurface"
        return self.surface.toShape()

    @property
    def rails(self):
        u0, u1, v0, v1 = self.ruled_surface.bounds()
        return self.ruled_surface.vIso(v0), self.ruled_surface.vIso(v1)

    @property
    def ruled_surface(self):
        if self._ruled_surface is None:
            self._ruled_surface = _utils.ruled_surface(self.edge1._edge, self.edge2._edge, True).Surface
        return self._ruled_surface

    def sample(self, num=3):
        ruled = self.ruled_surface
        u0, u1, v0, v1 = ruled.bounds()
        e1, e2 = self.rails
        if isinstance(num, int):
            params = np.linspace(u0, u1, num)
        return params

    def blendcurve_at(self, par):
        r1, r2 = self.rails
        return BlendCurve(self.edge1.valueAtPoint(r1.value(par)), self.edge2.valueAtPoint(r2.value(par)))

    def minimize_curvature(self, arg=3):
        self.edge1.size.reset()
        self.edge2.size.reset()
        e1, e2 = self.rails
        for p in self.sample(arg):
            bc = self.blendcurve_at(p)
            # print("Minimizing curvature @ {:3.3f} = ({:3.3f}, {:3.3f})".format(p, bc.point1.size, bc.point2.size))
            bc.minimize_curvature()
            self.edge1.size.add(val=bc.point1.size, point=e1.value(p))
            self.edge2.size.add(val=bc.point2.size, point=e2.value(p))
            # print("Minimized curvature @ {:3.3f} = ({:3.3f}, {:3.3f})".format(p, bc.point1.size, bc.point2.size))

    def auto_scale(self, arg=3):
        self.edge1.size.reset()
        self.edge2.size.reset()
        e1, e2 = self.rails
        for p in self.sample(arg):
            bc = self.blendcurve_at(p)
            bc.auto_scale()
            self.edge1.size.add(val=bc.point1.size, point=e1.value(p))
            self.edge2.size.add(val=bc.point2.size, point=e2.value(p))
            # print("Auto scaling @ {:3.3f} = ({:3.3f}, {:3.3f})".format(p, bc.point1.size, bc.point2.size))

    def perform(self, arg=20):
        bc_list = []
        for p in self.sample(arg):
            bc = self.blendcurve_at(p)
            # print("Computing BlendCurve @ {} from {} to {}".format(p, bc.point1.point, bc.point2.point))
            bc_list.append(bc.perform())
        self._curves = bc_list
        self._params = self.sample(arg)


def test_blend_surface():
    doc1 = FreeCAD.openDocument('/home/tomate/Documents/FC-Files/test_BlendSurface_1.FCStd')
    o1 = doc1.getObject('Ruled_Surface001')
    e1 = o1.Shape.Edge1
    f1 = o1.Shape.Face1
    o2 = doc1.getObject('Ruled_Surface')
    e2 = o2.Shape.Edge3
    f2 = o2.Shape.Face1

    from freecad.Curves import blend_curve as bc

    num = 21

    bs = bc.BlendSurface(e1, f1, e2, f2)
    # bs.edge1.angle = (90, 80, 100, 90)
    # bs.edge2.angle = (90, 90, 90, 70)
    bs.continuity = 3
    bs.minimize_curvature()
    # bs.auto_scale()
    bs.perform(num)
    Part.show(bs.edges)
    bsface = bs.face
    Part.show(bsface)
    shell = Part.Shell([f1, bsface, f2])
    print("Valid shell : {}".format(shell.isValid()))
    shell.check(True)


def main():
    # selection
    sel = FreeCADGui.Selection.getSelectionEx()
    edges = []
    pp = []
    for s in sel:
        edges.extend(s.SubObjects)
        pp.extend(s.PickedPoints)

    e0 = edges[0]
    p0 = e0.Curve.parameter(pp[0])
    e1 = edges[1]
    p1 = e1.Curve.parameter(pp[1])

    start = time()
    poe1 = PointOnEdge(e0, p0, 3)
    poe2 = PointOnEdge(e1, p1, 3)
    poe1.scale1 = 0.1
    poe2.scale2 = 0.1
    fillet = BlendCurve(poe1, poe2)
    fillet.nb_samples = 200
    fillet.auto_orient()
    # fillet.auto_scale()
    # fillet.minimize_angular_variation()
    # fillet.set_regular_poles()
    fillet.minimize_curvature()
    fillet.perform()
    print("Minimize time = {}s".format(time() - start))
    print("Final scales = {} - {}".format(poe1.tangent.Length, poe2.tangent.Length))
    Part.show(fillet.curve.toShape())
    return fillet


if __name__ == '__main__':
    main()

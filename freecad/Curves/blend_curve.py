# -*- coding: utf-8 -*-

__title__ = ""
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """"""

from time import time
from math import pi

import FreeCAD
import FreeCADGui
import Part
import numpy as np

from .gordon import InterpolateCurveNetwork
from . import _utils

CAN_MINIMIZE = True

try:
    from scipy.optimize import minimize
except ImportError:
    CAN_MINIMIZE = False

vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d


class PointOnEdge:
    """Defines a point and some derivative vectors
    located at a given 'parameter' on an 'edge'.
    The property 'continuity' defines the number of derivative vectors.
    Example :
    poe = PointOnEdge(myEdge, 0.0, 2)
    print(poe.vectors)
    will return the point and the 2 derivatives located at parameter 0.0
    on myEdge.
    """
    def __init__(self, edge, parameter=None, continuity=1, size=1.0):
        self._parameter = 0.0
        self._continuity = 1
        self._vectors = []
        self._scale = 1.0
        self._size = size
        self.edge = edge
        if parameter is None:
            self.to_start()
        else:
            self.parameter = parameter
        self.continuity = continuity

    def __repr__(self):
        return "{}(Edge({}),{},{})".format(self.__class__.__name__,
                                           hex(id(self.edge)),
                                           self.parameter,
                                           self.continuity)

    def __str__(self):
        return "{} (Edge({}), {:3.3f}, G{})".format(self.__class__.__name__,
                                                    hex(id(self.edge)),
                                                    self.parameter,
                                                    self.continuity)

    def set_vectors(self):
        res = [self._edge.Curve.getD0(self._parameter)]
        if self._continuity > 0:
            res.extend([self._edge.Curve.getDN(self._parameter, i) for i in range(1, self._continuity + 1)])
        self._vectors = res
        self.size = self._size

    def recompute_vectors(func):
        """Decorator that recomputes the point and derivative vectors"""
        def wrapper(self, arg):
            func(self, arg)
            self.set_vectors()
        return wrapper

    @property
    def parameter(self):
        "Defines the location of this PointOnEdge along the edge"
        return self._parameter

    @parameter.setter
    @recompute_vectors
    def parameter(self, par):
        if par < self._edge.FirstParameter:
            self._parameter = self._edge.FirstParameter
        elif par > self._edge.LastParameter:
            self._parameter = self._edge.LastParameter
        else:
            self._parameter = par

    @property
    def distance(self):
        "Defines the location of this PointOnEdge along the edge, by distance"
        segment = self._edge.Curve.toShape(self._edge.FirstParameter, self._parameter)
        return segment.Length

    @distance.setter
    def distance(self, dist):
        if dist > self._edge.Length:
            self.parameter = self._edge.LastParameter
        elif dist < -self._edge.Length:
            self.parameter = self._edge.FirstParameter
        else:
            self.parameter = self._edge.getParameterByLength(dist)

    @property
    def continuity(self):
        "Defines the number of derivative vectors of this PointOnEdge"
        return self._continuity

    @continuity.setter
    @recompute_vectors
    def continuity(self, val):
        if val < 0:
            self._continuity = 0
        elif val > 5:
            self._continuity = 5
        else:
            self._continuity = val

    @property
    def edge(self):
        "The support edge of this PointOnEdge"
        return self._edge

    @edge.setter
    @recompute_vectors
    def edge(self, edge):
        if isinstance(edge, Part.Wire):
            self._edge = edge.approximate(1e-10, 1e-7, 999, 25)
        elif edge.isDerivedFrom("Part::GeomCurve"):
            self._edge = edge.toShape()
        else:
            self._edge = edge

    # Public access to vectors
    def __getitem__(self, key):
        if key < len(self._vectors):
            return self._vectors[key] * pow(self._scale, key)

    @property
    def point(self):
        return self._vectors[0]

    @property
    def tangent(self):
        if len(self._vectors) > 1:
            return self._vectors[1] * self._scale

    @property
    def vectors(self):
        return [self._vectors[i] * pow(self._scale, i) for i in range(len(self._vectors))]
    # ########################

    @property
    def size(self):
        "The size of the tangent vector"
        return self._size

    @size.setter
    def size(self, val):
        """Scale the vectors so that tangent has the given length"""
        if abs(val) < 1e-7:
            raise ValueError("Size too small")
        self._size = val
        if len(self._vectors) > 1:
            self._scale = val / self._vectors[1].Length

    @property
    def bounds(self):
        return self._edge.ParameterRange

    def to_start(self):
        "Set point on edge's start"
        self.parameter = self._edge.FirstParameter

    def to_end(self):
        "Set point on edge's end"
        self.parameter = self._edge.LastParameter

    def reverse(self):
        """Reverse the odd derivative vectors by inverting the scale"""
        self.size = -self._size

    def get_tangent_edge(self):
        if self._continuity > 0:
            return Part.makeLine(self.point, self.point + self.tangent)

    def split_edge(self, first=True):
        "Cut the support edge at parameter, and return a wire"
        if (self._parameter > self._edge.FirstParameter) and (self._parameter < self._edge.LastParameter):
            return self._edge.split(self._parameter)
        else:
            return Part.Wire([self._edge])

    def first_segment(self):
        if self._parameter > self._edge.FirstParameter:
            return self._edge.Curve.toShape(self._edge.FirstParameter, self._parameter)

    def last_segment(self):
        if self._parameter < self._edge.LastParameter:
            return self._edge.Curve.toShape(self._parameter, self._edge.LastParameter)

    def front_segment(self):
        "Returns to edge segment that is in front of the tangent"
        if self._scale > 0:
            return [self.last_segment()]
        else:
            fs = self.first_segment()
            if fs:
                return [fs.reversed()]
        return []

    def rear_segment(self):
        "Returns to edge segment that is behind the tangent"
        if self._scale < 0:
            return [self.last_segment()]
        else:
            fs = self.first_segment()
            if fs:
                return [fs.reversed()]
        return []

    def shape(self):
        vecs = [FreeCAD.Vector()] + self.vectors[1:]
        pts = [p + self.point for p in vecs]
        return Part.makePolygon(pts)


class EdgeOnFace:
    """Defines an edge located on a face.
    Provides derivative data to create smooth surface from this edge.
    The property 'continuity' defines the number of derivative vectors.
    """
    def __init__(self, edge, face, continuity=1):
        self._face = face
        self._edge = edge
        self.set_angle(90.0)
        self.set_parameter(0.0)
        self.set_size(1.0)
        self.continuity = continuity

    def __repr__(self):
        return "{} (Edge {}, Face {}, G{})".format(self.__class__.__name__,
                                                   hex(id(self._edge)),
                                                   hex(id(self._face)),
                                                   self.continuity)

    def set_curve(func):
        """Decorator that creates an interpolating curve of values"""
        def wrapper(self, arg):
            periodic = False
            if hasattr(arg, "value"):
                func(self, arg)
            else:
                if isinstance(arg, (list, tuple)):
                    pts = []
                    par = []
                    for i, pair in enumerate(arg):
                        if isinstance(pair, (list, tuple)):
                            p, v = pair
                        elif isinstance(pair, (int, float)):
                            p = i / (len(arg) - 1)
                            v = pair
                        pts.append(FreeCAD.Vector(p, v, 0.0))
                        par.append(p)
                elif isinstance(arg, (int, float)):
                    pts = [FreeCAD.Vector(0, arg, 0.0),
                           FreeCAD.Vector(1, arg, 0.0)]
                    par = [0.0, 1.0]
                if len(pts) > 2 and self._edge.Curve.isPeriodic():
                    periodic = True
                    pts = pts[:-1]
                bs = Part.BSplineCurve()
                bs.interpolate(Points=pts, Parameters=par, PeriodicFlag=periodic)
                func(self, bs)
        return wrapper

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

    def get_real_param(self, param):
        if param < 0.0:
            param = 0.0
        elif param > 1.0:
            param = 1.0
        return self._edge.FirstParameter + param * (self._edge.LastParameter - self._edge.FirstParameter)

    def curve_on_surface(self):
        cos = self._face.curveOnSurface(self._edge)
        if cos is None:
            proj = self._face.project([self._edge])
            cos = self._face.curveOnSurface(proj.Edge1)
        return cos

    def cross_curve(self, param):
        bounds = self._face.ParameterRange
        cos, fp, lp = self.curve_on_surface()
        point = cos.value(self.get_real_param(param))
        tangent = cos.tangent(self.get_real_param(param))
        line = Part.Geom2d.Line2d(point, FreeCAD.Base.Vector2d(point.x + tangent.x, point.y + tangent.y))
        line.rotate(point, self.get_angle(param) * pi / 180)
        line3d = line.toShape(self._face.Surface, min(bounds), max(bounds))
        line3d.reverse()
        return line3d

    def get_angle(self, par):
        "Returns the angle of the cross curve at given parameter"
        return self._angle.value(par).y

    @set_curve
    def set_angle(self, angle=90.0):
        "Sets the angle of the cross curves"
        self._angle = angle

    def get_size(self, par):
        "Returns the size of the cross curve at given parameter"
        return self._size.value(par).y

    @set_curve
    def set_size(self, size=1.0):
        "Sets the size of the cross curves"
        self._size = size

    def get_parameter(self, par):
        "Returns the parameter on the cross curve at given parameter on base edge"
        return self._parameter.value(par).y

    @set_curve
    def set_parameter(self, parameter=0.0):
        "Sets the parameter on the cross curve"
        self._parameter = parameter

    def value(self, param):
        if isinstance(param, FreeCAD.Vector):
            param = self._edge.Curve.parameter(param)
        cc = self.cross_curve(param)
        par = self.get_parameter(param)
        size = self.get_size(param)
        return PointOnEdge(cc, par, self.continuity, size)

    def discretize(self, num=10):
        poe = []
        for i in np.linspace(0.0, 1.0, num):
            poe.append(self.value(i))
        return poe

    def shape(self, num=10):
        return Part.Compound([poe.shape() for poe in self.discretize(num)])


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
        if self.point1.continuity < 1 or self.point2.continuity < 1:
            return False
        line1 = self.point1.get_tangent_edge()
        line2 = self.point2.get_tangent_edge()
        cross = self.point1.tangent.cross(self.point2.tangent)
        if cross.Length < tol:  # tangent lines
            p1 = line1.Curve.parameter(self.point2.point)
            p2 = line2.Curve.parameter(self.point1.point)
        else:
            long_line1 = line1.Curve.toShape(-1e20, 1e20)
            long_line2 = line2.Curve.toShape(-1e20, 1e20)
            dist, pts, info = long_line1.distToShape(long_line2)
            p1 = info[0][2]
            p2 = info[0][5]
        if p1 < 0:
            self.scale1 = -self.scale1
        if p2 > 0:
            self.scale2 = -self.scale2

    def auto_scale(self, auto_orient=True):
        """Sets the scale of the 2 points proportional to chord length
        blend_curve.auto_scale(auto_orient=True)
        Can optionaly start with an auto_orientation"""

        # nb = self.point1.continuity + self.point2.continuity + 1
        # chord_length = self.point1.point.distanceToPoint(self.point2.point)
        # print("Tan1 : {:3.3f}, Tan2 : {:3.3f}".format(self.point1.tangent.Length, self.point2.tangent.Length))
        self.scale1 = 0.5 / (1 + self.point1.continuity)
        self.scale2 = 0.5 / (1 + self.point2.continuity)
        if auto_orient:
            self.auto_orient()
        # print("Tan1 : {:3.3f}, Tan2 : {:3.3f}".format(self.point1.tangent.Length, self.point2.tangent.Length))

    # Curve evaluation methods
    def _curvature_regularity_score(self, scales):
        "Returns difference between max and min curvature along curve"
        self.scale1, self.scale2 = scales
        self.perform()
        curva_list = [self.curve.curvature(p / self.nb_samples) for p in range(self.nb_samples + 1)]
        return max(curva_list) - min(curva_list)

    def _cp_regularity_score(self, scales):
        "Returns difference between max and min distance between consecutive poles"
        self.scale1, self.scale2 = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        lenghts = [e.Length for e in poly.Edges]
        return max(lenghts) - min(lenghts)

    def _total_cp_angular(self, scales):
        "Returns difference between max and min angle between consecutive poles"
        self.scale1, self.scale2 = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        angles = []
        for i in range(1, len(poly.Edges)):
            angles.append(poly.Edges[i - 1].Curve.Direction.getAngle(poly.Edges[i].Curve.Direction))
        return max(angles) - min(angles)

    def set_regular_poles(self):
        """Iterative function that sets
        a regular distance between control points"""
        self.scale1 = 0.01
        self.scale2 = 0.01
        self.auto_orient()
        minimize(self._cp_regularity_score,
                 [self.scale1, self.scale2],
                 method=self.min_method,
                 options=self.min_options)

    def minimize_curvature(self):
        """Iterative function that tries to minimize
        the curvature along the curve
        nb_samples controls the number of curvature samples"""
        self.scale1 = 0.01
        self.scale2 = 0.01
        self.auto_orient()
        minimize(self._curvature_regularity_score,
                 [self.scale1, self.scale2],
                 method=self.min_method,
                 options=self.min_options)

    def minimize_angular_variation(self):
        """Iterative function that tries to minimize
        the angular deviation between consecutive control points"""
        self.scale1 = 0.01
        self.scale2 = 0.01
        self.auto_orient()
        minimize(self._total_cp_angular,
                 [self.scale1, self.scale2],
                 method=self.min_method,
                 options=self.min_options)


class BlendSurface:
    """BSpline surface that smoothly interpolates two EdgeOnFace objects"""
    def __init__(self, edge1, edge2):
        self.edge1 = edge1
        self.edge2 = edge2
        self._surface = Part.BSplineSurface()
        self._curves = []

    def __repr__(self):
        return "{}(Edge1({}, G{}), Edge2({}, G{}))".format(self.__class__.__name__,
                                                           hex(id(self.edge1)),
                                                           self.edge1.continuity,
                                                           hex(id(self.edge2)),
                                                           self.edge2.continuity)

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
        return self._surface

    @property
    def face(self):
        "Returns the face that represent the BlendSurface"
        return self._surface.toShape()

    def ruled_surface(self):
        return _utils.ruled_surface(self.edge1._edge, self.edge2._edge).Surface

    def minimize_curvature(self, arg=3):
        if isinstance(arg, int):
            params = np.linspace(0.0, 1.0, arg)
        s1 = []
        s2 = []
        for p in params:
            bc = BlendCurve(self.edge1.value(p), self.edge2.value(p))
            # bc.point1 = self.edge1.value(p)
            # bc.point2 = self.edge2.value(p)
            print("Computing BlendCurve u={} from {} to {}".format(p, bc.point1.point, bc.point2.point))
            bc.minimize_curvature()
            s1.append(bc.point1.size)
            s2.append(bc.point2.size)
        self.edge1.set_size(s1)
        self.edge2.set_size(s2)

    def perform(self, arg=20):
        if isinstance(arg, int):
            params = np.linspace(0.0, 1.0, arg)

        bc_list = []
        # bc = BlendCurve(self.edge1.value(0.0), self.edge2.value(0.0))
        for p in params:
            bc = BlendCurve(self.edge1.value(p), self.edge2.value(p))
            # bc.point1 = self.edge1.value(p)
            # bc.point2 = self.edge2.value(p)
            print("Computing BlendCurve u={} from {} to {}".format(p, bc.point1.point, bc.point2.point))
            # bc.minimize_curvature()
            bc_list.append(bc.perform())
        self._curves = bc_list


def test_blend_surface():
    doc1 = FreeCAD.getDocument('test_BlendSurface_1')
    o1 = doc1.getObject('Ruled_Surface001')
    e1 = o1.Shape.Edge1
    f1 = o1.Shape.Face1
    o2 = doc1.getObject('Ruled_Surface')
    e2 = o2.Shape.Edge3
    f2 = o2.Shape.Face1

    from freecad.Curves import blend_curve as bc

    num = 21

    eof1 = bc.EdgeOnFace(e1, f1, 3)
    eof1.set_angle((90, 80, 100, 90))
    eof1.set_size((1.0, 0.5, 1.5, 1.0))
    Part.show(eof1.shape(num))

    eof2 = bc.EdgeOnFace(e2, f2, 3)
    eof2.set_angle((90, 90, 90, 70))
    eof2.set_size((1.0, 1.5, 1.5, 1.0))
    Part.show(eof2.shape(num))

    bs = bc.BlendSurface(eof1, eof2)
    bs.minimize_curvature()
    bs.perform(num)
    Part.show(bs.edges)


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

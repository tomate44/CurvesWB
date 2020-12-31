# -*- coding: utf-8 -*-

__title__ = ""
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """"""

from time import time

import FreeCAD
import FreeCADGui
import Part

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
    def __init__(self, edge, parameter=None, continuity=1, normalize=True):
        self._parameter = 0.0
        self._continuity = 1
        self._vectors = []
        self._scale = 1.0
        self.edge = edge
        if parameter is None:
            self.to_start()
        else:
            self.parameter = parameter
        self.continuity = continuity
        if normalize:
            self.normalize()

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
        self._scale = 1.0

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
        "Defines the number of derivative vectors of this PointOnEdge"
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
    def scale(self):
        "The internal scale factor applied to the original vectors"
        return self._scale

    @scale.setter
    def scale(self, val):
        self._scale = val

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
        self._scale = -self._scale

    def normalize(self):
        """Scale the vectors so that tangent length is 1.0"""
        self.size_tangent(1.0)

    def multiply(self, val):
        """Multiply the scale of the vectors by given factor"""
        self._scale *= val

    def size_tangent(self, val):
        """Scale the vectors so that tangent has the given length"""
        if len(self._vectors) > 1:
            self._scale = val * abs(self._scale) / (self._scale * self._vectors[1].Length)

    def length_list(self):
        return [v.Length for v in self.vectors]

    def get_tangent_edge(self):
        if self._continuity > 0:
            return Part.makeLine(self.point, self.point + self.tangent)

    def split_edge(self, first=True):
        "Cut the support edge at parameter, and return a wire"
        if (self._parameter > self._edge.FirstParameter) and (self._parameter < self._edge.LastParameter):
            return self._edge.split(self._parameter)

    def front_segment(self):
        "Returns to edge segment that is in front of the tangent"
        if self._scale > 0:
            if self._parameter < self._edge.LastParameter:
                return [self._edge.Curve.toShape(self._parameter, self._edge.LastParameter)]
        else:
            if self._parameter > self._edge.FirstParameter:
                return [self._edge.Curve.toShape(self._edge.FirstParameter, self._parameter).reversed()]
        return []

    def rear_segment(self):
        "Returns to edge segment that is behind the tangent"
        if self._scale < 0:
            if self._parameter < self._edge.LastParameter:
                return [self._edge.Curve.toShape(self._parameter, self._edge.LastParameter)]
        else:
            if self._parameter > self._edge.FirstParameter:
                return [self._edge.Curve.toShape(self._edge.FirstParameter, self._parameter).reversed()]
        return []


class Fillet3D:
    """Fillet3D generates a bezier curve that
    smoothly interpolates two PointOnEdge objects"""
    def __init__(self, point1, point2):
        self.min_method = 'Nelder-Mead'
        self.min_options = {"maxiter": 2000, "disp": True}
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
        "The PointOnEdge object that defines the start of the Fillet3D"
        return self._point1

    @point1.setter
    def point1(self, p):
        self._point1 = p

    @property
    def point2(self):
        "The PointOnEdge object that defines the end of the Fillet3D"
        return self._point2

    @point2.setter
    def point2(self, p):
        self._point2 = p

    @property
    def curve(self):
        "Returns the Bezier curve that represent the Fillet3D"
        return self._curve

    @property
    def shape(self):
        "Returns the edge that represent the Fillet3D"
        return self._curve.toShape()

    def perform(self, vecs=None):
        "Generate the Bezier curve that interpolates the 2 points"
        if vecs is None:
            self._curve.interpolate([self.point1.vectors, self.point2.vectors])
        else:
            self._curve.interpolate(vecs)
        return self._curve

    def auto_orient(self):
        """Orient the 2 point tangents toward their intersection"""
        if self.point1.continuity < 1 or self.point2.continuity < 1:
            return False
        line1 = self.point1.get_tangent_edge()
        line2 = self.point2.get_tangent_edge()
        long_line1 = line1.Curve.toShape(-1e20, 1e20)
        long_line2 = line2.Curve.toShape(-1e20, 1e20)
        dist, pts, info = long_line1.distToShape(long_line2)
        if info[0][0] == "Edge" and info[0][3] == "Edge":
            if info[0][2] < 0.0:
                self.point1.reverse()
            if info[0][5] > 0.0:
                self.point2.reverse()
            return True
        return False

    def auto_scale(self, auto_orient=True):
        """Sets the scale the 2 points proportional to chord length"""
        if auto_orient:
            self.auto_orient()
        # nb = self.point1.continuity + self.point2.continuity + 1
        chord_length = self.point1.point.distanceToPoint(self.point2.point)
        # print("Tan1 : {:3.3f}, Tan2 : {:3.3f}".format(self.point1.tangent.Length, self.point2.tangent.Length))
        self.point1.size_tangent(chord_length)
        self.point2.size_tangent(chord_length)
        # print("Tan1 : {:3.3f}, Tan2 : {:3.3f}".format(self.point1.tangent.Length, self.point2.tangent.Length))

    # Curve evaluation methods
    def _curvature_regularity_score(self, scales):
        "Returns difference between max and min curvature along curve"
        self.point1.scale, self.point2.scale = scales
        self.perform()
        curva_list = [self.curve.curvature(p / self.nb_samples) for p in range(self.nb_samples + 1)]
        return max(curva_list) - min(curva_list)

    def _cp_regularity_score(self, scales):
        "Returns difference between max and min distance between consecutive poles"
        self.point1.scale, self.point2.scale = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        lenghts = [e.Length for e in poly.Edges]
        return max(lenghts) - min(lenghts)

    def _total_cp_angular(self, scales):
        "Returns difference between max and min angle between consecutive poles"
        self.point1.scale, self.point2.scale = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        angles = []
        for i in range(1, len(poly.Edges)):
            angles.append(poly.Edges[i - 1].Curve.Direction.getAngle(poly.Edges[i].Curve.Direction))
        return max(angles) - min(angles)

    def set_regular_poles(self):
        """Iterative function that sets
        a regular distance between control points"""
        minimize(self._cp_regularity_score,
                 [self.point1.scale, self.point2.scale],
                 method=self.min_method,
                 options=self.min_options)

    def minimize_curvature(self):
        """Iterative function that tries to minimize
        the curvature along the curve
        nb_samples controls the number of curvature samples"""
        minimize(self._curvature_regularity_score,
                 [self.point1.scale, self.point2.scale],
                 method=self.min_method,
                 options=self.min_options)

    def minimize_angular_variation(self):
        """Iterative function that tries to minimize
        the angular deviation between consecutive control points"""
        minimize(self._total_cp_angular,
                 [self.point1.scale, self.point2.scale],
                 method=self.min_method,
                 options=self.min_options)


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
    poe1.size_tangent(0.1)
    poe2.size_tangent(0.1)
    fillet = Fillet3D(poe1, poe2)
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

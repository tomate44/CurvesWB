# -*- coding: utf-8 -*-

__title__ = "Curves to Surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Interpolate curves to surface"

import FreeCAD
import Part


class CurvesToSurface:
    def __init__(self, curves):
        self.curves = curves

    def convert_to_bsplines(self):
        for c in self.curves:
            if isinstance(c, Part.Edge):
                c = c.Curve.toBSpline()
            elif isinstance(c, Part.Wire):
                c = c.approximate()
            else:
                c = c.toBSpline()

    def match_degrees(self):
        max_degree = 0
        for c in self.curves:
            max_degree = max(max_degree, c.Degree)
        for c in self.curves:
            c.increaseDegree(max_degree)

    def find_knot(curve, knot, tolerance=1e-15):
        for i in range(1, curve.NbKnots + 1):
            if abs(knot - curve.getKnot(i)) < tolerance:
                return i
        return -1

    def match_knots(self, tolerance=1e-15):
        pass



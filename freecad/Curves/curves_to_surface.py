# -*- coding: utf-8 -*-

__title__ = "Curves to Surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Interpolate curves to surface"

import FreeCAD
import Part


class CurvesToSurface:
    def __init__(self, curves):
        self.curves = self.convert_to_bsplines(curves)

    def convert_to_bsplines(self, curves):
        nc = []
        for c in curves:
            if isinstance(c, Part.Edge):
                nc.append(c.Curve.toBSpline())
            elif isinstance(c, Part.Wire):
                nc.append(c.approximate())
            else:
                nc.append(c.toBSpline())
        return nc

    def print_curves(self):
        print([c.Degree for c in self.curves])
        for c in self.curves:
            print(c.getKnots())
        for c in self.curves:
            print(c.getMultiplicities())

    def __repr__(self):
        self.print_curves()
        return ""

    def match_degrees(self):
        max_degree = 0
        for c in self.curves:
            max_degree = max(max_degree, c.Degree)
        for c in self.curves:
            c.increaseDegree(max_degree)

    def orient_curves(self, c1, c2):
        """orient_curves(c1, c2)
        Orient c2 in same direction as c1 """
        if c1.isClosed():
            fp1 = 0.75 * c1.FirstParameter + 0.25 * c1.LastParameter
            lp1 = 0.25 * c1.FirstParameter + 0.75 * c1.LastParameter
        else:
            fp1 = c1.FirstParameter
            lp1 = c1.LastParameter
        if c2.isClosed():
            fp2 = 0.75 * c2.FirstParameter + 0.25 * c2.LastParameter
            lp2 = 0.25 * c2.FirstParameter + 0.75 * c2.LastParameter
        else:
            fp2 = c2.FirstParameter
            lp2 = c2.LastParameter
        ls1 = Part.makeLine(c1.value(fp1), c2.value(fp2))
        ls2 = Part.makeLine(c1.value(lp1), c2.value(lp2))
        d1 = ls1.distToShape(ls2)[0]
        ls1 = Part.makeLine(c1.value(fp1), c2.value(lp2))
        ls2 = Part.makeLine(c1.value(lp1), c2.value(fp2))
        d2 = ls1.distToShape(ls2)[0]
        if d1 < d2:
            c2.reverse()
            return True

    def auto_orient(self):
        for i in range(1, len(self.curves)):
            if self.orient_curves(self.curves[i - 1], self.curves[i]):
                print("Reversed curve #{}".format(i))

    def normalize_knots(self):
        for c in self.curves:
            fp = c.FirstParameter
            lp = c.LastParameter
            if (not fp == 0.0) or (not lp == 1.0):
                normalized_knots = [(k - fp) / (lp - fp) for k in c.getKnots()]
                c.setKnots(normalized_knots)

    def find_knot(self, curve, knot, tolerance=1e-15):
        for i in range(1, curve.NbKnots + 1):
            if abs(knot - curve.getKnot(i)) < tolerance:
                return i
        return -1

    def match_knots(self, tolerance=1e-15):
        first = self.curves[0]
        for cur_idx in range(1, len(self.curves)):
            for kno_idx in range(1, self.curves[cur_idx].NbKnots + 1):
                k = self.curves[cur_idx].getKnot(kno_idx)
                mult = self.curves[cur_idx].getMultiplicity(kno_idx)
                fk = self.find_knot(first, k, tolerance)
                if fk > -1:
                    om = first.getMultiplicity(fk)
                    first.increaseMultiplicity(fk, mult)
                    print("Increased mult of knot # {} from {} to {}".format(fk, om, mult))
                else:
                    first.insertKnot(k, mult)
                    print("Inserting knot {} mult {}".format(k, mult))
        for cur_idx in range(1, len(self.curves)):
            for kno_idx in range(1, first.NbKnots + 1):
                k = first.getKnot(kno_idx)
                mult = first.getMultiplicity(kno_idx)
                fk = self.find_knot(self.curves[cur_idx], k, tolerance)
                if fk > -1:
                    self.curves[cur_idx].increaseMultiplicity(fk, mult)
                else:
                    self.curves[cur_idx].insertKnot(k, mult)

    def parameters_at_poleidx(self, fac=1.0, idx=1, force_closed=False):
        if idx < 1:
            idx = 1
        elif idx > self.curves[0].NbPoles:
            idx = self.curves[0].NbPoles
        pts = [c.getPole(idx) for c in self.curves]
        if force_closed and pts[0].distanceToPoint(pts[-1]) > 1e-7:  # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0.0]
        for i in range(1, len(pts)):
            p = pts[i] - pts[i - 1]
            pl = pow(p.Length, fac)
            params.append(params[-1] + pl)
        return [p / params[-1] for p in params]

    def average_parameters(self, fac=1.0, force_closed=False):
        params_array = []
        for pole_idx in range(1, self.curves[0].NbPoles + 1):
            params_array.append(self.parameters_at_poleidx(fac, pole_idx, force_closed))
        params = []
        for idx in range(len(params_array[0])):
            pl = [params_array[i][idx] for i in range(len(params_array))]
            params.append(sum(pl) / len(pl))
        print("Average parameters : {}".format(params))
        return params

    def build_surface(self):
        self.match_degrees()
        self.auto_orient()
        self.normalize_knots()
        self.match_knots()
        # self.print_curves()



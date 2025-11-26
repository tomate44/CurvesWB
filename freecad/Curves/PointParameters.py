# SPDX-License-Identifier: LGPL-2.1-or-later

import Part


class PointParameters:
    "Computes parameters from a list of points"

    def __init__(self, pts, periodic=0):
        self.tol = 1e-7
        self.Periodic = periodic
        self.Points = pts
        self.Closed = pts[0].distanceToPoint(pts[-1]) < self.tol
        if periodic >= 0:
            idx = 0
            if self.Closed:
                idx = 1
            self.Points += self.Points[idx:idx + periodic + 1]

    def from_factor(self, fac=1.0):
        "Computes parameters from a parametrization factor"
        params = [0]
        for i in range(1, len(self.Points)):
            p = self.Points[i] - self.Points[i - 1]
            le = p.Length
            pl = pow(le, fac)
            params.append(params[-1] + pl)
        return params

    def from_axis(self, axis):
        params = []
        if self.Periodic or self.Closed:
            print("Impossible for periodic points")
            return params
        c = axis
        if hasattr(axis, "Curve"):
            c = axis.Curve
        for p in self.Points:
            par = c.parameter(p)
            if params and (par <= params[-1]):
                print(f"parameters are not monotically increasing ({par})")
            params.append(c.parameter(p))
        return params

    def from_chord(self):
        axis = Part.makeLine(self.Points[0], self.Points[-1])
        return self.from_axis(axis)

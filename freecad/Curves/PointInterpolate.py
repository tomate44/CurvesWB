# SPDX-License-Identifier: LGPL-2.1-or-later

import Part
import numpy as np
from freecad.Curves import PointParameters


class PointInterpolate:
    "Computes parameters from a list of points"

    def __init__(self, pts, degree=3, closing_continuity=-1):
        self.Points = pts
        self.Degree = degree
        self.Continuity = closing_continuity

    def interpolate(self):
        pp = PointParameters(self.Points, self.Continuity)
        ncp = len(knots) - degree - 1
        mx = np.array([[0.] * ncp for i in range(len(params))])
        bb = nurbs_tools.BsplineBasis()
        bb.knots = knots
        bb.degree = degree
        for irow in range(derivOrder + 1):
            bspl_basis[irow] = bb.evaluate(params[iparm], d=irow)
        for i in range(len(bspl_basis[derivOrder])):
            mx[iparm][i] = bspl_basis[derivOrder][i]

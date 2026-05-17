# SPDX-License-Identifier: LGPL-2.1-or-later

import numpy as np
from scipy.interpolate import make_interp_spline
import FreeCAD
import Part

from freecad.Curves.lib.precision import tol3d


class PointList:
    '''
    PointList object (mainly for interpolation)

    Attributes:
        Points: a list of consecutive FreeCAD.Vector
        Tolerance: geometric tolerance
    '''

    def __init__(self, pts=None, tol=tol3d):
        '''
        Initialisation of the PointList.

        Arguments:
            pts: list of FreeCAD.Vector(or Part.Vertex) or None
                  if None, a default list is created (see method debug_points)
            tol: geometric tolerance
        '''
        if pts is None:
            self.Points = self.debug_points()
        elif isinstance(pts[0], Part.Vertex):
            self.Points = [v.Point for v in pts]
        else:
            self.Points = [p for p in pts]
        self.Tolerance = tol

    def __str__(self):
        closed = ""
        if self.is_closed():
            closed = " Closed"
        return f"Point List : {self.Nb} points{closed}"

    def __repr__(self):
        return str(self)

    @property
    def Nb(self):
        'Number of Points'
        return len(self.Points)

    # *** Shapes

    @property
    def ShapePoints(self):
        'Returns a coumpound of vertexes'
        return Part.Compound([Part.Vertex(p) for p in self.Points])

    @property
    def ShapePolygon(self):
        'Returns a polygon wire of the points'
        return Part.makePolygon(self.Points)

    # *** Closedness

    def is_closed(self):
        'Returns True if first and last points are identical'
        return self.Points[0].distanceToPoint(self.Points[-1]) < self.Tolerance

    def set_closed(self):
        'If Point List is not closed, append first point'
        if not self.is_closed():
            # print(self.Points)
            self.Points.append(self.Points[0])

    def set_open(self):
        'If Point List is closed, remove last point'
        if self.is_closed():
            self.Points = self.Points[:-1]

    # *** Other methods

    def debug_points(self):
        '''
        Returns an open list of 8 points around a circle
        with alternating Z height.
        For debugging.
        '''
        ci = Part.Circle(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), 10.0)
        pts = ci.discretize(9)[:-1]
        offsetZ = 1
        for p in pts:
            p.z += offsetZ
            offsetZ = -offsetZ
        return pts

    def compute_params(self, param_factor=1.0, param_range=[0.0, 1.0]):
        '''
        Computes a list of parameters from the points
        param_factor (float) : parameterization factor, usually between 0.0 and 1.0
            0.0 -> Uniform / 0.5 -> Centripetal / 1.0 -> Chord-Length
        param_range : range of the computed params
            if None, the raw computed values are returned
        Returns a list of floats
        '''
        pl = [0]
        for i in range(1, len(self.Points)):
            p = self.Points[i] - self.Points[i - 1]
            span = pow(p.Length, param_factor)
            pl.append(pl[-1] + span)
        if param_range is not None:
            p0, p1 = param_range
            pl = [p0 + p1 * (p - pl[0]) / (pl[-1] - pl[0]) for p in pl]
            pl[0], pl[-1] = p0, p1
        self.Parameters = pl
        return pl

    def scipy_spline_to_freecad(self, spl):
        'Returns a Part.BSplineCurve from a scipy BSpline object'
        u, c, degree = spl.tck
        poles = [FreeCAD.Vector(*v) for v in c]
        knots = [u[0]]
        mults = [1]
        for k in u[1:]:
            if k == knots[-1]:
                mults[-1] += 1
            else:
                knots.append(k)
                mults.append(1)
        bsp = Part.BSplineCurve()
        bsp.buildFromPolesMultsKnots(poles, mults, knots, False, degree)
        return bsp

    def interpolate(self, param=1.0, periodic=False, degree=3):
        '''
        Interpolate points using scipy
        '''
        interp_type = 'not-a-knot'
        if periodic:
            self.set_closed()
            interp_type = 'periodic'
        if isinstance(param, (list, tuple)):
            self.Parameters = param
        else:
            self.compute_params(param)
        nppts = np.empty((len(self.Points), 3))
        for i, pt in enumerate(self.Points):
            nppts[i] = [pt[0], pt[1], pt[2]]
        spl = make_interp_spline(self.Parameters,
                                 nppts,
                                 k=min(degree, len(self.Points) - 1),
                                 bc_type=interp_type)
        fcbs = self.scipy_spline_to_freecad(spl)
        if periodic:
            fcbs.setPeriodic()
        return fcbs


'''
# Test script
npts = 17
radius = 10

# create interpolation points
ci = Part.Circle(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), radius)
pts = ci.discretize(npts)[:-1]
offsetZ = 1
for p in pts:
    p.z += offsetZ
    offsetZ = -offsetZ


ptsint = PointList(pts)
ptsint.compute_params(1.0)

bs = Part.BSplineCurve()
bs.interpolate(Points=pts, Parameters=ptsint.Parameters)
Part.show(bs.toShape(), "FC BSpline")

bs = ptsint.interpolate(1.0, True, 3)
Part.show(bs.toShape(), "periodic BSpline")
'''

import numpy as np
from scipy.interpolate import make_interp_spline
import FreeCAD
import Part


class PointList:
    def __init__(self, pts, tol=1e-7):
        self.Points = pts
        self.tol = tol

    def is_closed(self):
        return self.Points[0].distanceToPoint(self.Points[-1]) < self.tol

    def set_closed(self):
        if not self.is_closed():
            self.Points.append(self.Points[0])

    def set_open(self):
        if self.is_closed():
            self.Points = self.Points[:-1]

    def compute_params(self, param_factor=1.0, par_range=[0.0, 1.0]):
        """
        Computes a knot Sequence for a set of points
        param_factor (0-1) : parameterization factor
        param_factor=0 -> Uniform
        param_factor=0.5 -> Centripetal
        param_factor=1.0 -> Chord-Length
        par_range : range of the computed params
        """
        pl = [0]
        for i in range(1, len(self.Points)):
            p = self.Points[i] - self.Points[i - 1]
            span = pow(p.Length, param_factor)
            pl.append(pl[-1] + span)
        p0, p1 = par_range
        pl = [p0 + p1 * (p - pl[0]) / (pl[-1] - pl[0]) for p in pl]
        self.Parameters = pl
        return pl

    def scipy_spline_to_freecad(self, spl):
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
                                 k=degree,
                                 bc_type=interp_type)
        fcbs = self.scipy_spline_to_freecad(spl)
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

# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part
try:
    import numpy as np
    from scipy.interpolate import make_interp_spline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


from freecad.Curves.lib.precision import tol3d
from freecad.Curves.lib.point_list import PointList
from freecad.Curves.lib.timer import cls_timer
from freecad.Curves.lib.logger import FCLogger


class CurveFitting:
    '''
    Various methods to fit a BSpline Curve on a list of points

    Attributes:
        Points: a list of consecutive FreeCAD.Vector
        Tolerance: geometric tolerance
        ParamFactor: parametrization factor of the points
        Periodic: periodicity of the fitting curve
        Degree: degree of the fitting curve
        Parameters: parameters of the interpolated points
    '''

    def __init__(self, param_factor=1.0, tol=tol3d):
        '''
        Initialisation of the curve fitting algorithm.

        Attributes:
            param_factor: parametrization factor of the points
            tol: geometric tolerance
        '''
        self.log = FCLogger("Debug", "CurveFitting")
        self.ParamFactor = param_factor
        self.Tolerance = tol
        self.perform = None

    # Modes
    def set_scipy_mode(self, degree=3, bc=None):
        self.Degree = degree
        self.bc = bc
        self.perform = self.interpolate_scipy

    def set_makima_mode(self):
        self.perform = self.interpolate_makima

    def set_endtangents_mode(self, periodic=False):
        self.periodic = periodic
        self.perform = self.interpolate_with_end_tangents

    def set_fulltangents_mode(self, periodic=False):
        self.periodic = periodic
        self.perform = self.interpolate_with_tangents

    def _scipy_spline_to_freecad(self, spl):
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

    def makima_tangents(self, points, params):
        '''
        Computes tangents of points using modified Akima method.
        See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Akima1DInterpolator.html
        '''
        def delta(i):
            return (points[i + 1] - points[i]) / (params[i + 1] - params[i])

        def delta_list():
            deltas = [None] * (len(points) + 3)
            for i in range(len(points) - 1):
                deltas[i + 2] = delta(i)
            deltas[1] = 2 * deltas[2] - deltas[3]
            deltas[0] = 2 * deltas[1] - deltas[2]
            deltas[-2] = 2 * deltas[-3] - deltas[-4]
            deltas[-1] = 2 * deltas[-2] - deltas[-3]
            return deltas

        tans = [None] * len(points)
        deltas = delta_list()
        for i in range(len(points)):
            j = i + 2
            w1 = (deltas[j+1] - deltas[j]).Length
            w2 = (deltas[j-1] - deltas[j-2]).Length
            f1 = w1 / (w1 + w2)
            f2 = w2 / (w1 + w2)
            tan = f1 * deltas[j-1] + f2 * deltas[j]
            tans[i] = tan
        return tans

    @cls_timer
    def interpolate_scipy(self, points, parameters):
        '''
        Interpolate points using scipy

        Attributes:
            parameters (list of floats, or None): Optional list of parameters
            for the points. If None, parameters are computed using ParamFactor

        Returns:
            Part.BSplineCurve
        '''
        if not SCIPY_AVAILABLE:
            self.log.error("Function unavailable. Requires scipy and numpy python packages.")
            return
        if self.bc is None:
            interp_type = 'not-a-knot'
        else:
            interp_type = self.bc
        if self.Periodic:
            self._ptsl.set_closed()
            interp_type = 'periodic'
        if isinstance(parameters, (list, tuple)):
            self.Parameters = parameters
        else:
            self.Parameters = self._ptsl.compute_params(self.ParamFactor)
        nppts = np.empty((self._ptsl.Nb, 3))
        for i, pt in enumerate(self.Points):
            nppts[i] = [pt[0], pt[1], pt[2]]
        spl = make_interp_spline(self.Parameters,
                                 nppts,
                                 k=self.Degree,
                                 bc_type=interp_type)
        fcbs = self._scipy_spline_to_freecad(spl)
        if self.Periodic:
            fcbs.setPeriodic()
        return fcbs

    @cls_timer
    def interpolate_with_end_tangents(self, points, parameters, start_tangent, end_tangent):
        '''
        Interpolate points with tangent specified at first and last points

        Arguments:
            start_tangent (FreeCAD.Vector): Tangent vector of the first point
            end_tangent (FreeCAD.Vector): Tangent vector of the last point

        Returns:
            Part.BSplineCurve
        '''
        self.Parameters = self._ptsl.compute_params(self.ParamFactor)
        bsp = Part.BSplineCurve()
        bsp.interpolate(Points=self.Points,
                        PeriodicFlag=self.Periodic,
                        Tolerance=self.Tolerance,
                        Parameters=self.Parameters,
                        InitialTangent=start_tangent,
                        FinalTangent=end_tangent)
        return bsp

    @cls_timer
    def interpolate_with_tangents(self, tangents, flags):
        '''
        Interpolate points with tangent specified at each point

        Arguments:
            tangents (list of FreeCAD.Vector): Tangent vector of each point
            flags (list of bool): activation flags of each tangent vector

        Returns:
            Part.BSplineCurve with max C1 continuity
        '''
        if self.Periodic:
            self._ptsl.set_closed()
        self.Parameters = self._ptsl.compute_params(self.ParamFactor)
        if self.Periodic:
            self._ptsl.set_open()
        bsp = Part.BSplineCurve()
        bsp.interpolate(Points=self.Points,
                        PeriodicFlag=self.Periodic,
                        Tolerance=self.Tolerance,
                        Parameters=self.Parameters,
                        Tangents=tangents,
                        TangentFlags=flags)
        return bsp

    @cls_timer
    def interpolate_makima(self):
        params = self._ptsl.compute_params(self.ParamFactor)
        tans = self.makima_tangents(params)
        flags = [True] * len(tans)
        bs = self.interpolate_with_tangents(tans, flags)
        return bs


'''
from freecad.Curves.lib.curve_fitting import CurveFitting
import numpy as np
from scipy.interpolate import make_interp_spline

s0, s1, s2 = FreeCADGui.Selection.getSelection()
e1 = s0.Shape.Edge1
pts = [v.Point for v in s1.Shape.Vertexes]
e2 = s2.Shape.Edge1

bc1 = np.empty((3, 3))
# bc1[0] = list(e1.valueAt(e1.LastParameter))
bc1[0] = list(e1.Curve.getDN(e1.LastParameter, 1))
bc1[1] = list(e1.Curve.getDN(e1.LastParameter, 2))
bc1[2] = list(e1.Curve.getDN(e1.LastParameter, 3))

bc2 = np.empty((3, 3))
# bc2[0] = list(e2.valueAt(e1.FirstParameter))
bc2[0] = list(e2.Curve.getDN(e1.FirstParameter, 1))
bc2[1] = list(e2.Curve.getDN(e1.FirstParameter, 2))
bc2[2] = list(e2.Curve.getDN(e1.FirstParameter, 3))

bc = ([(1, bc1[0]), (2, bc1[1])], [(1, bc2[0]), (2, bc2[1])])


cf = CurveFitting(pts, 1.0, False, 5, 1e-7)
bs = cf.interpolate_scipy(None, bc)
Part.show(bs.toShape())

'''

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

    def __init__(self, pts=None, param_factor=1.0, periodic=False, degree=3, tol=tol3d):
        '''
        Initialisation of the curve fitting algorithm.

        Attributes:
            pts: a list of consecutive FreeCAD.Vector
            param_factor: parametrization factor of the points
            periodic: periodicity of the fitting curve
            degree: degree of the fitting curve
            tol: geometric tolerance
        '''
        self.log = FCLogger("Debug", "CurveFitting")
        self.Points = pts
        self.ParamFactor = param_factor
        self.Periodic = periodic
        self.Degree = degree
        self.Tolerance = tol
        self.Parameters = None

    @property
    def Points(self):
        return self._ptsl.Points

    @Points.setter
    def Points(self, pts):
        if isinstance(pts, PointList):
            self._ptsl = pts
        else:
            self._ptsl = PointList(pts)

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

    @cls_timer
    def scipy_interpolate(self, parameters=None):
        '''
        Interpolate points using scipy

        Attributes:
            parameters (list of floats, or None): Optional list of parameters for the points. If None, parameters are computed using ParamFactor

        Returns:
            Part.BSplineCurve
        '''
        if not SCIPY_AVAILABLE:
            self.log.error("Function unavailable. Requires scipy and numpy python packages.")
            return
        interp_type = 'not-a-knot'
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
                                 k=min(self.Degree, self._ptsl.Nb - 1),
                                 bc_type=interp_type)
        fcbs = self._scipy_spline_to_freecad(spl)
        if self.Periodic:
            fcbs.setPeriodic()
        return fcbs

    @cls_timer
    def interpolate_with_end_tangents(self, start_tangent, end_tangent):
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
        self.Parameters = self._ptsl.compute_params(self.ParamFactor)
        bsp = Part.BSplineCurve()
        bsp.interpolate(Points=self.Points,
                        PeriodicFlag=self.Periodic,
                        Tolerance=self.Tolerance,
                        Parameters=self.Parameters,
                        Tangents=tangents,
                        TangentFlags=flags)
        return bsp

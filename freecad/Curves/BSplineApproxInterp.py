# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2018 German Aerospace Center (DLR)

#  This file is a python port of the following files :
#
#  /src/geometry/CTiglBSplineApproxInterp.cpp
#
#  from the Tigl library : https://github.com/DLR-SC/tigl under Apache-2 license

import FreeCAD
import Part
import numpy as np
from freecad.Curves import nurbs_tools
#  from math import pi

DEBUG = False


def debug(o):
    if not DEBUG:
        return
    if isinstance(o, Part.BSplineCurve):
        FreeCAD.Console.PrintWarning("\nBSplineCurve\n")
        FreeCAD.Console.PrintWarning("Degree: {}\n".format(o.Degree))
        FreeCAD.Console.PrintWarning("NbPoles: {}\n".format(o.NbPoles))
        FreeCAD.Console.PrintWarning("Knots: {} ({:0.2f} - {:0.2f})\n".format(o.NbKnots, o.FirstParameter, o.LastParameter))
        FreeCAD.Console.PrintWarning("Mults: {}\n".format(o.getMultiplicities()))
        FreeCAD.Console.PrintWarning("Periodic: {}\n".format(o.isPeriodic()))
    elif isinstance(o, Part.BSplineSurface):
        FreeCAD.Console.PrintWarning("\nBSplineSurface\n************\n")
        try:
            u = o.uIso(o.UKnotSequence[0])
            debug(u)
        except Part.OCCError:
            FreeCAD.Console.PrintError("Failed to compute uIso curve\n")
        try:
            v = o.vIso(o.VKnotSequence[0])
            debug(v)
        except Part.OCCError:
            FreeCAD.Console.PrintError("Failed to compute vIso curve\n")
        FreeCAD.Console.PrintWarning("************\n")
    else:
        FreeCAD.Console.PrintMessage("{}\n".format(str(o)))


def square_distance(v1, v2):
    return pow(v2.x - v1.x, 2) + pow(v2.y - v1.y, 2)


def square_magnitude(v1):
    return pow(v1.x, 2) + pow(v1.y, 2)


def find(val, array, tol=1e-5):
    """Return index of val in array, within given tolerance
    Else return -1"""
    for i in range(len(array)):
        if abs(val - array[i]) < tol:
            return int(i)
    return -1


def insertKnot(knot, count, degree, knots, mults, tol=1e-5):
    """Insert knot in knots, with multiplicity count in mults"""
    if (knot < knots[0] or knot > knots[-1]):
        raise RuntimeError("knot out of range")

    pos = find(knot, knots, tol)
    if (pos == -1):  # knot not found, insert new one
        pos = 0
        while (knots[pos] < knot):
            pos += 1
        knots.insert(pos, knot)
        mults.insert(pos, min(count, degree))
    else:  # knot found, increase multiplicity
        mults[pos] = min(mults[pos] + count, degree)


def bsplineBasisMat(degree, knots, params, derivOrder):
    """Return a matrix of values of BSpline Basis functions(or derivatives)"""
    ncp = len(knots) - degree - 1
    mx = np.array([[0.] * ncp for i in range(len(params))])
    # math_Matrix mx(1, params.Length(), 1, ncp);
    # mx.Init(0.);
    bspl_basis = np.array([[0.] * (ncp) for i in range(derivOrder + 1)])
    # math_Matrix bspl_basis(1, derivOrder + 1, 1, degree + 1);
    # bspl_basis.Init(0.);
    # debug("params %s"%str(params))
    for iparm in range(len(params)):  # for (Standard_Integer iparm = 1; iparm <= params.Length(); ++iparm) {
        basis_start_index = 0

        bb = nurbs_tools.BsplineBasis()
        bb.knots = knots
        bb.degree = degree
        # span = bb.find_span(params[iparm])
        # res = bb.ders_basis_funs( span, params[iparm], derivOrder)
        for irow in range(derivOrder + 1):
            # debug("irow %s"%str(irow))
            # debug("bspl_basis[irow] %s"%str(bspl_basis[irow]))
            bspl_basis[irow] = bb.evaluate(params[iparm], d=irow)
            # debug("bspl_basis[irow] %s"%str(bspl_basis[irow]))
            # for ival in range(len(res[irow])):
                # bspl_basis[irow][ival+span] = res[irow][ival]
        # # if OCC_VERSION_HEX >= VERSION_HEX_CODE(7,1,0)
                # BSplCLib::EvalBsplineBasis(derivOrder, degree + 1, knots, params.Value(iparm), basis_start_index, bspl_basis);
        # # else
                # BSplCLib::EvalBsplineBasis(1, derivOrder, degree + 1, knots, params.Value(iparm), basis_start_index, bspl_basis);
        # # endif
        # if(derivOrder > 0):
            # help_vector = np.array([0.]*ncp) # (1, ncp);
            # # # help_vector.Init(0.);
            # # help_vector.Set(basis_start_index, basis_start_index + degree, bspl_basis.Row(derivOrder + 1));
            # mx[iparm] = bspl_basis[derivOrder] # mx.SetRow(iparm, help_vector);
        # else:
            # mx[iparm] = bspl_basis[derivOrder] #   mx.Set(iparm, iparm, basis_start_index, basis_start_index + degree, bspl_basis);
        for i in range(len(bspl_basis[derivOrder])):
            mx[iparm][basis_start_index + i] = bspl_basis[derivOrder][i]
    return mx


class BSplineApproxInterp(object):
    """BSpline curve approximating a list of points
    Some points can be interpolated, or be set as C0 kinks"""
    #  used in BSplineAlgorithms.reparametrizeBSplineContinuouslyApprox

    def __init__(self, points, nControlPoints, degree, continuous_if_closed):
        self.pnts = points
        self.indexOfApproximated = list(range(len(points)))
        self.degree = degree
        self.ncp = nControlPoints
        self.C2Continuous = continuous_if_closed
        self.indexOfInterpolated = list()
        self.indexOfKinks = list()

    def InterpolatePoint(self, pointIndex, withKink):
        """Switch point from approximation to interpolation
        If withKink, also set it as Kink"""
        if pointIndex not in self.indexOfApproximated:
            debug("Invalid index in CTiglBSplineApproxInterp::InterpolatePoint")
            debug("{} is not in {}".format(pointIndex, self.indexOfApproximated))
        else:
            debug("Successfully switched point # {} from approx to interp".format(pointIndex))
            self.indexOfApproximated.remove(pointIndex)
            self.indexOfInterpolated.append(int(pointIndex))
        if withKink:
            self.indexOfKinks.append(pointIndex)

    def FitCurveOptimal(self, initialParms, maxIter):
        """Iterative fitting of a BSpline curve on the points"""
        #  compute initial parameters, if initialParms empty
        if len(initialParms) == 0:
            parms = self.computeParameters(0.5)
        else:
            parms = initialParms

        if not len(parms) == len(self.pnts):
            raise RuntimeError("Number of parameters don't match number of points")

        #  Compute knots from parameters
        knots, mults = self.computeKnots(self.ncp, parms)

        # solve system
        iteration = 0
        result, error = self.python_solve(parms, knots, mults)  # TODO occKnots, occMults ???? See above
        if error is None:
            return None, None
        old_error = error * 2

        debug("FitCurveOptimal iteration # {}".format(iteration))
        debug("error = {}".format(error))
        while ((error > 0) and ((old_error - error) / max(error, 1e-6) > 1e-6) and (iteration < maxIter)):
            debug("FitCurveOptimal iteration # {}".format(iteration))
            old_error = error
            self.optimizeParameters(result, parms)
            result, error = self.python_solve(parms, knots, mults)
            if error is None:
                return None, None
            debug("error = {}".format(error))
            iteration += 1
        return result, error

    def computeParameters(self, alpha):
        """Computes parameters for the points self.pnts
        alpha is a parametrization factor
        alpha = 0.0 -> Uniform
        alpha = 0.5 -> Centripetal
        alpha = 1.0 -> ChordLength"""
        sum = 0.0
        nPoints = len(self.pnts)
        t = [0.0]
        #  calc total arc length: dt^2 = dx^2 + dy^2
        for i in range(1, nPoints):
            len2 = square_distance(self.pnts[i - 1], self.pnts[i])
            sum += pow(len2, alpha)  # / 2.)
            t.append(sum)
        #  normalize parameter with maximum
        tmax = t[-1]
        for i in range(1, nPoints):
            t[i] /= tmax
        #  reset end value to achieve a better accuracy
        t[-1] = 1.0
        return t

    def computeKnots(self, ncp, parms):
        """Computes knots and mults from parameters"""
        order = self.degree + 1
        if (ncp < order):
            raise RuntimeError("Number of control points to small!")

        umin = min(parms)
        umax = max(parms)

        knots = [0] * (ncp - self.degree + 1)
        mults = [0] * (ncp - self.degree + 1)
        # debug("computeKnots(ncp, params, knots, mults):\n%s\n%s\n%s\n%s"%(ncp, parms, knots, mults))

        #  fill multiplicity at start
        knots[0] = umin
        mults[0] = order

        #  number of knots between the multiplicities
        N = (ncp - order)
        #  set uniform knot distribution
        for i in range(1, N + 1):
            knots[i] = umin + (umax - umin) * float(i) / float(N + 1)
            mults[i] = 1

        #  fill multiplicity at end
        knots[N + 1] = umax
        mults[N + 1] = order

        for i in self.indexOfKinks:
            insertKnot(parms[i], self.degree, self.degree, knots, mults, 1e-4)

        # debug("computeKnots(ncp, params, knots, mults):\n%s\n%s\n%s\n%s"%(ncp, parms, knots, mults))
        return knots, mults

    def maxDistanceOfBoundingBox(self, points):
        """return maximum distance of a group of points"""
        maxDistance = 0.
        for i in range(len(points)):
            for j in range(len(points)):
                distance = points[i].distanceToPoint(points[j])
                if (maxDistance < distance):
                    maxDistance = distance
        return maxDistance

    def isClosed(self):
        """Returns True if first and last points are close enough"""
        if not self.C2Continuous:
            return False
        maxDistance = self.maxDistanceOfBoundingBox(self.pnts)
        error = 1e-12 * maxDistance
        return self.pnts[0].distanceToPoint(self.pnts[-1]) < error

    def firstAndLastInterpolated(self):
        """Returns True if first and last points must be interpolated"""
        first = 0 in self.indexOfInterpolated
        last = (len(self.pnts) - 1) in self.indexOfInterpolated
        return first and last

    def matrix(self, nrow, ncol, val=0.):
        """nrow x ncol matrix filled with val"""
        return np.array([[val] * ncol for i in range(nrow)])

    def getContinuityMatrix(self, nCtrPnts, contin_cons, params, flatKnots):
        """Additional matrix for continuity conditions on closed curves"""
        continuity_entries = self.matrix(contin_cons, nCtrPnts)
        continuity_params1 = [params[0]]  # TColStd_Array1OfReal continuity_params1(params[0], 1, 1);
        continuity_params2 = [params[-1]]  # TColStd_Array1OfReal continuity_params2(params[params.size() - 1], 1, 1);

        # bsa = BSplineAlgorithms(1e-6)
        diff1_1 = bsplineBasisMat(self.degree, flatKnots, continuity_params1, 1)
        diff1_2 = bsplineBasisMat(self.degree, flatKnots, continuity_params2, 1)
        #  math_Matrix diff1_1 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params1, 1);
        #  math_Matrix diff1_2 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params2, 1);
        diff2_1 = bsplineBasisMat(self.degree, flatKnots, continuity_params1, 2)
        diff2_2 = bsplineBasisMat(self.degree, flatKnots, continuity_params2, 2)
        #  math_Matrix diff2_1 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params1, 2);
        #  math_Matrix diff2_2 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params2, 2);

        #  Set C1 condition
        continuity_entries[0] = diff1_1 - diff1_2
        #  Set C2 condition
        continuity_entries[1] = diff2_1 - diff2_2

        if not self.firstAndLastInterpolated():
            diff0_1 = bsplineBasisMat(self.degree, flatKnots, continuity_params1, 0)
            diff0_2 = bsplineBasisMat(self.degree, flatKnots, continuity_params2, 0)
            #  math_Matrix diff0_1 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params1, 0);
            #  math_Matrix diff0_2 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params2, 0);
            continuity_entries[2] = diff0_1 - diff0_2

        return continuity_entries

    def python_solve(self, params, knots, mults):
        """Compute the BSpline curve that fits the points
        Returns the curve, and the max error between points and curve
        This method is used by iterative function FitCurveOptimal"""

        # debug("python_solve(params, knots, mults):\n%s\n%s\n%s"%(params, knots, mults))

        #  TODO knots and mults are OCC arrays (1-based)
        #  TODO I replaced the following OCC objects with numpy arrays:
        # math_Matrix (Init, Set, Transposed, Multiplied, )
        # math_Gauss (Solve, IsDone)
        # math_Vector (Set)
        #  compute flat knots to solve system

        #  TODO check code below !!!
        # nFlatKnots = BSplCLib::KnotSequenceLength(mults, self.degree, False)
        # TColStd_Array1OfReal flatKnots(1, nFlatKnots)
        # BSplCLib::KnotSequence(knots, mults, flatKnots)
        flatKnots = []
        for i in range(len(knots)):
            flatKnots += [knots[i]] * mults[i]

        n_apprxmated = len(self.indexOfApproximated)
        n_intpolated = len(self.indexOfInterpolated)
        n_continuityConditions = 0
        if self.isClosed():
            #  C0, C1, C2
            n_continuityConditions = 3
            if self.firstAndLastInterpolated():
                #  Remove C0 as they are already equal by design
                n_continuityConditions -= 1
        #  Number of control points required
        nCtrPnts = len(flatKnots) - self.degree - 1

        if (nCtrPnts < (n_intpolated + n_continuityConditions) or nCtrPnts < (self.degree + 1 + n_continuityConditions)):
            raise RuntimeError("Too few control points for curve interpolation!")

        if (n_apprxmated == 0 and not nCtrPnts == (n_intpolated + n_continuityConditions)):
            raise RuntimeError("Wrong number of control points for curve interpolation!")

        #  Build left hand side of the equation
        n_vars = nCtrPnts + n_intpolated + n_continuityConditions
        lhs = np.array([[0.] * (n_vars) for i in range(n_vars)])
        # math_Matrix lhs(1, n_vars, 1, n_vars)
        # lhs.Init(0.)

        #  Allocate right hand side
        rhsx = np.array([0.] * n_vars)
        rhsy = np.array([0.] * n_vars)
        rhsz = np.array([0.] * n_vars)
        # debug(n_apprxmated)
        if (n_apprxmated > 0):
            #  Write b vector. These are the points to be approximated
            appParams = np.array([0.] * n_apprxmated)
            bx = np.array([0.] * n_apprxmated)
            by = np.array([0.] * n_apprxmated)
            bz = np.array([0.] * n_apprxmated)
            # appIndex = 0
            for idx in range(len(self.indexOfApproximated)):
                ioa = self.indexOfApproximated[idx]  # + 1
                p = self.pnts[ioa]
                bx[idx] = p.x
                by[idx] = p.y
                bz[idx] = p.z
                appParams[idx] = params[ioa]
                # debug(appParams[idx])
                # appIndex += 1

            #  Solve constrained linear least squares
            #  min(Ax - b) s.t. Cx = d
            #  Create left hand side block matrix
            #  A.T*A  C.T
            #  C      0
            # math_Matrix A = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, appParams)
            # math_Matrix At = A.Transposed()

            # bsa = BSplineAlgorithms(1e-6)
            A = bsplineBasisMat(self.degree, flatKnots, appParams, 0)
            # debug("self.degree %s"%str(self.degree))
            # debug("flatKnots %s"%str(flatKnots))
            # debug("appParams %s"%str(appParams))
            At = A.T
            mul = np.matmul(At, A)
            # debug(lhs)
            # debug(mul)
            for i in range(len(mul)):
                for j in range(len(mul)):
                    lhs[i][j] = mul[i][j]
            # debug("mul : %s"%str(mul.shape))
            # debug("rhsx : %s"%(rhsx.shape))
            # debug("np.matmul(At,bx) : %s"%(np.matmul(At,bx).shape))
            le = len(np.matmul(At, bx))
            rhsx[0:le] = np.matmul(At, bx)
            rhsy[0:le] = np.matmul(At, by)
            rhsz[0:le] = np.matmul(At, bz)
        # debug("lhs : %s"%str(lhs))
        if (n_intpolated + n_continuityConditions > 0):
            #  Write d vector. These are the points that should be interpolated as well as the continuity constraints for closed curve
            # math_Vector dx(1, n_intpolated + n_continuityConditions, 0.)
            dx = np.array([0.] * (n_intpolated + n_continuityConditions))
            dy = np.array([0.] * (n_intpolated + n_continuityConditions))
            dz = np.array([0.] * (n_intpolated + n_continuityConditions))
            if (n_intpolated > 0):
                interpParams = [0] * n_intpolated
                # intpIndex = 0
                # for (std::vector<size_t>::const_iterator it_idx = m_indexOfInterpolated.begin() it_idx != m_indexOfInterpolated.end() ++it_idx) {
                    # Standard_Integer ipnt = static_cast<Standard_Integer>(*it_idx + 1)
                for idx in range(len(self.indexOfInterpolated)):
                    ioi = self.indexOfInterpolated[idx]  # + 1
                    p = self.pnts[ioi]
                    dx[idx] = p.x
                    dy[idx] = p.y
                    dz[idx] = p.z
                    try:
                        interpParams[idx] = params[ioi]
                    except IndexError:
                        debug(ioi)
                    # intpIndex += 1

                C = bsplineBasisMat(self.degree, flatKnots, interpParams, 0)
                Ct = C.T
                # debug("C : %s"%str(C.shape))
                # debug("Ct : %s"%str(Ct.shape))
                # debug("lhs : %s"%str(lhs.shape))
                for i in range(nCtrPnts):
                    for j in range(n_intpolated):
                        lhs[i][j + nCtrPnts] = Ct[i][j]
                        lhs[j + nCtrPnts][i] = C[j][i]
                # lhs.Set(1, nCtrPnts, nCtrPnts + 1, nCtrPnts + n_intpolated, Ct)
                # lhs.Set(nCtrPnts + 1,  nCtrPnts + n_intpolated, 1, nCtrPnts, C)
                # debug("lhs : %s"%str(lhs.shape))

            #  sets the C2 continuity constraints for closed curves on the left hand side if requested
            if self.isClosed():
                continuity_entries = self.getContinuityMatrix(nCtrPnts, n_continuityConditions, params, flatKnots)
                continuity_entriest = continuity_entries.T
                debug("continuity_entries : {}".format(str(continuity_entries.shape)))
                for i in range(n_continuityConditions):
                    for j in range(nCtrPnts):
                        lhs[nCtrPnts + n_intpolated + i][j] = continuity_entries[i][j]
                        lhs[j][nCtrPnts + n_intpolated + i] = continuity_entriest[j][i]
                # lhs.Set(nCtrPnts + n_intpolated + 1, nCtrPnts + n_intpolated + n_continuityConditions, 1, nCtrPnts, continuity_entries)
                # lhs.Set(1, nCtrPnts, nCtrPnts + n_intpolated + 1, nCtrPnts + n_intpolated + n_continuityConditions, continuity_entries.Transposed())

            rhsx[nCtrPnts:n_vars + 1] = dx
            rhsy[nCtrPnts:n_vars + 1] = dy
            rhsz[nCtrPnts:n_vars + 1] = dz
            # rhsy.Set(nCtrPnts + 1, n_vars, dy)
            # rhsz.Set(nCtrPnts + 1, n_vars, dz)

        # math_Gauss solver(lhs)

        # math_Vector cp_x(1, n_vars)
        # math_Vector cp_y(1, n_vars)
        # math_Vector cp_z(1, n_vars)

        # solver.Solve(rhsx, cp_x)
        # if (!solver.IsDone()) {
            # raise RuntimeError("Singular Matrix")
        # }
        # debug("lhs : %s"%str(lhs))
        # debug("rhsx : %s"%str(rhsx))
        try:
            cp_x = np.linalg.solve(lhs, rhsx)
            cp_y = np.linalg.solve(lhs, rhsy)
            cp_z = np.linalg.solve(lhs, rhsz)
        except np.linalg.LinAlgError:
            debug("Numpy linalg solver failed\n")
            return None, None
        poles = [FreeCAD.Vector(cp_x[i], cp_y[i], cp_z[i]) for i in range(nCtrPnts)]

        result = Part.BSplineCurve()
        debug("{} poles : {}".format(len(poles), poles))
        debug("{} knots : {}".format(len(knots), knots))
        debug("{} mults : {}".format(len(mults), mults))
        debug("degree : {}".format(self.degree))
        debug("conti : {}".format(self.C2Continuous))
        result.buildFromPolesMultsKnots(poles, mults, knots, False, self.degree)

        #  compute error
        max_error = 0.
        for idx in range(len(self.indexOfApproximated)):
            ioa = self.indexOfApproximated[idx]
            p = self.pnts[ioa]
            par = params[ioa]
            error = result.value(par).distanceToPoint(p)
            max_error = max(max_error, error)
        return result, max_error

    def optimizeParameters(self, curve, params):
        # /**
        # * @brief Recalculates the curve parameters t_k after the
        # * control points are fitted to achieve an even better fit.
        # */
        #  optimize each parameter by finding it's position on the curve
        #  for (std::vector<size_t>::const_iterator it_idx = m_indexOfApproximated.begin(); it_idx != m_indexOfApproximated.end(); ++it_idx) {
        for i in self.indexOfApproximated:  # range(len(self.indexOfApproximated)):
            # parameter, error = self.projectOnCurve(self.pnts[i], curve, params[i])
            # debug("optimize Parameter %d from %0.4f to %0.4f"%(i,params[i],parameter))
            #  store optimised parameter
            params[i] = curve.parameter(self.pnts[i])  # parameter

    def projectOnCurve(self, pnt, curve, inital_Parm):
        maxIter = 10  # maximum No of iterations
        eps = 1.0e-6  # accuracy of arc length parameter

        t = inital_Parm
        edge = curve.toShape()

        #  newton step
        dt = 0
        f = 0

        itera = 0  # iteration counter
        while True:  # Newton iteration to get a better t parameter

            #  Get the derivatives of the spline wrt parameter t
            # gp_Vec p   = curve->DN(t, 0);
            # gp_Vec dp  = curve->DN(t, 1);
            # gp_Vec d2p = curve->DN(t, 2);
            p = edge.valueAt(t)
            dp = edge.derivative1At(t)
            d2p = edge.derivative2At(t)

            #  compute objective function and their derivative
            f = square_distance(pnt, p)

            df = (p - pnt).dot(dp)
            d2f = (p - pnt).dot(d2p) + square_magnitude(dp)

            #  newton iterate
            dt = -df / d2f
            t_new = t + dt

            #  if parameter out of range reset it to the start value
            if (t_new < curve.FirstParameter or t_new > curve.LastParameter):
                t_new = inital_Parm
                dt = 0.
            t = t_new

            itera += 1
            if (abs(dt) < eps or itera >= maxIter):
                break

        return t, pow(f, 0.5)

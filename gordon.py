# This file is a python port of the following files :
#
# /src/geometry/CTiglBSplineAlgorithms.cpp
# /src/geometry/CTiglBSplineApproxInterp.cpp
# /src/geometry/CTiglGordonSurfaceBuilder.cpp
# /src/geometry/CTiglInterpolateCurveNetwork.cpp
#
# from the Tigl library : https://github.com/DLR-SC/tigl under Apache-2 license

import FreeCAD
import Part
from math import pi

def debug(o):
    if isinstance(o,Part.BSplineCurve):
        FreeCAD.Console.PrintWarning("\nBSplineCurve\n")
        FreeCAD.Console.PrintWarning("Degree: %d\n"%(o.Degree))
        FreeCAD.Console.PrintWarning("NbPoles: %d\n"%(o.NbPoles))
        FreeCAD.Console.PrintWarning("Knots: %d (%0.2f - %0.2f)\n"%(o.NbKnots, o.FirstParameter, o.LastParameter))
        FreeCAD.Console.PrintWarning("Mults: %s\n"%(o.getMultiplicities()))
        FreeCAD.Console.PrintWarning("Periodic: %s\n"%(o.isPeriodic()))
    elif isinstance(o,Part.BSplineSurface):
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
        FreeCAD.Console.PrintMessage("%s\n"%o)


# TODO is this the good SquareDistance function ???
def SquareDistance(v1,v2):
    return(pow((v1.x-v2.x),2)+pow((v1.y-v2.y),2)+pow((v1.z-v2.z),2))

def SquareMagnitude(v1):
    return(pow(v1.x,2)+pow(v1.y,2)+pow(v1.z,2))

def find(val, array, tol=1e-5):
    for i in range(len(array)):
        if abs(val-array[i]) < tol:
            return(int(i))
    return(-1)

def IsInsideTolerance(array, value, tolerance = 1e-15):
    for i in range(len(array)):
        if abs(array[i] - value) <= tolerance:
            return(i)
    return(-1)

def LinspaceWithBreaks(umin, umax, n_values, breaks):
    du = float(umax - umin) / (n_values - 1)
    result = list() # size = n_values
    for i in range(n_values):
        result.append(i * du + umin)
    # now insert the break

    eps = 0.3
    # remove points, that are closer to each break point than du*eps
    for breakpoint in breaks:
        pos = IsInsideTolerance(result, breakpoint, du*eps) # std::find_if(result.begin(), result.end(), IsInsideTolerance(breakpoint, du*eps));
        if pos >= 0:
            # point found, replace it
            result[pos] = breakpoint
        else:
            # find closest element
            pos = IsInsideTolerance(result, breakpoint, (0.5 + 1e-8)*du) # std::find_if(result.begin(), result.end(), IsInsideTolerance(breakpoint, (0.5 + 1e-8)*du));
            if (result[pos] > breakpoint):
                result.insert(pos, breakpoint)
            else:
                result.insert(pos+1, breakpoint)
    return result

def insertKnot(knot, count, degree, knots, mults, tol = 1e-5):
    if (knot < knots[0] or knot > knots[-1]):
        raise RuntimeError("knot out of range")

    # pos = std::find_if(knots.begin(), knots.end(), helper_function_find(knot, tol)) - knots.begin();
    pos = find(knot, knots, tol)

    if (pos == -1):
        # knot not found, insert new one
        pos = 0;
        while (knots[pos] < knot):
            pos += 1
        knots.insert(pos, knot)
        mults.insert(pos, min(count, degree))
    else:
        # knot found, increase multiplicity
        mults[pos] = min(mults[pos] + count, degree)

class BSplineApproxInterp(object):
    # used in BSplineAlgorithms.reparametrizeBSplineContinuouslyApprox (around line 1100)
    def __init__(self, points, nControlPoints, degree, continuous_if_closed):
        self.pnts = points
        self.indexOfApproximated = range(len(points))
        self.degree = degree
        self.ncp = nControlPoints
        self.C2Continuous = continuous_if_closed
        self.indexOfInterpolated = list()
        self.indexOfKinks = list()
    def InterpolatePoint(self, pointIndex, withKink):
        if not pointIndex in self.indexOfApproximated:
            debug("Invalid index in CTiglBSplineApproxInterp::InterpolatePoint")
            debug("%d is not in %s"%(pointIndex, self.indexOfApproximated))
        else:
            debug("Successfully switched point #%d from approx to interp"%(pointIndex))
            self.indexOfApproximated.remove(pointIndex)
            self.indexOfInterpolated.append(int(pointIndex))
        if withKink:
            self.indexOfKinks.append(pointIndex)
    def FitCurveOptimal(self, initialParms, maxIter):
        parms = list()
        # compute initial parameters, if initialParms empty
        if len(initialParms) == 0:
            parms = self.computeParameters(0.5)
        else:
            parms = initialParms

        if not len(parms) == len(self.pnts):
            raise RuntimeError("Number of parameters don't match number of points")

        # Compute knots from parameters
        knots, mults = self.computeKnots(self.ncp, parms)
        #debug("python_solve(ncp, params, knots, ):\n%s\n%s\n%s"%(self.ncp, parms, knots))
        #TColStd_Array1OfInteger occMults(1, static_cast<Standard_Integer>(mults.size()));
        #TColStd_Array1OfReal occKnots(1, static_cast<Standard_Integer>(knots.size()));
        #for (size_t i = 0; i < knots.size(); ++i) {
            #Standard_Integer idx = static_cast<Standard_Integer>(i + 1);
            #occKnots.SetValue(idx, knots[i]);
            #occMults.SetValue(idx, mults[i]);
        #}
        iteration = 0;

        # solve system
        result, error = self.python_solve(parms, knots, mults) # TODO occKnots, occMults ???? See above
        old_error = error * 2

        while ( (error>0) and ((old_error-error)/max(error, 1e-6) > 1e-3) and (iteration < maxIter) ):
            old_error = error
            self.optimizeParameters(result, parms)
            result, error = self.python_solve(parms, knots, mults)
            iteration += 1
        
        return(result,error)
    def computeParameters(self, alpha):
        sum = 0.0

        nPoints = len(self.pnts)
        t= [0]*nPoints

        t[0] = 0.0
        # calc total arc length: dt^2 = dx^2 + dy^2
        for i in range(1,nPoints): #(size_t i = 1; i < nPoints; i++) {
            # Standard_Integer idx = static_cast<Standard_Integer>(i);
            len2 = SquareDistance(self.pnts[i-1],self.pnts[i])
            sum += pow(len2, alpha / 2.)
            #print(i)
            t[i] = sum

        # normalize parameter with maximum
        tmax = t[nPoints - 1]
        for i in range(1,nPoints):
            t[i] /= tmax

        # reset end value to achieve a better accuracy
        t[nPoints - 1] = 1.0
        return(t)
    def computeKnots(self, ncp, parms):
        order = self.degree + 1
        if (ncp < order):
            raise RuntimeError("Number of control points to small!")

        umin = min(parms)
        umax = max(parms)

        knots = [0]*(ncp - self.degree + 1)
        mults = [0]*(ncp - self.degree + 1)
        #debug("computeKnots(ncp, params, knots, mults):\n%s\n%s\n%s\n%s"%(ncp, parms, knots, mults))

        # fill multiplicity at start
        knots[0] = umin
        mults[0] = order

        # number of knots between the multiplicities
        N = (ncp - order)
        # set uniform knot distribution
        for i in range(1,N+1): #(size_t i = 1; i <= N; ++i ) {
            knots[i] = umin + (umax - umin) * float(i) / float(N + 1)
            mults[i] = 1

        # fill multiplicity at end
        knots[N + 1] = umax
        mults[N + 1] = order

        #for (std::vector<size_t>::const_iterator it = m_indexOfKinks.begin(); it != m_indexOfKinks.end(); ++it) {
            #size_t idx = *it;
        for i in range(len(self.indexOfKinks)):
            insertKnot(parms[i], self.degree, self.degree, knots, mults, 1e-4)
            
        #debug("computeKnots(ncp, params, knots, mults):\n%s\n%s\n%s\n%s"%(ncp, parms, knots, mults))
        return(knots, mults)
    def maxDistanceOfBoundingBox(self, points):
        maxDistance = 0.
        for i in range(len(points)): #(int i = points.Lower(); i <= points.Upper(); ++i) {
            for j in range(len(points)): #for (int j = points.Lower(); j <= points.Upper(); ++j) {
                distance = points[i].distanceToPoint(points[j])
                if (maxDistance < distance):
                    maxDistance = distance
        return(maxDistance)
    def isClosed(self):
        maxDistance = self.maxDistanceOfBoundingBox(self.pnts)
        error = 1e-12*maxDistance
        return(self.pnts[0].distanceToPoint(self.pnts[-1]) < error)
    def firstAndLastInterpolated(self):
        first = 0 in self.indexOfInterpolated
        last = (len(self.pnts) - 1) in self.indexOfInterpolated
        #std::find(m_indexOfInterpolated.begin(), m_indexOfInterpolated.end(), m_pnts.Length() - 1) != m_indexOfInterpolated.end();
        return(first and last)
    def matrix(self,nrow,ncol, val=0. ):
        import numpy as np
        return(np.array([[val]*ncol for i in range(nrow)]))
    def getContinuityMatrix(self, nCtrPnts, contin_cons, params, flatKnots):
        continuity_entries = self.matrix(contin_cons, nCtrPnts)
        continuity_params1 = [params[0]] # TColStd_Array1OfReal continuity_params1(params[0], 1, 1);
        continuity_params2 = [params[-1]] # TColStd_Array1OfReal continuity_params2(params[params.size() - 1], 1, 1);

        bsa = BSplineAlgorithms(1e-6)
        diff1_1 = bsa.bsplineBasisMat(self.degree, flatKnots, continuity_params1, 1)
        diff1_2 = bsa.bsplineBasisMat(self.degree, flatKnots, continuity_params2, 1)
        # math_Matrix diff1_1 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params1, 1);
        # math_Matrix diff1_2 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params2, 1);
        diff2_1 = bsa.bsplineBasisMat(self.degree, flatKnots, continuity_params1, 2)
        diff2_2 = bsa.bsplineBasisMat(self.degree, flatKnots, continuity_params2, 2)
        # math_Matrix diff2_1 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params1, 2);
        # math_Matrix diff2_2 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params2, 2);

        # Set C1 condition
        continuity_entries[0] = diff1_1 - diff1_2
        # Set C2 consition
        continuity_entries[1] = diff2_1 - diff2_2
        
        if not self.firstAndLastInterpolated():
            diff0_1 = bsa.bsplineBasisMat(self.degree, flatKnots, continuity_params1, 0)
            diff0_2 = bsa.bsplineBasisMat(self.degree, flatKnots, continuity_params2, 0)
            # math_Matrix diff0_1 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params1, 0);
            # math_Matrix diff0_2 = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, continuity_params2, 0);
            continuity_entries[2] = diff0_1 - diff0_2

        return(continuity_entries)
    def python_solve(self, params, knots, mults):
        import numpy as np
        #debug("python_solve(params, knots, mults):\n%s\n%s\n%s"%(params, knots, mults))
        #from scipy import linalg
        #return()
        # TODO knots and mults are OCC arrays (1-based)
        # TODO I replaced the following OCC objects with numpy arrays:
        #math_Matrix (Init, Set, Transposed, Multiplied, )
        #math_Gauss (Solve, IsDone)
        #math_Vector (Set)
        # compute flat knots to solve system
        
        # TODO check code below !!!
        #nFlatKnots = BSplCLib::KnotSequenceLength(mults, self.degree, False)
        #TColStd_Array1OfReal flatKnots(1, nFlatKnots)
        #BSplCLib::KnotSequence(knots, mults, flatKnots)
        flatKnots = []
        for i in range(len(knots)):
            flatKnots += [knots[i]]*mults[i]
            

        n_apprxmated = len(self.indexOfApproximated)
        n_intpolated = len(self.indexOfInterpolated)
        n_continuityConditions = 0
        if self.isClosed() and self.C2Continuous:
            # C0, C1, C2
            n_continuityConditions = 3
            if self.firstAndLastInterpolated():
                # Remove C0 as they are already equal by design
                n_continuityConditions -= 1
        
        # Number of control points required
        nCtrPnts = len(flatKnots) - self.degree - 1

        if (nCtrPnts < (n_intpolated + n_continuityConditions) or nCtrPnts < (self.degree + 1 + n_continuityConditions)):
            debug("nCtrPnts %d n_intpolated %d n_continuityConditions %d self.degree %d "%(nCtrPnts, n_intpolated, n_continuityConditions, self.degree))
            raise RuntimeError("Too few control points for curve interpolation!")

        if (n_apprxmated == 0 and not nCtrPnts == (n_intpolated + n_continuityConditions)):
            raise RuntimeError("Wrong number of control points for curve interpolation!")

        # Build left hand side of the equation
        n_vars = nCtrPnts + n_intpolated + n_continuityConditions
        lhs = np.array([[0.]*(n_vars) for i in range(n_vars)])
        #math_Matrix lhs(1, n_vars, 1, n_vars)
        #lhs.Init(0.)
        
        # Allocate right hand side
        #math_Vector rhsx(1, n_vars)
        #math_Vector rhsy(1, n_vars)
        #math_Vector rhsz(1, n_vars)
        rhsx = np.array([0.]*n_vars)
        rhsy = np.array([0.]*n_vars)
        rhsz = np.array([0.]*n_vars)
        #debug(n_apprxmated)
        if (n_apprxmated > 0):
            # Write b vector. These are the points to be approximated
            appParams = np.array([0.]*n_apprxmated) # TColStd_Array1OfReal appParams(1, n_apprxmated)
            #math_Vector bx(1, n_apprxmated)
            #math_Vector by(1, n_apprxmated)
            #math_Vector bz(1, n_apprxmated)
            bx = np.array([0.]*n_apprxmated)
            by = np.array([0.]*n_apprxmated)
            bz = np.array([0.]*n_apprxmated)
        
            appIndex = 0
            for it_idx in range(len(self.indexOfApproximated)): #for (std::vector<size_t>::const_iterator it_idx = m_indexOfApproximated.begin() it_idx != m_indexOfApproximated.end() ++it_idx) {
                ipnt = self.indexOfApproximated[it_idx] # + 1
                p = self.pnts[ipnt]
                
                bx[appIndex] = p.x
                by[appIndex] = p.y
                bz[appIndex] = p.z
                appParams[appIndex] = params[self.indexOfApproximated[it_idx]]
                #debug(appParams[appIndex])
                appIndex += 1

            # Solve constrained linear least squares
            # min(Ax - b) s.t. Cx = d
            # Create left hand side block matrix
            # A.T*A  C.T
            # C      0
            #math_Matrix A = CTiglBSplineAlgorithms::bsplineBasisMat(m_degree, flatKnots, appParams)
            #math_Matrix At = A.Transposed()
            
            bsa = BSplineAlgorithms(1e-6)
            A = bsa.bsplineBasisMat(self.degree, flatKnots, appParams, 0)
            #debug("self.degree %s"%str(self.degree))
            #debug("flatKnots %s"%str(flatKnots))
            #debug("appParams %s"%str(appParams))
            At = A.T
            mul = np.matmul(At,A)
            #debug(lhs)
            #debug(mul)
            for i in range(len(mul)):
                for j in range(len(mul)):
                    lhs[i][j] = mul[i][j]
            #debug("mul : %s"%str(mul.shape))
            #debug("rhsx : %s"%(rhsx.shape))
            #debug("np.matmul(At,bx) : %s"%(np.matmul(At,bx).shape))
            l = len(np.matmul(At,bx))
            rhsx[0:l] = np.matmul(At,bx)
            rhsy[0:l] = np.matmul(At,by)
            rhsz[0:l] = np.matmul(At,bz)
        #debug("lhs : %s"%str(lhs))
        if (n_intpolated + n_continuityConditions > 0):
            # Write d vector. These are the points that should be interpolated as well as the continuity constraints for closed curve
            #math_Vector dx(1, n_intpolated + n_continuityConditions, 0.)
            dx = np.array([0.]*(n_intpolated + n_continuityConditions))
            dy = np.array([0.]*(n_intpolated + n_continuityConditions))
            dz = np.array([0.]*(n_intpolated + n_continuityConditions))
            if(n_intpolated > 0):
                interpParams = [0]*n_intpolated
                intpIndex = 0
                #for (std::vector<size_t>::const_iterator it_idx = m_indexOfInterpolated.begin() it_idx != m_indexOfInterpolated.end() ++it_idx) {
                    #Standard_Integer ipnt = static_cast<Standard_Integer>(*it_idx + 1)
                for it_idx in range(len(self.indexOfInterpolated)): #for (std::vector<size_t>::const_iterator it_idx = m_indexOfApproximated.begin() it_idx != m_indexOfApproximated.end() ++it_idx) {
                    ipnt = it_idx # + 1
                    p = self.pnts[ipnt]
                    dx[intpIndex] = p.x
                    dy[intpIndex] = p.y
                    dz[intpIndex] = p.z
                    try:
                        interpParams[intpIndex] = params[self.indexOfInterpolated[it_idx]]
                    except:
                        debug(self.indexOfInterpolated[it_idx])
                    intpIndex += 1

                C = bsa.bsplineBasisMat(self.degree, flatKnots, interpParams, 0)
                Ct = C.T
                #debug("C : %s"%str(C.shape))
                #debug("Ct : %s"%str(Ct.shape))
                #debug("lhs : %s"%str(lhs.shape))
                for i in range(nCtrPnts):
                    for j in range(n_intpolated):
                        lhs[i][j + nCtrPnts] = Ct[i][j]
                        lhs[j + nCtrPnts][i] = C[j][i]
                #lhs.Set(1, nCtrPnts, nCtrPnts + 1, nCtrPnts + n_intpolated, Ct)
                #lhs.Set(nCtrPnts + 1,  nCtrPnts + n_intpolated, 1, nCtrPnts, C)
                #debug("lhs : %s"%str(lhs.shape))
                
            # sets the C2 continuity constraints for closed curves on the left hand side if requested
            if (self.isClosed() and self.C2Continuous):
                continuity_entries = self.getContinuityMatrix(nCtrPnts, n_continuityConditions, params, flatKnots)
                continuity_entriest = continuity_entries.T
                debug("continuity_entries : %s"%str(continuity_entries.shape))
                for i in range(n_continuityConditions):
                    for j in range(nCtrPnts):
                        lhs[nCtrPnts + n_intpolated + i][j] = continuity_entries[i][j]
                        lhs[j][nCtrPnts + n_intpolated + i] = continuity_entriest[j][i]
                #lhs.Set(nCtrPnts + n_intpolated + 1, nCtrPnts + n_intpolated + n_continuityConditions, 1, nCtrPnts, continuity_entries)
                #lhs.Set(1, nCtrPnts, nCtrPnts + n_intpolated + 1, nCtrPnts + n_intpolated + n_continuityConditions, continuity_entries.Transposed())

            rhsx[nCtrPnts:n_vars+1] = dx
            rhsy[nCtrPnts:n_vars+1] = dy
            rhsz[nCtrPnts:n_vars+1] = dz
            #rhsy.Set(nCtrPnts + 1, n_vars, dy)
            #rhsz.Set(nCtrPnts + 1, n_vars, dz)

        #math_Gauss solver(lhs)

        #math_Vector cp_x(1, n_vars)
        #math_Vector cp_y(1, n_vars)
        #math_Vector cp_z(1, n_vars)

        #solver.Solve(rhsx, cp_x)
        #if (!solver.IsDone()) {
            #raise RuntimeError("Singular Matrix")
        #}
        #debug("lhs : %s"%str(lhs))
        #debug("rhsx : %s"%str(rhsx))
        
        cp_x = np.linalg.solve(lhs, rhsx)
        if not np.allclose(np.dot(lhs, cp_x), rhsx):
            raise RuntimeError("Singular Matrix")

        #solver.Solve(rhsy, cp_y)
        #if (!solver.IsDone()) {
            #raise RuntimeError("Singular Matrix")
        #}
        cp_y = np.linalg.solve(lhs, rhsy)
        if not np.allclose(np.dot(lhs, cp_y), rhsy):
            raise RuntimeError("Singular Matrix")
        
        #solver.Solve(rhsz, cp_z)
        #if (!solver.IsDone()) {
            #raise RuntimeError("Singular Matrix")
        #}
        cp_z = np.linalg.solve(lhs, rhsz)
        if not np.allclose(np.dot(lhs, cp_z), rhsz):
            raise RuntimeError("Singular Matrix")
        
        poles = [FreeCAD.Vector(cp_x[i], cp_y[i], cp_z[i]) for i in range(nCtrPnts)]
        #TColgp_Array1OfPnt poles(1, nCtrPnts)
        #for (Standard_Integer icp = 1 icp <= nCtrPnts ++icp) {
            #gp_Pnt pnt(cp_x.Value(icp), cp_y.Value(icp), cp_z.Value(icp))
            #poles.SetValue(icp, pnt)
        #}

        result = Part.BSplineCurve()
        result.buildFromPolesMultsKnots(poles, mults, knots, False, self.degree)

        # compute error
        max_error = 0.
        #for (std::vector<size_t>::const_iterator it_idx = m_indexOfApproximated.begin() it_idx != m_indexOfApproximated.end() ++it_idx) {
            #Standard_Integer ipnt = static_cast<Standard_Integer>(*it_idx + 1)
        for it_idx in range(len(self.indexOfApproximated)):
            ipnt = it_idx # + 1
            p = self.pnts[ipnt]
            par = params[self.indexOfApproximated[it_idx]]

            error = result.value(par).distanceToPoint(p)
            max_error = max(max_error, error)
        return(result, max_error)
    def optimizeParameters(self, curve, m_t):
        #/**
        #* @brief Recalculates the curve parameters t_k after the
        #* control points are fitted to achieve an even better fit.
        #*/
        # optimize each parameter by finding it's position on the curve
        # for (std::vector<size_t>::const_iterator it_idx = m_indexOfApproximated.begin(); it_idx != m_indexOfApproximated.end(); ++it_idx) {
        for i in range(len(self.indexOfApproximated)):
            parameter, error = self.projectOnCurve(self.pnts[i], curve, m_t[i])

            # store optimised parameter
            m_t[i] = parameter
    def projectOnCurve(self, pnt, curve, inital_Parm):
        maxIter = 10 # maximum No of iterations
        eps  = 1.0e-6 # accuracy of arc length parameter

        t = inital_Parm
        edge = curve.toShape()

        # newton step
        dt = 0
        f = 0

        itera = 0 # iteration counter
        while True: # Newton iteration to get a better t parameter

            # Get the derivatives of the spline wrt parameter t
            #gp_Vec p   = curve->DN(t, 0);
            #gp_Vec dp  = curve->DN(t, 1);
            #gp_Vec d2p = curve->DN(t, 2);
            p = edge.valueAt(t)
            dp = edge.derivative1At(t)
            d2p = edge.derivative2At(t)

            # compute objective function and their derivative
            f = SquareDistance(pnt, p)

            df = (p - pnt).dot(dp)
            d2f = (p - pnt).dot(d2p) + SquareMagnitude(dp)

            # newton iterate
            dt = -df / d2f
            t_new = t + dt

            # if parameter out of range reset it to the start value
            if (t_new < curve.FirstParameter or t_new > curve.LastParameter):
                t_new = inital_Parm
                dt = 0.
            t = t_new

            itera += 1
            if (abs(dt) < eps or itera >= maxIter):
                break

        return(t, pow(f,0.5))

class SurfAdapterView(object):
    def __init__(self, surf, direc):
        self.s = surf
        self.d = direc
    @property
    def NbKnots(self):
        return(self.getNKnots())
    @property
    def NbPoles(self):
        return(self.getNPoles())
    @property
    def Degree(self):
        return(self.getDegree())

    def insertKnot(self, knot, mult, tolerance=1e-15):
        try:
            if self.d == 0:
                self.s.insertUKnot(abs(knot), mult, tolerance)
            else:
                self.s.insertVKnot(abs(knot), mult, tolerance)
        except Part.OCCError:
            debug("failed to insert knot : %f - %d - %f"%(knot, mult, tolerance))
            raise RuntimeError
    def getKnot(self, idx):
        if self.d == 0:
            return(self.s.getUKnot(idx))
        else:
            return(self.s.getVKnot(idx))
    def getKnots(self):
        if self.d == 0:
            return(self.s.getUKnots())
        else:
            return(self.s.getVKnots())
    def getMultiplicities(self):
        if self.d == 0:
            return(self.s.getUMultiplicities())
        else:
            return(self.s.getVMultiplicities())
    def increaseMultiplicity(self, idx, mult):
        if self.d == 0:
            return(self.s.increaseUMultiplicity(idx, mult))
        else:
            return(self.s.increaseVMultiplicity(idx, mult))
    def getMult(self, idx):
        if self.d == 0:
            return(self.s.getUMultiplicity(idx))
        else:
            return(self.s.getVMultiplicity(idx))
    def getMultiplicity(self, idx):
        return(self.getMult(idx))
    def getNKnots(self):
        if self.d == 0:
            return(self.s.NbUKnots)
        else:
            return(self.s.NbVKnots)
    def getNPoles(self):
        if self.d == 0:
            return(self.s.NbUPoles)
        else:
            return(self.s.NbVPoles)
    def getDegree(self):
        if self.d == 0:
            return(int(self.s.UDegree))
        else:
            return(int(self.s.VDegree))

class BSplineAlgorithms(object):
    """Various BSpline algorithms"""
    def __init__(self, tol=1e-8):
        self.REL_TOL_CLOSED = tol
        if tol > 0.0:
            self.tol = tol # parametric tolerance
    def error(self,mes):
        print(mes)
    def scale(self, c):
        res = 0
        if isinstance(c, (tuple,list)):
            for cu in c:
                res = max(res,self.scale(cu))
        elif isinstance(c, (Part.BSplineCurve, Part.BezierCurve)):
            pts = c.getPoles()
            for p in pts[1:]:
                res = max(res, p.distanceToPoint(pts[0]))
        return(res)
    def scale_pt_array(self, points):
        theScale = 0.
        for uidx in range(len(points)):
            pFirst = points[uidx][0]
            for vidx in range(1, len(points[0])):
                dist = pFirst.distanceToPoint(points[uidx][vidx])
                theScale = max(theScale, dist)
        return theScale
    def bsplineBasisMat(self, degree, knots, params, derivOrder):
        import numpy as np
        #from scipy import linalg
        import nurbs_tools # import BsplineBasis
        ncp = len(knots) - degree - 1
        mx = np.array([[0.]*ncp for i in range(len(params))])
        #math_Matrix mx(1, params.Length(), 1, ncp);
        #mx.Init(0.);
        bspl_basis = np.array([[0.]*(ncp) for i in range(derivOrder + 1)])
        #math_Matrix bspl_basis(1, derivOrder + 1, 1, degree + 1);
        #bspl_basis.Init(0.);
        #debug("params %s"%str(params))
        for iparm in range(len(params)): # for (Standard_Integer iparm = 1; iparm <= params.Length(); ++iparm) {
            basis_start_index = 0
            
            bb = nurbs_tools.BsplineBasis()
            bb.knots = knots
            bb.degree = degree
            #span = bb.find_span(params[iparm])
            #res = bb.ders_basis_funs( span, params[iparm], derivOrder)
            for irow in range(derivOrder+1):
                #debug("irow %s"%str(irow))
                #debug("bspl_basis[irow] %s"%str(bspl_basis[irow]))
                bspl_basis[irow] = bb.evaluate(params[iparm],d=irow)
                #debug("bspl_basis[irow] %s"%str(bspl_basis[irow]))
                #for ival in range(len(res[irow])):
                    #bspl_basis[irow][ival+span] = res[irow][ival]
            ##if OCC_VERSION_HEX >= VERSION_HEX_CODE(7,1,0)
                    #BSplCLib::EvalBsplineBasis(derivOrder, degree + 1, knots, params.Value(iparm), basis_start_index, bspl_basis);
            ##else
                    #BSplCLib::EvalBsplineBasis(1, derivOrder, degree + 1, knots, params.Value(iparm), basis_start_index, bspl_basis);
            ##endif
            #if(derivOrder > 0):
                #help_vector = np.array([0.]*ncp) #(1, ncp);
                ###help_vector.Init(0.);
                ##help_vector.Set(basis_start_index, basis_start_index + degree, bspl_basis.Row(derivOrder + 1));
                #mx[iparm] = bspl_basis[derivOrder] #mx.SetRow(iparm, help_vector);
            #else:
                #mx[iparm] = bspl_basis[derivOrder] #  mx.Set(iparm, iparm, basis_start_index, basis_start_index + degree, bspl_basis);
            for i in range(len(bspl_basis[derivOrder])):
                mx[iparm][basis_start_index+i] = bspl_basis[derivOrder][i]
        return(mx)
    def intersections(self, spline1, spline2, tol3d):
        # light weight simple minimizer
        # check parametrization of B-splines beforehand
        # find out the average scale of the two B-splines in order to being able to handle a more approximate curves and find its intersections
        splines_scale = (self.scale(spline1) + self.scale(spline2)) / 2.
        intersection_params_vector = []
        inters = spline1.intersectCC(spline2)
        #GeomAPI_ExtremaCurveCurve intersectionObj(spline1, spline2);
        #debug("intersectCC results")
        if len(inters) >= 2:
            debug("\n*********************\n2 intersectCC results\n*********************")
            p1 = FreeCAD.Vector(inters[0].X, inters[0].Y, inters[0].Z)
            p2 = FreeCAD.Vector(inters[1].X, inters[1].Y, inters[1].Z)
            if (p1.distanceToPoint(p2) < tol3d * splines_scale):
                inters = [p1]
        for intpt in inters:
            if isinstance(intpt,Part.Point):
                inter = FreeCAD.Vector(intpt.X, intpt.Y, intpt.Z)
            else:
                inter = intpt
            #debug(intpt)
            param1 = spline1.parameter(inter)
            param2 = spline2.parameter(inter)
            #intersectionObj.Parameters(intersect_idx, param1, param2);
            # filter out real intersections
            point1 = spline1.value(param1);
            point2 = spline2.value(param2);
            if (point1.distanceToPoint(point2) < tol3d * splines_scale):
                intersection_params_vector.append([param1, param2])
            else:
                debug("Curves do not intersect each other")
                
            # for closed B-splines:
            if len(inters) == 1:
                if spline1.isClosed():
                    if abs(param1 - spline1.getKnot(1)) < self.tol:
                        # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the end of the closed curve, so add it by hand
                        intersection_params_vector.append([spline1.getKnot(spline1.NbKnots), param2])
                    elif  abs(param1 - spline1.getKnot(spline1.NbKnots)) < self.tol:
                        # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the beginning of the closed curve, so add it by hand
                        intersection_params_vector.append([spline1.getKnot(1), param2])
                elif  spline2.isClosed():
                    if abs(param2 - spline2.getKnot(1)) < self.tol:
                        # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the end of the closed curve, so add it by hand
                        intersection_params_vector.append([param1, spline2.getKnot(spline2.NbKnots)])
                    elif abs(param2 - spline2.getKnot(spline2.NbKnots)) < self.tol:
                        # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the beginning of the closed curve, so add it by hand
                        intersection_params_vector.append([param1, spline2.getKnot(1)])

        if len(inters) == 0:
            debug("intersectCC failed !")
            e1 = spline1.toShape()
            e2 = spline2.toShape()
            d,pts,info = e1.distToShape(e2)
            if d > tol3d * splines_scale:
                debug("distToShape over tolerance !")
            p1,p2 = pts[0]
            intersection_params_vector.append([spline1.parameter(p1), spline2.parameter(p2)])
        return(intersection_params_vector)
    def isUDirClosed(self, points, tolerance):
        uDirClosed = True
        # check that first row and last row are the same
        for v_idx in range(len(points[0])): #(int v_idx = points.LowerCol(); v_idx <= points.UpperCol(); ++v_idx) {
            uDirClosed = uDirClosed and (points[0][v_idx].distanceToPoint(points[-1][v_idx]) < tolerance)
        return(uDirClosed)
    def isVDirClosed(self, points, tolerance):
        vDirClosed = True
        # check that first row and last row are the same
        for u_idx in range(len(points)): #(int v_idx = points.LowerCol(); v_idx <= points.UpperCol(); ++v_idx) {
            vDirClosed = vDirClosed and (points[u_idx][0].distanceToPoint(points[u_idx][-1]) < tolerance)
        return(vDirClosed)
    def curvesToSurface(self, curves, vParameters, continuousIfClosed):
        # check amount of given parameters
        if not len(vParameters) == len(curves):
            raise ValueError("The amount of given parameters has to be equal to the amount of given B-splines!")

        # check if all curves are closed
        tolerance = self.scale(curves) * self.REL_TOL_CLOSED
        makeClosed = continuousIfClosed # and curves[0].toShape().isPartner(curves[-1].toShape())

        self.matchDegree(curves)
        nCurves = len(curves)

        # create a common knot vector for all splines
        compatSplines = self.createCommonKnotsVectorCurve(curves, self.tol)

        firstCurve = compatSplines[0]
        numControlPointsU = firstCurve.NbPoles

        degreeV = 0
        degreeU = firstCurve.Degree
        knotsV = list()
        multsV = list()

        if makeClosed:
            nPointsAdapt = nCurves - 1
        else:
            nPointsAdapt = nCurves

        # create matrix of new control points with size which is possibly DIFFERENT from the size of controlPoints
        cpSurf = list()
        interpPointsVDir = [0] * nPointsAdapt

        # now continue to create new control points by interpolating the remaining columns of controlPoints in Skinning direction (here v-direction) by B-splines
        for cpUIdx in range(numControlPointsU): #(int cpUIdx = 1; cpUIdx <= numControlPointsU; ++cpUIdx) {
            for cpVIdx in range(nPointsAdapt): #(int cpVIdx = 1; cpVIdx <= nPointsAdapt; ++cpVIdx) {
                #print("%dx%d - %d"%(cpUIdx, cpVIdx, compatSplines[cpVIdx].NbPoles))
                interpPointsVDir[cpVIdx] = compatSplines[cpVIdx].getPole(cpUIdx+1)
            interpSpline = Part.BSplineCurve()
            #print("interpSpline")
            #print(interpPointsVDir[:2])
            #print(vParameters)
            #print(makeClosed)
            interpSpline.interpolate(Points=interpPointsVDir, Parameters=vParameters, PeriodicFlag=makeClosed, Tolerance=self.tol)
            
            #debug(interpSpline)
            if makeClosed:
                self.clampBSpline(interpSpline)
            #debug(interpSpline)

            if cpUIdx == 0:
                degreeV = interpSpline.Degree
                knotsV = interpSpline.getKnots()
                multsV = interpSpline.getMultiplicities()
                cpSurf = [[0]*interpSpline.NbPoles for i in range(numControlPointsU)] # new TColgp_HArray2OfPnt(1, static_cast<Standard_Integer>(numControlPointsU), 1, interpSpline->NbPoles());

            # the final surface control points are the control points resulting from
            # the interpolation
            for i in range(interpSpline.NbPoles): # for (int i = cpSurf->LowerCol(); i <= cpSurf->UpperCol(); ++i) {
                cpSurf[cpUIdx][i] = interpSpline.getPole(i+1)

            # check degree always the same
            assert(degreeV == interpSpline.Degree)
            
        knotsU = firstCurve.getKnots()
        multsU = firstCurve.getMultiplicities()
        
        #makeClosed = False
        
        skinnedSurface = Part.BSplineSurface()
        #debug("NbPoles = %dx%d"%(len(cpSurf),len(cpSurf[0])))
        #debug("Degree U = %d"%degreeU)
        #debug("NbKnots U = %d"%len(knotsU))
        #debug("mults U = %s = %d"%(multsU,sum(multsU)))
        #debug("U-closed : %s"%firstCurve.isPeriodic())
        #debug("Degree V = %d"%degreeV)
        #debug("NbKnots V = %d"%len(knotsV))
        #debug("mults V = %s = %d"%(multsV, sum(multsV)))
        #debug("V-closed : %s"%makeClosed)
        skinnedSurface.buildFromPolesMultsKnots(cpSurf, multsU, multsV, knotsU, knotsV, firstCurve.isPeriodic(), makeClosed, degreeU, degreeV)

        return skinnedSurface
    def matchDegree(self, curves):
        maxDegree = 0
        for bs in curves: #(std::vector<Handle(Geom_BSplineCurve) >::const_iterator it = bsplines.begin(); it != bsplines.end(); ++it) {
            curDegree = bs.Degree
            if (curDegree > maxDegree):
                maxDegree = curDegree
        for bs in curves: #(std::vector<Handle(Geom_BSplineCurve) >::const_iterator it = bsplines.begin(); it != bsplines.end(); ++it) {
            curDegree = bs.Degree
            if (curDegree < maxDegree):
                bs.increaseDegree(maxDegree)
    def flipSurface(self, surf):
        result = surf.copy()
        result.exchangeUV()
        return(result)
    def haveSameRange(self, splines_vector, par_tolerance):
        begin_param_dir = splines_vector[0].getKnot(1)
        end_param_dir = splines_vector[0].getKnot(splines_vector[0].NbKnots)
        for spline_idx in range(1,len(splines_vector)): #(unsigned int spline_idx = 1; spline_idx < splines_vector.size(); ++spline_idx) {
            curSpline = splines_vector[spline_idx]
            begin_param_dir_surface = curSpline.getKnot(1)
            end_param_dir_surface = curSpline.getKnot(curSpline.NbKnots)
            if (abs(begin_param_dir_surface - begin_param_dir) > par_tolerance or abs(end_param_dir_surface - end_param_dir) > par_tolerance):
                return(False)
        return(True)
    def haveSameDegree(self, splines):
        degree = splines[0].Degree
        for splineIdx in range(1, len(splines)): #(unsigned int splineIdx = 1; splineIdx < splines.size(); ++splineIdx) {
            if not splines[splineIdx].Degree == degree:
                return(False)
        return(True)
    def findKnot(self, spline, knot, tolerance=1e-15):
        for curSplineKnotIdx in range(spline.NbKnots): #(int curSplineKnotIdx = 1; curSplineKnotIdx <= spline.getNKnots(); ++curSplineKnotIdx) {
            if (abs(spline.getKnot(curSplineKnotIdx+1) - knot) < tolerance):
                return curSplineKnotIdx
        return -1
    def pointsToSurface(self, points, uParams, vParams, uContinuousIfClosed, vContinuousIfClosed):
        debug("-   pointsToSurface")
        tolerance = self.REL_TOL_CLOSED * self.scale_pt_array(points)
        makeVDirClosed = vContinuousIfClosed and self.isVDirClosed(points, tolerance)
        makeUDirClosed = uContinuousIfClosed and self.isUDirClosed(points, tolerance)

        # GeomAPI_Interpolate does not want to have the last point,
        # if the curve should be closed. It internally uses the first point
        # as the last point
        if makeUDirClosed:
            nPointsUpper = len(points)-1
        else:
            nPointsUpper = len(points) # points.UpperRow()

        # first interpolate all points by B-splines in u-direction
        uSplines = list()
        for cpVIdx in range(len(points[0])): #for (int cpVIdx = points.LowerCol(); cpVIdx <= points.UpperCol(); ++cpVIdx) {
            points_u = [0]*nPointsUpper
            for iPointU in range(nPointsUpper):#for (int iPointU = points_u->Lower(); iPointU <= points_u->Upper(); ++iPointU) {
                points_u[iPointU] = points[iPointU][cpVIdx]
            curve = Part.BSplineCurve()
            curve.interpolate(Points=points_u, Parameters=uParams, PeriodicFlag=makeUDirClosed, Tolerance=self.tol)

            if makeUDirClosed:
                self.clampBSpline(curve)
            uSplines.append(curve)

        # now create a skinned surface with these B-splines which represents the interpolating surface
        interpolatingSurf = self.curvesToSurface(uSplines, vParams, makeVDirClosed )
        return(interpolatingSurf)
    def createCommonKnotsVectorCurve(self, curves, tol):
        # TODO: Match parameter range
        # Create a copy that we can modify
        splines_adapter = [c.copy() for c in curves]
        self.makeGeometryCompatibleImpl(splines_adapter, tol)
        return(splines_adapter)
    def createCommonKnotsVectorSurface(self, old_surfaces_vector, tol):
        # all B-spline surfaces must have the same parameter range in u- and v-direction
        # TODO: Match parameter range

        # Create a copy that we can modify
        adapterSplines = list() #[s.copy() for s in old_surfaces_vector]
        for i in range(len(old_surfaces_vector)): #(size_t i = 0; i < old_surfaces_vector.size(); ++i) {
            debug(old_surfaces_vector[i])
            adapterSplines.append(SurfAdapterView(old_surfaces_vector[i].copy(), 0))
        # first in u direction
        self.makeGeometryCompatibleImpl(adapterSplines, tol)

        for i in range(len(old_surfaces_vector)): #(size_t i = 0; i < old_surfaces_vector.size(); ++i) adapterSplines[i].setDir(vdir);
            adapterSplines[i].d = 1

        # now in v direction
        self.makeGeometryCompatibleImpl(adapterSplines, tol)

        return([ads.s for ads in adapterSplines])
    def reparametrizeBSpline(self, spline, umin, umax, tol):
        knots = spline.getKnots()
        ma = knots[-1]
        mi = knots[0]
        if abs(mi - umin) > tol or abs(ma - umax) > tol:
            ran = ma-mi
            newknots = [(k-mi)/ran for k in knots]
            spline.setKnots(newknots)
    def getKinkParameters(self, curve):
        if not curve:
            raise ValueError("Null Pointer curve")

        eps = self.tol

        kinks = list()
        for knotIndex in range(2,curve.NbKnots): #(int knotIndex = 2; knotIndex < curve->NbKnots(); ++knotIndex) {
            if curve.getMultiplicity(knotIndex) == curve.Degree:
                knot = curve.getKnot(knotIndex)
                # check if really a kink
                angle = curve.tangent(knot + eps)[0].getAngle(curve.tangent(knot - eps)[0])
                if (angle > 6./180. * pi):
                    kinks.append(knot)
        return(kinks)
    def reparametrizeBSplineContinuouslyApprox(self, spline, old_parameters, new_parameters, n_control_pnts):
        #return(spline)
        from FreeCAD import Base
        vec2d = Base.Vector2d
        if not len(old_parameters) == len(new_parameters):
            self.error("parameter sizes don't match")

        # create a B-spline as a function for reparametrization
        old_parameters_pnts = [0]*len(old_parameters) #new TColgp_HArray1OfPnt2d(1, old_parameters.size());
        for parameter_idx in range(len(old_parameters)): #(size_t parameter_idx = 0; parameter_idx < old_parameters.size(); ++parameter_idx) {
            occIdx = parameter_idx # + 1
            old_parameters_pnts[occIdx] = vec2d(old_parameters[parameter_idx], 0)

        reparametrizing_spline = Part.Geom2d.BSplineCurve2d()
        reparametrizing_spline.interpolate(Points=old_parameters_pnts, Parameters=new_parameters, PeriodicFlag=False, Tolerance=self.tol)


        # Create a vector of parameters including the intersection parameters
        breaks = new_parameters[1:-1]
        #for (size_t ipar = 1; ipar < new_parameters.size() - 1; ++ipar) {
            #breaks.push_back(new_parameters[ipar]);
        #}

        par_tol = 1e-10

        ##define MODEL_KINKS
        ##ifdef MODEL_KINKS
            ## remove kinks from breaks
            #kinks = self.getKinkParameters(spline)
            #for ikink in range(len(kinks)): #(size_t ikink = 0; ikink < kinks.size(); ++ikink) {
                #kink = kinks[ikink]
                #std::vector<double>::iterator it = std::find_if(breaks.begin(), breaks.end(), IsInsideTolerance(kink, par_tol));
                #if (it != breaks.end()) {
                    #breaks.erase(it);
                #}
            #}
        ##endif

        # create equidistance array of parameters, including the breaks
        parameters = LinspaceWithBreaks(new_parameters[0], new_parameters[-1], max(101, n_control_pnts*2), breaks)
        
        ##ifdef MODEL_KINKS
            ## insert kinks into parameters array at the correct position
            #for (size_t ikink = 0; ikink < kinks.size(); ++ikink) {
                #double kink = kinks[ikink];
                #parameters.insert( 
                    #std::upper_bound( parameters.begin(), parameters.end(), kink),
                    #kink);
            #}
        ##endif

        # Compute points on spline at the new parameters
        # Those will be approximated later on
        points = list()
        for i in range(len(parameters)): #(size_t i = 1; i <= parameters.size(); ++i) {
            oldParameter = reparametrizing_spline.value(parameters[i]).x
            points.append(spline.value(oldParameter))

        makeContinuous = spline.isClosed() and (spline.tangent(spline.FirstParameter)[0].getAngle(spline.tangent(spline.LastParameter)[0]) < 6./180. * pi)

        ## Create the new spline as a interpolation of the old one
        #CTiglBSplineApproxInterp approximationObj(points, static_cast<int>(n_control_pnts), 3, makeContinuous);
        approximationObj = BSplineApproxInterp(points, n_control_pnts, 3, makeContinuous)

        breaks.insert(0, new_parameters[0])
        breaks.append(new_parameters[-1])
        ## Interpolate points at breaking parameters (required for gordon surface)
        #for (size_t ibreak = 0; ibreak < breaks.size(); ++ibreak) {
        for ibreak in range(len(breaks)):
            thebreak = breaks[ibreak]
            pos = IsInsideTolerance(parameters, thebreak, par_tol)
            #size_t idx = static_cast<size_t>(
                #std::find_if(parameters.begin(), parameters.end(), IsInsideTolerance(thebreak)) -
                #parameters.begin());
            approximationObj.InterpolatePoint(thebreak, False)

        ###ifdef MODEL_KINKS
            ##for (size_t ikink = 0; ikink < kinks.size(); ++ikink) {
                ##double kink = kinks[ikink];
                ##size_t idx = static_cast<size_t>(
                    ##std::find_if(parameters.begin(), parameters.end(), IsInsideTolerance(kink, par_tol)) -
                    ##parameters.begin());
                ##approximationObj.InterpolatePoint(idx, true);
            ##}
        ###endif

        result, error = approximationObj.FitCurveOptimal(parameters, 10)
        if not isinstance(result, Part.BSplineCurve):
            raise ValueError("FitCurveOptimal failed to compute a valid curve")
        #Handle(Geom_BSplineCurve) reparametrized_spline = result.curve;
        #assert(!reparametrized_spline.IsNull());
        #return(reparametrized_spline)
        return(result)
    def clampBSpline(self, curve):
        if not curve.isPeriodic():
            return()
        #curve.setNotPeriodic()
        curve.trim(curve.FirstParameter, curve.LastParameter)
        # TODO is the code below really needed in FreCAD ?
        #Handle(Geom_Curve) c = new Geom_TrimmedCurve(curve, curve->FirstParameter(), curve->LastParameter());
        #curve = GeomConvert::CurveToBSplineCurve(c);
    def makeGeometryCompatibleImpl(self, splines_vector, par_tolerance):
        # all B-spline splines must have the same parameter range in the chosen direction
        if not self.haveSameRange(splines_vector, par_tolerance):
            self.error("B-splines don't have the same parameter range at least in one direction (u / v) in method createCommonKnotsVectorImpl!")
        # all B-spline splines must have the same degree in the chosen direction
        if not self.haveSameDegree(splines_vector):
            self.error("B-splines don't have the same degree at least in one direction (u / v) in method createCommonKnotsVectorImpl!")
        # create a vector of all knots in chosen direction (u or v) of all splines
        resultKnots = list()
        for spline in splines_vector: #(typename std::vector<SplineAdapter>::const_iterator splineIt = splines_vector.begin(); splineIt != splines_vector.end(); ++splineIt) {
            for k in spline.getKnots(): #(int knot_idx = 1; knot_idx <= spline.getNKnots(); ++knot_idx) {
                resultKnots.append(k)

        # sort vector of all knots in given direction of all splines
        #std::sort(resultKnots.begin(), resultKnots.end());
        # delete duplicate knots, so that in all_knots are all unique knots
        #resultKnots.erase(std::unique(resultKnots.begin(), resultKnots.end(), helper_function_unique(par_tolerance)), resultKnots.end());
        resultKnots.sort()
        prev = resultKnots[0]
        unique = [prev]
        for i in range(1, len(resultKnots)):
            if abs(resultKnots[i]-prev) > par_tolerance:
                unique.append(resultKnots[i])
            prev = resultKnots[i]
        resultKnots = unique
        
        # find highest multiplicities
        resultMults = [0]*len(resultKnots)
        for spline in splines_vector:
            for knotIdx in range(len(resultKnots)): #(unsigned int knotIdx = 0; knotIdx < resultKnots.size(); ++knotIdx) {
                # get multiplicity of current knot in surface
                splKnotIdx = self.findKnot(spline, resultKnots[knotIdx], par_tolerance)
                if (splKnotIdx > -1):
                    resultMults[knotIdx] = max(resultMults[knotIdx], spline.getMultiplicity(splKnotIdx+1))

        for spline in splines_vector:
            #debug("\n%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))
            for knotIdx in range(len(resultKnots)): #(unsigned int knotIdx = 0; knotIdx < resultKnots.size(); ++knotIdx) {
                # get multiplicity of current knot in surface
                splKnotIdx = self.findKnot(spline, resultKnots[knotIdx], par_tolerance)
                if (splKnotIdx > -1):
                    if int(spline.getMultiplicity(knotIdx+1)) < resultMults[knotIdx]:
                        #debug("increasing mult %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                        spline.increaseMultiplicity(knotIdx+1, resultMults[knotIdx])
                else:
                    #debug("inserting knot %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                    spline.insertKnot(resultKnots[knotIdx], resultMults[knotIdx], par_tolerance)

        #debug("---Mult increase\n%s\n%s"%(resultKnots, resultMults))
        ## now insert missing knots in all splines
        #for spline in splines_vector:
            #debug("\n%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))
            #for knotIdx in range(len(resultKnots)):
                #knots = spline.getKnots()
                #for k in knots:
                    #if abs(resultKnots[knotIdx]-k) < par_tolerance:
                        #if int(spline.getMultiplicity(knotIdx+1)) > resultMults[knotIdx]:
                            #debug("increasing mult %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                            #spline.increaseMultiplicity(knotIdx+1, resultMults[knotIdx])
            #debug("\n%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))
                    ##cur = spline.getMultiplicity(knotIdx+1)
        #debug("---Mult increase\n%s\n%s"%(resultKnots, resultMults))
        #for spline in splines_vector:
            #for knotIdx in range(len(resultKnots)):
                #curmult = int(spline.getMultiplicity(knotIdx+1))
                #if int(resultMults[knotIdx]-curmult) > 0:
                    #debug("inserting knot %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                    #spline.insertKnot(resultKnots[knotIdx], resultMults[knotIdx], par_tolerance)
            #debug("%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))

class GordonSurfaceBuilder(object):
    """Build a Gordon surface from a network of curves"""
    def __init__(self, profiles, guides, params_u, params_v, tol=1e-5, par_tol=1e-7):
        self.par_tol = 1e-7
        debug("-- GordonSurfaceBuilder initialisation")
        debug("%d profiles and %d guides"%(len(profiles),len(guides)))
        debug(params_u)
        debug(params_v)
        if (len(profiles) < 2) or (len(guides) < 2):
            self.error("Not enough guides or profiles")
        else:
            self.profiles = profiles
            self.guides = guides
        self.intersectionParamsU = params_u
        self.intersectionParamsV = params_v
        self.has_performed = False
        if tol > 0.0:
            self.tolerance = tol
        if par_tol > 0.0:
            self.par_tol = par_tol
    def error(self,mes):
        print(mes)
    def perform(self):
        if self.has_performed:
            return()
        self.create_gordon_surface(self.profiles, self.guides, self.intersectionParamsU, self.intersectionParamsV)
        self.has_performed = True
    def surface_gordon(self):
        self.perform()
        return(self.gordonSurf)
    def surface_profiles(self):
        self.perform()
        return(self.skinningSurfProfiles)
    def surface_guides(self):
        self.perform()
        return(self.skinningSurfGuides)
    def surface_intersections(self):
        self.perform()
        return(self.tensorProdSurf)
    def create_gordon_surface(self, profiles, guides, intersection_params_spline_u, intersection_params_spline_v):
        # check whether there are any u-directional and v-directional B-splines in the vectors
        if len(profiles) < 2:
            self.error("There must be at least two profiles for the gordon surface.")
        if len(guides)  < 2:
            self.error("There must be at least two guides for the gordon surface.")
        # check B-spline parametrization is equal among all curves
        umin = profiles[0].FirstParameter
        umax = profiles[0].LastParameter
        # TODO
        #for (CurveArray::const_iterator it = m_profiles.begin(); it != m_profiles.end(); ++it) {
            #assertRange(*it, umin, umax, 1e-5);

        vmin = guides[0].FirstParameter
        vmax = guides[0].LastParameter
        # TODO
        #for (CurveArray::const_iterator it = m_guides.begin(); it != m_guides.end(); ++it) {
            #assertRange(*it, vmin, vmax, 1e-5);

        # TODO: Do we really need to check compatibility?
        # We don't need to do this, if the curves were reparametrized before
        # In this case, they might be even incompatible, as the curves have been approximated
        self.check_curve_network_compatibility(profiles, guides, intersection_params_spline_u, intersection_params_spline_v, self.tolerance)

        # setting everything up for creating Tensor Product Surface by interpolating intersection points of profiles and guides with B-Spline surface
        # find the intersection points:
        intersection_pnts = [[0]*len(intersection_params_spline_v) for i in range(len(intersection_params_spline_u))]
        #TColgp_Array2OfPnt intersection_pnts(1, static_cast<Standard_Integer>(intersection_params_spline_u.size()),
                                           # 1, static_cast<Standard_Integer>(intersection_params_spline_v.size()));

        # use splines in u-direction to get intersection points
        for spline_idx in range(len(profiles)): #(size_t spline_idx = 0; spline_idx < profiles.size(); ++spline_idx) {
            for intersection_idx in range(len(intersection_params_spline_u)): #(size_t intersection_idx = 0; intersection_idx < intersection_params_spline_u.size(); ++intersection_idx) {
                spline_u = self.profiles[spline_idx]
                parameter = intersection_params_spline_u[intersection_idx]
                intersection_pnts[intersection_idx][spline_idx] = spline_u.value(parameter)

        # check, whether to build a closed continuous surface
        bsa = BSplineAlgorithms(self.par_tol)
        curve_u_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(guides)
        curve_v_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(profiles)
        tp_tolerance      = bsa.REL_TOL_CLOSED * bsa.scale_pt_array(intersection_pnts)
                                                                                    # TODO No IsEqual in FreeCAD
        makeUClosed = False #bsa.isUDirClosed(intersection_pnts, tp_tolerance)# and guides[0].toShape().isPartner(guides[-1].toShape()) #.isEqual(guides[-1], curve_u_tolerance);
        makeVClosed = False #bsa.isVDirClosed(intersection_pnts, tp_tolerance)# and profiles[0].toShape().IsPartner(profiles[-1].toShape())

        # Skinning in v-direction with u directional B-Splines
        debug("-   Skinning profiles")
        surfProfiles = bsa.curvesToSurface(profiles, intersection_params_spline_v, makeVClosed)
        # therefore reparametrization before this method

        # Skinning in u-direction with v directional B-Splines
        debug("-   Skinning guides")
        surfGuides = bsa.curvesToSurface(guides, intersection_params_spline_u, makeUClosed)

        # flipping of the surface in v-direction; flipping is redundant here, therefore the next line is a comment!
        surfGuides = bsa.flipSurface(surfGuides)

        # if there are too little points for degree in u-direction = 3 and degree in v-direction=3 creating an interpolation B-spline surface isn't possible in Open CASCADE

        # Open CASCADE doesn't have a B-spline surface interpolation method where one can give the u- and v-directional parameters as arguments
        tensorProdSurf = bsa.pointsToSurface(intersection_pnts, intersection_params_spline_u, intersection_params_spline_v, makeUClosed, makeVClosed)

        # match degree of all three surfaces
        degreeU = max(max(surfGuides.UDegree, surfProfiles.UDegree), tensorProdSurf.UDegree)
        degreeV = max(max(surfGuides.VDegree, surfProfiles.VDegree), tensorProdSurf.VDegree)

        # check whether degree elevation is necessary (does method elevate_degree_u()) and if yes, elevate degree
        surfGuides.increaseDegree(degreeU, degreeV)
        surfProfiles.increaseDegree(degreeU, degreeV)
        tensorProdSurf.increaseDegree(degreeU, degreeV)

        surfaces_vector_unmod = [surfGuides, surfProfiles, tensorProdSurf]

        # create common knot vector for all three surfaces
        surfaces_vector = bsa.createCommonKnotsVectorSurface(surfaces_vector_unmod, self.par_tol)

        assert(len(surfaces_vector) == 3)

        self.skinningSurfGuides = surfaces_vector[0]
        self.skinningSurfProfiles = surfaces_vector[1]
        self.tensorProdSurf = surfaces_vector[2]

        print("Number of Poles")
        print("skinningSurfGuides : %d x %d"%(self.skinningSurfGuides.NbUPoles, self.skinningSurfGuides.NbVPoles))
        print("skinningSurfProfiles : %d x %d"%(self.skinningSurfProfiles.NbUPoles, self.skinningSurfProfiles.NbVPoles))
        print("tensorProdSurf : %d x %d"%(self.tensorProdSurf.NbUPoles, self.tensorProdSurf.NbVPoles))

        assert(self.skinningSurfGuides.NbUPoles == self.skinningSurfProfiles.NbUPoles and self.skinningSurfProfiles.NbUPoles == self.tensorProdSurf.NbUPoles)
        assert(self.skinningSurfGuides.NbVPoles == self.skinningSurfProfiles.NbVPoles and self.skinningSurfProfiles.NbVPoles == self.tensorProdSurf.NbVPoles)

        self.gordonSurf = self.skinningSurfProfiles.copy()

        # creating the Gordon Surface = s_u + s_v - tps by adding the control points
        for cp_u_idx in range(1, self.gordonSurf.NbUPoles+1): #(int cp_u_idx = 1; cp_u_idx <= self.gordonSurf->NbUPoles(); ++cp_u_idx) {
            for cp_v_idx in range(1, self.gordonSurf.NbVPoles+1): #(int cp_v_idx = 1; cp_v_idx <= self.gordonSurf->NbVPoles(); ++cp_v_idx) {
                cp_surf_u = self.skinningSurfProfiles.getPole(cp_u_idx, cp_v_idx)
                cp_surf_v = self.skinningSurfGuides.getPole(cp_u_idx, cp_v_idx)
                cp_tensor = self.tensorProdSurf.getPole(cp_u_idx, cp_v_idx)
                self.gordonSurf.setPole(cp_u_idx, cp_v_idx, cp_surf_u + cp_surf_v - cp_tensor)
    def check_curve_network_compatibility(self, profiles, guides, intersection_params_spline_u, intersection_params_spline_v, tol):
        # find out the 'average' scale of the B-splines in order to being able to handle a more approximate dataset and find its intersections
        bsa = BSplineAlgorithms(self.par_tol)
        splines_scale = 0.5 * (bsa.scale(profiles) + bsa.scale(guides))

        if abs(intersection_params_spline_u[0]) > (splines_scale * tol) or abs(intersection_params_spline_u[-1] - 1.) > (splines_scale * tol):
            self.error("WARNING: B-splines in u-direction must not stick out, spline network must be 'closed'!")
        if abs(intersection_params_spline_v[0]) > (splines_scale * tol) or abs(intersection_params_spline_v[-1] - 1.) > (splines_scale * tol):
            self.error("WARNING: B-splines in v-direction mustn't stick out, spline network must be 'closed'!")

        # check compatibility of network
        for u_param_idx in range(len(intersection_params_spline_u)): #(size_t u_param_idx = 0; u_param_idx < intersection_params_spline_u.size(); ++u_param_idx) {
            spline_u_param = intersection_params_spline_u[u_param_idx]
            spline_v = guides[u_param_idx]
            for v_param_idx in range(len(intersection_params_spline_v)): #(size_t v_param_idx = 0; v_param_idx < intersection_params_spline_v.size(); ++v_param_idx) {
                spline_u = profiles[v_param_idx]
                spline_v_param = intersection_params_spline_v[v_param_idx]

                p_prof = spline_u.value(spline_u_param)
                p_guid = spline_v.value(spline_v_param)
                distance = p_prof.distanceToPoint(p_guid)

                if (distance > splines_scale * tol):
                    self.error("B-spline network is incompatible (e.g. wrong parametrization) or intersection parameters are in a wrong order!")

class InterpolateCurveNetwork(object):
    """Bspline surface interpolating a network of curves"""
    def __init__(self, profiles, guides, tol=1e-5, tol2=1e-10):
        self.tolerance = 1e-5
        self.par_tolerance = 1e-10
        self.has_performed = False
        if (len(profiles) < 2) or (len(guides) < 2):
            self.error("Not enough guides or profiles")
        else:
            self.profiles = profiles
            self.guides = guides
        if tol > 0.0:
            self.tolerance = tol
        if tol2 > 0.0:
            self.par_tolerance = tol2
    def error(self,mes):
        print(mes)
    def perform(self):
        if self.has_performed:
            return()
        debug("-> ")
        self.make_curves_compatible()
        debug("-> make_curves_compatible -> OK")
        builder = GordonSurfaceBuilder(self.profiles, self.guides, self.intersectionParamsU, self.intersectionParamsV, self.tolerance)
        debug("-> GordonSurfaceBuilder -> OK")
        self.gordon_surf = builder.surface_gordon()
        debug("-> builder.surface_gordon -> OK")
        self.skinning_surf_profiles = builder.surface_profiles()
        debug("-> builder.surface_profiles -> OK")
        self.skinning_surf_guides = builder.surface_guides()
        debug("-> builder.surface_guides -> OK")
        self.tensor_prod_surf = builder.surface_intersections()
        self.has_performed = True
    def surface_profiles(self):
        self.perform()
        return(self.skinning_surf_profiles)
    def surface_guides(self):
        self.perform()
        return(self.skinning_surf_guides)
    def surface_intersections(self):
        self.perform()
        return(self.tensor_prod_surf)
    def parameters_profiles(self):
        self.perform()
        return(self.intersection_params_v)
    def parameters_guides(self):
        self.perform()
        return(self.intersection_params_u)
    def surface(self):
        self.perform()
        return(self.gordon_surf)
    def compute_intersections(self, intersection_params_u, intersection_params_v):
        debug("\ncompute_intersections")
        for spline_u_idx in range(len(self.profiles)):
            for spline_v_idx in range(len(self.guides)):
                
                currentIntersections = BSplineAlgorithms(self.par_tolerance).intersections(self.profiles[spline_u_idx], self.guides[spline_v_idx], self.par_tolerance)
                if len(currentIntersections) < 1:
                    self.error("U-directional B-spline and v-directional B-spline don't intersect each other!")
                    self.error("profile %d / guide %d"%(spline_u_idx, spline_v_idx))
                elif len(currentIntersections) == 1:
                    intersection_params_u[spline_u_idx][spline_v_idx] = currentIntersections[0][0]
                    intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]
                    # for closed curves
                elif len(currentIntersections) == 2:
                    debug("*** 2 intersections")
                    debug(currentIntersections)
                    # only the u-directional B-spline curves are closed
                    if (self.profiles[0].isClosed()):
                        debug("U-closed")
                        if (spline_v_idx == 0):
                            intersection_params_u[spline_u_idx][spline_v_idx] = min(currentIntersections[0][0], currentIntersections[1][0])
                        elif (spline_v_idx == len(self.guides) - 1):
                            intersection_params_u[spline_u_idx][spline_v_idx] = max(currentIntersections[0][0], currentIntersections[1][0])
                        # intersection_params_vector[0].second == intersection_params_vector[1].second
                        intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]
   
                    # only the v-directional B-spline curves are closed
                    if (self.guides[0].isClosed()):
                        debug("V-closed")
                        if (spline_u_idx == 0):
                            intersection_params_v[spline_u_idx][spline_v_idx] = min(currentIntersections[0][1], currentIntersections[1][1])
                        elif (spline_u_idx == len(self.profiles) - 1):
                            intersection_params_v[spline_u_idx][spline_v_idx] = max(currentIntersections[0][1], currentIntersections[1][1])
                        # intersection_params_vector[0].first == intersection_params_vector[1].first
                        intersection_params_u[spline_u_idx][spline_v_idx] = currentIntersections[0][0]
                    # TODO: both u-directional splines and v-directional splines are closed
                    # elif len(currentIntersections) == 4:
                    debug("%dx%d = (%.4f, %.4f)"%(spline_u_idx, spline_v_idx, intersection_params_u[spline_u_idx][spline_v_idx], intersection_params_v[spline_u_idx][spline_v_idx]))
                else:
                    self.error("U-directional B-spline and v-directional B-spline have more than two intersections with each other!")
    def sort_curves(self, intersection_params_u, intersection_params_v):
        import curve_network_sorter
        sorterObj = curve_network_sorter.CurveNetworkSorter(self.profiles, self.guides, intersection_params_u, intersection_params_v)
        sorterObj.Perform()

        # get the sorted matrices and vectors
        intersection_params_u = sorterObj.parmsIntersProfiles
        intersection_params_v = sorterObj.parmsIntersGuides

        # TODO check the code below
        # copy sorted curves back into our curve arrays
        #struct Caster {
            #Handle(Geom_BSplineCurve) operator()(const Handle(Geom_Curve)& curve) {
                #return Handle(Geom_BSplineCurve)::DownCast(curve);
            #}
        #} caster;

        #std::transform(sorterObj.Profiles().begin(), sorterObj.Profiles().end(), m_profiles.begin(), caster);
        #std::transform(sorterObj.Guides().begin(), sorterObj.Guides().end(), m_guides.begin(), caster);
        self.profiles = sorterObj.profiles
        self.guides = sorterObj.guides
    def make_curves_compatible(self):
        # reparametrize into [0,1]
        bsa = BSplineAlgorithms()
        for c in self.profiles:
            bsa.reparametrizeBSpline(c, 0., 1., self.par_tolerance)
        for c in self.guides:
            bsa.reparametrizeBSpline(c, 0., 1., self.par_tolerance)
        # now the parameter range of all  profiles and guides is [0, 1]

        nGuides = len(self.guides)
        nProfiles = len(self.profiles)
        # now find all intersections of all B-splines with each other
        intersection_params_u = [[0]*nGuides for k in range(nProfiles)] #(0, nProfiles - 1, 0, nGuides - 1);
        intersection_params_v = [[0]*nGuides for k in range(nProfiles)] #(0, nProfiles - 1, 0, nGuides - 1);
        self.compute_intersections(intersection_params_u, intersection_params_v)
        debug("------make_curves_compatible------")
        debug("intersection_params_u\n%s"%intersection_params_u)
        debug("intersection_params_v\n%s"%intersection_params_v)
        # sort intersection_params_u and intersection_params_v and u-directional and v-directional B-spline curves
        self.sort_curves(intersection_params_u, intersection_params_v)

        # eliminate small inaccuracies of the intersection parameters:
        self.eliminate_inaccuracies_network_intersections(self.profiles, self.guides, intersection_params_u, intersection_params_v)

        newParametersProfiles = list()
        for spline_v_idx in range(1, nGuides+1): #(int spline_v_idx = 1; spline_v_idx <= nGuides; ++spline_v_idx) {
            summ = 0
            for spline_u_idx in range(1, nProfiles+1):
                summ += intersection_params_u[spline_u_idx - 1][spline_v_idx - 1]
            newParametersProfiles.append(summ / nProfiles)

        newParametersGuides = list()
        for spline_u_idx in range(1, nProfiles+1):
            summ = 0
            for spline_v_idx in range(1, nGuides+1):
                summ += intersection_params_v[spline_u_idx - 1][spline_v_idx - 1]
            newParametersGuides.append(summ / nGuides)

        if (newParametersProfiles[0] > self.tolerance or newParametersGuides[0] > self.tolerance):
            self.error("At least one B-splines has no intersection at the beginning.")

        # Get maximum number of control points to figure out detail of spline
        max_cp_u = 0
        max_cp_v = 0
        for c in self.profiles:
            max_cp_u = max(max_cp_u, c.NbPoles)
        for c in self.guides:
            max_cp_v = max(max_cp_v, c.NbPoles)

        # we want to use at least 10 and max 80 control points to be able to reparametrize the geometry properly
        mincp = 10
        maxcp = 80

        # since we interpolate the intersections, we cannot use fewer control points than curves
        # We need to add two since we want c2 continuity, which adds two equations
        min_u = max(nGuides + 2, mincp)
        min_v = max(nProfiles + 2, mincp)

        max_u = max(min_u, maxcp);
        max_v = max(min_v, maxcp);
        
        # Clamp(val, min, max) : return std::max(min, std::min(val, max));
        max_cp_u = max(min_u, min(max_cp_u + 10, max_u))
        max_cp_v = max(min_v, min(max_cp_v + 10, max_v))

        # reparametrize u-directional B-splines
        for spline_u_idx in range(nProfiles): #(int spline_u_idx = 0; spline_u_idx < nProfiles; ++spline_u_idx) {
            oldParametersProfile = list()
            for spline_v_idx in range(nGuides):
                oldParametersProfile.append(intersection_params_u[spline_u_idx][spline_v_idx])
            # eliminate small inaccuracies at the first knot
            if (abs(oldParametersProfile[0]) < self.tolerance):
                oldParametersProfile[0] = 0.
            if (abs(newParametersProfiles[0]) < self.tolerance):
                newParametersProfiles[0] = 0.
            # eliminate small inaccuracies at the last knot
            if (abs(oldParametersProfile[-1] - 1.) < self.tolerance):
                oldParametersProfile[-1] = 1.
            if (abs(newParametersProfiles[-1] - 1.) < self.tolerance):
                newParametersProfiles[-1] = 1.

            profile = self.profiles[spline_u_idx]
            profile = bsa.reparametrizeBSplineContinuouslyApprox(profile, oldParametersProfile, newParametersProfiles, max_cp_u)

        # reparametrize v-directional B-splines
        for spline_v_idx in range(nGuides):
            oldParameterGuide = list()
            for spline_u_idx in range(nProfiles):
                oldParameterGuide.append(intersection_params_v[spline_u_idx][spline_v_idx])
            # eliminate small inaccuracies at the first knot
            if (abs(oldParameterGuide[0]) < self.tolerance):
                oldParameterGuide[0] = 0.
            if (abs(newParametersGuides[0]) < self.tolerance):
                newParametersGuides[0] = 0.
            # eliminate small inaccuracies at the last knot
            if (abs(oldParameterGuide[-1] - 1.) < self.tolerance):
                oldParameterGuide[-1] = 1.
            if (abs(newParametersGuides[-1] - 1.) < self.tolerance):
                newParametersGuides[-1] = 1.

            guide = self.guides[spline_v_idx]
            guide = bsa.reparametrizeBSplineContinuouslyApprox(guide, oldParameterGuide, newParametersGuides, max_cp_v)
            
        self.intersectionParamsU = newParametersProfiles
        self.intersectionParamsV = newParametersGuides
    def eliminate_inaccuracies_network_intersections(self, sortedProfiles, sortedGuides, intersection_params_u, intersection_params_v):
        nProfiles = len(sortedProfiles)
        nGuides = len(sortedGuides)
        #tol = 0.001
        # eliminate small inaccuracies of the intersection parameters:

        # first intersection
        for spline_u_idx in range(nProfiles):
            if (abs(intersection_params_u[spline_u_idx][0] - sortedProfiles[0].getKnot(1)) < self.tolerance):
                if (abs(sortedProfiles[0].getKnot(1)) < self.par_tolerance):
                    intersection_params_u[spline_u_idx][0] = 0
                else:
                    intersection_params_u[spline_u_idx][0] = sortedProfiles[0].getKnot(1)

        for spline_v_idx in range(nGuides):
            if (abs(intersection_params_v[0][spline_v_idx] - sortedGuides[0].getKnot(1)) < self.tolerance):
                if (abs(sortedGuides[0].getKnot(1)) < self.par_tolerance):
                    intersection_params_v[0][spline_v_idx] = 0
                else:
                    intersection_params_v[0][spline_v_idx] = sortedGuides[0].getKnot(1)

        # last intersection
        for spline_u_idx in range(nProfiles):
            if (abs(intersection_params_u[spline_u_idx][nGuides - 1] - sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots)) < self.tolerance):
                intersection_params_u[spline_u_idx][nGuides - 1] = sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots)

        for spline_v_idx in range(nGuides):
            if (abs(intersection_params_v[nProfiles - 1][spline_v_idx] - sortedGuides[0].getKnot(sortedGuides[0].NbKnots)) < self.tolerance):
                intersection_params_v[nProfiles - 1][spline_v_idx] = sortedGuides[0].getKnot(sortedGuides[0].NbKnots)

def main():
    
    import FreeCAD
    import FreeCADGui
    import Part
    
    data = ["test-S2R-2","Compound","Compound001"]
    #data = ["Gordon-sphere","Compound","Compound001"]
    data = ["test-birail-3","Compound","Compound001"]
    #data = ["Gordon-2","profiles","guides"]
    
    doc = FreeCAD.open(u"/home/tomate/.FreeCAD/Mod/CurvesWB/TestFiles/%s.fcstd"%data[0])
    # Create array of curves
    guide_edges = doc.getObject(data[1]).Shape.Edges
    profile_edges = doc.getObject(data[2]).Shape.Edges
    guide_curves = [e.Curve.toBSpline() for e in guide_edges]
    profile_curves = [e.Curve.toBSpline() for e in profile_edges]

    # create the gordon surface
    gordon = InterpolateCurveNetwork(profile_curves, guide_curves, 1e-5)

    # display curves and resulting surface
    Part.show(gordon.surface().toShape())
    FreeCAD.ActiveDocument.recompute()

if __name__ == "__main__":
    main()




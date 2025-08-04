# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2018 German Aerospace Center (DLR)

# This file is a python port of the following files :
#
# /src/geometry/CTiglBSplineAlgorithms.cpp
#
# from the Tigl library : https://github.com/DLR-SC/tigl under Apache-2 license

import FreeCAD
import Part
from FreeCAD import Base
from math import pi
from freecad.Curves.BSplineApproxInterp import BSplineApproxInterp

vec2d = Base.Vector2d
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
            u = o.uIso(o.getUKnot(1))
            debug(u)
        except Part.OCCError:
            FreeCAD.Console.PrintError("Failed to compute uIso curve\n")
        try:
            v = o.vIso(o.getVKnot(1))
            debug(v)
        except Part.OCCError:
            FreeCAD.Console.PrintError("Failed to compute vIso curve\n")
        FreeCAD.Console.PrintWarning("************\n")
    else:
        FreeCAD.Console.PrintMessage("{}\n".format(str(o)))


def IsInsideTolerance(array, value, tolerance=1e-15):
    """Return index of value in array, within given tolerance
    Else return -1"""
    for i in range(len(array)):
        if abs(array[i] - value) <= tolerance:
            return i
    return -1


def LinspaceWithBreaks(umin, umax, n_values, breaks):
    """Returns a knot sequence of n_values between umin and umax
    that will also contain the breaks"""
    du = float(umax - umin) / (n_values - 1)
    result = list()  # size = n_values
    for i in range(n_values):
        result.append(i * du + umin)
    # now insert the break

    eps = 0.3
    # remove points, that are closer to each break point than du*eps
    for break_point in breaks:
        pos = IsInsideTolerance(result, break_point, du * eps)  # std::find_if(result.begin(), result.end(), IsInsideTolerance(breakpoint, du*eps));
        if pos >= 0:
            # point found, replace it
            result[pos] = break_point
        else:
            # find closest element
            pos = IsInsideTolerance(result, break_point, (0.5 + 1e-8) * du)
            if (result[pos] > break_point):
                result.insert(pos, break_point)
            else:
                result.insert(pos + 1, break_point)
    return result


class SurfAdapterView(object):
    def __init__(self, surf, direc):
        self.s = surf
        self.d = direc

    @property
    def NbKnots(self):
        return self.getNKnots()

    @property
    def NbPoles(self):
        return self.getNPoles()

    @property
    def Degree(self):
        return self.getDegree()

    def insertKnot(self, knot, mult, tolerance=1e-15):
        try:
            if self.d == 0:
                self.s.insertUKnot(knot, mult, tolerance)
            else:
                self.s.insertVKnot(knot, mult, tolerance)
        except Part.OCCError:
            debug("failed to insert knot : %f - %d - %f" % (knot, mult, tolerance))
            raise RuntimeError

    def getKnot(self, idx):
        if self.d == 0:
            return self.s.getUKnot(idx)
        else:
            return self.s.getVKnot(idx)

    def getKnots(self):
        if self.d == 0:
            return self.s.getUKnots()
        else:
            return self.s.getVKnots()

    def getMultiplicities(self):
        if self.d == 0:
            return self.s.getUMultiplicities()
        else:
            return self.s.getVMultiplicities()

    def increaseMultiplicity(self, idx, mult):
        if self.d == 0:
            return self.s.increaseUMultiplicity(idx, mult)
        else:
            return self.s.increaseVMultiplicity(idx, mult)

    def getMult(self, idx):
        if self.d == 0:
            return self.s.getUMultiplicity(idx)
        else:
            return self.s.getVMultiplicity(idx)

    def getMultiplicity(self, idx):
        return self.getMult(idx)

    def getNKnots(self):
        if self.d == 0:
            return self.s.NbUKnots
        else:
            return self.s.NbVKnots

    def getNPoles(self):
        if self.d == 0:
            return self.s.NbUPoles
        else:
            return self.s.NbVPoles

    def getDegree(self):
        if self.d == 0:
            return int(self.s.UDegree)
        else:
            return int(self.s.VDegree)

    def isPeriodic(self):
        if self.d == 0:
            return self.s.isUPeriodic()
        else:
            return self.s.isVPeriodic()


class BSplineAlgorithms(object):
    """Various BSpline algorithms"""

    def __init__(self, tol=1e-8):
        self.REL_TOL_CLOSED = tol
        if tol > 0.0:
            self.tol = tol  # parametric tolerance

    def error(self, mes):
        print(mes)

    def scale(self, c):
        """Returns the max size of a curve (or list of curves) poles"""
        res = 0
        if isinstance(c, (tuple, list)):
            for cu in c:
                res = max(res, self.scale(cu))
        elif isinstance(c, (Part.BSplineCurve, Part.BezierCurve)):
            pts = c.getPoles()
            for p in pts[1:]:
                res = max(res, p.distanceToPoint(pts[0]))
        return res

    def scale_pt_array(self, points):
        """Returns the max distance of a 2D array of points"""
        theScale = 0.
        for uidx in range(len(points)):
            pFirst = points[uidx][0]
            for vidx in range(1, len(points[0])):
                dist = pFirst.distanceToPoint(points[uidx][vidx])
                theScale = max(theScale, dist)
        return theScale

    def isUDirClosed(self, points, tolerance):
        """check that first row and last row of a 2D array of points are the same"""
        uDirClosed = True
        for v_idx in range(len(points[0])):
            uDirClosed = uDirClosed and (points[0][v_idx].distanceToPoint(points[-1][v_idx]) < tolerance)
        return uDirClosed

    def isVDirClosed(self, points, tolerance):
        """check that first column and last column of a 2D array of points are the same"""
        vDirClosed = True
        for u_idx in range(len(points)):
            vDirClosed = vDirClosed and (points[u_idx][0].distanceToPoint(points[u_idx][-1]) < tolerance)
        return vDirClosed

    def matchDegree(self, curves):
        """Match degree of all curves by increasing degree where needed"""
        maxDegree = 0
        for bs in curves:
            curDegree = bs.Degree
            if (curDegree > maxDegree):
                maxDegree = curDegree
        for bs in curves:
            curDegree = bs.Degree
            if (curDegree < maxDegree):
                bs.increaseDegree(maxDegree)

    def flipSurface(self, surf):
        """Flip U/V parameters of a surface"""
        result = surf.copy()
        result.exchangeUV()
        return result

    def haveSameRange(self, splines_vector, par_tolerance):
        """Check that all curves have the same parameter range"""
        begin_param_dir = splines_vector[0].getKnot(1)
        end_param_dir = splines_vector[0].getKnot(splines_vector[0].NbKnots)
        for spline_idx in range(1, len(splines_vector)):  # (unsigned int spline_idx = 1; spline_idx < splines_vector.size(); ++spline_idx) {
            curSpline = splines_vector[spline_idx]
            begin_param_dir_surface = curSpline.getKnot(1)
            end_param_dir_surface = curSpline.getKnot(curSpline.NbKnots)
            if (abs(begin_param_dir_surface - begin_param_dir) > par_tolerance or abs(end_param_dir_surface - end_param_dir) > par_tolerance):
                return False
        return True

    def haveSameDegree(self, splines):
        """Check that all curves have the same degree"""
        degree = splines[0].Degree
        for splineIdx in range(1, len(splines)):  # (unsigned int splineIdx = 1; splineIdx < splines.size(); ++splineIdx) {
            if not splines[splineIdx].Degree == degree:
                return False
        return True

    def findKnot(self, spline, knot, tolerance=1e-15):
        """Return index of knot in spline, within given tolerance
        Else return -1"""
        for curSplineKnotIdx in range(spline.NbKnots):  # (int curSplineKnotIdx = 1; curSplineKnotIdx <= spline.getNKnots(); ++curSplineKnotIdx) {
            if (abs(spline.getKnot(curSplineKnotIdx + 1) - knot) < tolerance):
                return curSplineKnotIdx
        return -1

    def clampBSpline(self, curve):
        """If curve is periodic, it is trimmed to First / Last Parameters"""
        if not curve.isPeriodic():
            return
        # curve.setNotPeriodic()
        curve.trim(curve.FirstParameter, curve.LastParameter)
        # TODO is the code below really needed in FreCAD ?
        # Handle(Geom_Curve) c = new Geom_TrimmedCurve(curve, curve->FirstParameter(), curve->LastParameter());
        # curve = GeomConvert::CurveToBSplineCurve(c);

    def makeGeometryCompatibleImpl(self, splines_vector, par_tolerance):
        """Modify all the splines, so that they have the same knots / mults"""
        # all B-spline splines must have the same parameter range in the chosen direction
        if not self.haveSameRange(splines_vector, par_tolerance):
            self.error("B-splines don't have the same parameter range at least in one direction (u / v) in method createCommonKnotsVectorImpl!")
        # all B-spline splines must have the same degree in the chosen direction
        if not self.haveSameDegree(splines_vector):
            self.error("B-splines don't have the same degree at least in one direction (u / v) in method createCommonKnotsVectorImpl!")

        # # The parametric tolerance must be smaller than half of the minimum knot distance
        # for spline in splines_vector:
        #     for idx in range(spline.NbKnots - 1):
        #         knot_dist = spline.getKnot(idx + 2) - spline.getKnot(idx + 1)
        #         par_tolerance = min(par_tolerance, knot_dist / 2.0)
        #
        # # insert all knots in first spline
        # firstSpline = splines_vector[0]
        # for spline in splines_vector[1:]:
        #     for knot_idx in range(1, spline.NbKnots + 1):
        #         knot = spline.getKnot(knot_idx)
        #         mult = spline.getMultiplicity(knot_idx)
        #         firstSpline.insertKnot(knot, mult, par_tolerance)
        #
        # # now insert knots from first into all others
        # for spline in splines_vector[1:]:
        #     for knot_idx in range(1, firstSpline.NbKnots + 1):
        #         knot = firstSpline.getKnot(knot_idx)
        #         mult = firstSpline.getMultiplicity(knot_idx)
        #         spline.insertKnot(knot, mult, par_tolerance)
        #     if not (spline.NbKnots == firstSpline.NbKnots):
        #         self.error("Unexpected error in Algorithm makeGeometryCompatibleImpl.\nPlease contact the developers.")

        # create a vector of all knots in chosen direction (u or v) of all splines
        resultKnots = list()
        for spline in splines_vector:
            for k in spline.getKnots():
                resultKnots.append(k)

        # sort vector of all knots in given direction of all splines
        resultKnots.sort()
        prev = resultKnots[0]
        unique = [prev]
        for i in range(1, len(resultKnots)):
            if abs(resultKnots[i] - prev) > par_tolerance:
                unique.append(resultKnots[i])
            prev = resultKnots[i]
        resultKnots = unique

        # find highest multiplicities
        resultMults = [0] * len(resultKnots)
        for spline in splines_vector:
            for knotIdx in range(len(resultKnots)):
                # get multiplicity of current knot in surface
                splKnotIdx = self.findKnot(spline, resultKnots[knotIdx], par_tolerance)
                if (splKnotIdx > -1):
                    resultMults[knotIdx] = max(resultMults[knotIdx], spline.getMultiplicity(splKnotIdx + 1))

        for spline in splines_vector:
            # debug("\n%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))
            for knotIdx in range(len(resultKnots)):
                # get multiplicity of current knot in surface
                splKnotIdx = self.findKnot(spline, resultKnots[knotIdx], par_tolerance)
                if (splKnotIdx > -1):
                    # print("getting mult {} / {}, periodic = {}".format(splKnotIdx + 1, len(spline.getMultiplicities()), spline.isPeriodic()))
                    if int(spline.getMultiplicity(splKnotIdx + 1)) < resultMults[knotIdx]:
                        # debug("increasing mult %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                        spline.increaseMultiplicity(splKnotIdx + 1, resultMults[knotIdx])
                else:
                    # debug("inserting knot %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                    spline.insertKnot(resultKnots[knotIdx], resultMults[knotIdx], par_tolerance)

    def createCommonKnotsVectorCurve(self, curves, tol):
        """Modify all the splines, so that they have the same knots / mults"""
        # TODO: Match parameter range
        # Create a copy that we can modify
        splines_adapter = [c.copy() for c in curves]
        self.makeGeometryCompatibleImpl(splines_adapter, tol)
        return splines_adapter

    def createCommonKnotsVectorSurface(self, old_surfaces_vector, tol):
        """Make all the surfaces have the same knots / mults"""
        # all B-spline surfaces must have the same parameter range in u- and v-direction
        # TODO: Match parameter range

        # Create a copy that we can modify
        adapterSplines = list()
        for i in range(len(old_surfaces_vector)):
            # debug(old_surfaces_vector[i])
            adapterSplines.append(SurfAdapterView(old_surfaces_vector[i].copy(), 0))
        # first in u direction
        self.makeGeometryCompatibleImpl(adapterSplines, tol)

        for i in range(len(old_surfaces_vector)):
            adapterSplines[i].d = 1

        # now in v direction
        self.makeGeometryCompatibleImpl(adapterSplines, tol)

        return [ads.s for ads in adapterSplines]

    def reparametrizeBSpline(self, spline, umin, umax, tol):
        """reparametrize BSpline to range [umin, umax]"""
        knots = spline.getKnots()
        ma = knots[-1]
        mi = knots[0]
        if abs(mi - umin) > tol or abs(ma - umax) > tol:
            ran = ma - mi
            # fix from edwilliams16
            # https://forum.freecadweb.org/viewtopic.php?f=22&t=75293&p=653658#p653658
            fracknots = [(k - mi) / ran for k in knots]
            newknots = [umin * (1 - f) + umax * f for f in fracknots]
            spline.setKnots(newknots)

    def getKinkParameters(self, curve):
        """Returns a list of knots of sharp points in curve"""
        if not curve:
            raise ValueError("Null Pointer curve")

        eps = self.tol

        kinks = list()
        for knotIndex in range(2, curve.NbKnots):
            if curve.getMultiplicity(knotIndex) == curve.Degree:
                knot = curve.getKnot(knotIndex)
                # check if really a kink
                angle = curve.tangent(knot + eps)[0].getAngle(curve.tangent(knot - eps)[0])
                if (angle > 6. / 180. * pi):
                    kinks.append(knot)
        return kinks

# Below are the most important methods of BSplineAlgorithms

    def intersections(self, spline1, spline2, tol3d):
        """Returns a list of tuples (param1, param2) that are intersection parameters of spline1 with spline2"""
        # light weight simple minimizer
        # check parametrization of B-splines beforehand
        # find out the average scale of the two B-splines in order to being able to handle a more approximate curves and find its intersections
        splines_scale = (self.scale(spline1) + self.scale(spline2)) / 2.
        intersection_params_vector = []
        inters = spline1.intersectCC(spline2)
        # GeomAPI_ExtremaCurveCurve intersectionObj(spline1, spline2);
        # debug("intersectCC results")
        if len(inters) >= 2:
            debug("\n*********************\n2 intersectCC results\n*********************")
            p1 = FreeCAD.Vector(inters[0].X, inters[0].Y, inters[0].Z)
            p2 = FreeCAD.Vector(inters[1].X, inters[1].Y, inters[1].Z)
            if (p1.distanceToPoint(p2) < tol3d * splines_scale):
                inters = [p1]
        for intpt in inters:
            if isinstance(intpt, Part.Point):
                inter = FreeCAD.Vector(intpt.X, intpt.Y, intpt.Z)
            else:
                inter = intpt
            # debug(intpt)
            param1 = spline1.parameter(inter)
            param2 = spline2.parameter(inter)
            # intersectionObj.Parameters(intersect_idx, param1, param2);
            # filter out real intersections
            point1 = spline1.value(param1)
            point2 = spline2.value(param2)
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
                if abs(param1 - spline1.getKnot(spline1.NbKnots)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the beginning of the closed curve, so add it by hand
                    intersection_params_vector.append([spline1.getKnot(1), param2])
            elif spline2.isClosed():
                if abs(param2 - spline2.getKnot(1)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the end of the closed curve, so add it by hand
                    intersection_params_vector.append([param1, spline2.getKnot(spline2.NbKnots)])
                if abs(param2 - spline2.getKnot(spline2.NbKnots)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the beginning of the closed curve, so add it by hand
                    intersection_params_vector.append([param1, spline2.getKnot(1)])

        if len(inters) == 0:
            debug("intersectCC failed !")
            e1 = spline1.toShape()
            e2 = spline2.toShape()
            d, pts, info = e1.distToShape(e2)
            if d > tol3d * splines_scale:
                debug("distToShape over tolerance ! %f > %f" % (d, tol3d * splines_scale))
            p1, p2 = pts[0]
            intersection_params_vector.append([spline1.parameter(p1), spline2.parameter(p2)])
        return intersection_params_vector

    def curvesToSurface(self, curves, vParameters, continuousIfClosed):
        """Returns a surface that skins the list of curves"""
        # check amount of given parameters
        if not len(vParameters) == len(curves):
            raise ValueError("The amount of given parameters has to be equal to the amount of given B-splines!")

        # check if all curves are closed
        tolerance = self.scale(curves) * self.REL_TOL_CLOSED
        makeClosed = continuousIfClosed  # and curves[0].toShape().isPartner(curves[-1].toShape())

        self.matchDegree(curves)
        nCurves = len(curves)

        # create a common knot vector for all splines
        compatSplines = self.createCommonKnotsVectorCurve(curves, tolerance)

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

        # now continue to create new control points by interpolating the remaining columns of controlPoints
        # in Skinning direction (here v-direction) by B-splines
        for cpUIdx in range(numControlPointsU):  # (int cpUIdx = 1; cpUIdx <= numControlPointsU; ++cpUIdx) {
            for cpVIdx in range(nPointsAdapt):  # (int cpVIdx = 1; cpVIdx <= nPointsAdapt; ++cpVIdx) {
                # print("%dx%d - %d"%(cpUIdx, cpVIdx, compatSplines[cpVIdx].NbPoles))
                interpPointsVDir[cpVIdx] = compatSplines[cpVIdx].getPole(cpUIdx + 1)
            interpSpline = Part.BSplineCurve()
            try:
                interpSpline.interpolate(Points=interpPointsVDir, Parameters=vParameters, PeriodicFlag=makeClosed, Tolerance=tolerance)
            except Part.OCCError:
                print("interpSpline creation failed")
                print("%d points" % len(interpPointsVDir))
                for p in interpPointsVDir:
                    print("%0.4f %0.4f %0.4f" % (p.x, p.y, p.z))
                print("%d parameters" % len(vParameters))
                for p in vParameters:
                    print("%0.4f" % p)
                # print(vParameters)
                print("Closed : %s" % makeClosed)

            # debug(interpSpline)
            if makeClosed:
                self.clampBSpline(interpSpline)
            # debug(interpSpline)

            if cpUIdx == 0:
                degreeV = interpSpline.Degree
                knotsV = interpSpline.getKnots()
                multsV = interpSpline.getMultiplicities()
                cpSurf = [[0] * interpSpline.NbPoles for i in range(numControlPointsU)]
                # new TColgp_HArray2OfPnt(1, static_cast<Standard_Integer>(numControlPointsU), 1, interpSpline->NbPoles());

            # the final surface control points are the control points resulting from
            # the interpolation
            for i in range(interpSpline.NbPoles):  # for (int i = cpSurf->LowerCol(); i <= cpSurf->UpperCol(); ++i) {
                cpSurf[cpUIdx][i] = interpSpline.getPole(i + 1)

            # check degree always the same
            assert (degreeV == interpSpline.Degree)

        knotsU = firstCurve.getKnots()
        multsU = firstCurve.getMultiplicities()

        # makeClosed = False

        skinnedSurface = Part.BSplineSurface()
        skinnedSurface.buildFromPolesMultsKnots(cpSurf, multsU, multsV, knotsU, knotsV, firstCurve.isPeriodic(), makeClosed, degreeU, degreeV)

        return skinnedSurface

    def pointsToSurface(self, points, uParams, vParams, uContinuousIfClosed, vContinuousIfClosed):
        """Returns a surface that skins the 2D array of points"""
        # debug("-   pointsToSurface")
        tolerance = self.REL_TOL_CLOSED * self.scale_pt_array(points)
        makeVDirClosed = vContinuousIfClosed and self.isVDirClosed(points, tolerance)
        makeUDirClosed = uContinuousIfClosed and self.isUDirClosed(points, tolerance)

        # GeomAPI_Interpolate does not want to have the last point,
        # if the curve should be closed. It internally uses the first point
        # as the last point
        if makeUDirClosed:
            nPointsUpper = len(points) - 1
        else:
            nPointsUpper = len(points)  # points.UpperRow()

        # first interpolate all points by B-splines in u-direction
        uSplines = list()
        for cpVIdx in range(len(points[0])):  # for (int cpVIdx = points.LowerCol(); cpVIdx <= points.UpperCol(); ++cpVIdx) {
            points_u = [0] * nPointsUpper
            for iPointU in range(nPointsUpper):  # for (int iPointU = points_u->Lower(); iPointU <= points_u->Upper(); ++iPointU) {
                points_u[iPointU] = points[iPointU][cpVIdx]
            curve = Part.BSplineCurve()
            curve.interpolate(Points=points_u, Parameters=uParams, PeriodicFlag=makeUDirClosed, Tolerance=tolerance)

            if makeUDirClosed:
                self.clampBSpline(curve)
            uSplines.append(curve)

        # now create a skinned surface with these B-splines which represents the interpolating surface
        interpolatingSurf = self.curvesToSurface(uSplines, vParams, makeVDirClosed)
        return interpolatingSurf

    def reparametrizeBSplineContinuouslyApprox(self, spline, old_parameters, new_parameters, n_control_pnts):
        """Approximate spline while moving old_parameters to new_parameters"""
        if not len(old_parameters) == len(new_parameters):
            self.error("parameter sizes don't match")

        # create a B-spline as a function for reparametrization
        old_parameters_pnts = [vec2d(old_parameters[i], 0) for i in range(len(old_parameters))]

        reparametrizing_spline = Part.Geom2d.BSplineCurve2d()
        try:
            reparametrizing_spline.interpolate(Points=old_parameters_pnts, Parameters=new_parameters, PeriodicFlag=False, Tolerance=self.tol)
        except Exception:
            self.error("reparametrizing_spline failed")
            self.error("nb_pts = %d" % (len(old_parameters_pnts)))
            self.error("nb_par = %d" % (len(new_parameters)))
            self.error("pts = %s" % old_parameters_pnts)
            self.error("pars = %s" % new_parameters)

        # Create a vector of parameters including the intersection parameters
        breaks = new_parameters[1:-1]
        par_tol = 1e-10
        # kinks is the list of C0 knots of input spline without tangency
        kinks = self.getKinkParameters(spline)
        # convert kink parameters into reparametrized parameter using the
        # inverse reparametrization function
        for ikink in range(len(kinks)):
            kinks[ikink] = reparametrizing_spline.parameter(vec2d(kinks[ikink], 0.))

        for kink in kinks:
            pos = IsInsideTolerance(breaks, kink, par_tol)
            if pos >= 0:
                breaks.pop(pos)

        # create equidistance array of parameters, including the breaks
        parameters = LinspaceWithBreaks(new_parameters[0], new_parameters[-1], max(101, n_control_pnts * 2), breaks)

        # insert kinks into parameters array at the correct position
        for kink in kinks:
            parameters.append(kink)
        parameters.sort()

        # Compute points on spline at the new parameters
        # Those will be approximated later on
        points = list()
        for i in range(len(parameters)):  # (size_t i = 1; i <= parameters.size(); ++i) {
            oldParameter = reparametrizing_spline.value(parameters[i]).x
            points.append(spline.value(oldParameter))

        makeContinuous = spline.isClosed() and (spline.tangent(spline.FirstParameter)[0].getAngle(spline.tangent(spline.LastParameter)[0]) < 6. / 180. * pi)

        # # Create the new spline as a interpolation of the old one
        approximationObj = BSplineApproxInterp(points, n_control_pnts, 3, makeContinuous)

        breaks.insert(0, new_parameters[0])
        breaks.append(new_parameters[-1])
        # # Interpolate points at breaking parameters (required for gordon surface)
        # for (size_t ibreak = 0; ibreak < breaks.size(); ++ibreak) {
        for thebreak in breaks:
            pos = IsInsideTolerance(parameters, thebreak, par_tol)
            if pos >= 0:
                approximationObj.InterpolatePoint(pos, False)

        for kink in kinks:
            pos = IsInsideTolerance(parameters, kink, par_tol)
            if pos >= 0:
                approximationObj.InterpolatePoint(pos, True)

        result, error = approximationObj.FitCurveOptimal(parameters, 10)
        if not isinstance(result, Part.BSplineCurve):
            return None
        return result


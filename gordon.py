import FreeCAD
import Part
from math import pi

def debug(string):
    FreeCAD.Console.PrintMessage("%s\n"%string)

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
        if self.d == 0:
            self.s.insertUKnot(knot, mult, tolerance)
        else:
            self.s.insertVKnot(knot, mult, tolerance)
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
    def __init__(self):
        self.REL_TOL_CLOSED = 1e-8
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
    def intersections(self, spline1, spline2, tol):
        # light weight simple minimizer
        # check parametrization of B-splines beforehand
        # find out the average scale of the two B-splines in order to being able to handle a more approximate curves and find its intersections
        splines_scale = (self.scale(spline1) + self.scale(spline2)) / 2.
        intersection_params_vector = []
        inters = spline1.intersectCC(spline2)
        #GeomAPI_ExtremaCurveCurve intersectionObj(spline1, spline2);
        debug("intersectCC results")
        if len(inters) == 0:
            self.error("intersectCC failed !")
            e1 = spline1.toShape()
            e2 = spline2.toShape()
            d,pts,info = e1.distToShape(e2)
            if d > tol:
                self.error("distToShape over tolerance !")
            self.error("using average point")
            p1,p2 = pts[0]
            av = .5*(p1+p2)
            inters = [av]
            
        for intpt in inters:
            if isinstance(intpt,Part.Point):
                inter = FreeCAD.Vector(intpt.X, intpt.Y, intpt.Z)
            else:
                inter = intpt
            debug(intpt)
            param1 = spline1.parameter(inter)
            param2 = spline2.parameter(inter)
            #intersectionObj.Parameters(intersect_idx, param1, param2);
            # filter out real intersections
            point1 = spline1.value(param1);
            point2 = spline2.value(param2);
            if (point1.distanceToPoint(point2) < tol * splines_scale):
                intersection_params_vector.append([param1, param2])
            else:
                debug("Curves do not intersect each other")
            # for closed B-splines:
            if (len(inters) == 1 and spline1.isClosed() and abs(param1 - spline1.getKnot(1)) < 1e-6):
                # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the end of the closed curve, so add it by hand
                intersection_params_vector.append([spline1.getKnot(spline1.NbKnots), param2])
            if (len(inters) == 1 and spline1.isClosed() and abs(param1 - spline1.getKnot(spline1.NbKnots)) < 1e-6):
                # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the beginning of the closed curve, so add it by hand
                intersection_params_vector.append([spline1.getKnot(1), param2])
            if (len(inters) == 1 and spline2.isClosed() and abs(param2 - spline2.getKnot(1)) < 1e-6):
                # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the end of the closed curve, so add it by hand
                intersection_params_vector.append([param1, spline2.getKnot(spline2.NbKnots)])
            if (len(inters) == 1 and spline2.isClosed() and abs(param2 - spline2.getKnot(spline2.NbKnots)) < 1e-6):
                # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at the beginning of the closed curve, so add it by hand
                intersection_params_vector.append([param1, spline2.getKnot(1)])
        #debug(intersection_params_vector)
        return(intersection_params_vector)
    def isUDirClosed(self, points, tolerance):
        uDirClosed = True
        # check that first row and last row are the same
        for v_idx in range(len(points[0])): #(int v_idx = points.LowerCol(); v_idx <= points.UpperCol(); ++v_idx) {
            uDirClosed = uDirClosed & (points[0][v_idx].distanceToPoint(points[-1][v_idx]) < tolerance)
        return(uDirClosed)
    def isVDirClosed(self, points, tolerance):
        vDirClosed = True
        # check that first row and last row are the same
        for u_idx in range(len(points)): #(int v_idx = points.LowerCol(); v_idx <= points.UpperCol(); ++v_idx) {
            vDirClosed = vDirClosed & (points[u_idx][0].distanceToPoint(points[u_idx][-1]) < tolerance)
        return(vDirClosed)
    def curvesToSurface(self, curves, vParameters, continuousIfClosed):
        # check amount of given parameters
        if not len(vParameters) == len(curves):
            raise ValueError("The amount of given parameters has to be equal to the amount of given B-splines!")

        # check if all curves are closed
        tolerance = self.scale(curves) * self.REL_TOL_CLOSED
        makeClosed = continuousIfClosed & curves[0].toShape().isPartner(curves[-1].toShape())

        self.matchDegree(curves)
        nCurves = len(curves)

        # create a common knot vector for all splines
        compatSplines = self.createCommonKnotsVectorCurve(curves, 1e-15)

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
                print("%dx%d - %d"%(cpUIdx, cpVIdx, compatSplines[cpVIdx].NbPoles))
                interpPointsVDir[cpVIdx] = compatSplines[cpVIdx].getPole(cpUIdx+1)
            interpSpline = Part.BSplineCurve()
            print("interpSpline")
            #print(interpPointsVDir)
            print(vParameters)
            print(makeClosed)
            interpSpline.interpolate(Points=interpPointsVDir, Parameters=vParameters, PeriodicFlag=makeClosed, Tolerance=1e-5)

            if makeClosed:
                self.clampBSpline(interpSpline)

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
        
        skinnedSurface = Part.BSplineSurface()
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
    def pointsToSurface(self, points, uParams, vParams, uContinousIfClosed, vContinousIfClosed):
        debug("-   pointsToSurface")
        tolerance = self.REL_TOL_CLOSED * self.scale_pt_array(points)
        makeVDirClosed = vContinousIfClosed & self.isVDirClosed(points, tolerance)
        makeUDirClosed = uContinousIfClosed & self.isUDirClosed(points, tolerance)

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
            curve.interpolate(Points=points_u, Parameters=uParams, PeriodicFlag=makeUDirClosed, Tolerance=1e-15)

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
    def createCommonKnotsVectorSurface(self, old_surfaces_vector):
        # all B-spline surfaces must have the same parameter range in u- and v-direction
        # TODO: Match parameter range

        # Create a copy that we can modify
        adapterSplines = list() #[s.copy() for s in old_surfaces_vector]
        for i in range(len(old_surfaces_vector)): #(size_t i = 0; i < old_surfaces_vector.size(); ++i) {
            adapterSplines.append(SurfAdapterView(old_surfaces_vector[i].copy(), 0))
        # first in u direction
        self.makeGeometryCompatibleImpl(adapterSplines, 1e-15)

        for i in range(len(old_surfaces_vector)): #(size_t i = 0; i < old_surfaces_vector.size(); ++i) adapterSplines[i].setDir(vdir);
            adapterSplines[i].d = 1

        # now in v direction
        self.makeGeometryCompatibleImpl(adapterSplines, 1e-15)

        return([ads.s for ads in adapterSplines])
    def getKinkParameters(self, curve):
        if not curve:
            raise ValueError("Null Pointer curve")

        eps = 1e-8

        kinks = list()
        for knotIndex in range(2,curve.NbKnots): #(int knotIndex = 2; knotIndex < curve->NbKnots(); ++knotIndex) {
            if curve.getMultiplicity(knotIndex) == curve.Degree:
                knot = curve.getKnot(knotIndex)
                # check if really a kink
                angle = curve.tangent(knot + eps)[0].getAngle(curve.tangent(knot - eps)[0])
                if (angle > 6./180. * pi):
                    kinks.append(knot)
        return(kinks)

    def reparametrizeBSpline(self, spline, umin, umax, tol):
        knots = spline.getKnots()
        ma = knots[-1]
        mi = knots[0]
        if abs(mi - umin) > tol or abs(ma - umax) > tol:
            ran = ma-mi
            newknots = [(k-mi)/ran for k in knots]
            spline.setKnots(newknots)
        
    def reparametrizeBSplineContinuouslyApprox(self, spline, old_parameters, new_parameters, n_control_pnts):
        #from FreeCAD import Base
        #vec2d = Base.Vector2d
        #if not len(old_parameters) == len(new_parameters):
            #self.error("parameter sizes dont match")

        ## create a B-spline as a function for reparametrization
        #old_parameters_pnts = [0]*len(old_parameters) #new TColgp_HArray1OfPnt2d(1, old_parameters.size());
        #for parameter_idx in range(len(old_parameters)): #(size_t parameter_idx = 0; parameter_idx < old_parameters.size(); ++parameter_idx) {
            #occIdx = parameter_idx + 1
            #old_parameters_pnts[occIdx] = vec2d(old_parameters[parameter_idx], 0)

        #reparametrizing_spline = Part.Geom2d.BSplineCurve2d()
        #reparametrizing_spline.interpolate(Points=old_parameters_pnts, Parameters=new_parameters, PeriodicFlag=False, Tolerance=1e-15)


        ## Create a vector of parameters including the intersection parameters
        #breaks = new_parameters[:]
        ##for (size_t ipar = 1; ipar < new_parameters.size() - 1; ++ipar) {
            ##breaks.push_back(new_parameters[ipar]);
        ##}

        #par_tol = 1e-10

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

        ## create equidistance array of parameters, including the breaks
        #std::vector<double> parameters = LinspaceWithBreaks(new_parameters.front(),
                                                            #new_parameters.back(),
                                                            #std::max(static_cast<size_t>(101), n_control_pnts*2),
                                                            #breaks);
    ##ifdef MODEL_KINKS
        ## insert kinks into parameters array at the correct position
        #for (size_t ikink = 0; ikink < kinks.size(); ++ikink) {
            #double kink = kinks[ikink];
            #parameters.insert( 
                #std::upper_bound( parameters.begin(), parameters.end(), kink),
                #kink);
        #}
    ##endif

        ## Compute points on spline at the new parameters
        ## Those will be approximated later on
        #TColgp_Array1OfPnt points(1, static_cast<Standard_Integer>(parameters.size()));
        #for (size_t i = 1; i <= parameters.size(); ++i) {
            #double oldParameter = reparametrizing_spline->Value(parameters[i-1]).X();
            #points(static_cast<Standard_Integer>(i)) = spline->Value(oldParameter);
        #}

        #bool makeContinous = spline->IsClosed() &&
                #spline->DN(spline->FirstParameter(), 1).Angle(spline->DN(spline->LastParameter(), 1)) < 6. / 180. * M_PI;

        ## Create the new spline as a interpolation of the old one
        #CTiglBSplineApproxInterp approximationObj(points, static_cast<int>(n_control_pnts), 3, makeContinous);

        #breaks.insert(breaks.begin(), new_parameters.front());
        #breaks.push_back(new_parameters.back());
        ## Interpolate points at breaking parameters (required for gordon surface)
        #for (size_t ibreak = 0; ibreak < breaks.size(); ++ibreak) {
            #double thebreak = breaks[ibreak];
            #size_t idx = static_cast<size_t>(
                #std::find_if(parameters.begin(), parameters.end(), IsInsideTolerance(thebreak)) -
                #parameters.begin());
            #approximationObj.InterpolatePoint(idx);
        #}

    ##ifdef MODEL_KINKS
        #for (size_t ikink = 0; ikink < kinks.size(); ++ikink) {
            #double kink = kinks[ikink];
            #size_t idx = static_cast<size_t>(
                #std::find_if(parameters.begin(), parameters.end(), IsInsideTolerance(kink, par_tol)) -
                #parameters.begin());
            #approximationObj.InterpolatePoint(idx, true);
        #}
    ##endif

        #CTiglApproxResult result = approximationObj.FitCurveOptimal(parameters);
        #Handle(Geom_BSplineCurve) reparametrized_spline = result.curve;

        #assert(!reparametrized_spline.IsNull());

        #return(reparametrized_spline)
        return(spline)

    def clampBSpline(self, curve):
        if not curve.isPeriodic():
            return()
        curve.setNotPeriodic()
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

        debug("---\n%s\n%s"%(resultKnots, resultMults))
        # now insert missing knots in all splines
        for spline in splines_vector:
            debug("\n%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))
            for knotIdx in range(len(resultKnots)):
                knots = spline.getKnots()
                for k in knots:
                    if abs(resultKnots[knotIdx]-k) < par_tolerance:
                        if spline.getMultiplicity(knotIdx+1) > resultMults[knotIdx]:
                            debug("increasing mult %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                            spline.increaseMultiplicity(knotIdx+1, resultMults[knotIdx])
                    #cur = spline.getMultiplicity(knotIdx+1)
                    else:
                        debug("inserting knot %f / %d"%(resultKnots[knotIdx], resultMults[knotIdx]))
                        spline.insertKnot(resultKnots[knotIdx], resultMults[knotIdx], par_tolerance)
            debug("%d - %d poles\n%s\n%s"%(spline.Degree, spline.NbPoles, spline.getKnots(), spline.getMultiplicities()))

class GordonSurfaceBuilder(object):
    """Build a Gordon surface from a network of curves"""
    def __init__(self, profiles, guides, params_u, params_v, tol=1e-5):
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

        # check, whether to build a closed continous surface
        bsa = BSplineAlgorithms()
        curve_u_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(guides)
        curve_v_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(profiles)
        tp_tolerance      = bsa.REL_TOL_CLOSED * bsa.scale_pt_array(intersection_pnts)
                                                                                    # TODO No IsEqual in FreeCAD
        makeUClosed = bsa.isUDirClosed(intersection_pnts, tp_tolerance) and guides[0].isPartner(guides[-1]) #.isEqual(guides[-1], curve_u_tolerance);
        makeVClosed = bsa.isVDirClosed(intersection_pnts, tp_tolerance) and profiles[0].IsPartner(profiles[-1])

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
        surfaces_vector = bsa.createCommonKnotsVectorSurface(surfaces_vector_unmod)

        assert(len(surfaces_vector) == 3)

        self.skinningSurfGuides = surfaces_vector[0]
        self.skinningSurfProfiles = surfaces_vector[1]
        self.tensorProdSurf = surfaces_vector[2]

        print("Number of U Poles")
        print("skinningSurfGuides : %d"%self.skinningSurfGuides.NbUPoles)
        print("skinningSurfProfiles : %d"%self.skinningSurfProfiles.NbUPoles)
        print("tensorProdSurf : %d"%self.tensorProdSurf.NbUPoles)

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
        bsa = BSplineAlgorithms()
        splines_scale = 0.5 * (bsa.scale(profiles) + bsa.scale(guides))

        if abs(intersection_params_spline_u[0]) > (splines_scale * tol) or abs(intersection_params_spline_u[-1] - 1.) > (splines_scale * tol):
            self.error("WARNING: B-splines in u-direction must not stick out, spline network must be 'closed'!")
        if abs(intersection_params_spline_v[0]) > (splines_scale * tol) or abs(intersection_params_spline_v[-1] - 1.) > (splines_scale * tol):
            self.error("WARNING: B-splines in v-direction mustn't stick out, spline network must be 'closed'!")

        # check compatibilty of network
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
    def __init__(self, profiles, guides, tol=1e-5):
        self.tolerance = 1e-5
        self.has_performed = False
        if (len(profiles) < 2) or (len(guides) < 2):
            self.error("Not enough guides or profiles")
        else:
            self.profiles = profiles
            self.guides = guides
        if tol > 0.0:
            self.tolerance = tol
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
                
                currentIntersections = BSplineAlgorithms().intersections(self.profiles[spline_u_idx], self.guides[spline_v_idx], self.tolerance)
                if len(currentIntersections) < 1:
                    self.error("U-directional B-spline and v-directional B-spline don't intersect each other!")
                    self.error("profile %d / guide %d"%(spline_u_idx, spline_v_idx))
                elif len(currentIntersections) == 1:
                    intersection_params_u[spline_u_idx][spline_v_idx] = currentIntersections[0][0]
                    intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]
                    debug("%dx%d = (%.4f, %.4f)"%(spline_u_idx, spline_v_idx, intersection_params_u[spline_u_idx][spline_v_idx], intersection_params_v[spline_u_idx][spline_v_idx]))
                    # for closed curves
                elif len(currentIntersections) == 2:
                    debug("*** 2 intersections")
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
                elif len(currentIntersections) > 2:
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
            bsa.reparametrizeBSpline(c, 0., 1., 1e-15)
        for c in self.guides:
            bsa.reparametrizeBSpline(c, 0., 1., 1e-15)
        # now the parameter range of all  profiles and guides is [0, 1]

        nGuides = len(self.guides)
        nProfiles = len(self.profiles)
        # now find all intersections of all B-splines with each other
        intersection_params_u = [[0]*nGuides for k in range(nProfiles)] #(0, nProfiles - 1, 0, nGuides - 1);
        intersection_params_v = [[0]*nGuides for k in range(nProfiles)] #(0, nProfiles - 1, 0, nGuides - 1);
        self.compute_intersections(intersection_params_u, intersection_params_v)
        debug("------------")
        debug(intersection_params_u)
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

        if (newParametersProfiles[0] > 1e-5 or newParametersGuides[0] > 1e-5):
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
            if (abs(oldParametersProfile[0]) < 1e-5):
                oldParametersProfile[0] = 0.
            if (abs(newParametersProfiles[0]) < 1e-5):
                newParametersProfiles[0] = 0.
            # eliminate small inaccuracies at the last knot
            if (abs(oldParametersProfile[-1] - 1.) < 1e-5):
                oldParametersProfile[-1] = 1.
            if (abs(newParametersProfiles[-1] - 1.) < 1e-5):
                newParametersProfiles[-1] = 1.

            profile = self.profiles[spline_u_idx]
            profile = bsa.reparametrizeBSplineContinuouslyApprox(profile, oldParametersProfile, newParametersProfiles, max_cp_u)

        # reparametrize v-directional B-splines
        for spline_v_idx in range(nGuides):
            oldParameterGuide = list()
            for spline_u_idx in range(nProfiles):
                oldParameterGuide.append(intersection_params_v[spline_u_idx][spline_v_idx])
            # eliminate small inaccuracies at the first knot
            if (abs(oldParameterGuide[0]) < 1e-5):
                oldParameterGuide[0] = 0.
            if (abs(newParametersGuides[0]) < 1e-5):
                newParametersGuides[0] = 0.
            # eliminate small inaccuracies at the last knot
            if (abs(oldParameterGuide[-1] - 1.) < 1e-5):
                oldParameterGuide[-1] = 1.
            if (abs(newParametersGuides[-1] - 1.) < 1e-5):
                newParametersGuides[-1] = 1.

            guide = self.guides[spline_v_idx]
            guide = bsa.reparametrizeBSplineContinuouslyApprox(guide, oldParameterGuide, newParametersGuides, max_cp_v)
            
        self.intersectionParamsU = newParametersProfiles
        self.intersectionParamsV = newParametersGuides

    def eliminate_inaccuracies_network_intersections(self, sortedProfiles, sortedGuides, intersection_params_u, intersection_params_v):
        nProfiles = len(sortedProfiles)
        nGuides = len(sortedGuides)
        tol = 0.001
        # eliminate small inaccuracies of the intersection parameters:

        # first intersection
        for spline_u_idx in range(nProfiles):
            if (abs(intersection_params_u[spline_u_idx][0] - sortedProfiles[0].getKnot(1)) < tol):
                if (abs(sortedProfiles[0].getKnot(1)) < 1e-10):
                    intersection_params_u[spline_u_idx][0] = 0
                else:
                    intersection_params_u[spline_u_idx][0] = sortedProfiles[0].getKnot(1)

        for spline_v_idx in range(nGuides):
            if (abs(intersection_params_v[0][spline_v_idx] - sortedGuides[0].getKnot(1)) < tol):
                if (abs(sortedGuides[0].getKnot(1)) < 1e-10):
                    intersection_params_v[0][spline_v_idx] = 0
                else:
                    intersection_params_v[0][spline_v_idx] = sortedGuides[0].getKnot(1)

        # last intersection
        for spline_u_idx in range(nProfiles):
            if (abs(intersection_params_u[spline_u_idx][nGuides - 1] - sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots)) < tol):
                intersection_params_u[spline_u_idx][nGuides - 1] = sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots)

        for spline_v_idx in range(nGuides):
            if (abs(intersection_params_v[nProfiles - 1][spline_v_idx] - sortedGuides[0].getKnot(sortedGuides[0].NbKnots)) < tol):
                intersection_params_v[nProfiles - 1][spline_v_idx] = sortedGuides[0].getKnot(sortedGuides[0].NbKnots)



def main():
    
    import FreeCAD
    import FreeCADGui
    import Part
    
    data = ["test-S2R-2","Compound","Compound001"]
    #data = ["test-birail-3","Compound","Compound001"]
    
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
else:
    main()



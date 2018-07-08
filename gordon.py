class BSplineAlgorithms(object):
    """Various BSpline algorithms"""
    REL_TOL_CLOSED = 1e-8
    def error(self,mes):
        print(mes)
    def scale(self, c):
        res = 0
        if isinstance(c, (tuple,list)):
            for cu in c:
                res = max(res,self.scale(cu))
        else:
            pts = c.getPoles()
            for p in pts[1:]:
                res = max(res, p.distanceToPoint(pts[0]))
        return(res)

    def intersections(self, spline1, spline2, tol):
        # light weight simple minimizer
        # check parametrization of B-splines beforehand
        # find out the average scale of the two B-splines in order to being able to handle a more approximate curves and find its intersections
        splines_scale = (self.scale(spline1) + self.scale(spline2)) / 2.
        intersection_params_vector = []
        inters = spline1.intersectCC(spline2)
        #GeomAPI_ExtremaCurveCurve intersectionObj(spline1, spline2);
        for inter in inters:
            param1 = spline1.parameter(inter)
            param2 = spline2.parameter(inter)
            #intersectionObj.Parameters(intersect_idx, param1, param2);
            # filter out real intersections
            point1 = spline1.value(param1);
            point2 = spline2.value(param2);
            if (point1.distanceToPoint(point2) < tolerance * splines_scale):
                intersection_params_vector.append([param1, param2])
            else:
                self.error("Curves do not intersect each other")
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
        return intersection_params_vector

class GordonSurfaceBuilder(object):
    """Build a Gordon surface from a network of curves"""
    def __init__(self, profiles, guides, params_u, params_v, tol=1e-5):
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
        return(self.gordon_surf)
    def surface_profiles(self):
        self.perform()
        return(self.skinning_surf_profiles)
    def surface_guides(self):
        self.perform()
        return(self.skinning_surf_guides)
    def surface_intersections(self):
        self.perform()
        return(self.tensor_prod_surf)
    def create_gordon_surface(self, profiles, guides, intersection_params_spline_u, intersection_params_spline_v):
        # check whether there are any u-directional and v-directional B-splines in the vectors
        if len(profiles) < 2):
            self.error("There must be at least two profiles for the gordon surface.")
        if len(guides)  < 2):
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
        intersection_pnts = list()
        #TColgp_Array2OfPnt intersection_pnts(1, static_cast<Standard_Integer>(intersection_params_spline_u.size()),
                                           # 1, static_cast<Standard_Integer>(intersection_params_spline_v.size()));

        # use splines in u-direction to get intersection points
        for spline_idx in range(len(profiles)): #(size_t spline_idx = 0; spline_idx < profiles.size(); ++spline_idx) {
            for intersection_idx in range(len(intersection_params_spline_u)): #(size_t intersection_idx = 0; intersection_idx < intersection_params_spline_u.size(); ++intersection_idx) {
                Handle(Geom_BSplineCurve) spline_u = profiles[spline_idx];
                double parameter = intersection_params_spline_u[intersection_idx];
                intersection_pnts[intersection_idx + 1][spline_idx + 1] = spline_u.value(parameter)

        # check, whether to build a closed continous surface
        bsa = BSplineAlgorithms()
        curve_u_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(guides)
        curve_v_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(profiles)
        tp_tolerance      = bsa.REL_TOL_CLOSED * bsa.scale(intersection_pnts)
                                                                                    # TODO No IsEqual in FreeCAD
        makeUClosed = bsa.isUDirClosed(intersection_pnts, tp_tolerance) && guides[0].isEqual(guides[-1], curve_u_tolerance);
        makeVClosed = bsa.isVDirClosed(intersection_pnts, tp_tolerance) && profiles.front()->IsEqual(profiles.back(), curve_v_tolerance);
    
    
    def check_curve_network_compatibility(self, profiles, guides, intersection_params_spline_u, intersection_params_spline_v, tol):
        pass    

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
        self.make_curves_compatible()
        builder = GordonSurfaceBuilder(self.profiles, self.guides, self.intersectionParamsU, self.intersectionParamsV, self.tolerance)
        self.gordon_surf = builder.surface_gordon()
        self.skinning_surf_profiles = builder.surface_profiles()
        self.skinning_surf_guides = builder.surface_guides()
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
        return(self.surface)
    
    def compute_intersections(self, intersection_params_u, intersection_params_v):
        for spline_u_idx in range(len(self.profiles)):
            for spline_v_idx in range(len(self.guides)):
                currentIntersections = BSplineAlgorithms().intersections(self.profiles[spline_u_idx], self.guides[spline_v_idx], self.tolerance)
                if len(currentIntersections) < 1:
                    self.error("U-directional B-spline and v-directional B-spline don't intersect each other!")
                elif len(currentIntersections) == 1:
                    intersection_params_u[spline_u_idx][spline_v_idx] = currentIntersections[0][0]
                    intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]
                    # for closed curves
                elif len(currentIntersections) == 2:
                    # only the u-directional B-spline curves are closed
                    if (self.profiles[0].isClosed()):
                        if (spline_v_idx == 0):
                            intersection_params_u[spline_u_idx][spline_v_idx] = min(currentIntersections[0][0], currentIntersections[1][0])
                        elif (spline_v_idx == len(self.guides) - 1):
                            intersection_params_u[spline_u_idx][spline_v_idx] = max(currentIntersections[0][0], currentIntersections[1][0])
                        # intersection_params_vector[0].second == intersection_params_vector[1].second
                        intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]
   
                    # only the v-directional B-spline curves are closed
                    if (self.guides[0].isClosed()):
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
        pass
    
    def make_curves_compatible(self):
        pass
    
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
            if (abs(intersection_params_u[spline_u_idx][nGuides - 1] - sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots())) < tol):
                intersection_params_u[spline_u_idx][nGuides - 1] = sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots())

        for spline_v_idx in range(nGuides):
            if (abs(intersection_params_v[nProfiles - 1][spline_v_idx] - sortedGuides[0].getKnot(sortedGuides[0].NbKnots())) < tol):
                intersection_params_v[nProfiles - 1][spline_v_idx] = sortedGuides[0].getKnot(sortedGuides[0].NbKnots())



def main():
    
    import FreeCAD
    import FreeCADGui
    import Part
    doc = FreeCAD.open(u"/home/tomate/.FreeCAD/Mod/CurvesWB/TestFiles/Gordon-2.fcstd")

    # Create array of curves
    guide_curves = doc.getObject('guides').Shape.Edges
    profile_curves = doc.getObject('profiles').Shape.Edges

    # create the gordon surface
    gordon = InterpolateCurveNetwork(profile_curves, guide_curves, 1.e-4)

    # display curves and resulting surface
    Part.show(gordon.surface())
    FreeCAD.ActiveDocument.recompute()

if __name__ == "__main__":
    main()
else:
    main()



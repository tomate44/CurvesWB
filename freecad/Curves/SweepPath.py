import FreeCAD
from FreeCAD import Vector
import Part
from freecad.Curves import curves_to_surface as CTS


err = FreeCAD.Console.PrintError
warn = FreeCAD.Console.PrintWarning
message = FreeCAD.Console.PrintMessage


def normalize(geom):
    """normalize([bpline_objects, ...])
    Batch normalize knots of supplied bspline geometries.
    works on curves and surfaces.
    """
    for g in geom:
        g.scaleKnotsToBounds()


def contact_points(curve, pt1, pt2):
    """contact_points(bspline_curve, pt1, pt2)
    Trim or extend bspline_curve to contact points.
    The bspline_curve is also oriented from pt1 to pt2
    """
    p1 = curve.parameter(pt1)
    p2 = curve.parameter(pt2)
    fp = curve.FirstParameter
    lp = curve.LastParameter
    if p1 > p2:
        curve.reverse()
        contact_points(curve, pt1, pt2)
        return
    if p1 == fp:
        curve.setPole(1, pt1)
    if p2 == lp:
        curve.setPole(curve.NbPoles, pt2)
    try:
        curve.segment(p1, p2)
    except Part.OCCError:
        err(f"Failed to segment BSpline curve ({fp}, {lp})\n")
        err(f"between ({p1}, {p2})\n")
    curve.scaleKnotsToBounds()


def contact_shapes(bscurve, shape1, shape2):
    """contact_shapes(bspline_curve, shape1, shape2)
    Trim or extend bspline_curve to contact shapes.
    The bspline_curve is also oriented from shape1 to shape2
    """
    edge = bscurve.toShape()
    pt1 = edge.distToShape(shape1)[1][0][1]
    pt2 = edge.distToShape(shape2)[1][0][1]
    contact_points(bscurve, pt1, pt2)


class BSplineFacade:
    """Class BSplineFacade is a collection of functions
    that work both on BSpline curves and BSpline surfaces.
    The geom argument of the functions is either :
    - a BSpline Curve
    - U or V dimension of a BSpline Surface in the form (surf, 0 or 1)
    """

    def getDegree(geom):
        "Returns the degree of the BSpline geom"
        if isinstance(geom, Part.BSplineCurve):
            return geom.Degree
        elif isinstance(geom, (list, tuple)):
            if geom[1] == 0:
                return geom[0].UDegree
            elif geom[1] == 1:
                return geom[0].VDegree

    def getKnots(geom):
        "Returns the knots of the BSpline geom"
        if isinstance(geom, Part.BSplineCurve):
            return geom.getKnots()
        elif isinstance(geom, (list, tuple)):
            if geom[1] == 0:
                return geom[0].getUKnots()
            elif geom[1] == 1:
                return geom[0].getVKnots()

    def getMults(geom):
        "Returns the multiplicities of the BSpline geom"
        if isinstance(geom, Part.BSplineCurve):
            return geom.getMultiplicities()
        elif isinstance(geom, (list, tuple)):
            if geom[1] == 0:
                return geom[0].getUMultiplicities()
            elif geom[1] == 1:
                return geom[0].getVMultiplicities()

    def incDegree(geom, d):
        """incDegree(geom, d)
        Raise the degree of the BSpline geom to d
        """
        if isinstance(geom, Part.BSplineCurve):
            geom.increaseDegree(d)
        elif isinstance(geom, (list, tuple)):
            if geom[1] == 0:
                geom[0].increaseDegree(d, geom[0].VDegree)
            elif geom[1] == 1:
                geom[0].increaseDegree(geom[0].UDegree, d)

    def insKnotsMults(geom, knots, mults, tol=1e-10, add=False):
        """insKnots(geom, knots, mults, tol=1e-10, add=False)
        Inserts the knots and mults into the BSpline geom
        """
        # message(f"insKnotsMults: {geom}\n")
        # geom.scaleKnotsToBounds()
        # print(knots)
        # print(mults)
        # print(getKnots(geom))
        # print(getMults(geom))
        # print(geom.getPoles())
        if isinstance(geom, Part.BSplineCurve):
            geom.insertKnots(knots, mults, tol, add)
        elif isinstance(geom, (list, tuple)):
            if geom[1] == 0:
                geom[0].insertUKnots(knots, mults, tol, add)
            elif geom[1] == 1:
                geom[0].insertVKnots(knots, mults, tol, add)
        # return geom

    def syncDegree(geo1, geo2):
        """syncDegree(geo1, geo2)
        Raise the degree of one of the BSpline geoms
        to match the other one.
        """
        d1 = BSplineFacade.getDegree(geo1)
        d2 = BSplineFacade.getDegree(geo2)
        if d1 > d2:
            BSplineFacade.incDegree(geo2, d1)
        elif d2 > d1:
            BSplineFacade.incDegree(geo1, d2)

    def syncAllDegrees(*geo_list):
        """syncAllDegrees(geo_list)
        Raise the degree of the BSpline geoms
        the highest one.
        """
        deg = max([BSplineFacade.getDegree(g) for g in geo_list])
        for geo in geo_list:
            BSplineFacade.incDegree(geo, deg)

    def insKnots(geo1, geo2, tol=1e-10, add=False):
        """insKnots(geo1, geo2, tol=1e-10, add=False)
        Inserts the knots and mults of geo2 into the BSpline geo1
        """
        knots = BSplineFacade.getKnots(geo2)
        mults = BSplineFacade.getMults(geo2)
        # print(knots, mults)
        BSplineFacade.insKnotsMults(geo1, knots, mults, tol, add)

    def syncKnots(geo1, geo2, tol=1e-10):
        """syncKnots(geo1, geo2, tol=1e-10)
        Mutual knots insertion (geo1 and geo2 are modified)
        to make the 2 BSpline geometries compatible.
        """
        # k = getKnots(geo1)
        # m = getMults(geo1)
        # k2 = getKnots(geo2)
        # m2 = getMults(geo2)
        geo3 = geo1
        BSplineFacade.insKnots(geo1, geo2, tol, False)
        BSplineFacade.insKnots(geo2, geo3, tol, False)

    def syncAllKnots(geo_list, tol=1e-10):
        """syncAllKnots(geo_list, tol=1e-10)
        Knots insertion to make the BSpline geometries compatible.
        """
        for geo in geo_list[1:]:
            BSplineFacade.insKnots(geo_list[0], geo, tol, False)
        for geo in geo_list[1:]:
            BSplineFacade.insKnots(geo, geo_list[0], tol, False)


class SweepProfile:
    def __init__(self, prof=None, par=None):
        self._curve = None
        self._shape = None
        self._param = par
        if hasattr(prof, "value"):
            self.Curve = prof.toBSpline()
        elif hasattr(prof, "Curve"):
            self.Curve = prof.Curve.toBSpline(prof.FirstParameter, prof.LastParameter)
            self._shape = prof
        elif isinstance(prof, Part.Wire):
            self.Curve = prof.approximate()

    @property
    def Curve(self):
        return self._curve

    @Curve.setter
    def Curve(self, c):
        self._curve = c

    @property
    def Shape(self):
        if self._shape is None:
            self._shape = self._curve.toShape()
        return self._shape

    @property
    def Parameter(self):
        return self._param

    @Parameter.setter
    def Parameter(self, p):
        self._param = p
    #
    # def duplicateAt(self, par):
    #     return SweepProfile(self.Curve, par)


class PathInterpolation:
    def __init__(self, path, profiles=None):
        self.profiles = []
        self.FaceSupport = None
        self.localLoft = None
        if hasattr(path, "value"):
            self.path = path.toShape()
        elif hasattr(path, "valueAt"):
            self.path = path
        else:
            raise (TypeError, "Path must be a curve or an edge")
        if profiles is not None:
            self.add_profiles(profiles)

    def transitionMatrixAt(self, par):
        """Path local CS"""
        poc = self.path.valueAt(par)
        tan = self.path.tangentAt(par)  # derivative1At(par)
        if self.FaceSupport is not None:
            u, v = self.FaceSupport.Surface.parameter(poc)
            nor = self.FaceSupport.Surface.normal(u, v)
        else:
            nor = self.path.normalAt(par)
        cho = tan.cross(nor)
        m = FreeCAD.Matrix(cho.x, tan.x, nor.x, poc.x,
                           cho.y, tan.y, nor.y, poc.y,
                           cho.z, tan.z, nor.z, poc.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        return m

    def computeLocalProfile(self, prof):
        m = self.transitionMatrixAt(prof.Parameter)
        m = m.inverse()
        locprof = prof.Curve.copy()
        for i in range(locprof.NbPoles):
            pole = locprof.getPole(i + 1)
            np = m.multVec(pole)
            locprof.setPole(i + 1, np)
        locprof.translate(FreeCAD.Vector(0, prof.Parameter, 0))
        prof.Curve = locprof
        return prof

    def add_profiles(self, prof):
        if isinstance(prof, (list, tuple)):
            for p in prof:
                self.add_profile(p)
            return
        lp = self.computeLocalProfile(prof)
        self.profiles.append(lp)

    def prepare(self):
        """Add end profiles outside of the path range
        in case some extrapolation is needed
        """
        p0 = self.profiles[0]
        p1 = self.profiles[-1]
        u0, u1 = self.path.ParameterRange
        path_range = u1 - u0
        if self.path.isClosed:
            path_range = -path_range
        self.profiles.append(SweepProfile(p1, p1.Parameter - path_range))
        self.profiles.append(SweepProfile(p0, p0.Parameter + path_range))
        self.sort_profiles()
        self.interpolate_local_profiles()
        fp = self.profileAt(u0)
        lp = self.profileAt(u1)
        self.profiles.append(fp)
        self.profiles.append(lp)
        self.sort_profiles()

    def interpolate_local_profiles(self):
        self.sort_profiles()
        # self.prepare()
        locprofs = [p.Curve for p in self.profiles]
        print(locprofs)
        cts = CTS.CurvesToSurface(locprofs)
        cts.match_curves(1e-7)
        cts.Parameters = self.profile_parameters()
        cts.interpolate()
        self.localLoft = cts._surface
        return self.localLoft

    def profileAt(self, par, tol=1e-7):
        for p in self.profiles:
            if abs(par - p.Parameter) < tol:
                return p
        print(f"extracting profile @ {par}")
        if self.localLoft is None:
            self.interpolate_local_profiles()
        locprof = self.localLoft.vIso(par)
        fp = locprof.getPole(1)
        locprof.translate(FreeCAD.Vector(0, -fp.y, 0))
        m = self.transitionMatrixAt(par)
        for i in range(locprof.NbPoles):
            pole = locprof.getPole(i + 1)
            np = m.multVec(pole)
            locprof.setPole(i + 1, np)
        return SweepProfile(locprof, par)

    def intermediate_profiles(self, num):
        if num < 1:
            return
        path_range = self.path.LastParameter - self.path.FirstParameter
        step = path_range / (num + 1)
        profs = []
        for i in range(len(self.profiles) - 1):
            lrange = self.profiles[i + 1].Parameter - self.profiles[i].Parameter
            nb = int(lrange / step)
            lstep = lrange / (nb + 1)
            for j in range(nb):
                par = self.profiles[i].Parameter + (j + 1) * lstep
                profs.append(self.profileAt(par))
        return profs

    def sort_profiles(self):
        self.profiles.sort(key=lambda x: x.Parameter)

    def profile_parameters(self):
        return [p.Parameter for p in self.profiles]


class RotationPathInterpolation(PathInterpolation):
    def __init__(self, path, profiles, center):
        self.Center = center
        super().__init__(path, profiles)

    def transitionMatrixAt(self, par):
        message(f"RotationPath matrix at {par}\n")
        poc = self.path.valueAt(par)
        cho = self.Center - poc
        der = self.path.tangentAt(par)  # derivative1At(par)
        if self.FaceSupport is not None:
            u, v = self.FaceSupport.Surface.parameter(poc)
            nor = self.FaceSupport.Surface.normal(u, v)
        else:
            nor = cho.cross(der)
            nor.normalize()
        m = FreeCAD.Matrix(cho.x, der.x, nor.x, poc.x,
                           cho.y, der.y, nor.y, poc.y,
                           cho.z, der.z, nor.z, poc.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        return m


class RotationSweep:
    def __init__(self, path, profiles, closed=False):
        self.path = path
        self.closed = closed
        self.tol = 1e-7
        self.Center = self.getCenter(profiles)
        self.add_profiles(profiles)
        self.sort_profiles()
        self.trim_profiles()
        if not self.closed:
            self.trim_path()

    @property
    def Center(self):
        return self._center

    @Center.setter
    def Center(self, center):
        if isinstance(center, Part.Vertex):
            self._center = center.Point
        else:
            self._center = center

    def getCenter(self, profiles):
        center = FreeCAD.Vector()
        sh = profiles[0].Shape
        if len(profiles) == 1:
            warn("RotationSweep: Only 1 profile provided.\n")
            warn("Choosing center opposite to path.\n")
            dist, pts, info = self.path.distToShape(sh)
            par = profiles[0].Curve.parameter(pts[0][1])
            fp = sh.FirstParameter
            lp = sh.LastParameter
            if abs(par - fp) > abs(par - lp):
                center = sh.valueAt(fp)
            else:
                center = sh.valueAt(lp)
        else:
            for p in profiles[1:]:
                dist, pts, info = p.Shape.distToShape(sh)
                center += pts[0][1]
            center = center / (len(profiles) - 1)
        message(f"Center found at {center}\n")
        return center

    def add_profiles(self, prof):
        if isinstance(prof, (list, tuple)):
            for p in prof:
                self.add_profile(p)
            return
        dist, pts, info = self.path.distToShape(prof)
        par = self.path.Curve.parameter(pts[0][0])
        self.profiles.append(SweepProfile(prof, par))

    def loftProfiles(self):
        cl = [c.Curve for c in self.profiles]
        cts = CTS.CurvesToSurface(cl)
        cts.match_degrees()
        # self.auto_orient()
        # self.auto_twist()
        cts.normalize_knots()
        # CTS.match_knots(cts.curves)
        BSplineFacade.syncAllKnots(cts.curves, 1e-8)
        cts.Parameters = self.profile_parameters()
        cts.interpolate()
        # wl = [Part.Wire([c]) for c in self.profiles]
        # loft = Part.makeLoft(wl, False, False, self.closed, 3)
        s = cts._surface
        s.scaleKnotsToBounds()
        return s  # loft.Face1.Surface

    def ruledToCenter(self, curve, center):
        bs = Part.BSplineSurface()
        # poles = [[center] * curve.NbPoles, curve.getPoles()]
        poles = [curve.getPoles(), [center] * curve.NbPoles]
        bs.buildFromPolesMultsKnots(poles,
                                    [2, 2], curve.getMultiplicities(),
                                    [0.0, 1.0], curve.getKnots(),
                                    False, curve.isPeriodic(),
                                    1, curve.Degree)
        return bs

    def trim_profiles(self):
        center = self.Center
        # edges = []
        for i, prof in enumerate(self.profiles):
            message(f"Connecting curve #{i}\n")
            # c = prof.Curve
            contact_shapes(prof.Curve, self.path, Part.Vertex(center))
        #     edges.append(c.toShape())
        # self.profiles = edges

    def trim_path(self):
        # c = self.path.Curve
        contact_shapes(self.path.Curve, self.profiles[0], self.profiles[-1])
        # self.path = c.toShape()

    def compute(self):
        c = self.path.Curve
        # S1
        loft = self.loftProfiles()
        normalize([c, loft])
        BSplineFacade.syncDegree(c, [loft, 1])
        BSplineFacade.syncKnots(c, [loft, 1], 1e-7)
        # S2
        ruled = self.ruledToCenter(c, self.getCenter())
        BSplineFacade.syncDegree([ruled, 0], [loft, 0])
        BSplineFacade.insKnots([ruled, 0], [loft, 0], 1e-7)
        # S3
        pts_interp = CTS.U_linear_surface(loft)
        BSplineFacade.syncDegree([pts_interp, 0], [loft, 0])
        BSplineFacade.insKnots([pts_interp, 0], [loft, 0], 1e-7)
        # return loft, ruled, pts_interp
        gordon = CTS.Gordon(loft, ruled, pts_interp)
        return gordon.gordon()

    def prepare(self):
        if len(self.profiles) == 1:
            self.computeLocalProfiles()
            add_profs = []
            fp = self.path.FirstParameter
            lp = self.path.LastParameter
            if self.profiles[0].Parameter > fp:
                add_profs.append(self.profiles[0].duplicateAt(fp))
            if self.profiles[0].Parameter < lp:
                add_profs.append(self.profiles[0].duplicateAt(lp))
            self.profiles.extend(add_profs)
            self.interpolate_local_profiles()

    @property
    def Face(self):
        g = self.compute()
        return g.toShape()
        return Part.Compound([s.toShape() for s in g])


"""
import FreeCADGui

sel = FreeCADGui.Selection.getSelectionEx()
el = []
for so in sel:
    el.extend(so.SubObjects)

center = el[1].valueAt(el[1].FirstParameter)
rsp = RotationSweepPath(el[0], center)
rsp.add_profile(el[1:])
rsp.interpolate_local_profiles()

# Part.show(rsp.localLoft.toShape())

for i, p in enumerate(rsp.profiles[1:-1]):
    # Part.show(p.Shape)
    pass # Part.show(rsp.get_profile(p.Parameter).toShape())

profs = rsp.insert_profiles(8)
for p in profs:
    Part.show(p.toShape(), f"Profile@{p}")

"""


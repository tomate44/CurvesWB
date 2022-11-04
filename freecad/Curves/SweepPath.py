import FreeCAD
from FreeCAD import Vector
import Part
from freecad.Curves import curves_to_surface as CTS


DEBUG = False
err = FreeCAD.Console.PrintError
warn = FreeCAD.Console.PrintWarning
message = FreeCAD.Console.PrintMessage


def vec2str(vec):
    if isinstance(vec, (list, tuple)):
        if len(vec) == 0:
            return str(vec)
        strl = "["
        for v in vec:
            strl += vec2str(v)
            strl += ", "
        return strl[:-2] + "]"
    if isinstance(vec, FreeCAD.Vector):
        return f"Vec({vec.x:5.3f}, {vec.y:5.3f}, {vec.z:5.3f})"
    return f"{vec:5.3f}"


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
    if p1 > p2:
        curve.reverse()
        p1 = curve.parameter(pt1)
        p2 = curve.parameter(pt2)
        message("Curve reversed.\n")
    fp = curve.FirstParameter
    lp = curve.LastParameter
    if p1 == fp:
        curve.setPole(1, pt1)
        message("Forcing contact at start\n")
    if p2 == lp:
        curve.setPole(curve.NbPoles, pt2)
        message("Forcing contact at end\n")
    try:
        curve.segment(p1, p2)
        message(f"Segmenting curve to ({p1}, {p2})\n")
    except Part.OCCError:
        err(f"Failed to segment BSpline curve ({fp}, {lp})\n")
        err(f"between ({p1}, {p2})\n")
    curve.scaleKnotsToBounds()
    # return curve


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
        # print(knots)
        # print(mults)
        # print(BSplineFacade.getKnots(geom))
        # print(BSplineFacade.getMults(geom))
        if isinstance(geom, Part.BSplineCurve):
            # print(f"{geom.NbPoles} Poles")
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
        if hasattr(prof, "Curve") and hasattr(prof, "Parameter"):
            self.Curve = prof.Curve.copy()
            if par is None:
                self.Parameter = prof.Parameter
        elif hasattr(prof, "value"):
            self.Curve = prof.toBSpline()
        elif hasattr(prof, "Curve"):
            self.Curve = prof.Curve.toBSpline(prof.FirstParameter,
                                              prof.LastParameter)
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
        if (self._shape is None) and (self._curve is not None):
            self._shape = self._curve.toShape()
        return self._shape

    @property
    def Parameter(self):
        return self._param

    @Parameter.setter
    def Parameter(self, p):
        self._param = p

    def __repr__(self):
        return f"SweepProfile({self.Curve}) @ {self.Parameter}"

    def translate(self, offset):
        self._param += offset

    def move_to(self, par):
        self._param = par


class LocalProfile(SweepProfile):
    def __init__(self, prof=None, par=None):
        super().__init__(prof, par)

    def translate(self, offset):
        self._param += offset
        if self._curve is not None:
            self._curve.translate(FreeCAD.Vector(0, offset, 0))

    def move_to(self, par):
        self._param = par
        if self._curve is not None:
            self._curve.translate(FreeCAD.Vector(0, par - self._param, 0))


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

    def sort_profiles(self):
        self.profiles.sort(key=lambda x: x.Parameter)

    def profile_parameters(self):
        return [p.Parameter for p in self.profiles]

    def profile_curves(self):
        # if self.path.Curve.isPeriodic():
        #     return [p.Curve for p in self.profiles[:-1]]
        return [p.Curve for p in self.profiles]

    def transitionMatrixAt(self, par):
        """Path local CS"""
        poc = self.path.valueAt(par)
        tan = self.path.tangentAt(par)  # derivative1At(par)
        if self.FaceSupport is not None:
            u, v = self.FaceSupport.Surface.parameter(poc)
            snor = self.FaceSupport.Surface.normal(u, v)
            nor = snor.cross(tan)
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
        return LocalProfile(locprof, prof.Parameter)

    def add_profiles(self, prof):
        if isinstance(prof, (list, tuple)):
            for p in prof:
                self.add_profiles(p)
            return
        lp = self.computeLocalProfile(prof)
        self.profiles.append(lp)

    def offset_profile(self, prof, par):
        sp = LocalProfile(prof)
        sp.translate(par)
        print(f"Inserting local profile @ {sp.Parameter}")
        self.profiles.append(sp)

    def extend(self, periodic=False):
        """Add end profiles outside of the path range
        in case some extrapolation is needed
        """
        u0, u1 = self.path.ParameterRange
        path_range = u1 - u0
        if periodic:
            path_range = -path_range
            profs = self.profiles[:]
            for p in profs:
                self.offset_profile(p, -path_range)
                self.offset_profile(p, path_range)
        else:
            fp = self.profiles[0]
            lp = self.profiles[-1]
            for i in range(1, 4):
                self.offset_profile(fp, -i * path_range)
                self.offset_profile(lp, i * path_range)
        self.sort_profiles()
        self.interpolate_local_profiles()

    def interpolate_local_profiles(self):
        self.sort_profiles()
        # self.prepare()
        locprofs = self.profile_curves()
        # print(locprofs)
        cts = CTS.CurvesToSurface(locprofs)
        cts.match_curves(1e-7)
        cts.Parameters = self.profile_parameters()
        cts.interpolate()
        self.localLoft = cts._surface
        u0, u1 = self.localLoft.bounds()[0:2]
        # print(u0, u1, self.profiles[0].Parameter,self.profiles[-1].Parameter)
        self.localLoft.scaleKnotsToBounds(u0, u1, self.profiles[0].Parameter,
                                          self.profiles[-1].Parameter)
        print(f"interpolate_local_profiles {cts.Parameters} -> ")
        print(self.localLoft.getVKnots())
        return self.localLoft

    def profileAt(self, par, tol=1e-7):
        # print(f"extracting profile @ {par}")
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
        # print(f"profileAt({par}) = {locprof}")
        return SweepProfile(locprof, par)


class RotationPathInterpolation(PathInterpolation):
    def __init__(self, path, profiles, center):
        self.Center = center
        super().__init__(path, profiles)

    def transitionMatrixAt(self, par, stretch=True):
        # message(f"RotationPath matrix at {par}\n")
        poc = self.path.valueAt(par)
        cho = self.Center - poc
        der = self.path.tangentAt(par)  # * cho.Length  # derivative1At(par)
        if not stretch:
            der.multiply(cho.Length)
        if self.FaceSupport is not None:
            # print(self.FaceSupport)
            u, v = self.FaceSupport.Surface.parameter(poc)
            snor = self.FaceSupport.Surface.normal(u, v)
            nor = snor.cross(der)
        else:
            nor = der.cross(cho)
        nor.normalize()
        if not stretch:
            nor.multiply(cho.Length)
        m = FreeCAD.Matrix(cho.x, der.x, nor.x, poc.x,
                           cho.y, der.y, nor.y, poc.y,
                           cho.z, der.z, nor.z, poc.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        return m


class RotationSweep:
    def __init__(self, path, profiles, trim=True):
        message("\n---------- RotationSweep ----------\n")
        self.FaceSupport = None
        self.profiles = []
        self.interpolator = None
        self.tol = 1e-7

        self.TrimPath = trim
        if len(profiles) == 1:
            self.TrimPath = False
            message("TrimPath disabled, needs at least 2 profiles\n")

        if self.TrimPath:
            self.path = path
            self.trim_path(profiles)
        else:
            c = path.Curve.toBSpline(path.FirstParameter, path.LastParameter)
            c.scaleKnotsToBounds()
            self.path = c.toShape()

        self.Center = self.getCenter(path, profiles)
        self.add_profiles(profiles)
        self.sort_profiles()
        if not self.TrimPath:
            self.extend(self.path.isClosed())

    @property
    def Center(self):
        return self._center

    @Center.setter
    def Center(self, center):
        if isinstance(center, Part.Vertex):
            self._center = center.Point
        else:
            self._center = center

    def getCenter(self, path, profiles):
        center = FreeCAD.Vector()
        sh = profiles[0]
        if len(profiles) == 1:
            warn("RotationSweep: Only 1 profile provided.\n")
            warn("Choosing center point opposite to path.\n")
            dist, pts, info = path.distToShape(sh)
            par = profiles[0].Curve.parameter(pts[0][1])
            fp = sh.FirstParameter
            lp = sh.LastParameter
            if abs(par - fp) > abs(par - lp):
                center = sh.valueAt(fp)
            else:
                center = sh.valueAt(lp)
        else:
            for p in profiles[1:]:
                dist, pts, info = p.distToShape(sh)
                center += pts[0][1]
            center = center / (len(profiles) - 1)
        message(f"Center found at {vec2str(center)}\n")
        return center

    def add_profiles(self, prof):
        if isinstance(prof, (list, tuple)):
            for p in prof:
                self.add_profiles(p)
            return
        dist, pts, info = self.path.distToShape(prof)
        par = self.path.Curve.parameter(pts[0][0])
        print(info)
        message(f"Adding profile @ {vec2str(par)}\n")
        c = prof.Curve
        print(c.length())
        contact_shapes(c, self.path, Part.Vertex(self.Center))
        print(c.length())
        self.profiles.append(SweepProfile(c, par))

    # def trim_profiles(self, profs=None):
    #     if profs is None:
    #         profs = self.profiles
    #
    #     for i in range(len(profs)):
    #         message(f"Connecting curve #{i}\n")
    #         c = profs[i].Curve
    #         contact_shapes(c, self.path, Part.Vertex(self.Center))
    #         profs[i] = c.toShape()

    def trim_path(self, profiles=None):
        if profiles is None:
            profiles = [p.Shape for p in self.profiles]
        params = []
        for prof in profiles:
            dist, pts, info = self.path.distToShape(prof)
            par = self.path.Curve.parameter(pts[0][0])
            params.append(par)
        c = self.path.Curve
        # contact_shapes(c, min(params), max(params))
        c.segment(min(params), max(params))
        c.scaleKnotsToBounds()
        self.path = c.toShape()

    def sort_profiles(self):
        self.profiles.sort(key=lambda x: x.Parameter)

    def profile_parameters(self):
        # print(self.profiles)
        params = [p.Parameter for p in self.profiles]
        if not self.TrimPath and self.path.Curve.isPeriodic():
            params.append(self.profiles[0].Parameter + self.path.Curve.period())
        return params

    def loftProfiles(self):
        # print(self.profile_parameters())
        cl = [c.Curve for c in self.profiles]
        cts = CTS.CurvesToSurface(cl)
        cts.Periodic = self.path.Curve.isPeriodic()
        # cts.match_degrees()
        # cts.normalize_knots()
        # BSplineFacade.syncAllKnots(cts.curves, 1e-7)
        cts.match_curves(1e-7)
        cts.Parameters = self.profile_parameters()
        message(f"loftProfiles : {vec2str(cts.Parameters)}\n")
        cts.interpolate()
        s = cts._surface
        s.scaleKnotsToBounds()
        return s

    def ruledToCenter(self, curve, center):
        bs = Part.BSplineSurface()
        poles = [curve.getPoles(), [center] * curve.NbPoles]
        bs.buildFromPolesMultsKnots(poles,
                                    [2, 2], curve.getMultiplicities(),
                                    [0.0, 1.0], curve.getKnots(),
                                    False, curve.isPeriodic(),
                                    1, curve.Degree)
        return bs

    def compute(self):
        print("RotationSweep.compute")
        self.sort_profiles()
        # for p in self.profiles:
        #     print(p)
        c = self.path.Curve
        # S1
        loft = self.loftProfiles()
        normalize([c, loft])
        if self.path.Curve.isPeriodic():
            loft.setVPeriodic()
        BSplineFacade.syncDegree(c, [loft, 1])
        BSplineFacade.syncKnots(c, [loft, 1], 1e-7)
        # S2
        ruled = self.ruledToCenter(c, self.Center)
        BSplineFacade.syncDegree([ruled, 0], [loft, 0])
        BSplineFacade.insKnots([ruled, 0], [loft, 0], 1e-7)
        # S3
        pts_interp = CTS.U_linear_surface(loft)
        BSplineFacade.syncDegree([pts_interp, 0], [loft, 0])
        BSplineFacade.insKnots([pts_interp, 0], [loft, 0], 1e-7)
        if DEBUG:
            return loft, ruled, pts_interp
        gordon = CTS.Gordon(loft, ruled, pts_interp)
        return gordon.gordon()

    def extend(self, periodic=False):
        profs = [SweepProfile(p.Curve, p.Parameter) for p in self.profiles]
        self.interpolator = RotationPathInterpolation(self.path,
                                                      profs,
                                                      self.Center)
        self.interpolator.FaceSupport = self.FaceSupport
        self.interpolator.extend(periodic)
        if self.path.FirstParameter < min(self.profile_parameters()):
            fp = self.interpolator.profileAt(self.path.FirstParameter)
            self.profiles.insert(0, fp)
        if self.path.LastParameter > max(self.profile_parameters()):
            # if not self.path.Curve.isPeriodic():
            lp = self.interpolator.profileAt(self.path.LastParameter)
            self.profiles.append(lp)

    def insert_profiles(self, num=0):
        if num < 1:
            return
        params = self.profile_parameters()
        print(f"Insert Profiles in {vec2str(params)}")
        if self.interpolator is None:
            profs = [SweepProfile(p.Curve, p.Parameter) for p in self.profiles]
            self.interpolator = RotationPathInterpolation(self.path,
                                                          profs,
                                                          self.Center)
            self.interpolator.FaceSupport = self.FaceSupport
        path_range = self.path.LastParameter - self.path.FirstParameter
        step = path_range / (num + 1)
        profs = []
        count = 1
        for i in range(len(params) - 1):
            lrange = params[i + 1] - params[i]
            nb = int(lrange / step)
            lstep = lrange / (nb + 1)
            for j in range(nb):
                par = params[i] + (j + 1) * lstep
                print(f"Insert profile #{count} @ {vec2str(par)}")
                count += 1
                intpro = self.interpolator.profileAt(par)
                contact_shapes(intpro.Curve, self.path, Part.Vertex(self.Center))
                profs.append(intpro)
                # print(profs[-1].Curve.getPoles())
        self.profiles.extend(profs)

    @property
    def Face(self):
        g = self.compute()
        if DEBUG:
            return Part.Compound([s.toShape() for s in g] + [c.Shape for c in self.profiles])
        return g.toShape()


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


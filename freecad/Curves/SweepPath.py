# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part
from freecad.Curves import curves_to_surface as CTS


DEBUG = False
err = FreeCAD.Console.PrintError
warn = FreeCAD.Console.PrintWarning
message = FreeCAD.Console.PrintMessage


def debug(*args):
    if DEBUG:
        for a in args:
            message(str(a) + "\n")


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
                try:
                    geom[0].insertUKnots(knots, mults, tol, add)
                except Part.OCCError:
                    err(f"Failed to insert UKnots {knots}\n{mults}\n")
                    err(f"into {geom[0].getUKnots()} - {geom[0].getUMultiplicities()}\n")
            elif geom[1] == 1:
                try:
                    geom[0].insertVKnots(knots, mults, tol, add)
                except Part.OCCError:
                    err(f"Failed to insert VKnots {knots}\n{mults}\n")
                    err(f"into {geom[0].getVKnots()} - {geom[0].getVMultiplicities()}\n")
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
        return f"SweepProfile(@ {vec2str(self.Parameter)})"

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


class Sweep:
    """Sweeps some profiles along a path,
    using the Gordon surface algorithm.
    """

    def __init__(self, path, profiles=[], trim=True):
        self.Tol2D = 1e-6  # Mainly for knot insertion
        self.Tol3D = 1e-7
        c = path.Curve.toBSpline(path.FirstParameter, path.LastParameter)
        if c.isClosed() and not c.isPeriodic():
            c.setPeriodic()
        self.Path = c.toShape()
        self.TrimPath = trim
        self.Profiles = [SweepProfile(p) for p in profiles]

    def trim_path(self, profiles=None):
        debug(f"Sweep.trim_path({self.TrimPath})")
        c = self.Path.Curve
        if profiles is None:
            profiles = [p.Shape for p in self.Profiles]
        if self.TrimPath and len(profiles) > 1:
            params = []
            for prof in profiles:
                dist, pts, info = self.Path.distToShape(prof)
                par = self.Path.Curve.parameter(pts[0][0])
                params.append(par)
            c.segment(min(params), max(params))
        c.scaleKnotsToBounds()
        c.setKnot(1, 0.0)
        c.setKnot(c.NbKnots, 1.0)
        self.Path = c.toShape()
        debug(f"path ParameterRange({self.Path.ParameterRange})")

    def trim_profiles(self):
        debug("Sweep.trim_profiles()")
        for i, prof in enumerate(self.Profiles):
            c = prof.Curve
            dist, pts, info = prof.Shape.distToShape(self.Path)
            par = c.parameter(pts[0][0])
            if abs(par - c.FirstParameter) >= abs(par - c.LastParameter):
                c.segment(c.FirstParameter, par)
            else:
                c.segment(par, c.LastParameter)
                c.reverse()
            c.scaleKnotsToBounds()
            npar = self.Path.Curve.parameter(pts[0][1])
            prof.Curve = c
            prof.Parameter = npar
            debug(f"Sweep.trim_profiles #{i} @{npar}")

    def sort_profiles(self):
        self.Profiles.sort(key=lambda x: x.Parameter)

    def profile_parameters(self):
        # print(self.profiles)
        params = [p.Parameter for p in self.Profiles]
        if self.Path.Curve.isPeriodic():
            params.append(self.Profiles[0].Parameter + self.Path.Curve.period())
        return params

    def loftProfiles(self):
        cl = [c.Curve for c in self.Profiles]
        debug(f"{cl}\n")
        cts = CTS.CurvesToSurface(cl, self.Tol2D, self.Tol3D)
        cts.Periodic = self.Path.Curve.isPeriodic()
        cts.match_curves()
        cts.Parameters = self.profile_parameters()
        debug(f"loftProfiles : {vec2str(cts.Parameters)}")
        cts.interpolate()
        s = cts._surface
        s.scaleKnotsToBounds()
        return s

    def compute_S1(self):
        loft = self.loftProfiles()
        c = self.Path.Curve
        if c.isPeriodic():
            loft.setVPeriodic()
        BSplineFacade.syncDegree(c, [loft, 1])
        BSplineFacade.syncKnots(c, [loft, 1], self.Tol2D)
        self.Path = c.toShape()
        return loft

    def compute_S2(self):
        debug("Sweep.compute_S2()")
        pts = [p.Curve.value(p.Curve.FirstParameter) for p in self.Profiles]
        bc = Part.BSplineCurve()
        kwargs = {"Points": pts,
                  "PeriodicFlag": self.Path.Curve.isPeriodic(),
                  "Parameters": self.profile_parameters(),
                  "Tolerance": self.Tol3D}
        bc.interpolate(**kwargs)
        ruled = Part.makeRuledSurface(bc.toShape(), self.Path)
        surf = ruled.Face1.Surface
        surf.exchangeUV()
        BSplineFacade.syncDegree([surf, 0], [self.S1, 0])
        BSplineFacade.insKnots([surf, 0], [self.S1, 0], self.Tol2D)
        return surf

    def compute_S3(self):
        pts_interp = CTS.U_linear_surface(self.S1)
        BSplineFacade.syncDegree([pts_interp, 0], [self.S1, 0])
        BSplineFacade.insKnots([pts_interp, 0], [self.S1, 0], self.Tol2D)
        return pts_interp

    def set_curves(self):
        self.trim_path()
        self.trim_profiles()
        self.sort_profiles()
        debug(f"Profiles are ready :\n{self.Profiles}\n")

    def compute(self):
        debug("Sweep.compute")
        self.sort_profiles()
        self.S1 = self.compute_S1()
        self.S2 = self.compute_S2()
        self.S3 = self.compute_S3()
        return self.S1, self.S2, self.S3

    def get_surface(self):
        self.compute()
        gordon = CTS.Gordon(self.S1, self.S2, self.S3)
        return gordon.gordon()

    @property
    def Face(self):
        if DEBUG:
            g = self.compute()
            return Part.Compound([s.toShape() for s in g] + [c.Shape for c in self.Profiles])
        s = self.get_surface()
        return s.toShape()


class RotationSweep(Sweep):
    """Sweeps some profiles along a path,
    rotating around a center point.
    """

    def __init__(self, path, profiles=[], trim=True, center=None):
        super().__init__(path, profiles, trim)
        if center is None:
            self.Center = self.getCenter()
        else:
            self.Center = center

    def getCenter(self):
        center = FreeCAD.Vector()
        sh = self.Profiles[0].Shape
        if len(self.Profiles) == 1:
            debug("RotationSweep: Only 1 profile provided.\n")
            debug("Choosing center point opposite to path.\n")
            dist, pts, info = self.Path.distToShape(sh)
            par = self.Profiles[0].Curve.parameter(pts[0][1])
            fp = sh.FirstParameter
            lp = sh.LastParameter
            if abs(par - fp) > abs(par - lp):
                center = sh.valueAt(fp)
            else:
                center = sh.valueAt(lp)
        else:
            for p in self.Profiles[1:]:
                dist, pts, info = p.Shape.distToShape(sh)
                center += pts[0][1]
            center = center / (len(self.Profiles) - 1)
        debug(f"Center found at {vec2str(center)}\n")
        return center

    def trim_profiles(self):
        debug("RotationSweep.trim_profiles()")
        # super().trim_profiles()
        cv = Part.Vertex(self.Center)
        for prof in self.Profiles:
            c = prof.Curve
            dist1, pts1, info1 = prof.Shape.distToShape(cv)
            dist2, pts2, info2 = prof.Shape.distToShape(self.Path)
            par1 = c.parameter(pts1[0][0])
            par2 = c.parameter(pts2[0][0])
            if par1 > par2:
                c.segment(par2, par1)
                c.reverse()
            elif par1 < par2:
                c.segment(par1, par2)
            c.scaleKnotsToBounds()
            npar = self.Path.Curve.parameter(pts2[0][1])
            prof.Curve = c
            prof.Parameter = npar
            debug(f"{prof}\n")

    def compute_S2(self):
        debug("SweepAround.compute_S2()")
        bs = Part.BSplineSurface()
        curve = self.Path.Curve
        poles = [[self.Center] * curve.NbPoles, curve.getPoles()]
        weights = [curve.getWeights(), curve.getWeights()]
        bs.buildFromPolesMultsKnots(poles,
                                    [2, 2], curve.getMultiplicities(),
                                    [0.0, 1.0], curve.getKnots(),
                                    False, curve.isPeriodic(),
                                    1, curve.Degree, weights)
        BSplineFacade.syncDegree([bs, 0], [self.S1, 0])
        BSplineFacade.insKnots([bs, 0], [self.S1, 0], self.Tol2D)
        return bs


class SweepInterpolator:
    def __init__(self, sweep, extend=True, extra=0):
        self.Sweep = sweep
        self.Extend = extend
        self.NumExtra = extra
        self.FaceSupport = None
        self.localLoft = None
        self.TopNormal = None

    def valueAt(self, par):
        return self.Sweep.Path.valueAt(par)

    def tangentAt(self, par):
        return self.Sweep.Path.tangentAt(par)

    def normalAt(self, par):
        if isinstance(self.FaceSupport, Part.Face):
            u, v = self.FaceSupport.Surface.parameter(self.valueAt(par))
            snor = self.FaceSupport.Surface.normal(u, v)
            return snor.cross(self.tangentAt(par))
        else:
            return self.Sweep.Path.normalAt(par)

    def binormalAt(self, par):
        return self.normalAt(par).cross(self.tangentAt(par))

    def transitionMatrixAt(self, par):
        """Path local CS"""
        poc = self.valueAt(par)
        bno = self.binormalAt(par)
        tan = self.tangentAt(par)
        nor = self.normalAt(par)
        m = FreeCAD.Matrix(bno.x, tan.x, nor.x, poc.x,
                           bno.y, tan.y, nor.y, poc.y,
                           bno.z, tan.z, nor.z, poc.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        return m

    def sort_profiles(self):
        self.LocalProfiles.sort(key=lambda x: x.Parameter)

    def profile_parameters(self):
        return [p.Parameter for p in self.LocalProfiles]

    def profile_curves(self):
        return [p.Curve for p in self.LocalProfiles]

    def computeLocalProfiles(self):
        locprofs = []
        for prof in self.Sweep.Profiles:
            # print(prof.Parameter)
            m = self.transitionMatrixAt(prof.Parameter)
            m = m.inverse()
            locprof = prof.Curve.copy()
            for i in range(locprof.NbPoles):
                pole = locprof.getPole(i + 1)
                np = m.multVec(pole)
                locprof.setPole(i + 1, np)
            locprof.translate(FreeCAD.Vector(0, prof.Parameter, 0))
            locprofs.append(LocalProfile(locprof, prof.Parameter))
        self.LocalProfiles = locprofs

    def offset_profile(self, prof, par):
        sp = LocalProfile(prof)
        sp.translate(par)
        debug(f"Inserting local profile @ {sp.Parameter}")
        self.LocalProfiles.append(sp)

    def interpolate_local_profiles(self):
        self.sort_profiles()
        locprofs = self.profile_curves()
        cts = CTS.CurvesToSurface(locprofs, self.Sweep.Tol2D, self.Sweep.Tol3D)
        cts.match_curves()
        cts.Parameters = self.profile_parameters()
        cts.interpolate()
        self.localLoft = cts._surface
        u0, u1 = self.localLoft.bounds()[0:2]
        # print(u0, u1, self.profiles[0].Parameter,self.profiles[-1].Parameter)
        self.localLoft.scaleKnotsToBounds(u0, u1, self.LocalProfiles[0].Parameter,
                                          self.LocalProfiles[-1].Parameter)
        debug(f"interpolate_local_profiles @ {cts.Parameters}")
        # print(self.localLoft.getVKnots())
        return self.localLoft

    def profileAt(self, par):
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
        if self.TopNormal:
            pl = Part.Plane(locprof.getPole(1), self.TopNormal)
            pt = pl.projectPoint(locprof.getPole(2))
            locprof.setPole(2, pt)
        return SweepProfile(locprof, par)

    def extend(self, periodic=False):
        """Add end profiles outside of the path range
        in case some extrapolation is needed
        """
        if not self.Extend:
            return
        u0, u1 = self.Sweep.Path.ParameterRange
        path_range = u1 - u0
        params = self.profile_parameters()
        minpar = min(params)
        maxpar = max(params)
        if periodic:
            path_range = -path_range
            profs = self.LocalProfiles[:]
            for p in profs:
                self.offset_profile(p, -path_range)
                self.offset_profile(p, path_range)
        else:
            fp = self.LocalProfiles[0]
            lp = self.LocalProfiles[-1]
            for i in range(1, 4):
                self.offset_profile(fp, -i * path_range)
                self.offset_profile(lp, i * path_range)
        self.sort_profiles()
        self.interpolate_local_profiles()
        if u0 < minpar:
            fp = self.profileAt(u0)
            self.Sweep.Profiles.insert(0, fp)
            debug(f"inserting start profile @ {fp.Parameter}")
        if (u1 > maxpar) and (not self.Sweep.Path.Curve.isPeriodic()):
            lp = self.profileAt(u1)
            self.Sweep.Profiles.append(lp)
            debug(f"inserting end profile @ {lp.Parameter}")

    def addExtra(self):
        if self.NumExtra < 1:
            return
        params = self.Sweep.profile_parameters()
        debug(f"Insert {self.NumExtra} Profiles in {vec2str(params)}")
        u0, u1 = self.Sweep.Path.ParameterRange
        path_range = u1 - u0
        step = path_range / (self.NumExtra + 1)
        profs = []
        count = 1
        for i in range(len(params) - 1):
            lrange = params[i + 1] - params[i]
            nb = int(lrange / step)
            lstep = lrange / (nb + 1)
            for j in range(nb):
                par = params[i] + (j + 1) * lstep
                debug(f"Insert profile #{count} @ {vec2str(par)}")
                count += 1
                intpro = self.profileAt(par)
                profs.append(intpro)
        self.Sweep.Profiles.extend(profs)

    def compute(self):
        self.computeLocalProfiles()
        self.extend()
        self.addExtra()


class SweepAroundInterpolator(SweepInterpolator):
    def __init__(self, sweepAround, extend=False, extra=0):
        super().__init__(sweepAround, extend, extra)

    def normalAt(self, par):
        # if isinstance(self.TopNormal, FreeCAD.Vector):
        #     return self.TopNormal  # * chord.Length
        if isinstance(self.FaceSupport, Part.Face):
            u, v = self.FaceSupport.Surface.parameter(self.valueAt(par))
            snor = self.FaceSupport.Surface.normal(u, v)
            return snor.cross(self.tangentAt(par))  # * chord.Length
        else:
            return self.tangentAt(par).cross(self.binormalAt(par))

    def binormalAt(self, par):
        return self.Sweep.Center - self.valueAt(par)

    def setSmoothTop(self, idx=None):
        if idx is not None and idx < len(self.Sweep.Profiles):
            p = self.Sweep.Profiles[idx]
            ct = p.Curve.tangent(p.Curve.FirstParameter)[0]
            self.TopNormal = ct.cross(self.tangentAt(p.Parameter))
            return
        v = FreeCAD.Vector()
        for p in self.Sweep.Profiles:
            ct = p.Curve.tangent(p.Curve.FirstParameter)[0]
            v += ct.cross(self.tangentAt(p.Parameter))
        self.TopNormal = v / len(self.Sweep.Profiles)



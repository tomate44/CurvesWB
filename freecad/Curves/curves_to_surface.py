# -*- coding: utf-8 -*-

__title__ = "Curves to Surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Interpolate curves to surface"

import FreeCAD
import Part


PrintError = FreeCAD.Console.PrintError


class SurfaceAdapter:
    """Adapter to work on one direction of a BSpline surface
    with BSpline curve tools"""

    def __init__(self, surf, direction=0):
        self.surface = surf
        self.direction = direction

    @property
    def NbKnots(self):
        if self.direction == 0:
            return self.surface.NbUKnots
        elif self.direction == 1:
            return self.surface.NbVKnots

    def getKnot(self, idx):
        if self.direction == 0:
            return self.surface.getUKnot(idx)
        elif self.direction == 1:
            return self.surface.getVKnot(idx)

    def getMultiplicity(self, idx):
        if self.direction == 0:
            return self.surface.getUMultiplicity(idx)
        elif self.direction == 1:
            return self.surface.getVMultiplicity(idx)

    def increaseMultiplicity(self, idx, mult):
        if self.direction == 0:
            return self.surface.increaseUMultiplicity(idx, mult)
        elif self.direction == 1:
            return self.surface.increaseVMultiplicity(idx, mult)

    def insertKnot(self, k, mult, tol=0.0):
        if self.direction == 0:
            return self.surface.insertUKnot(k, mult, tol)
        elif self.direction == 1:
            return self.surface.insertVKnot(k, mult, tol)


def _find_knot(curve, knot, tolerance=1e-15):
    for i in range(1, curve.NbKnots + 1):
        if abs(knot - curve.getKnot(i)) < tolerance:
            return i
    return -1


def match_knots(curves, tolerance=1e-15):
    "Set the knot sequence of each curve to a common one"
    first = curves[0]
    for cur_idx in range(1, len(curves)):
        for kno_idx in range(1, curves[cur_idx].NbKnots + 1):
            k = curves[cur_idx].getKnot(kno_idx)
            mult = curves[cur_idx].getMultiplicity(kno_idx)
            fk = _find_knot(first, k, tolerance)
            if fk > -1:
                om = first.getMultiplicity(fk)
                if om < mult:
                    first.increaseMultiplicity(fk, mult)
                    print("Increased mult of knot # {} from {} to {}".format(fk, om, mult))
            else:
                first.insertKnot(k, mult)
                print("Inserting knot {} mult {}".format(k, mult))
    for cur_idx in range(1, len(curves)):
        for kno_idx in range(1, first.NbKnots + 1):
            k = first.getKnot(kno_idx)
            mult = first.getMultiplicity(kno_idx)
            fk = _find_knot(curves[cur_idx], k, tolerance)
            if fk > -1:
                curves[cur_idx].increaseMultiplicity(fk, mult)
            else:
                curves[cur_idx].insertKnot(k, mult)


def U_linear_surface(surf):
    "Returns a copy of surf that is linear in the U direction"
    poles = [surf.getPoles()[0], surf.getPoles()[-1]]
    bs = Part.BSplineSurface()
    bs.buildFromPolesMultsKnots(poles,
                                [2, 2], surf.getVMultiplicities(),
                                [0, 1], surf.getVKnots(),
                                False, surf.isVPeriodic(),
                                1, surf.VDegree)
    return bs


def print_main_poles(surf):
    pts = surf.getPoles()
    print("O: {}\nU: {}\nV: {}".format(pts[0][0],
                                       pts[-1][0],
                                       pts[0][-1]))


def orient_curves(c1, c2):
    """orient_curves(c1, c2)
    Orient c2 in same direction as c1 """
    def value(c, p):
        if isinstance(c, Part.Edge):
            return c.valueAt(p)
        else:
            return c.value(p)

    def test_params(c1):
        if c1.isClosed():
            fp1 = 0.75 * c1.FirstParameter + 0.25 * c1.LastParameter
            lp1 = 0.25 * c1.FirstParameter + 0.75 * c1.LastParameter
        else:
            fp1 = c1.FirstParameter
            lp1 = c1.LastParameter
        return fp1, lp1

    def line(c1, par1, c2, par2):
        p1 = value(c1, par1)
        p2 = value(c2, par2)
        if p1.distanceToPoint(p2) < 1e-7:
            return Part.Vertex(p1)
        return Part.makeLine(p1, p2)

    if isinstance(c1, FreeCAD.Vector) or isinstance(c2, FreeCAD.Vector):
        return False
    if c1.length() < 1e-7 or c2.length() < 1e-7:
        return False

    fp1, lp1 = test_params(c1)
    fp2, lp2 = test_params(c2)
    ls1 = line(c1, fp1, c2, fp2)
    ls2 = line(c1, lp1, c2, lp2)
    d1 = ls1.distToShape(ls2)[0]
    ls1 = line(c1, fp1, c2, lp2)
    ls2 = line(c1, lp1, c2, fp2)
    d2 = ls1.distToShape(ls2)[0]
    if d1 < d2:
        c2.reverse()
        return True


def shift_origin(c1, c2, num=36):
    """if c1 and c2 are two periodic BSpline curves
    c2 origin will be moved to minimize twist"""
    pts1 = c1.discretize(num)
    pts2 = c2.discretize(num)
    pts2 *= 2
    min_dist = 1e50
    good_offset = 0
    for offset_idx in range(num):
        total_length = 0
        for pt_idx in range(num):
            ls = Part.makeLine(pts1[pt_idx], pts2[pt_idx + offset_idx])
            total_length += ls.Length
        if total_length < min_dist:
            min_dist = total_length
            good_offset = offset_idx
    knot = c2.parameter(pts2[good_offset])
    c2.insertKnot(knot, 1)
    fk = _find_knot(c2, knot, 1e-15)
    if fk > -1:
        c2.setOrigin(fk)
    else:
        print("shift_origin: failed to insert knot")


def ruled_surface(e1, e2, normalize=False, autotwist=0):
    """creates a ruled surface between 2 edges, with automatic orientation.
    If normalize is True, the surface will be normalized in U direction
    If curves are closed and autotwist is True,
    origin of edge e2 will be moved to minimize twist"""
    c1 = e1.Curve.toBSpline()
    c2 = e2.Curve.toBSpline()
    orient_curves(c1, c2)
    if c1.isClosed and c2.isClosed and autotwist:
        shift_origin(c1, c2, autotwist)
    if normalize:
        kl = c1.getKnots()
        normalized_knots = [(k - kl[0]) / (kl[-1] - kl[0]) for k in kl]
        c1.setKnots(normalized_knots)
        kl = c2.getKnots()
        normalized_knots = [(k - kl[0]) / (kl[-1] - kl[0]) for k in kl]
        c2.setKnots(normalized_knots)
    return Part.makeRuledSurface(c1.toShape(), c2.toShape())


class CurvesToSurface:
    def __init__(self, curves):
        self.curves = self._convert_to_bsplines(curves)
        self._periodic = False
        self._params = None
        self._surface = None
        self.all_closed = None
        self.force_periodic_if_closed = True

    @property
    def Periodic(self):
        "Periodicity in the lofting direction"
        return self._periodic

    @Periodic.setter
    def Periodic(self, p):
        if self._periodic is not bool(p):
            self._periodic = bool(p)
            if self._params is not None:
                print("Periodicity changed. You must recompute parameters.")

    @property
    def Parameters(self):
        "List of interpolating parameters of the curves"
        return self._params

    @Parameters.setter
    def Parameters(self, par):
        if isinstance(par, (list, tuple)):
            pf = 0
            if self._periodic:
                pf = 1
            if len(par) == len(self.curves) + pf:
                self._params = par
            else:
                print("Wrong number of parameters")
                print(f"Periodic = {self._periodic}")
                print(len(par))
                print(len(self.curves))

    @property
    def Surface(self):
        "Builds and returns the loft surface"
        self.build_surface()
        return self._surface

    @property
    def Face(self):
        "Builds and returns the loft face"
        return self.Surface.toShape()

    def _convert_to_bsplines(self, curves):
        nc = []
        for c in curves:
            if isinstance(c, Part.Edge):
                nc.append(c.Curve.toBSpline())
            elif isinstance(c, Part.Wire):
                nc.append(c.approximate())
            else:
                nc.append(c.toBSpline())
        return nc

    def _print_curves(self):
        print([c.Degree for c in self.curves])
        for c in self.curves:
            print(c.getKnots())
        for c in self.curves:
            print(c.getMultiplicities())

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, len(self.curves))

    def repeated_points(self, pts, tol=1e-7):
        d = 0
        for i in range(len(pts) - 1):
            d += pts[i].distanceToPoint(pts[i + 1])
        if d < tol * len(pts):
            return True
        return False

    def check_all_closed(self):
        self.all_closed = True
        for c in self.curves:
            if not c.isClosed():
                self.all_closed = False
        if self.all_closed and self.force_periodic_if_closed:
            for c in self.curves:
                if not c.isPeriodic():
                    c.setPeriodic()
                    print("Forcing periodic : {}".format(c.isPeriodic()))
                else:
                    print("Already periodic")

    def auto_orient(self):
        "Automatically match curves orientation"
        for i in range(1, len(self.curves)):
            if orient_curves(self.curves[i - 1], self.curves[i]):
                print("Reversed curve #{}".format(i))

    def auto_twist(self, num=36):
        """When all the curves are closed, auto_twist will eventually
        move the origin of the curves[1:] to minimize twist.
        num is the number of test points on each curve"""
        if self.all_closed is None:
            self.check_all_closed()
        if self.all_closed is False:
            return
        for cur_idx in range(1, len(self.curves)):
            shift_origin(self.curves[cur_idx - 1], self.curves[cur_idx], num)

    def match_degrees(self):
        "Match all curve degrees to the highest one"
        max_degree = 0
        for c in self.curves:
            max_degree = max(max_degree, c.Degree)
        for c in self.curves:
            c.increaseDegree(max_degree)

    def normalize_knots(self):
        "Set all curves knots to the [0,1] interval"
        for c in self.curves:
            c.scaleKnotsToBounds()

    def match_knots(self, tol=1e-15):
        self.normalize_knots()
        for c in self.curves[1:]:
            self.curves[0].insertKnots(c.getKnots(), c.getMultiplicities(), tol, False)
        for c in self.curves[1:]:
            c.insertKnots(self.curves[0].getKnots(), self.curves[0].getMultiplicities(), tol, False)

    def match_curves(self, tol=1e-15):
        self.match_degrees()
        self.normalize_knots()
        self.match_knots(tol)

    def _parameters_at_poleidx(self, fac=1.0, idx=1):
        """Compute the parameters list from parametrization factor fac (in [0.0, 1.0])
        with pole #idx of each curve"""
        if idx < 1:
            idx = 1
        elif idx > self.curves[0].NbPoles:
            idx = self.curves[0].NbPoles
        pts = [c.getPole(idx) for c in self.curves]
        if self.Periodic and pts[0].distanceToPoint(pts[-1]) > 1e-7:  # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0.0]
        for i in range(1, len(pts)):
            p = pts[i] - pts[i - 1]
            pl = pow(p.Length, fac)
            params.append(params[-1] + pl)
        if params[-1] < 1e-7:
            return False
        return [p / params[-1] for p in params]

    def set_parameters(self, fac=1.0):
        "Compute an average parameters list from parametrization factor in [0.0, 1.0]"
        params_array = []
        for pole_idx in range(1, self.curves[0].NbPoles + 1):
            params = self._parameters_at_poleidx(fac, pole_idx)
            if params:
                params_array.append(params)
        params = []
        for idx in range(len(params_array[0])):
            pl = [params_array[i][idx] for i in range(len(params_array))]
            params.append(sum(pl) / len(pl))
        # print("Average parameters : {}".format(params))
        self.Parameters = params

    def interpolate_multipoints(self, pts):
        fpts = []
        for i in range(len(pts)):
            fpts.append(FreeCAD.Vector(i, 0, 0))
        bs = Part.BSplineCurve()
        bs.interpolate(Points=fpts, Parameters=self.Parameters, PeriodicFlag=self.Periodic)
        return [pts[0]] * bs.NbPoles

    def interpolate(self):
        "interpolate the poles of the curves and build the surface"
        if self.Parameters is None:
            self.set_parameters(1.0)
        nbp = [c.NbPoles for c in self.curves]
        print(nbp)
        poles_array = []
        bs = Part.BSplineCurve()
        for pole_idx in range(1, self.curves[0].NbPoles + 1):
            pts = [c.getPole(pole_idx) for c in self.curves]
            # print(pts, self.Parameters)
            try:
                bs.interpolate(Points=pts, Parameters=self.Parameters, PeriodicFlag=self.Periodic)
                poles_array.append(bs.getPoles())
            except Part.OCCError:
                if self.repeated_points(pts, 1e-5):
                    print(f"Repeated points detected at Pole #{pole_idx}")
                    poles_array.append(self.interpolate_multipoints(pts))
                else:
                    print("Curve interpolation error. Bad data :")
                    for d in (pts, self.Parameters, self.Periodic):
                        print(d)
        maxlen = 0
        for poles in poles_array:
            maxlen = max(maxlen, len(poles))
        weights = []
        poles = []
        for p in poles_array:
            if len(p) < maxlen:
                poles.append([p[0]] * maxlen)
            else:
                poles.append(p)
            weights.append([1.0] * maxlen)
        self._surface = Part.BSplineSurface()
        args = (poles_array,
                self.curves[0].getMultiplicities(), bs.getMultiplicities(),
                self.curves[0].getKnots(), bs.getKnots(),
                self.curves[0].isPeriodic(), bs.isPeriodic(),
                self.curves[0].Degree, bs.Degree, weights)
        try:
            self._surface.buildFromPolesMultsKnots(*args)
        except Part.OCCError as exc:
            print("\n*** CurvesToSurface interpolation error ***\n")
            print(f"{len(poles_array)} x {len(poles_array[0])} Poles")
            print(f"{sum(self.curves[0].getMultiplicities()[:-1])} x {sum(bs.getMultiplicities()[:-1])} Mults")
            for data in args[1:-1]:
                print(data)
            raise exc
        return self._surface

    def build_surface(self):
        "Make curves compatible and build surface"
        self.match_curves()
        self.auto_orient()
        self.auto_twist()
        self.set_parameters(1.0)
        self.interpolate()


class Gordon:
    """Gordon Surface algorithm on 3 surfaces : S1 + S2 - S3"""

    def __init__(self, s1, s2, s3):
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

    def check_bounds(self):
        u0, u1, v0, v1 = self.s1.bounds()
        if not self.s2.bounds() == (u0, u1, v0, v1):
            print("S1 and S2 bounds don't match")
            return False
        if not self.s3.bounds() == (u0, u1, v0, v1):
            print("S1 and S3 bounds don't match")
            return False
        return True

    def check_corner(self, uv, tol=1e-7):
        check = True
        u, v = uv
        p1 = self.s1.value(u, v)
        p2 = self.s2.value(u, v)
        if p2.distanceToPoint(p1) > tol:
            print("S1 and S2 points @({}, {}) don't match".format(u, v))
            print(f"{p1} != {p2}")
            check = False
        p3 = self.s3.value(u, v)
        if p3.distanceToPoint(p1) > tol:
            print("S1 and S3 points @({}, {}) don't match".format(u, v))
            print(f"{p1} != {p3}")
            check = False
        return check

    def check_corners(self, tolerance=1e-7):
        u0, u1, v0, v1 = self.s1.bounds()
        check = True
        for p in [(u0, v0), (u0, v1), (u1, v0), (u1, v1)]:
            check = check and self.check_corner(p, tol=tolerance)
        return check

    def input_surfaces_match(self, tol=1e-7):
        return self.check_bounds() and self.check_corners(tol)

    def match_degrees_and_knots(self):
        max_Udegree = 0
        max_Vdegree = 0
        for c in [self.s1, self.s2, self.s3]:
            max_Udegree = max(max_Udegree, c.UDegree)
            max_Vdegree = max(max_Vdegree, c.VDegree)
        for c in [self.s1, self.s2, self.s3]:
            c.increaseDegree(max_Udegree, max_Vdegree)

        ad1 = SurfaceAdapter(self.s1, 0)
        ad2 = SurfaceAdapter(self.s2, 0)
        ad3 = SurfaceAdapter(self.s3, 0)
        match_knots([ad1, ad2, ad3])
        ad1.direction = 1
        ad2.direction = 1
        ad3.direction = 1
        match_knots([ad1, ad2, ad3])
        self.s1 = ad1.surface
        self.s2 = ad2.surface
        self.s3 = ad3.surface

    def gordon(self):
        ns = self.s1.copy()
        for i in range(1, len(self.s1.getPoles()) + 1):
            for j in range(1, len(self.s1.getPoles()[0]) + 1):
                ns.setPole(i, j, self.s1.getPole(i, j) + self.s2.getPole(i, j) - self.s3.getPole(i, j))
        return ns

    @property
    def Surface(self):
        # self.input_surfaces_match()
        self.match_degrees_and_knots()
        return self.gordon()


class CurvesOn2Rails:
    """Surface defined by a series of curves on 2 rails"""

    def __init__(self, curves, rails):
        self.tol2d = 1e-15
        self.tol3d = 1e-7
        self.curves = self.curve_convert(curves)
        self.rails = self.curve_convert(rails)

    def curve_convert(self, geolist):
        curves = []
        for geo in geolist:
            if isinstance(geo, FreeCAD.Vector):
                bs = Part.BSplineCurve()
                bs.setPole(1, geo)
                bs.setPole(2, geo)
                curves.append(bs)
            else:
                curves.append(geo)
        return curves

    def check_isocurves(self):
        "Check if the curves are intersecting both rails at the same parameter"
        for c in self.curves:
            par1 = self.rails[0].parameter(c.intersect(self.rails[0], self.tol3d)[0])
            par2 = self.rails[1].parameter(c.intersect(self.rails[1], self.tol3d)[0])
            if abs(par2 - par1) > self.tol2d:
                return False
        return True

    def build_surface(self):
        cts = CurvesToSurface(self.curves)
        s1 = cts.Surface
        s2 = ruled_surface(self.rails[0].toShape(), self.rails[1].toShape(), True).Surface
        s2.exchangeUV()
        s3 = U_linear_surface(s1)
        gordon = Gordon(s1, s2, s3)
        if gordon.input_surfaces_match():
            return gordon.Surface
        return gordon.Surface




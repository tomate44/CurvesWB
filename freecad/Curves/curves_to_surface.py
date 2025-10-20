# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Curves to Surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Interpolate curves to surface"

import FreeCAD
import Part
from freecad.Curves import _utils


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

    def insertKnot(self, k, mult, tol=1e-9):
        if self.direction == 0:
            return self.surface.insertUKnot(k, mult, tol)
        elif self.direction == 1:
            try:
                return self.surface.insertVKnot(k, mult, tol)
            except:
                PrintError(f"insertVKnot error, {k}, {mult}\n")
                PrintError(f"{self.surface.getVKnots()}\n")

def _find_knot(curve, knot, tolerance=1e-9):
    for i in range(1, curve.NbKnots + 1):
        if abs(knot - curve.getKnot(i)) < tolerance:
            return i
    return -1


def match_knots(curves, tolerance=1e-9):
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
                    # print("Increased mult of knot # {} from {} to {}".format(fk, om, mult))
            else:
                first.insertKnot(k, mult, tolerance)
                # print("Inserting knot {} mult {}".format(k, mult))
    for cur_idx in range(1, len(curves)):
        for kno_idx in range(1, first.NbKnots + 1):
            k = first.getKnot(kno_idx)
            mult = first.getMultiplicity(kno_idx)
            fk = _find_knot(curves[cur_idx], k, tolerance)
            if fk > -1:
                curves[cur_idx].increaseMultiplicity(fk, mult)
            else:
                curves[cur_idx].insertKnot(k, mult, tolerance)


def U_linear_surface(surf):
    "Returns a copy of surf that is linear in the U direction"
    poles = [surf.getPoles()[0], surf.getPoles()[-1]]
    weights = [surf.getWeights()[0], surf.getWeights()[-1]]
    bs = Part.BSplineSurface()
    bs.buildFromPolesMultsKnots(poles,
                                [2, 2], surf.getVMultiplicities(),
                                [0, 1], surf.getVKnots(),
                                False, surf.isVPeriodic(),
                                1, surf.VDegree, weights)
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

    def test_params(cu):
        if cu.isClosed():
            fp = 0.75 * cu.FirstParameter + 0.25 * cu.LastParameter
            lp = 0.25 * cu.FirstParameter + 0.75 * cu.LastParameter
        else:
            fp = cu.FirstParameter
            lp = cu.LastParameter
        return fp, lp

    def line(cu1, par1, cu2, par2):
        p1 = value(cu1, par1)
        p2 = value(cu2, par2)
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
    fk = _find_knot(c2, knot, 1e-9)
    if fk > -1:
        c2.setOrigin(fk)
    else:
        print("shift_origin: failed to insert knot")


def ruled_surface(e1, e2, normalize=False, autotwist=0):
    """creates a ruled surface between 2 edges, with automatic orientation.
    If normalize is True, the surface will be normalized in U direction
    If curves are closed and autotwist is True,
    origin of edge e2 will be moved to minimize twist"""
    c1 = e1.Curve.toBSpline(e1.FirstParameter, e1.LastParameter)
    c2 = e2.Curve.toBSpline(e2.FirstParameter, e2.LastParameter)
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


def orient_surface(surf1, surf2, tol=1e-7):
    """Modify surf2 to have surf1 orientation
    with a combination of ReverseU, ReverseV, SwapUV
    """
    def match(p1, p2):
        return p1.distanceToPoint(p2) < tol
    FreeCAD.Console.PrintMessage("---\n")
    # surface params O, X, Y
    params = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))
    pts1 = [surf1.value(u, v) for u, v in params]
    pts2 = [surf2.value(u, v) for u, v in params]
    # O match O and X match Y
    if match(pts1[0], pts2[0]):
        if match(pts1[1], pts2[2]):
            surf2.exchangeUV()
            FreeCAD.Console.PrintMessage("exchange UV\n")
        return surf2
    # O match X
    elif match(pts1[0], pts2[1]):
        # reverse U
        FreeCAD.Console.PrintMessage("reverse U\n")
        c = surf2.vIso(0.0)
        c.reverse()
        uknots = c.getKnots()
        umults = c.getMultiplicities()
        vknots = surf2.getVKnots()
        vmults = surf2.getVMultiplicities()
        poles = surf2.getPoles()
        poles.reverse()
        weights = surf2.getWeights()
        weights.reverse()
        nbs = Part.BSplineSurface()
        nbs.buildFromPolesMultsKnots(poles,
                                     umults, vmults,
                                     uknots, vknots,
                                     c.isPeriodic(), surf2.isVPeriodic(),
                                     c.Degree, surf2.VDegree,
                                     weights)
        # Y match O
        if match(pts1[2], pts2[0]):
            nbs.exchangeUV()
            FreeCAD.Console.PrintMessage("exchange UV\n")
        surf2 = nbs
        return nbs
    # O match Y
    elif match(pts1[0], pts2[1]):
        # reverse V
        FreeCAD.Console.PrintMessage("reverse V\n")
        c = surf2.uIso(0.0)
        c.reverse()
        vknots = c.getKnots()
        vmults = c.getMultiplicities()
        uknots = surf2.getUKnots()
        umults = surf2.getUMultiplicities()
        poles = surf2.getPoles()
        poles = [row.reverse() for row in poles]
        weights = surf2.getWeights()
        weights = [row.reverse() for row in weights]
        nbs = Part.BSplineSurface()
        nbs.buildFromPolesMultsKnots(poles,
                                     umults, vmults,
                                     uknots, vknots,
                                     surf2.isUPeriodic(), c.isPeriodic(),
                                     surf2.UDegree, c.Degree,
                                     weights)
        # X match O
        if match(pts1[2], pts2[0]):
            nbs.exchangeUV()
            FreeCAD.Console.PrintMessage("exchange UV\n")
        surf2 = nbs
        return nbs
    else:
        return surf2


class CurvesToSurface:
    def __init__(self, curves, tol2d=1e-9, tol3d=1e-7):
        self.tol2d = tol2d
        self.tol3d = tol3d
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
                nc.append(c.Curve.toBSpline(c.FirstParameter, c.LastParameter))
            elif isinstance(c, Part.Wire):
                nc.append(c.approximate())
            elif isinstance(c, FreeCAD.Vector):
                bs = Part.BSplineCurve()
                bs.setPole(1, c)
                bs.setPole(2, c)
                nc.append(bs)
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

    def repeated_points(self, pts):
        for i in range(len(pts) - 1):
            d = pts[i].distanceToPoint(pts[i + 1])
            if d < self.tol3d:
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

    def match_knots(self):
        self.normalize_knots()
        for c in self.curves[1:]:
            self.curves[0].insertKnots(c.getKnots(), c.getMultiplicities(), self.tol2d, False)
        for c in self.curves[1:]:
            c.insertKnots(self.curves[0].getKnots(), self.curves[0].getMultiplicities(), self.tol2d, False)

    def match_curves(self):
        self.match_degrees()
        self.normalize_knots()
        self.match_knots()

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

    def pts_weights_interp(self, idx):
        bs = Part.BSplineCurve()
        pts = []
        wpts = []
        op = []
        ow = []
        for i, c in enumerate(self.curves):
            w = c.getWeight(idx)
            wpts.append(FreeCAD.Vector(i, w, 0.0))
            pts.append(c.getPole(idx) * w)
        try:
            bs.interpolate(Points=pts, Parameters=self.Parameters, PeriodicFlag=self.Periodic)
            op = bs.getPoles()
        except Part.OCCError:
            if self.repeated_points(pts):
                # print(f"Repeated points detected at Pole #{pole_idx}")
                op = self.interpolate_multipoints(pts)
            else:
                print("Curve interpolation error. Bad data :")
                for d in (pts, self.Parameters, self.Periodic):
                    print(d)
        try:
            bs.interpolate(Points=wpts, Parameters=self.Parameters, PeriodicFlag=self.Periodic)
            ow = [p.y for p in bs.getPoles()]
        except Part.OCCError:
            print("Weight interpolation error.")
        for i in range(len(op)):
            op[i] /= ow[i]
        return op, ow, bs

    def interpolate(self):
        "interpolate the poles of the curves and build the surface"
        if self.Parameters is None:
            self.set_parameters(1.0)
        # nbp = [c.NbPoles for c in self.curves]
        # print(nbp)
        poles_array = []
        weights_array = []
        for pole_idx in range(1, self.curves[0].NbPoles + 1):
            op, ow, bs = self.pts_weights_interp(pole_idx)
            poles_array.append(op)
            weights_array.append(ow)
        maxlen = 0
        for poles in poles_array:
            maxlen = max(maxlen, len(poles))
        # weights = []
        poles = []
        for p in poles_array:
            if len(p) < maxlen:
                poles.append([p[0]] * maxlen)
            else:
                poles.append(p)
            # weights.append([1.0] * maxlen)
        self._surface = Part.BSplineSurface()
        args = (poles_array,
                self.curves[0].getMultiplicities(), bs.getMultiplicities(),
                self.curves[0].getKnots(), bs.getKnots(),
                self.curves[0].isPeriodic(), bs.isPeriodic(),
                self.curves[0].Degree, bs.Degree, weights_array)
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
        self.interpolate()


class Gordon:
    """Gordon Surface algorithm on 3 surfaces : S1 + S2 - S3"""

    def __init__(self, s1, s2, s3, tol2d=1e-9, tol3d=1e-7):
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3
        self.tol2d = tol2d
        self.tol3d = tol3d

    def normalize_surfaces(self):
        for surf in [self.s1, self.s2, self.s3]:
            if not surf.bounds() == (0.0, 1.0, 0.0, 1.0):
                surf.scaleKnotsToBounds(0.0, 1.0, 0.0, 1.0)

    def same_bounds(self, s1, s2):
        bounds = zip(s1.bounds(), s2.bounds())
        diff = [abs(a - b) for a, b in bounds]
        is_same = (max(diff) < self.tol2d)
        if not is_same:
            print("Surface bounds don't match")
            print(s1.bounds())
            print(s2.bounds())
        return is_same

    def check_bounds(self):
        result = self.same_bounds(self.s1, self.s2) and self.same_bounds(self.s1, self.s3)
        return result

    def same_corner(self, s1, s2, uv):
        u, v = uv
        p1 = s1.value(u, v)
        p2 = s2.value(u, v)
        d = p2.distanceToPoint(p1)
        is_same = (d < self.tol3d)
        if not is_same:
            print("Surface corners @({}, {}) don't match. Distance = {}".format(u, v, d))
            print(f"{p1} != {p2}")
        return is_same

    def check_corner(self, uv):
        result = self.same_corner(self.s1, self.s2, uv) and self.same_corner(self.s1, self.s3, uv)
        return result

    def check_corners(self):
        u0, u1, v0, v1 = self.s1.bounds()
        check = True
        for p in [(u0, v0), (u0, v1), (u1, v0), (u1, v1)]:
            check = check and self.check_corner(p)
        return check

    def input_surfaces_match(self):
        return self.check_bounds() and self.check_corners()

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
        match_knots([ad1, ad2, ad3], self.tol2d)
        ad1.direction = 1
        ad2.direction = 1
        ad3.direction = 1
        match_knots([ad1, ad2, ad3], self.tol2d)
        self.s1 = ad1.surface
        self.s2 = ad2.surface
        self.s3 = ad3.surface
        assert (self.s1.NbUPoles == self.s2.NbUPoles)
        assert (self.s1.NbUPoles == self.s3.NbUPoles)
        assert (self.s1.NbVPoles == self.s2.NbVPoles)
        assert (self.s1.NbVPoles == self.s3.NbVPoles)

    def gordon(self):
        ns = self.s1.copy()
        for i in range(1, len(self.s1.getPoles()) + 1):
            for j in range(1, len(self.s1.getPoles()[0]) + 1):
                w1 = self.s1.getWeight(i, j)
                # print(i,j)
                # Part.show(self.s2.toShape())
                w2 = self.s2.getWeight(i, j)
                w3 = self.s3.getWeight(i, j)
                # w1, w2, w3 = 1, 1, 1
                p1 = self.s1.getPole(i, j) * w1
                p2 = self.s2.getPole(i, j) * w2
                p3 = self.s3.getPole(i, j) * w3
                nw = w1 + w2 - w3
                np = (p1 + p2 - p3) / nw
                ns.setPole(i, j, np)
                ns.setWeight(i, j, nw)
        return ns

    @property
    def Surface(self):
        self.normalize_surfaces()
        if not self.input_surfaces_match():
            self.s2 = orient_surface(self.s1, self.s2, self.tol3d)
            self.s3 = orient_surface(self.s1, self.s3, self.tol3d)
        self.match_degrees_and_knots()
        return self.gordon()


class CurvesOn2Rails:
    """Surface defined by a series of curves on 2 rails"""

    def __init__(self, curves, rails):
        self.tol2d = 1e-7
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
                geo.scaleKnotsToBounds()
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

    def sort_curves(self, s):
        intersect = []
        for i, c in enumerate(self.curves):
            u1, v1 = s.parameter(c.value(c.FirstParameter))
            u2, v2 = s.parameter(c.value(c.LastParameter))
            diff = abs(v1 - v2)
            if (diff > self.tol2d) and (diff < (1 - self.tol2d)):
                FreeCAD.Console.PrintMessage(f"Curve {i + 1} is not Iso (diff = {diff}). Ignoring.\n")
                continue
            if u1 > u2:
                c.reverse()
                FreeCAD.Console.PrintMessage(f"Reversing curve {i + 1}.\n")
            intersect.append((v1, c))
        intersect.sort()
        for i in intersect:
            print(i)
        if abs(intersect[0][0]) > self.tol3d:
            FreeCAD.Console.PrintMessage("Inserting flat profile at 0.0\n")
            intersect.insert(0, (0.0, s.vIso(0.0)))
        if abs(intersect[-1][0] - 1.0) > self.tol3d:
            FreeCAD.Console.PrintMessage("Inserting flat profile at 1.0\n")
            intersect.append((1.0, s.vIso(1.0)))
        params = [tup[0] for tup in intersect]
        curves = [tup[1] for tup in intersect]
        return params, curves

    def build_surface(self):
        try:
            ruled = _utils.ruled_surface(self.rails[0].toShape(), self.rails[1].toShape(), True)
        except Part.OCCError:
            ruled = ruled_surface(self.rails[0].toShape(), self.rails[1].toShape(), True)
        s2 = ruled.Surface
        s2.exchangeUV()
        # self.ruled = s2.toShape()
        params, curves = self.sort_curves(s2)
        cts = CurvesToSurface(curves)
        cts.Parameters = params
        s1 = cts.Surface
        s3 = U_linear_surface(s1)
        # Part.show(Part.Compound([s1.toShape(), s2.toShape(), s3.toShape(), ]))
        gordon = Gordon(s1, s2, s3, self.tol2d, self.tol3d)
        return gordon.Surface




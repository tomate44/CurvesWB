# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Nurbs tools"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Collection of tools for Nurbs."

import FreeCAD
import Part

message = FreeCAD.Console.PrintMessage


def error(s):
    FreeCAD.Console.PrintError(s)


def get_bspline_data(curve):  # returns a dictionary of the BSpline data
    """returns a dictionary of the BSpline data
    """
    dic = dict()
    dic["Type"] = curve.__repr__()
    dic["Continuity"] = curve.Continuity
    dic["Degree"] = curve.Degree
    dic["KnotSequence"] = curve.KnotSequence
    dic["Poles"] = curve.getPoles()
    dic["Weights"] = curve.getWeights()
    dic["isClosed"] = curve.isClosed()
    dic["isPeriodic"] = curve.isPeriodic()
    dic["isRational"] = curve.isRational()
    return dic


def is_same(c1, c2, tol=1e-7, full=False):  # Check if BSpline curves c1 and c2 are equal
    """Check if BSpline curves c1 and c2 are equal
    return a bool
    """
    valid = True
    if full:
        message("\nCurves comparison\n")
    dat1 = get_bspline_data(c1)
    dat2 = get_bspline_data(c2)
    for key in ['Type', 'Continuity', 'Degree', 'isClosed', 'isPeriodic', 'isRational']:
        if not dat1[key] == dat2[key]:
            if full:
                message("{} mismatch : {} != {}\n".format(key, str(dat1[key]), str(dat2[key])))
                valid = False
            else:
                return False
    for key in ["KnotSequence", "Poles", "Weights"]:
        if not len(dat1[key]) == len(dat2[key]):
            if full:
                message("{} list length mismatch : {} != {}\n".format(key, str(len(dat1[key])), str(len(dat2[key]))))
                valid = False
            else:
                return False
    i = 0
    for k1, k2 in zip(dat1["KnotSequence"], dat2["KnotSequence"]):
        if abs(k1 - k2) > tol:
            if full:
                message("Knot #{} mismatch : {} != {}\n".format(i, k1, k2))
                valid = False
            else:
                return False
        i += 1
    i = 0
    for p1, p2 in zip(dat1["Poles"], dat2["Poles"]):
        if p1.distanceToPoint(p2) > tol:
            if full:
                message("Pole #{} mismatch : {} != {}\n".format(i, p1, p2))
                valid = False
            else:
                return False
        i += 1
    i = 0
    for w1, w2 in zip(dat1["Weights"], dat2["Weights"]):
        if abs(w1 - w2) > tol:
            if full:
                message("Weight #{} mismatch : {} != {}\n".format(i, w1, w2))
                valid = False
            else:
                return False
        i += 1
    if full:
        if valid:
            message("Curves are matching.")
        else:
            return False
    return True


def remove_duplicates(curves, tol=1e-7):  # remove duplicate curves from a list
    "remove duplicate curves from a list"
    ret = []
    dups = 0
    for i, c1 in enumerate(curves):
        found = False
        for j, c2 in enumerate(ret):
            # print("checking curves #{} and #{}".format(i,j+i+1))
            if is_same(c1, c2, tol):
                found = True
                dups += 1
                break
        if not found:
            ret.append(c1)
    message("Removed {} duplicate curves\n".format(dups))
    return ret


def is_subsegment(edge_1, edge_2, num=20, tol=1e-7):  # check if edge_1 is a trim of edge_2.
    """check if edge_1 is a trim of edge_2.
    Usage :
    is_subsegment(edge_1, edge_2, num=20, tol=1e-7) ---> bool
    'num' points are sampled on edge_1
    return False if a point is farther than tol.
    """
    try:
        e1 = edge_1.toShape()
        e2 = edge_2.toShape()
    except AttributeError:
        e1 = edge_1
        e2 = edge_2
    for p in e1.discretize(num):
        d, pts, info = Part.Vertex(p).distToShape(e2)
        if d > tol:
            return False
    return True


def remove_subsegments(edges, num=20, tol=1e-7):  # remove subsegment edges from a list
    "remove subsegment edges from a list"
    ret = []
    dups = 0
    for i, e1 in enumerate(edges):
        found = False
        for j, e2 in enumerate(edges):
            if not i == j:
                if is_subsegment(e1, e2, num, tol):
                    if is_subsegment(e2, e1, num, tol):  # e1 == e2
                        for k, e3 in enumerate(ret):
                            if is_subsegment(e1, e3, num, tol):
                                found = True
                                dups += 1
                                break
                    else:
                        found = True
                        dups += 1
                        break
        if not found:
            ret.append(e1)
    message("Removed {} subsegment edges\n".format(dups))
    return ret


class BsplineBasis(object):
    """Computes basis functions of a bspline curve, and its derivatives"""
    def __init__(self):
        self.knots = [0.0, 0.0, 1.0, 1.0]
        self.degree = 1

    def find_span(self, u):
        """ Determine the knot span index.
        - input: parameter u (float)
        - output: the knot span index (int)
        Nurbs Book Algo A2.1 p.68
        """
        n = len(self.knots) - self.degree - 1
        if u == self.knots[n + 1]:
            return n - 1
        low = self.degree
        high = n + 1
        mid = int((low + high) / 2)
        while (u < self.knots[mid] or u >= self.knots[mid + 1]):
            if (u < self.knots[mid]):
                high = mid
            else:
                low = mid
            mid = int((low + high) / 2)
        return mid

    def basis_funs(self, i, u):
        """ Compute the nonvanishing basis functions.
        - input: start index i (int), parameter u (float)
        - output: basis functions values N (list of floats)
        Nurbs Book Algo A2.2 p.70
        """
        N = [0. for x in range(self.degree + 1)]
        N[0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1, self.degree + 1):
            left.append(u - self.knots[i + 1 - j])
            right.append(self.knots[i + j] - u)
            saved = 0.0
            for r in range(j):
                temp = N[r] / (right[r + 1] + left[j - r])
                N[r] = saved + right[r + 1] * temp
                saved = left[j - r] * temp
            N[j] = saved
        return N

    def ders_basis_funs(self, i, u, n):
        """ Compute nonzero basis functions and their derivatives.
        First section is A2.2 modified to store functions and knot differences.
        - input: start index i (int), parameter u (float), number of derivatives n (int)
        - output: basis functions and derivatives ders (array2d of floats)
        Nurbs Book Algo A2.3 p.72
        """
        ders = [[0.0 for x in range(self.degree + 1)] for y in range(n + 1)]
        ndu = [[1.0 for x in range(self.degree + 1)] for y in range(self.degree + 1)]
        ndu[0][0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1, self.degree + 1):
            left.append(u - self.knots[i + 1 - j])
            right.append(self.knots[i + j] - u)
            saved = 0.0
            for r in range(j):
                ndu[j][r] = right[r + 1] + left[j - r]
                temp = ndu[r][j - 1] / ndu[j][r]
                ndu[r][j] = saved + right[r + 1] * temp
                saved = left[j - r] * temp
            ndu[j][j] = saved

        for j in range(0, self.degree + 1):
            ders[0][j] = ndu[j][self.degree]
        for r in range(0, self.degree + 1):
            s1 = 0
            s2 = 1
            a = [[0.0 for x in range(self.degree + 1)] for y in range(2)]
            a[0][0] = 1.0
            for k in range(1, n + 1):
                d = 0.0
                rk = r - k
                pk = self.degree - k
                if r >= k:
                    a[s2][0] = a[s1][0] / ndu[pk + 1][rk]
                    d = a[s2][0] * ndu[rk][pk]
                if rk >= -1:
                    j1 = 1
                else:
                    j1 = -rk
                if (r - 1) <= pk:
                    j2 = k - 1
                else:
                    j2 = self.degree - r
                for j in range(j1, j2 + 1):
                    a[s2][j] = (a[s1][j] - a[s1][j - 1]) / ndu[pk + 1][rk + j]
                    d += a[s2][j] * ndu[rk + j][pk]
                if r <= pk:
                    a[s2][k] = -a[s1][k - 1] / ndu[pk + 1][r]
                    d += a[s2][k] * ndu[r][pk]
                ders[k][r] = d
                j = s1
                s1 = s2
                s2 = j
        r = self.degree
        for k in range(1, n + 1):
            for j in range(0, self.degree + 1):
                ders[k][j] *= r
            r *= (self.degree - k)
        return ders

    def evaluate(self, u, d):
        """ Compute the derivative d of the basis functions.
        - input: parameter u (float), derivative d (int)
        - output: derivative d of the basis functions (list of floats)
        """
        n = len(self.knots) - self.degree - 1
        f = [0.0 for x in range(n)]
        span = self.find_span(u)
        ders = self.ders_basis_funs(span, u, d)
        for i, val in enumerate(ders[d]):
            f[span - self.degree + i] = val
        return f


class KnotVector(object):
    """Knot vector object to use in Bsplines"""
    def __init__(self, v=[0.0, 1.0]):
        if isinstance(v, Part.BSplineCurve):
            self.vector = v.getKnots()
        else:
            self.vector = v

    def __repr__(self):
        return "KnotVector({})".format(str(self._vector))

    @property
    def vector(self):
        return self._vector

    @vector.setter
    def vector(self, v):
        self._vector = v
        self._vector.sort()
        self._min_max()

    @property
    def knots(self):
        """Get the list of unique knots, without duplicates"""
        return list(set(self._vector))

    @property
    def mults(self):
        """Get the list of multiplicities of the knot vector"""
        no_duplicates = self.knots
        return [self._vector.count(k) for k in no_duplicates]

    @classmethod
    def create_uniform(cls, degree, nb_poles):
        """Create a uniform knotVector from given degree and Nb of poles"""
        if degree >= nb_poles:
            error("create_uniform : degree >= nb_poles")
            return None
        nb_int_knots = nb_poles - degree - 1
        start = [0.0 for k in range(degree + 1)]
        mid = [float(k) for k in range(1, nb_int_knots + 1)]
        end = [float(nb_int_knots + 1) for k in range(degree + 1)]
        return cls(start + mid + end)

    @classmethod
    def create_from_points(cls, pts, fac=1.0, force_closed=False):
        # Computes a knot Sequence for a set of points
        # fac (0.0 - 1.0) : parameterization factor
        # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        if force_closed and pts[0].distanceToPoint(pts[-1]) > 1e-7:  # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0.0]
        for i in range(1, len(pts)):
            p = pts[i] - pts[i - 1]
            if isinstance(p, FreeCAD.Vector):
                le = p.Length
            else:
                le = p.length()
            pl = pow(le, fac)
            params.append(params[-1] + pl)
        return cls(params)

    def _min_max(self):
        """Compute the min and max values of the knot vector"""
        self.maxi = max(self._vector)
        self.mini = min(self._vector)

    def reverse(self):
        """Reverse the knot vector"""
        newknots = [(self.maxi + self.mini - k) for k in self._vector]
        newknots.reverse()
        self._vector = newknots
        return self._vector

    def normalize(self):
        """Normalize the knot vector to [0.0, 1.0]"""
        return self.scale()

    def scale(self, length=1.0):
        """Scales the knot vector to a [0.0, length]"""
        if length <= 0.0:
            error("scale error : bad value")
        else:
            ran = self.maxi - self.mini
            newknots = [length * (k - self.mini) / ran for k in self._vector]
            self._vector = newknots
            self._min_max()
            return self._vector

    def transpose(self, u0, u1):
        """Transpose the knot vector to [u0, u1]"""
        if u0 > u1:
            error("transpose error : u0 > u1")
        else:
            ran = self.maxi - self.mini
            newknots = [u0 + ((u1 - u0) * (k - self.mini) / ran) for k in self._vector]
            self._vector = newknots
            self._min_max()
            return self._vector

    def reversed_param(self, pa):
        """Returns the image of the parameter when the knot vector is reversed"""
        newvec = KnotVector()
        newvec.vector = [self._vector[0], pa, self._vector[-1]]
        newvec.reverse()
        return newvec.vector[1]


def parameterization(pts, fac, force_closed=False):
    # Computes a knot Sequence for a set of points
    # fac (0-1) : parameterization factor
    # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
    if force_closed and pts[0].distanceToPoint(pts[-1]) > 1e-7:  # we need to add the first point as the end point
        pts.append(pts[0])
    params = [0]
    for i in range(1, len(pts)):
        p = pts[i] - pts[i - 1]
        if isinstance(p, FreeCAD.Vector):
            le = p.Length
        else:
            le = p.length()
        pl = pow(le, fac)
        params.append(params[-1] + pl)
    return params


def createKnotsFromPointParameters(degree, params):
    """NURBS Book, eq. 9.8"""
    knots = [0.0] * (degree + 1)
    for j in range(len(params) - degree - 1):
        knots.append(sum(params[j:j + degree]) / degree)
    knots.extend([1.0] * (degree + 1))
    return knots


def createKnotsFromPointParameters2(degree, nb_data_pts, nb_ctrl_pts, params):
    """NURBS Book, eq. 9.69"""
    knots = [0.0] * (degree + 1)
    d = float(nb_data_pts) / float(nb_ctrl_pts - degree)
    for j in range(1, nb_ctrl_pts - degree):
        i = int(j * d)
        a = (j * d) - i
        k = ((1.0 - a) * params[i - 1]) + (a * params[i])
        knots.append(k)
    knots.extend([1.0 for _ in range(degree + 1)])
    return knots


# ---------------------------------------------------


def nearest_parameter(bs, pt):
    try:
        par = bs.parameter(pt)
    except Part.OCCError:
        # failed. We try with distToShape
        error("parameter error at {}".format(par))
        v = Part.Vertex(pt)
        e = bs.toShape()
        d, p, i = v.distToShape(e)
        pt1 = p[0][1]
        par = bs.parameter(pt1)
    return par


def bspline_copy(bs, reverse=False, scale=1.0):
    """Copy a BSplineCurve, with knotvector optionally reversed and scaled
    newbspline = bspline_copy(bspline, reverse = False, scale = 1.0)"""
    mults = bs.getMultiplicities()
    weights = bs.getWeights()
    poles = bs.getPoles()
    knots = KnotVector(bs)
    perio = bs.isPeriodic()
    ratio = bs.isRational()
    if scale:
        knots.scale(scale)
    if reverse:
        mults.reverse()
        weights.reverse()
        poles.reverse()
        knots.reverse()
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots.vector, perio, bs.Degree, weights, ratio)
    return bspline


def curvematch(c1, c2, par1, level=0, scale=1.0):
    '''Modifies the start of curve C2 so that it joins curve C1 at parameter par1
    - level (integer) is the level of continuity at join point (C0, G1, G2, G3, etc)
    - scale (float) is a scaling factor of the modified poles of curve C2
    newC2 = curvematch(C1, C2, par1, level=0, scale=1.0)'''
    c1 = c1.toNurbs()
    c2 = c2.toNurbs()
    len1 = c1.length()
    # len2 = c2.length()
    len2 = c2.EndPoint.distanceToPoint(c2.StartPoint)
    # scale the knot vector of C2
    seq2 = KnotVector(c2.KnotSequence).scale(1.0 * abs(scale) * len2)
    # get a scaled / reversed copy of C1
    if scale < 0:
        bs1 = bspline_copy(c1, True, len1)  # reversed
    else:
        bs1 = bspline_copy(c1, False, len1)  # not reversed
    if par1 <= c1.FirstParameter:
        par = c1.FirstParameter
    elif par1 >= c1.LastParameter:
        par = c1.LastParameter
    else:
        par = par1
    pt1 = c1.value(par)  # point on input curve C1
    npar = nearest_parameter(bs1, pt1)

    p1 = bs1.getPoles()
    basis1 = BsplineBasis()
    basis1.knots = bs1.KnotSequence
    basis1.degree = bs1.Degree

    p2 = c2.getPoles()
    basis2 = BsplineBasis()
    basis2.knots = seq2
    basis2.degree = c2.Degree

    # Compute the (level+1) first poles of C2
    lev = 0
    while lev <= level:
        # FreeCAD.Console.PrintMessage("\nDerivative %d\n"%lev)
        ev1 = basis1.evaluate(npar, d=lev)
        ev2 = basis2.evaluate(c2.FirstParameter, d=lev)
        # FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(lev,ev1))
        # FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(lev,ev2))
        poles1 = FreeCAD.Vector()
        for i in range(len(ev1)):
            poles1 += 1.0 * ev1[i] * p1[i]
        val = ev2[lev]
        if val == 0:
            error("Zero !")
            break
        else:
            poles2 = FreeCAD.Vector()
            for i in range(lev):
                poles2 += 1.0 * ev2[i] * p2[i]
            np = (poles1 - poles2)
            np.multiply(1.0 / val)
            # FreeCAD.Console.PrintMessage("Moving P%d from (%0.2f,%0.2f,%0.2f) to (%0.2f,%0.2f,%0.2f)\n"%(lev,p2[lev].x,p2[lev].y,p2[lev].z,np.x,np.y,np.z))
            p2[lev] = np
        lev += 1
    nc = c2.copy()
    for i in range(len(p2)):
        nc.setPole(i + 1, p2[i])
    return nc


class blendCurve(object):
    def __init__(self, e1=None, e2=None):
        self.param1 = 0.0
        self.param2 = 0.0
        self.cont1 = 1
        self.cont2 = 1
        self.scale1 = 1.0
        self.scale2 = 1.0
        self.Curve = None
        self.autoScale = True
        self.maxDegree = 25  # int(Part.BSplineCurve().MaxDegree)
        self.setEdges(e1, e2)

    def setEdges(self, e1, e2):
        if e1 and e2 and hasattr(e1, "Curve") and hasattr(e2, "Curve"):
            self.edge1 = e1.Curve.toBSpline(e1.FirstParameter, e1.LastParameter)
            self.edge2 = e2.Curve.toBSpline(e2.FirstParameter, e2.LastParameter)
            if self.param1 < e1.FirstParameter:
                self.param1 = e1.FirstParameter
            elif self.param1 > e1.LastParameter:
                self.param1 = e1.LastParameter
            if self.param2 < e2.FirstParameter:
                self.param2 = e2.FirstParameter
            elif self.param2 > e2.LastParameter:
                self.param2 = e2.LastParameter
        else:
            error("blendCurve initialisation error")
            self.edge1 = None
            self.edge2 = None
            self.param1 = 0.0
            self.param2 = 0.0

    def getChord(self):
        v1 = self.edge1.value(self.param1)
        v2 = self.edge2.value(self.param2)
        try:
            return Part.LineSegment(v1, v2)
        except Part.OCCError:  # v1 == v2
            return False

    def compute(self):
        nbPoles = self.cont1 + self.cont2 + 2
        e = self.getChord()
        if not e:
            self.Curve = None
            return
        try:
            poles = e.discretize(nbPoles)
        except Part.OCCError:
            self.Curve = None
            return
        degree = nbPoles - 1
        if degree > self.maxDegree:
            degree = self.maxDegree
        kv = KnotVector.create_uniform(degree, nbPoles)
        weights = [1.0 for k in range(nbPoles)]
        be = Part.BSplineCurve()
        be.buildFromPolesMultsKnots(poles, kv.mults, kv.knots, False, degree, weights, False)
        nc = curvematch(self.edge1, be, self.param1, self.cont1, self.scale1)
        rev = bspline_copy(nc, True, False)
        self.Curve = curvematch(self.edge2, rev, self.param2, self.cont2, self.scale2)

    def getPoles(self):
        if self.Curve:
            return self.Curve.getPoles()

    def getCurves(self):
        result = []
        e1 = self.edge1.copy()
        e2 = self.edge2.copy()
        if self.scale1 > 0:
            if self.param1 > e1.FirstParameter:
                e1.segment(e1.FirstParameter, self.param1)
                result.append(e1)
        elif self.scale1 < 0:
            if self.param1 < e1.LastParameter:
                e1.segment(self.param1, e1.LastParameter)
                result.append(e1)
        if self.Curve:
            result.append(self.Curve)
        if self.scale2 > 0:
            if self.param2 > e2.FirstParameter:
                e2.segment(e2.FirstParameter, self.param2)
                result.append(e2)
        elif self.scale2 < 0:
            if self.param2 < e2.LastParameter:
                e2.segment(self.param2, e2.LastParameter)
                result.append(e2)
        return result

    def getEdges(self):
        return [c.toShape() for c in self.getCurves()]

    def getWire(self):
        return Part.Wire(Part.__sortEdges__(self.getEdges()))

    def getJoinedCurve(self):
        c = self.getCurves()
        c0 = c[0]
        for cu in c[1:]:
            c0.join(cu)
        return c0

    def shape(self):
        if self.Curve:
            return self.Curve.toShape()
        else:
            return None

    def curve(self):
        return self.Curve


# ---------------------------------------------------

def move_param(c, p1, p2):
    c1 = c.copy()
    c2 = c.copy()
    c1.segment(c.FirstParameter, float(p2))
    c2.segment(float(p2), c.LastParameter)
    # print("\nSegment 1 -> %r"%c1.getKnots())
    # print("Segment 2 -> %r"%c2.getKnots())
    knots1 = KnotVector(c1).scale(p1 - c.FirstParameter)
    knots2 = KnotVector(c2).scale(c.LastParameter - p1)
    c1.setKnots(knots1)
    c2.setKnots(knots2)
    # print("New 1 -> %r"%c1.getKnots())
    # print("New 2 -> %r"%c2.getKnots())
    return c1, c2


def move_params(c, p1, p2):
    curves = list()
    p1.insert(0, c.FirstParameter)
    p1.append(c.LastParameter)
    p2.insert(0, c.FirstParameter)
    p2.append(c.LastParameter)
    for i in range(len(p1) - 1):
        c1 = c.copy()
        c1.segment(p2[i], p2[i + 1])
        knots1 = KnotVector(c1).scale(p1[i + 1] - p1[i], p1[i])
        print("{} -> {}".format(c1.getKnots(), knots1))
        c1.setKnots(knots1)
        curves.append(c1)
    return curves


def join_curve(c1, c2):
    c = Part.BSplineCurve()
    # poles (sequence of Base.Vector), [mults , knots, periodic, degree, weights (sequence of float), CheckRational]
    new_poles = c1.getPoles()
    new_poles.extend(c2.getPoles()[1:])
    new_weights = c1.getWeights()
    new_weights.extend(c2.getWeights()[1:])
    new_mults = c1.getMultiplicities()[:-1]
    new_mults.append(c1.Degree)
    new_mults.extend(c2.getMultiplicities()[1:])
    knots1 = c1.getKnots()
    knots2 = [knots1[-1] + k for k in c2.getKnots()]
    new_knots = knots1
    new_knots.extend(knots2[1:])
    print("poles   -> %r" % new_poles)
    print("weights -> %r" % new_weights)
    print("mults   -> %r" % new_mults)
    print("knots   -> %r" % new_knots)
    c.buildFromPolesMultsKnots(new_poles, new_mults, new_knots, False, c1.Degree, new_weights, True)
    return c


def join_curves(curves):
    c0 = curves[0]
    for c in curves[1:]:
        c0 = join_curve(c0, c)
    return c0


def reparametrize(c, p1, p2):
    '''Reparametrize a BSplineCurve so that parameter p1 is moved to p2'''
    if not isinstance(p1, (list, tuple)):
        c1, c2 = move_param(c, p1, p2)
        c = join_curve(c1, c2)
        return c
    else:
        curves = move_params(c, p1, p2)
        c = join_curves(curves)
        return c


def param_samples(edge, samples=10):
    fp = edge.FirstParameter
    lp = edge.LastParameter
    ra = lp - fp
    return [fp + float(i) * ra / (samples - 1) for i in range(samples)]


def nurbs_quad(poles, param_range=[0.0, 1.0, 0.0, 1.0], extend_factor=1.0):
    """Create a Nurbs Quad surface between the four supplied poles.
    The parameter range is given by param_range
    The surface can be extended multiple times with extend_factor
    This is used as a projection surface for face mapping.
    """
    s0, s1, t0, t1 = param_range
    bs = Part.BSplineSurface()
    umults = [2, 2]
    vmults = [2, 2]
    uknots = [s0, s1]
    vknots = [t0, t1]
    if extend_factor > 1.0:
        ur = s1 - s0
        vr = t1 - t0
        uknots = [s0 - extend_factor * ur, s1 + extend_factor * ur]
        vknots = [t0 - extend_factor * vr, t1 + extend_factor * vr]
        diag_1 = poles[1][1] - poles[0][0]
        diag_2 = poles[1][0] - poles[0][1]
        np1 = poles[0][0] - extend_factor * diag_1
        np2 = poles[0][1] - extend_factor * diag_2
        np3 = poles[1][0] + extend_factor * diag_2
        np4 = poles[1][1] + extend_factor * diag_1
        poles = [[np1, np2], [np3, np4]]
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots,
                                False, False, 1, 1)
    return bs


class EdgeInterpolator(object):
    """interpolate data along a path shape
    ei = EdgeInterpolator(edge or wire)"""
    def __init__(self, shape):
        self.data = list()
        self.pts = list()
        self.parameters = list()
        self.curve = Part.BSplineCurve()
        if isinstance(shape, Part.Edge):
            self.path = shape
        elif isinstance(shape, Part.Wire):
            path = shape.approximate(1e-8, 1e-3, 99, 5)  # &tol2d, &tol3d, &maxseg, &maxdeg
            self.path = path.toShape()
        else:
            FreeCAD.Console.PrintError("EdgeInterpolator input must be edge or wire")
            raise ValueError

    def add_data(self, p, dat):
        """add a datum on path, at given parameter
        ei.add_data(parameter, datum)"""
        if len(self.data) == 0:
            self.data.append((p, dat))
        else:
            if isinstance(dat, type(self.data[0][1])):
                self.data.append((p, dat))
            else:
                FreeCAD.Console.PrintError("Bad type of data")

    def add_mult_data(self, dat):
        """add multiple data values"""
        if isinstance(dat, (list, tuple)):
            for d in dat:
                self.add_data(d[0], d[1])
        else:
            FreeCAD.Console.PrintError("Argument must be list or tuple")

    def get_point(self, val):
        v = FreeCAD.Vector(0, 0, 0)
        if isinstance(val, (list, tuple)):
            if len(val) >= 1:
                v.x = val[0]
            if len(val) >= 2:
                v.y = val[1]
            if len(val) >= 3:
                v.z = val[2]
        elif isinstance(val, FreeCAD.Base.Vector2d):
            v.x = val.x
            v.y = val.y
        elif isinstance(val, FreeCAD.Vector):
            v = val
        else:
            FreeCAD.Console.PrintError("Failed to convert %s data to FreeCAD.Vector" % type(val))
        return v

    def vec_to_dat(self, v):
        val = self.data[0][1]
        if isinstance(val, (list, tuple)):
            if len(val) == 1:
                return [v.x]
            elif len(val) == 2:
                return [v.x, v.y]
            if len(val) == 3:
                return [v.x, v.y, v.z]
        elif isinstance(val, FreeCAD.Base.Vector2d):
            return FreeCAD.Base.Vector2d(v.x, v.y)
        elif isinstance(val, FreeCAD.Vector):
            return v
        else:
            FreeCAD.Console.PrintError("Failed to convert FreeCAD.Vector to %s" % type(val))

    def build_params_and_points(self):
        self.sort()
        for t in self.data:
            self.parameters.append(t[0])
            self.pts.append(self.get_point(t[1]))

    def sort(self):
        from operator import itemgetter
        self.data = sorted(self.data, key=itemgetter(0))

    def interpolate(self):
        if len(self.data) > 1:
            self.build_params_and_points()
            self.curve.interpolate(Points=self.pts, Parameters=self.parameters)

    def valueAt(self, p):
        if len(self.data) > 1:
            vec = self.curve.value(p)
            return self.vec_to_dat(vec)
        else:
            return self.data[0][1]


def test(parm):
    bb = BsplineBasis()
    bb.knots = [0., 0., 0., 0., 1., 2., 3., 3., 3., 3.]
    bb.degree = 3
    # parm = 2.5

    span = bb.find_span(parm)
    print("Span index : %d" % span)
    f0 = bb.evaluate(parm, d=0)
    f1 = bb.evaluate(parm, d=1)
    f2 = bb.evaluate(parm, d=2)
    print("Basis functions    : %r" % f0)
    print("First derivatives  : %r" % f1)
    print("Second derivatives : %r" % f2)

    # compare to splipy results
    try:
        import splipy
    except ImportError:
        print("splipy is not installed.")
        return False

    basis1 = splipy.BSplineBasis(order=bb.degree + 1, knots=bb.knots)

    print("splipy results :")
    print(basis1.evaluate(parm, d=0).A1.tolist())
    print(basis1.evaluate(parm, d=1).A1.tolist())
    print(basis1.evaluate(parm, d=2).A1.tolist())


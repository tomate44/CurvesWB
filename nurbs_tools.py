# -*- coding: utf-8 -*-

__title__ = "Nurbs tools"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Collection of tools for Nurbs."

import FreeCAD
import Part

#import _utils
#debug = _utils.debug
#debug = _utils.doNothing

def error(s):
    FreeCAD.Console.PrintError(s)

# This KnotVector class is equivalent to the following knotSeq* functions
# I am not sure what is best: a class or a set of independant functions ?

class KnotVector(object):
    """Knot vector object to use in Bsplines"""
    def __init__(self, v=[0.0, 1.0]):
        self._vector = v
        self._min_max()

    def __repr__(self):
        return("KnotVector(%s)"%str(self._vector))

    @property
    def vector(self):
        return(self._vector)

    @vector.setter
    def vector(self, v):
        self._vector = v
        self._vector.sort()
        self._min_max()

    def _min_max(self):
        """Compute the min and max values of the knot vector"""
        self.maxi = max(self._vector)
        self.mini = min(self._vector)

    def reverse(self):
        """Reverse the knot vector"""
        newknots = [(self.maxi + self.mini - k) for k in self._vector]
        newknots.reverse()
        self._vector = newknots

    def normalize(self):
        """Normalize the knot vector"""
        self.scale()

    def scale(self, length=1.0):
        """Scales the knot vector to a given length"""
        if length <= 0.0:
            error("scale error : bad value")
        else:
            ran = self.maxi - self.mini
            newknots = [length * (k-self.mini)/ran for k in self._vector]
            self._vector = newknots
            self._min_max()

    def reversed_param(self, pa):
        """Returns the image of the parameter when the knot vector is reversed"""
        newvec = KnotVector()
        newvec.vector = [self._vector[0], pa, self._vector[-1]]
        newvec.reverse()
        return(newvec.vector[1])

    def create_uniform(self, degree, nb_poles):
        """Create a uniform knotVector from given degree and Nb of poles"""
        if degree >= nb_poles:
            error("create_uniform : degree >= nb_poles")
        else:
            nb_int_knots = nb_poles - degree - 1
            start = [0.0 for k in range(degree+1)]
            mid = [float(k) for k in range(1,nb_int_knots+1)]
            end = [float(nb_int_knots+1) for k in range(degree+1)]
            self._vector = start + mid + end
            self._min_max()

    def get_mults(self):
        """Get the list of multiplicities of the knot vector"""
        no_duplicates = list(set(self._vector))
        return([self._vector.count(k) for k in no_duplicates])

    def get_knots(self):
        """Get the list of unique knots, without duplicates"""
        return(list(set(self._vector)))

# ---------------------------------------------------

def knotSeqReverse(knots):
    """Reverse a knot vector
    revKnots = knotSeqReverse(knots)"""
    ma = max(knots)
    mi = min(knots)
    newknots = [ma+mi-k for k in knots]
    newknots.reverse()
    return(newknots)

def knotSeqNormalize(knots):
    """Normalize a knot vector
    normKnots = knotSeqNormalize(knots)"""
    ma = max(knots)
    mi = min(knots)
    ran = ma-mi
    newknots = [(k-mi)/ran for k in knots]
    return(newknots)

def knotSeqScale(knots, length = 1.0):
    """Scales a knot vector to a given length
    newknots = knotSeqScale(knots, length = 1.0)"""
    if length <= 0.0:
        error("knotSeqScale : length <= 0.0")
    else:
        ma = max(knots)
        mi = min(knots)
        ran = ma-mi
        newknots = [length * (k-mi)/ran for k in knots]
        return(newknots)

def paramReverse(pa,fp,lp):
    """Returns the image of parameter param when knot sequence [fp,lp] is reversed.
    newparam = paramReverse(param,fp,lp)"""
    seq = [fp,pa,lp]
    return(knotSeqReverse(seq)[1])

def createKnots(degree, nbPoles):
    """Create a uniform knotVector from given degree and Nb of poles
    knotVector = createKnots(degree, nbPoles)"""
    if degree >= nbPoles:
        error("createKnots : degree >= nbPoles")
    else:
        nbIntKnots = nbPoles - degree - 1
        start = [0.0 for k in range(degree+1)]
        mid = [float(k) for k in range(1,nbIntKnots+1)]
        end = [float(nbIntKnots+1) for k in range(degree+1)]
        return(start+mid+end)

def createKnotsMults(degree, nbPoles):
    """Create a uniform knotVector and a multiplicities list from given degree and Nb of poles
    knots, mults = createKnotsMults(degree, nbPoles)"""
    if degree >= nbPoles:
        error("createKnotsMults : degree >= nbPoles")
    else:
        nbIntKnots = nbPoles - degree - 1
        knots = [0.0] + [float(k) for k in range(1,nbIntKnots+1)] + [float(nbIntKnots+1)]
        mults = [degree+1] + [1 for k in range(nbIntKnots)] + [degree+1]
        return(knots, mults)

# ---------------------------------------------------

def bspline_copy(bs, reverse = False, scale = 1.0):
    """Copy a BSplineCurve, with knotvector optionally reversed and scaled
    newbspline = bspline_copy(bspline, reverse = False, scale = 1.0)"""
    # Part.BSplineCurve.buildFromPolesMultsKnots( poles, mults , knots, periodic, degree, weights, CheckRational )
    mults = bs.getMultiplicities()
    weights = bs.getWeights()
    poles = bs.getPoles()
    knots = bs.getKnots()
    perio = bs.isPeriodic()
    ratio = bs.isRational()
    if scale:
        knots = knotSeqScale(knots, scale)
    if reverse:
        mults.reverse()
        weights.reverse()
        poles.reverse()
        knots = knotSeqReverse(knots)
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults , knots, perio, bs.Degree, weights, ratio)
    return(bspline)


class BsplineBasis:
    """Computes basis functions of a bspline curve, and its derivatives"""
    def __init__(self):
        self.knots = [0.0, 0.0, 1.0, 1.0]
        self.degree = 1

    def find_span(self,u):
        """ Determine the knot span index.
        - input: parameter u (float)
        - output: the knot span index (int)
        Nurbs Book Algo A2.1 p.68
        """
        n = len(self.knots)-self.degree-1
        if u == self.knots[n+1]:
            return(n-1)
        low = self.degree
        high = n+1
        mid = int((low+high)/2)
        while (u < self.knots[mid] or u >= self.knots[mid+1]):
            if (u < self.knots[mid]):
                high = mid
            else:
                low = mid
            mid = int((low+high)/2)
        return(mid)

    def basis_funs(self, i, u):
        """ Compute the nonvanishing basis functions.
        - input: start index i (int), parameter u (float)
        - output: basis functions values N (list of floats)
        Nurbs Book Algo A2.2 p.70
        """
        N = [0. for x in range(self.degree+1)]
        N[0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1,self.degree+1):
            left.append(u-self.knots[i+1-j])
            right.append(self.knots[i+j]-u)
            saved = 0.0
            for r in range(j):
                temp = N[r] / (right[r+1] + left[j-r])
                N[r] = saved + right[r+1] * temp
                saved = left[j-r]*temp
            N[j] = saved
        return(N)

    def ders_basis_funs(self, i, u, n):
        """ Compute nonzero basis functions and their derivatives.
        First section is A2.2 modified to store functions and knot differences.
        - input: start index i (int), parameter u (float), number of derivatives n (int)
        - output: basis functions and derivatives ders (array2d of floats)
        Nurbs Book Algo A2.3 p.72
        """
        ders = [[0.0 for x in range(self.degree+1)] for y in range(n+1)]
        ndu = [[1.0 for x in range(self.degree+1)] for y in range(self.degree+1)] 
        ndu[0][0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1,self.degree+1):
            left.append(u-self.knots[i+1-j])
            right.append(self.knots[i+j]-u)
            saved = 0.0
            for r in range(j):
                ndu[j][r] = right[r+1] + left[j-r]
                temp = ndu[r][j-1] / ndu[j][r]
                ndu[r][j] = saved + right[r+1] * temp
                saved = left[j-r]*temp
            ndu[j][j] = saved

        for j in range(0,self.degree+1):
            ders[0][j] = ndu[j][self.degree]
        for r in range(0,self.degree+1):
            s1 = 0
            s2 = 1
            a = [[0.0 for x in range(self.degree+1)] for y in range(2)]
            a[0][0] = 1.0
            for k in range(1,n+1):
                d = 0.0
                rk = r-k
                pk = self.degree-k
                if r >= k:
                    a[s2][0] = a[s1][0] / ndu[pk+1][rk]
                    d = a[s2][0] * ndu[rk][pk]
                if rk >= -1:
                    j1 = 1
                else:
                    j1 = -rk
                if (r-1) <= pk:
                    j2 = k-1
                else:
                    j2 = self.degree-r
                for j in range(j1,j2+1):
                    a[s2][j] = (a[s1][j]-a[s1][j-1]) / ndu[pk+1][rk+j]
                    d += a[s2][j] * ndu[rk+j][pk]
                if r <= pk:
                    a[s2][k] = -a[s1][k-1] / ndu[pk+1][r]
                    d += a[s2][k] * ndu[r][pk]
                ders[k][r] = d
                j = s1
                s1 = s2
                s2 = j
        r = self.degree
        for k in range(1,n+1):
            for j in range(0,self.degree+1):
                ders[k][j] *= r
            r *= (self.degree-k)
        return(ders)

    def evaluate(self, u, d):
        """ Compute the derivative d of the basis functions.
        - input: parameter u (float), derivative d (int)
        - output: derivative d of the basis functions (list of floats)
        """
        n = len(self.knots)-self.degree-1
        f = [0.0 for x in range(n)]
        span = self.find_span(u)
        ders = self.ders_basis_funs(span, u, d)
        for i,val in enumerate(ders[d]):
            f[span-self.degree+i] = val
        return(f)

def test():
    bb = BsplineBasis()
    bb.knots = [0.,0.,0.,0.,1.,2.,3.,3.,3.,3.]
    bb.degree = 3
    parm = 3.0

    span = bb.find_span(parm)
    print("Span index : %d"%span)
    f0 = bb.evaluate(parm,d=0)
    f1 = bb.evaluate(parm,d=1)
    f2 = bb.evaluate(parm,d=2)
    print("Basis functions    : %r"%f0)
    print("First derivatives  : %r"%f1)
    print("Second derivatives : %r"%f2)
    
    # compare to splipy results
    try:
        import splipy
    except ImportError:
        print("splipy is not installed.")
        return(False)
    
    basis1 = splipy.BSplineBasis(order=bb.degree+1, knots=bb.knots)
    
    print("splipy results :")
    print(basis1.evaluate(parm,d=0).A1.tolist())
    print(basis1.evaluate(parm,d=1).A1.tolist())
    print(basis1.evaluate(parm,d=2).A1.tolist())


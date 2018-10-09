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

class BsplineBasis(object):
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

# This KnotVector class is equivalent to the following knotSeq* functions
# I am not sure what is best: a class or a set of independent functions ?

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

def knotSeqScale(knots, length = 1.0, start = 0.0):
    """Scales a knot vector to a given length
    newknots = knotSeqScale(knots, length = 1.0)"""
    if length <= 0.0:
        error("knotSeqScale : length <= 0.0")
    else:
        ma = max(knots)
        mi = min(knots)
        ran = ma-mi
        newknots = [start+(length*(k-mi)/ran) for k in knots]
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

def nearest_parameter(bs,pt):
    try:
        par = bs.parameter(pt)
    except Part.OCCError:
        # failed. We try with distToShape
        error("parameter error at %f"%par)
        v = Part.Vertex(pt)
        e = bs.toShape()
        d,p,i = v.distToShape(e)
        pt1 = p[0][1]
        par = bs.parameter(pt1)
    return(par)

def bspline_copy(bs, reverse = False, scale = 1.0):
    """Copy a BSplineCurve, with knotvector optionally reversed and scaled
    newbspline = bspline_copy(bspline, reverse = False, scale = 1.0)
    Part.BSplineCurve.buildFromPolesMultsKnots( poles, mults , knots, periodic, degree, weights, CheckRational )"""
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

def curvematch(c1, c2, par1, level=0, scale=1.0):
    '''Modifies the start of curve C2 so that it joins curve C1 at parameter par1
    - level (integer) is the level of continuity at join point (C0, G1, G2, G3, etc)
    - scale (float) is a scaling factor of the modified poles of curve C2
    newC2 = curvematch(C1, C2, par1, level=0, scale=1.0)'''
    c1 = c1.toNurbs()
    c2 = c2.toNurbs()
    len1 = c1.length()
    #len2 = c2.length()
    len2 = c2.EndPoint.distanceToPoint(c2.StartPoint)
    # scale the knot vector of C2
    seq2 = knotSeqScale(c2.KnotSequence, 1.0 * abs(scale) * len2)
    # get a scaled / reversed copy of C1
    if scale < 0:
        bs1 = bspline_copy(c1, True, len1) # reversed
    else:
        bs1 = bspline_copy(c1, False, len1) # not reversed
    if par1 <= c1.FirstParameter:
        par = c1.FirstParameter
    elif par1 >= c1.LastParameter:
        par = c1.LastParameter
    else:
        par = par1
    pt1 = c1.value(par) # point on input curve C1
    npar = nearest_parameter(bs1,pt1)

    p1 = bs1.getPoles()
    basis1 = BsplineBasis()
    basis1.knots = bs1.KnotSequence
    basis1.degree = bs1.Degree
    
    p2 = c2.getPoles()
    basis2 = BsplineBasis()
    basis2.knots = seq2
    basis2.degree = c2.Degree
    
    # Compute the (level+1) first poles of C2
    l = 0
    while l <= level:
        #FreeCAD.Console.PrintMessage("\nDerivative %d\n"%l)
        ev1 = basis1.evaluate(npar,d=l)
        ev2 = basis2.evaluate(c2.FirstParameter,d=l)
        #FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(l,ev1))
        #FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(l,ev2))
        poles1 = FreeCAD.Vector()
        for i in range(len(ev1)):
            poles1 += 1.0*ev1[i]*p1[i]
        val = ev2[l]
        if val == 0:
            error("Zero !")
            break
        else:
            poles2 = FreeCAD.Vector()
            for i in range(l):
                poles2 += 1.0*ev2[i]*p2[i]
            np = (poles1-poles2)
            np.multiply(1.0/val)
            #FreeCAD.Console.PrintMessage("Moving P%d from (%0.2f,%0.2f,%0.2f) to (%0.2f,%0.2f,%0.2f)\n"%(l,p2[l].x,p2[l].y,p2[l].z,np.x,np.y,np.z))
            p2[l] = np
        l += 1
    nc = c2.copy()
    for i in range(len(p2)):
        nc.setPole(i+1,p2[i])
    return(nc)

class blendCurve(object):
    def __init__(self, e1 = None, e2 = None):
        self.param1 = 0.0
        self.param2 = 0.0
        self.cont1 = 1
        self.cont2 = 1
        self.scale1 = 1.0
        self.scale2 = 1.0
        self.Curve = None
        self.autoScale = True
        self.maxDegree = 25 # int(Part.BSplineCurve().MaxDegree)
        self.setEdges(e1,e2)

    def setEdges(self, e1, e2):
        if e1 and e2:
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
            return(Part.LineSegment(v1,v2))
        except Part.OCCError: # v1 == v2
            return(False)
    
    #def getChordLength(self):
        #ls = self.getChord()
        #if not ls:
            #self.chordLength = 0
        #else:
            #self.chordLength = ls.length()
        #if self.chordLength < 1e-6:
            #error("error : chordLength < 1e-6")
            #self.chordLength = 1.0

    # doesn't work
    #def autoscale(self, w1, w2, w3, maxscale, numsteps):
        #minscale = .01
        #best = 1e50
        #res = None
        #old_scale1 = self.scale1
        #old_scale2 = self.scale2
        #sign1 = self.scale1 / abs(self.scale1)
        #sign2 = self.scale2 / abs(self.scale2)
        #r = [minscale + float(i)*(maxscale-minscale)/(numsteps-1) for i in range(numsteps)]
        #for s1 in r:
            #for s2 in r:
                #self.scale1 = sign1 * s1
                #self.scale2 = sign2 * s2
                #self.compute()
                #a,b,c = eval_smoothness(self.shape(), samples=10)
                #score = a*w1 + b*w2 + c*w3
                #if score < best:
                    #best = score
                    #res = (self.scale1, self.scale2)
        #self.scale1 = old_scale1
        #self.scale2 = old_scale2
        #return(res)

    def compute(self):
        nbPoles = self.cont1 + self.cont2 + 2
        e = self.getChord()
        if not e:
            self.Curve = None
            return()
        try:
            poles = e.discretize(nbPoles)
        except Part.OCCError:
            self.Curve = None
            return()
        degree = nbPoles - 1
        if degree > self.maxDegree:
            degree = self.maxDegree
        knots, mults = createKnotsMults(degree, nbPoles)
        weights = [1.0 for k in range(nbPoles)]
        be = Part.BSplineCurve()
        be.buildFromPolesMultsKnots(poles, mults , knots, False, degree, weights, False)
        nc = curvematch(self.edge1, be, self.param1, self.cont1, self.scale1)
        rev = bspline_copy(nc, True, False)
        self.Curve = curvematch(self.edge2, rev, self.param2, self.cont2, self.scale2)

    def getPoles(self):
        if self.Curve:
            return(self.Curve.getPoles())
    
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
        return(result)
    
    def getEdges(self):
        return([c.toShape() for c in self.getCurves()])

    def getWire(self):
        return(Part.Wire(Part.__sortEdges__(self.getEdges())))
    
    def getJoinedCurve(self):
        c = self.getCurves()
        c0 = c[0]
        for cu in c[1:]:
            c0.join(cu)
        return(c0)        

    def shape(self):
        if self.Curve:
            return(self.Curve.toShape())
        else:
            return(None)

    def curve(self):
        return(self.Curve)
            

# ---------------------------------------------------

def move_param(c,p1,p2):
    c1 = c.copy()
    c2 = c.copy()
    c1.segment(c.FirstParameter,float(p2))
    c2.segment(float(p2),c.LastParameter)
    #print("\nSegment 1 -> %r"%c1.getKnots())
    #print("Segment 2 -> %r"%c2.getKnots())
    knots1 = knotSeqScale(c1.getKnots(), p1-c.FirstParameter)
    knots2 = knotSeqScale(c2.getKnots(), c.LastParameter-p1)
    c1.setKnots(knots1)
    c2.setKnots(knots2)
    #print("New 1 -> %r"%c1.getKnots())
    #print("New 2 -> %r"%c2.getKnots())
    return(c1,c2)

def move_params(c,p1,p2):
    curves = list()
    p1.insert(0,c.FirstParameter)
    p1.append(c.LastParameter)
    p2.insert(0,c.FirstParameter)
    p2.append(c.LastParameter)
    for i in range(len(p1)-1):
        c1 = c.copy()
        c1.segment(p2[i],p2[i+1])
        knots1 = knotSeqScale(c1.getKnots(), p1[i+1]-p1[i], p1[i])
        print("%s -> %s"%(c1.getKnots(),knots1))
        c1.setKnots(knots1)
        curves.append(c1)
    return(curves)

def join_curve(c1,c2):
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
    print("poles   -> %r"%new_poles)
    print("weights -> %r"%new_weights)
    print("mults   -> %r"%new_mults)
    print("knots   -> %r"%new_knots)
    c.buildFromPolesMultsKnots(new_poles, new_mults, new_knots, False, c1.Degree, new_weights, True)
    return(c)

def join_curves(curves):
    c0 = curves[0]
    for c in curves[1:]:
        c0 = join_curve(c0,c)
    return(c0)

def reparametrize(c, p1, p2):
    '''Reparametrize a BSplineCurve so that parameter p1 is moved to p2'''
    if not isinstance(p1,(list, tuple)):
        c1,c2 = move_param(c, p1, p2)
        c = join_curve(c1,c2)
        return(c)
    else:
        curves = move_params(c, p1, p2)
        c = join_curves(curves)
        return(c)

def param_samples(edge, samples=10):
    fp = edge.FirstParameter
    lp = edge.LastParameter
    ra = lp-fp
    return([fp+float(i)*ra/(samples-1) for i in range(samples)])

# doesn't work
#def eval_smoothness(edge, samples=10):
    #params = param_samples(edge, samples)
    ## compute length score
    #chord = edge.valueAt(edge.LastParameter) - edge.valueAt(edge.FirstParameter)
    #if chord.Length > 1e-7: 
        #length_score = (edge.Length / chord.Length) - 1.0
    #else:
        #length_score = None
    ## compute tangent and curvature scores
    #tans = list()
    #curv = list()
    #for p in params:
        #tans.append(edge.tangentAt(p))
        #curv.append(edge.curvatureAt(p))
    #poly = Part.makePolygon(tans)
    #tangent_score = poly.Length
    #m = max(curv)
    #if m > 1e-7:
        #curvature_score = (m-min(curv))/m
    #else:
        #curvature_score = 0.0
    #return(length_score,tangent_score,curvature_score)
    
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
            path = shape.approximate(1e-8,1e-3,99,5) # &tol2d,&tol3d,&maxseg,&maxdeg
            self.path = path.toShape()
        else:
            FreeCAD.Console.PrintError("EdgeInterpolator input must be edge or wire")
            raise ValueError

    def add_data(self, p, dat):
        """add a datum on path, at given parameter
        ei.add_data(parameter, datum)"""
        if len(self.data) == 0:
            self.data.append((p,dat))
        else:
            if type(dat) == type(self.data[0][1]):
                self.data.append((p,dat))
            else:
                FreeCAD.Console.PrintError("Bad type of data")

    def add_mult_data(self, dat):
        """add multiple data values"""
        if isinstance(dat,(list,tuple)):
            for d in dat:
                self.add_data(d[0],d[1])
        else:
            FreeCAD.Console.PrintError("Argument must be list or tuple")

    def get_point(self, val):
        v = FreeCAD.Vector(0,0,0)
        if isinstance(val,(list, tuple)):
            if len(val) >= 1:
                v.x = val[0]
            if len(val) >= 2:
                v.y = val[1]
            if len(val) >= 3:
                v.z = val[2]
        elif isinstance(val,FreeCAD.Base.Vector2d):
            v.x = val.x
            v.y = val.y
        elif isinstance(val,FreeCAD.Vector):
            v = val
        else:
            FreeCAD.Console.PrintError("Failed to convert %s data to FreeCAD.Vector"%type(val))
        return(v)

    def vec_to_dat(self, v):
        val = self.data[0][1]
        if isinstance(val,(list, tuple)):
            if len(val) == 1:
                return([v.x])
            elif len(val) == 2:
                return([v.x, v.y])
            if len(val) == 3:
                return([v.x, v.y, v.z])
        elif isinstance(val,FreeCAD.Base.Vector2d):
            return(FreeCAD.Base.Vector2d(v.x, v.y))
        elif isinstance(val,FreeCAD.Vector):
            return(v)
        else:
            FreeCAD.Console.PrintError("Failed to convert FreeCAD.Vector to %s"%type(val))

    def build_params_and_points(self):
        self.sort()
        for t in self.data:
            self.parameters.append(t[0])
            self.pts.append(self.get_point(t[1]))
           
    def sort(self):
        from operator import itemgetter
        self.data = sorted(self.data,key=itemgetter(0))

    def interpolate(self):
        self.build_params_and_points()
        self.curve.interpolate(Points=self.pts, Parameters=self.parameters)

    def valueAt(self, p):
        vec = self.curve.value(p)
        return(self.vec_to_dat(vec))


        


def test(parm):
    bb = BsplineBasis()
    bb.knots = [0.,0.,0.,0.,1.,2.,3.,3.,3.,3.]
    bb.degree = 3
    #parm = 2.5

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


import math
import FreeCAD
import Part
import nurbs_tools

def error(s):
    FreeCAD.Console.PrintError(s)

def curvematch(c1, c2, par1, level=0, scale=1.0):
    '''Modifies the start of curve C2 so that it joins curve C1 at parameter par1
    - level (integer) is the level of continuity at join point (C0, G1, G2, G3, etc)
    - scale (float) is a scaling factor of the modified poles of curve C2
    newC2 = curvematch(C1, C2, par1, level=0, scale=1.0)'''
    c1 = c1.toNurbs()
    c2 = c2.toNurbs()
    len1 = c1.length()
    len2 = c2.length()
    # scale the knot vector of C2
    seq2 = nurbs_tools.knotSeqScale(c2.KnotSequence, 0.5 * abs(scale) * len2)
    # get a scaled / reversed copy of C1
    if scale < 0:
        bs1 = nurbs_tools.bspline_copy(c1, True, len1) # reversed
    else:
        bs1 = nurbs_tools.bspline_copy(c1, False, len1) # not reversed
    pt1 = c1.value(par1) # point on input curve C1
    par1 = bs1.parameter(pt1) # corresponding parameter on reversed / scaled curve bs1

    p1 = bs1.getPoles()
    basis1 = nurbs_tools.BsplineBasis()
    basis1.knots = bs1.KnotSequence
    basis1.degree = bs1.Degree
    
    p2 = c2.getPoles()
    basis2 = nurbs_tools.BsplineBasis()
    basis2.knots = seq2
    basis2.degree = c2.Degree
    
    # Compute the (level+1) first poles of C2
    l = 0
    while l <= level:
        #FreeCAD.Console.PrintMessage("\nDerivative %d\n"%l)
        ev1 = basis1.evaluate(par1,d=l)
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
            np = (1.0*poles1-poles2)/val
            #FreeCAD.Console.PrintMessage("Moving P%d from (%0.2f,%0.2f,%0.2f) to (%0.2f,%0.2f,%0.2f)\n"%(l,p2[l].x,p2[l].y,p2[l].z,np.x,np.y,np.z))
            p2[l] = np
        l += 1
    nc = c2.copy()
    for i in range(len(p2)):
        nc.setPole(i+1,p2[i])
    return(nc)

class blendCurve:
    def __init__(self, e1 = None, e2 = None):
        if e1 and e2:
            self.edge1 = e1
            self.edge2 = e2
            self.param1 = e1.FirstParameter
            self.param2 = e2.FirstParameter
            self.cont1 = 0
            self.cont2 = 0
            self.scale1 = 1.0
            self.scale2 = 1.0
            self.Curve = Part.BSplineCurve()
            self.getChordLength()
            self.autoScale = True
            self.maxDegree = int(self.Curve.MaxDegree)
        else:
            error("blendCurve initialisation error")
    
    def getChord(self):
        v1 = self.edge1.valueAt(self.param1)
        v2 = self.edge2.valueAt(self.param2)
        ls = Part.LineSegment(v1,v2)
        return(ls)
    
    def getChordLength(self):
        ls = self.getChord()
        self.chordLength = ls.length()
        if self.chordLength < 1e-6:
            error("error : chordLength < 1e-6")
            self.chordLength = 1.0

    def compute(self):
        nbPoles = self.cont1 + self.cont2 + 2
        e = self.getChord()
        poles = e.discretize(nbPoles)
        degree = nbPoles - 1
        if degree > self.maxDegree:
            degree = self.maxDegree
        knots, mults = nurbs_tools.createKnotsMults(degree, nbPoles)
        weights = [1.0 for k in range(nbPoles)]
        be = Part.BSplineCurve()
        be.buildFromPolesMultsKnots(poles, mults , knots, False, degree, weights, False)
        nc = curvematch(self.edge1.Curve, be, self.param1, self.cont1, self.scale1)
        rev = nurbs_tools.bspline_copy(nc, True, False)
        self.Curve = curvematch(self.edge2.Curve, rev, self.param2, self.cont2, self.scale2)

    def getPoles(self):
        self.compute()
        return(self.Curve.getPoles())

    def shape(self):
        self.compute()
        return(self.Curve.toShape())

    def curve(self):
        self.compute()
        return(self.Curve)



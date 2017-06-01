from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from operator import itemgetter

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

fac = 1.0
DEBUG = False
EXTEND = True

class profile:
    
    def __init__(self, curve):
        self.realCurve = curve
        self.localCurve1 = None
        self.localCurve2 = None
        self.Rail1Param = 0.0
        self.Rail2Param = 0.0

class birail:
    
    def __init__(self, ruledSurf):
        self.ruled = ruledSurf
        self.rails = (ruledSurf.Edges[0], ruledSurf.Edges[2])
        self.normTan = False
        self.normBin = False
        self.normNor = True

    def tangentAt(self, p, i):
        if self.normTan:
            return(self.rails[i].tangentAt(p))
        else:
            return(self.rails[i].derivative1At(p))
        
    def normalAt(self, p, i):
        v = self.ruled.ParameterRange[2:]
        n = self.ruled.normalAt(p,v[i]).negative()
        if self.normNor:
            n.normalize()
        return(n)
    
    def binormalAt(self, p, i):
        # TODO check for 0-length vector
        v1 = self.rails[0].valueAt(p)
        v2 = self.rails[1].valueAt(p)
        v = v2.sub(v1)
        if self.normBin:
            v.normalize()
        if i == 0:
            return(v)
        elif i == 1:
            return(v.negative())

    def frameAt(self, p, i):
        t = self.tangentAt(p,i)
        b = self.binormalAt(p,i)
        n = self.normalAt(p,i)
        return((b, t, n))

    def matrixAt(self, p, i):
        t = self.rails[i].valueAt(p)
        u,v,w = self.frameAt(p,i)
        m = FreeCAD.Matrix( u.x, v.x, w.x, t.x,
                            u.y, v.y, w.y, t.y,
                            u.z, v.z, w.z, t.z,
                            0.0, 0.0, 0.0, 1.0)
        return(m)
    

class SweepOn2Rails:
    
    def __init__(self):
        self.birail = None
        self.interpoCurves = []
        self.profiles = []
        self.extend = False
        self.profileSamples = 20
        self.railSamples = 40
        self.parametrization = 0.5
        
    def setRails(self, ruledSurf):
        # TODO: Check for twisted Ruled Surface
        self.birail = birail(ruledSurf)
        
    def setProfiles(self, plist):
        data = []
        self.knots1, self.knots2 = [],[]
        bslist = []
        for pro in plist:
            bslist.append(Part.Edge(pro.Curve.toBSpline(), pro.FirstParameter, pro.LastParameter))
        for pro in bslist:
            dts1 = pro.distToShape(self.birail.rails[0])
            dts2 = pro.distToShape(self.birail.rails[1])
            #FreeCAD.Console.PrintMessage('\nProfile :\n%s\n%s\n'%(str(dts1),str(dts2)))
            sols1 = dts1[1][0]
            sols2 = dts2[1][0]
            #FreeCAD.Console.PrintMessage("%s\n"%str(sols1))
            k1 = self.birail.rails[0].Curve.parameter(sols1[1])
            k2 = self.birail.rails[1].Curve.parameter(sols2[1])
            data.append((k1,k2,pro))
        sortedProfs = sorted(data,key=itemgetter(0))
        self.profiles = []
        for datum in sortedProfs:
            self.knots1.append(datum[0])
            self.knots2.append(datum[1])
            p = profile(datum[2])
            p.Rail1Param = datum[0]
            p.Rail2Param = datum[1]
            self.profiles.append(p)
            FreeCAD.Console.PrintMessage("\n Profile : %f - %f\n"%(p.Rail1Param,p.Rail2Param))
        if len(plist) == 1:
            self.extend = True
            FreeCAD.Console.PrintMessage('\n1 Profile given\n')
        FreeCAD.Console.PrintMessage('\nProfiles sorted\n')

    def getLocalProfile(self, pro):
        m1 = self.birail.matrixAt(pro.Rail1Param,0)
        m2 = self.birail.matrixAt(pro.Rail1Param,1)
        # Not sure it will work on Curve Poles ----v
        pts = pro.realCurve.Curve.getPoles()
        c1 = pro.realCurve.Curve.copy()
        c2 = pro.realCurve.Curve.copy()
        for i in range(len(pts)):
            #np = m1.inverse().multiply(p)
            c1.setPole(i+1, m1.inverse().multiply(pts[i]))
            c2.setPole(i+1, m2.inverse().multiply(pts[i]))
        pro.localCurve1 = Part.Edge(c1, pro.realCurve.FirstParameter, pro.realCurve.LastParameter)
        pro.localCurve2 = Part.Edge(c2, pro.realCurve.FirstParameter, pro.realCurve.LastParameter)

    def getLocalProfiles(self):
        for pro in self.profiles:
            self.getLocalProfile(pro)

    def extendProfiles(self):
        FreeCAD.Console.PrintMessage('\nextending ...\n')
        p0 = self.profiles[0]
        p1 = self.profiles[-1]
        if (not p0.Rail1Param == self.birail.rails[0].FirstParameter) and (not p0.Rail2Param == self.birail.rails[1].FirstParameter):
            p = profile(p0.realCurve)
            p.Rail1Param = self.birail.rails[0].FirstParameter
            p.Rail2Param = self.birail.rails[1].FirstParameter
            p.localCurve1 = p0.localCurve1.copy()
            p.localCurve2 = p0.localCurve2.copy()
            # Warning : p.realCurve is wrong here
            self.profiles.insert(0,p)
            self.knots1.insert(0,p.Rail1Param)
            self.knots2.insert(0,p.Rail2Param)
        if (not p1.Rail1Param == self.birail.rails[0].LastParameter) and (not p1.Rail2Param == self.birail.rails[1].LastParameter):
            p = profile(p1.realCurve)
            p.Rail1Param = self.birail.rails[0].LastParameter
            p.Rail2Param = self.birail.rails[1].LastParameter
            p.localCurve1 = p1.localCurve1.copy()
            p.localCurve2 = p1.localCurve2.copy()
            # Warning : p.realCurve is wrong here
            self.profiles.append(p)
            self.knots1.append(p.Rail1Param)
            self.knots2.append(p.Rail2Param)
        FreeCAD.Console.PrintMessage('\nNumber of profiles : %d\n'%len(self.profiles))
        for p in self.profiles:
            FreeCAD.Console.PrintMessage("\n Profile : %f - %f\n"%(p.Rail1Param,p.Rail2Param))

    def translateLocalProfiles(self, vec):
        for i in range(len(self.profiles)):
            pro = self.profiles[i]
            v = FreeCAD.Vector(vec)
            v.multiply(i)
            pro.localCurve1.translate(v)
            pro.localCurve2.translate(v)

    def showLocalProfiles(self):
        for pro in self.profiles:
            Part.show(pro.localCurve1)
            Part.show(pro.localCurve1)

    def railsInfo(self):
        FreeCAD.Console.PrintMessage('\nInfo Rail 1\n')
        FreeCAD.Console.PrintMessage('knots : %s\n'%(str(self.knots1)))
        FreeCAD.Console.PrintMessage('\nInfo Rail 2\n')
        FreeCAD.Console.PrintMessage('knots : %s\n'%(str(self.knots2)))
        
    def profilesInfo(self):
        pass

    def parameterization (self, pts, a, closed):
        # Computes a knot Sequence for a set of points
        # fac (0-1) : parameterization factor
        # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        if closed: # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0]
        for i in range(1,len(pts)):
            p = pts[i].sub(pts[i-1])
            pl = math.pow(p.Length,a)
            params.append(params[-1] + pl)
        return params
 
    def buildInterpoCurves(self):
        c1 = []
        c2 = []
        for i in range(self.profileSamples):
            pts1 = []
            pts2 = []
            for pro in self.profiles:
                fp = pro.localCurve1.FirstParameter
                lp = pro.localCurve1.LastParameter
                prange = lp-fp
                t = fp + 1.0 * prange * i / (self.profileSamples - 1)
                pts1.append(pro.localCurve1.valueAt(t))
                pts2.append(pro.localCurve2.valueAt(t))
            k1 = self.parameterization(pts1, self.parametrization, False)
            k2 = self.parameterization(pts2, self.parametrization, False)
            FreeCAD.Console.PrintMessage('\nParameters : %s\n'%str(k1))
            ic1 = Part.BSplineCurve()
            ic1.interpolate(Points = pts1, Parameters = k1) #, Tangents = v, TangentFlags = b)
            ic2 = Part.BSplineCurve()
            #c2.buildFromPolesMultsKnots(pts[1],m,self.knots2,False,1)
            ic2.interpolate(Points = pts2, Parameters = k2) #, Tangents = v, TangentFlags = b)
            c1.append(ic1)
            c2.append(ic2)
        self.interpoCurves = (c1,c2)

    def showInterpoCurves(self):
        for ic in self.interpoCurves:
            el = []
            for c in ic:
                el.append(Part.Edge(c))
            Part.show(Part.Compound(el))

    def discretize(self):
        p1 = []
        p2 = []
        for ri in range(self.profileSamples):
            pts1 = []
            pts2 = []
            for i in range(self.railSamples):
                # TODO Add a method that matches the samples to self.knots1, self.knots2 contents
                # Get the good matrices from the birail
                v0 = self.knots1[0]
                v1 = self.knots1[-1]
                pRange1 = v1-v0
                t1 = v0 + 1.0 * pRange1 * i / (self.railSamples-1)
                v2 = self.knots2[0]
                v3 = self.knots2[-1]
                pRange2 = v3-v2
                t2 = v2 + 1.0 * pRange2 * i / (self.railSamples-1)
                m1 = self.birail.matrixAt(t1,0)
                m2 = self.birail.matrixAt(t2,1)
                # Pick a point on interpolating curves
                e1 = Part.Edge(self.interpoCurves[0][ri])
                w0 = e1.FirstParameter
                w1 = e1.LastParameter
                qRange1 = w1-w0
                u1 = w0 + 1.0 * qRange1 * i / (self.railSamples-1)
                pt1 = e1.valueAt(u1)
                
                e2 = Part.Edge(self.interpoCurves[1][ri])
                w2 = e2.FirstParameter
                w3 = e2.LastParameter
                qRange2 = w3-w2
                u2 = w2 + 1.0 * qRange2 * i / (self.railSamples-1)
                pt2 = e2.valueAt(u2)
                
                pts1.append(m1.multiply(FreeCAD.Vector(pt1.x, pt1.y-(1.0*(len(self.profiles)-1) * i / (self.railSamples-1)), pt1.z)))
                pts2.append(m2.multiply(FreeCAD.Vector(pt2.x, pt2.y-(1.0*(len(self.profiles)-1) * i / (self.railSamples-1)), pt2.z)))
            p1.append(pts1)
            p2.append(pts2)
        self.results = (p1,p2)
 
    def mix(self, method = "Rail1"):
        # mix the 2 sets of points here
        pt1 = []
        for row in self.results[0]:
            pt1 += row
        pt2 = []
        for row in self.results[1]:
            pt2 += row

        if method == "Rail1":
            self.result = pt1
        elif method == "Rail2":
            self.result = pt2
        else: #elif method == "Average":
            pt = []
            for i in range(len(pt1)):
                p1 = FreeCAD.Vector(pt1[i])
                p2 = FreeCAD.Vector(pt2[i])
                p1.multiply(0.5)
                p2.multiply(0.5)
                pt.append(p1.add(p2))
            self.result = pt
        
    def shape(self):
        v = [Part.Vertex(p) for p in self.result]
        c = Part.Compound(v)
        return(c)
 
    def build(self):
        self.getLocalProfiles()
        if self.extend:
            self.extendProfiles()
        self.translateLocalProfiles(FreeCAD.Vector(0,1,0))
        self.buildInterpoCurves()
        self.discretize()



def main():
    doc = App.getDocument("test_birail")
    obj = doc.getObject("Ruled_Surface")
    face = obj.Shape.Face1

    obj = doc.getObject("Spline005")
    e1 = obj.Shape.Edge1
    
    obj = doc.getObject("Spline006")
    e2 = obj.Shape.Edge1

    obj = doc.getObject("Spline007")
    e3 = obj.Shape.Edge1
    
    s2r = SweepOn2Rails()
    s2r.parametrization = 1.0
    s2r.extend = True
    s2r.setRails(face)
    s2r.setProfiles([e1,e2,e3]) #((e1,e2,e3))
    s2r.build()
    #s2r.showLocalProfiles()
    s2r.showInterpoCurves()
    s2r.mix("Rail1")
    Part.show(s2r.shape())

if __name__ == '__main__':
    main()




# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import math
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH
from FreeCAD import Base
from operator import itemgetter


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
        self.FirstParameter = 0.0
        self.LastParameter = 1.0

class birail:
    
    def __init__(self, ruledSurf):
        self.ruled = ruledSurf
        s = ruledSurf.Surface
        v0 = ruledSurf.ParameterRange[2]
        v1 = ruledSurf.ParameterRange[3]
        c1 = s.vIso(v0)
        c2 = s.vIso(v1)
        self.rails = (Part.Edge(c1),Part.Edge(c2))
        self.normTan = False
        self.normBin = False
        self.normNor = True
        self.paramCurves = []

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
        self.transvec = FreeCAD.Vector(0,1,0)
        self.fac = 10
        
    def setRails(self, ruledSurf):
        # TODO: Check for twisted Ruled Surface
        self.birail = birail(ruledSurf)

    def getContactParams(self, pro):
        dts1 = pro.distToShape(self.birail.rails[0])
        dts2 = pro.distToShape(self.birail.rails[1])
        #FreeCAD.Console.PrintMessage('\nProfile :\n%s\n%s\n'%(str(dts1),str(dts2)))
        sols1 = dts1[1][0]
        sols2 = dts2[1][0]
        #FreeCAD.Console.PrintMessage("%s\n"%str(sols1))
        rail1ContactParam = self.birail.rails[0].Curve.parameter(sols1[1])
        rail2ContactParam = self.birail.rails[1].Curve.parameter(sols2[1])
        # Check and reverse profile here
        pro1ContactParam = pro.Curve.parameter(sols1[0])
        pro2ContactParam = pro.Curve.parameter(sols2[0])
        FreeCAD.Console.PrintMessage('\nProfile parameters :\n%s\n%s\n'%(str(pro1ContactParam),str(pro2ContactParam)))
        #if pro1ContactParam > pro2ContactParam:
            #return((rail1ContactParam, rail2ContactParam, pro, pro2ContactParam, pro1ContactParam))
        #else:
            #return((rail1ContactParam, rail2ContactParam, pro, pro1ContactParam, pro2ContactParam))
        return((rail1ContactParam, rail2ContactParam, pro, pro1ContactParam, pro2ContactParam))
            
    def setProfiles(self, plist):
        data = []
        self.knots1, self.knots2 = [],[]
        for pro in plist:
            pts = pro.discretize(100)
            bspline = Part.BSplineCurve()
            bspline.approximate(Points = pts, ParamType = 'Chordlength') # 'Uniform' 'Centripetal'
            bs = Part.Edge(bspline) #, pro.FirstParameter, pro.LastParameter)
            data.append(self.getContactParams(bs))
        sortedProfs = sorted(data,key=itemgetter(0)) # Sort profiles on rail1ContactParam
        self.profiles = []
        for datum in sortedProfs:
            self.knots1.append(datum[0])
            self.knots2.append(datum[1])
            p = profile(datum[2])
            p.Rail1Param = datum[0]
            p.Rail2Param = datum[1]
            p.FirstParameter = datum[3]
            p.LastParameter = datum[4]
            self.getLocalProfile(p)
            self.profiles.append(p)
            FreeCAD.Console.PrintMessage("\n Profile : %f - %f\n"%(p.Rail1Param,p.Rail2Param))
        if len(plist) == 1:
            self.extend = True
            FreeCAD.Console.PrintMessage('\n1 Profile given\n')
        FreeCAD.Console.PrintMessage('\nProfiles sorted\n')

    def setBirailParametrization(self):
        pts1 = []
        pts2 = []
        kts = []
        for i in range(len(self.knots1)):
            FreeCAD.Console.PrintMessage("\n param : %f - %f\n"%(self.knots1[i],self.knots2[i]))
            pts1.append(Base.Vector2d(i, self.knots1[i]))
            pts2.append(Base.Vector2d(i, self.knots2[i]))
            kts.append(i)
        bs1 = Part.Geom2d.BSplineCurve2d()
        bs1.interpolate(Points = pts1, Parameters = kts)
        bs2 = Part.Geom2d.BSplineCurve2d()
        bs2.interpolate(Points = pts2, Parameters = kts)
        self.birail.paramCurves = (bs1, bs2)            

    def getLocalProfile(self, pro):
        m1 = self.birail.matrixAt(pro.Rail1Param,0)
        m2 = self.birail.matrixAt(pro.Rail2Param,1)
        FreeCAD.Console.PrintMessage('\nMatrix 1\n%s\n'%str(m1))
        FreeCAD.Console.PrintMessage('\nMatrix 2\n%s\n'%str(m2))
        # Not sure it will work on Curve Poles ----v
        pts = pro.realCurve.Curve.getPoles()
        c1 = pro.realCurve.Curve.copy()
        c2 = pro.realCurve.Curve.copy()
        for i in range(len(pts)):
            #np = m1.inverse().multiply(p)
            c1.setPole(i+1, m1.inverse().multiply(pts[i]))
            c2.setPole(i+1, m2.inverse().multiply(pts[i]))
        pro.localCurve1 = Part.Edge(c1, pro.FirstParameter, pro.LastParameter)
        pro.localCurve2 = Part.Edge(c2, pro.FirstParameter, pro.LastParameter)

    def getLocalProfiles(self):
        i = 0
        for pro in self.profiles:
            FreeCAD.Console.PrintMessage('\nComputing local Profile %d\n'%(i+1))
            self.getLocalProfile(pro)
            i += 1

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

    def translateLocalProfiles(self):
        for i in range(len(self.profiles)):
            pro = self.profiles[i]
            v = FreeCAD.Vector(self.transvec)
            v.multiply(i * self.fac)
            pro.localCurve1.translate(v)
            pro.localCurve2.translate(v)

    def LocalProfiles(self):
        el = []
        for pro in self.profiles:
            el.append(pro.localCurve1)
        return(Part.Compound(el))

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
        k = range(len(self.profiles))
        for i in range(self.profileSamples):
            pts1 = []
            pts2 = []
            for pro in self.profiles:
                fp = pro.FirstParameter
                lp = pro.LastParameter
                prange = lp-fp
                t = fp + 1.0 * prange * i / (self.profileSamples - 1)
                pts1.append(pro.localCurve1.valueAt(t))
                pts2.append(pro.localCurve2.valueAt(t))
            #k1 = self.parameterization(pts1, self.parametrization, False)
            #k2 = self.parameterization(pts2, self.parametrization, False)
            #FreeCAD.Console.PrintMessage('\nParameters : %s\n'%str(k))
            ic1 = Part.BSplineCurve()
            ic1.interpolate(Points = pts1, Parameters = k) #, Tangents = v, TangentFlags = b)
            #ic1.approximate(Points = pts1, DegMin = 1, DegMax = 1, Tolerance = 1.0, Parameters = k)
            ic2 = Part.BSplineCurve()
            #c2.buildFromPolesMultsKnots(pts[1],m,self.knots2,False,1)
            ic2.interpolate(Points = pts2, Parameters = k) #, Tangents = v, TangentFlags = b)
            #ic2.approximate(Points = pts2, DegMin = 1, DegMax = 1, Tolerance = 1.0, Parameters = k)
            c1.append(ic1)
            c2.append(ic2)
        self.interpoCurves = (c1,c2)

    def InterpoCurves(self):
        el = []
        for ic in self.interpoCurves:
            for c in ic:
                el.append(Part.Edge(c))
        return(Part.Compound(el))

    def discretize(self):
        p1 = []
        p2 = []
        n = len(self.profiles) - 1
        #gr = int(1.0 * self.railSamples / n) + 1
        #self.railSamples = gr * n
        for i in range(self.railSamples):
            pts1 = []
            pts2 = []
            t = 1.0 * n * i / (self.railSamples - 1)
            # Get the good matrices from the birail
            t1 = self.birail.paramCurves[0].value(t).y
            t2 = self.birail.paramCurves[1].value(t).y
            m1 = self.birail.matrixAt(t1,0)
            m2 = self.birail.matrixAt(t2,1)
            for ri in range(self.profileSamples):


                # Pick a point on interpolating curves
                e1 = Part.Edge(self.interpoCurves[0][ri])
                pt1 = e1.valueAt(t) #u1)
                
                e2 = Part.Edge(self.interpoCurves[1][ri])
                pt2 = e2.valueAt(t) #u2)
                
                v = FreeCAD.Vector(self.transvec)
                v.multiply(- t * self.fac)
                
                pts1.append(m1.multiply(pt1.add(v)))
                pts2.append(m2.multiply(pt2.add(v)))
                
            p1.append(pts1)
            p2.append(pts2)
            
        self.results = (p1,p2)
 
    def downgradeArray(self):
        pt1 = []
        for row in self.result:
            pt1 += row
        return(pt1)

    def mix(self, method = "Rail1"):
        # mix the 2 sets of points here
        #pt1 = []
        #for row in self.results[0]:
            #pt1 += row
        #pt2 = []
        #for row in self.results[1]:
            #pt2 += row

        if method == "Rail1":
            self.result = self.results[0]
        elif method == "Rail2":
            self.result = self.results[1]
        elif method in ["Average","Blend"]:
            arr2d = []
            l = len(self.results[0][0])-1
            for i in range(len(self.results[0])):
                row = []
                for j in range(len(self.results[0][0])):
                    p1 = FreeCAD.Vector(self.results[0][i][j])
                    p2 = FreeCAD.Vector(self.results[1][i][j])
                    if method == "Average":
                        p1.multiply(0.5)
                        p2.multiply(0.5)
                    else:
                        p1.multiply(1.0*(l-j)/l)
                        p2.multiply(1.0*j/l)
                    row.append(p1.add(p2))
                arr2d.append(row)
            self.result = arr2d
        
    def shapeCloud(self):
        v = []
        for row in self.result:
            for pt in row:
                v.append(Part.Vertex(pt))
        c = Part.Compound(v)
        return(c)

    def shapeGrid(self):
        poly = []
        #polyV = []
        for row in self.result:
            poly.append(Part.makePolygon(row))
        for i in range(len(self.result[0])):
            row = []
            for j in range(len(self.result)):
                row.append(self.result[j][i])
            poly.append(Part.makePolygon(row))
        c = Part.Compound(poly)
        return(c)
 
    def build(self):
        #self.getLocalProfiles()
        if self.extend:
            self.extendProfiles()
        self.setBirailParametrization()
        self.translateLocalProfiles()
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
    s2r.fac = 1.0
    s2r.profileSamples = 100
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




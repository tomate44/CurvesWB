# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part
from FreeCAD import Vector
from FreeCAD import Base
import nurbs_tools

#doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()

class interp(object):
    def __init__(self):
        self.param = list()
        self.value = list()
        self.bs = Part.BSplineCurve()
        self.must_increase = True
    def add(self,p,v):
        if self.must_increase and not self.value == []:
            if self.dat_gt(v, self.value[-1]):
                self.param.append(p)
                self.value.append(v)
            else:
                FreeCAD.Console.PrintWarning("skipping keyframe %s - %s.\n"%(p,v))
                return()
        else:
            self.param.append(p)
            self.value.append(v)
        FreeCAD.Console.PrintMessage("add keyframe %s - %s.\n"%(p,v))
        self.build()
    def data_to_vec(self, dat):
        if isinstance(dat,(int, float)):
            return(Vector(dat,0,0))
        if isinstance(dat,(list, tuple)):
            if len(dat) == 1:
                return(Vector(dat[0],0,0))
            elif len(dat) == 2:
                return(Vector(dat[0],dat[1],0))
            elif len(dat) == 3:
                return(Vector(dat[0],dat[1],dat[2]))
        if isinstance(dat,Vector2d):
            return(Vector(v2.x,v2.y,0))
        if isinstance(dat,Base.Vector):
            return(dat)
    def vec_to_data(self, vec):
        dat = self.value[0]
        if isinstance(dat,(int, float)):
            return(vec.x)
        if isinstance(dat,(list, tuple)):
            if len(dat) == 1:
                return([vec.x])
            elif len(dat) == 2:
                return([vec.x,vec.y])
            elif len(dat) == 3:
                return([vec.x,vec.y,vec.z])
        if isinstance(dat,Vector2d):
            return(Base.Vector2d(vec.x,vec.y))
        if isinstance(dat,Base.Vector):
            return(vec)
    def dat_gt(self, d1, d2):
#        dat = self.value[0]
        if isinstance(d1,(int, float)):
            return(d1 > d2)
        if isinstance(d1,(list, tuple)):
            if len(d1) == 1:
                return(d1[0] > d2[0])
            elif len(d1) == 2:
                return( (d1[0] > d2[0]) and (d1[1] > d2[1]) )
            elif len(d1) == 3:
                return( (d1[0] > d2[0]) and (d1[1] > d2[1]) and (d1[2] > d2[2]) )
        if isinstance(d1,Vector2d):
            return( (d1.x > d2.x) and (d1.y > d2.y) )
        if isinstance(dat,Base.Vector):
            return( (d1.x > d2.x) and (d1.y > d2.y) and (d1.z > d2.z) )

    def build(self):
        if len(self.param) < 2:
            return()
        poles = [self.data_to_vec(v) for v in self.value]
        degree = 1
        mults = [2]+[1]*(len(self.param)-2)+[2]
        self.bs.buildFromPolesMultsKnots(poles,mults,self.param,False,degree)
    def valueAt(self,p):
        if len(self.value) == 0:
            v = False
        elif len(self.value) == 1:
            v = self.value[0]
        else:
            v = self.vec_to_data(self.bs.value(p))
        #print(p,v)
        return(v)
    def paramAt(self,v):
        if len(self.param) == 0:
            p = False
        elif len(self.param) == 1:
            p = self.param[0]
        else:
            p = self.bs.parameter(self.data_to_vec(v))
        
        print(p,v)
        return(p)

def ruled_surface(e1,e2):
    """ creates a ruled surface between 2 edges, with automatic orientation."""
    # Automatic orientation
    # /src/Mod/Part/App/PartFeatures.cpp#171
    p1 = e1.valueAt(e1.FirstParameter)
    p2 = e1.valueAt(e1.LastParameter)
    p3 = e2.valueAt(e2.FirstParameter)
    p4 = e2.valueAt(e2.LastParameter)
    if e1.Orientation == 'Reversed':
        p = p1
        p1 = p2
        p2 = p
    if e2.Orientation == 'Reversed':
        p = p3
        p3 = p4
        p4 = p
    v1 = p2 - p1
    v2 = p3 - p1
    n1 = v1.cross(v2)
    v3 = p3 - p4
    v4 = p2 - p4
    n2 = v3.cross(v4)
    if (n1.dot(n2) < 0):
        e = e2.copy()
        e.reverse()
        return(Part.makeRuledSurface(e1,e))
    else:
        return(Part.makeRuledSurface(e1,e2))

class Ribbon(object):
    def __init__(self, e1, f1, e2, f2):
        self.surf = ruled_surface(e1,e2).Surface
        c1 = self.surf.vIso(0.0).toShape()
        c2 = self.surf.vIso(1.0).toShape()
        from curveOnSurface import curveOnSurface
        self.rail1 = curveOnSurface(c1,f1)
        self.rail2 = curveOnSurface(c2,f2)
        self.build_param_ortho()
    def build_param_ortho(self, num=20):
        #surf = ruled_surface(self.rail1.edge, self.rail2.edge).Surface
        mid = self.surf.vIso(0.5)
        #c0 = surf.vIso(0.0)
        #c1 = surf.vIso(1.0)
        #v0 = c0.toShape()
        #v1 = c1.toShape()
        self.inter = interp()
        self.inter.add(0,(self.rail1.edge.Curve.FirstParameter,self.rail2.edge.Curve.FirstParameter))
        pl = Part.Plane()
        for i in range(1,num):
            v = float(i)/(num)
            pt = mid.value(v)
            tan = mid.tangent(v)[0]
            pl.Position = pt
            pl.Axis = tan
            pts0 = self.rail1.edge.Curve.intersectCS(pl)[0]
            pts1 = self.rail2.edge.Curve.intersectCS(pl)[0]
            pt0 = closest_point(pts0,pt)
            pt1 = closest_point(pts1,pt)
            if isinstance(pt0,FreeCAD.Vector) and isinstance(pt1,FreeCAD.Vector):
                p1 = nurbs_tools.nearest_parameter(self.rail1.edge.Curve, pt0)
                p2 = nurbs_tools.nearest_parameter(self.rail2.edge.Curve, pt1)
                self.inter.add(v, (p1, p2)) # (self.rail1.edge.Curve.parameter(pt0), self.rail2.edge.Curve.parameter(pt1)))
            else:
                FreeCAD.Console.PrintError("Failed to compute points at %f.\n"%v)
        self.inter.add(1,(self.rail1.edge.Curve.LastParameter, self.rail2.edge.Curve.LastParameter))
    def valueAt(self,p):
        if (p < 0.0) or (p > 1.0):
            return(False)
        else:
            par = self.inter.valueAt(p)
            v1 = self.rail1.edge.valueAt(par[0])
            v2 = self.rail2.edge.valueAt(par[1])
            return(v1,v2)
    def getNotches(self, num=20, l=1.0):
        notches = list()
        for i in range(num):
            par = 1.0*i / (num-1)
            p1, p2 = self.valueAt(par)
            ls = Part.LineSegment(p1, p2)
            p3 = ls.value(ls.FirstParameter - l)
            p4 = ls.value(ls.LastParameter + l)
            nls = Part.makeLine(p3, p4)
            sh1 = self.rail1.face.project([nls])
            sh2 = self.rail2.face.project([nls])
            if (len(sh1.Edges) > 0) and (len(sh2.Edges) > 0):
                notches.append((sh1.Edges[0], sh2.Edges[0]))
        return(notches)
    def get_blend_curves(self, num=20, l1=2, s1=1.0, l2=2, s2=1.0):
        n = self.getNotches(num)
        bcl = list()
        bc = nurbs_tools.blendCurve()
        #bc.param1 = 1.0
        #bc.param2 = 0.0
        bc.cont1 = l1
        bc.cont2 = l2
        bc.scale1 = s1
        bc.scale2 = -s2
        for tup in n:
            bc.param1 = tup[0].LastParameter
            bc.param2 = tup[1].FirstParameter
            bc.setEdges(tup[0],tup[1])
            bc.compute()
            bcl.append(bc.shape())
        return(bcl)
    def get_loft(self, num=20, l1=2, s1=1.0, l2=2, s2=1.0):
        bc = self.get_blend_curves(num, l1, s1, l2, s2)
        w = [Part.Wire([e]) for e in bc]
        loft = Part.makeLoft(w)
        return(loft)

            


        
def closest_point(pt_list,pt):
    """ returns the point in pt_list that is closest to pt."""
    dist = 1e50
    v = None
    for p in pt_list:
        d = Vector(p.X,p.Y,p.Z).distanceToPoint(pt)
        if d < dist:
            dist = d
            v = Vector(p.X,p.Y,p.Z)
    return(v)

def main():
    obj1 = FreeCAD.ActiveDocument.getObject('CV_BAMB_ELEC_SING_Face25')
    f1 = obj1.Shape.Face1
    surf = f1.Surface
    mid = surf.vIso(0.5)
    c0 = surf.vIso(0.0)
    c1 = surf.vIso(1.0)
    v0 = c0.toShape()
    v1 = c1.toShape()
    num = 200
    inter = interp()
    inter.add(0,(c0.FirstParameter,c1.FirstParameter))
    pl = Part.Plane()
    for i in range(1,num):
        v = float(i)/num
        pt = mid.value(v)
        tan = mid.tangent(v)[0]
        pl.Position = pt
        pl.Axis = tan
        pts0 = c0.intersectCS(pl)[0]
        pts1 = c1.intersectCS(pl)[0]
        pt0 = closest_point(pts0,pt)
        pt1 = closest_point(pts1,pt)
        print(pt0,pt1)
        inter.add(v,(c0.parameter(pt0),c1.parameter(pt1)))
    inter.add(1,(c0.LastParameter,c1.LastParameter))
#        c = Part.makeCircle(0.3,pt,tan)
#        inf0 = c.distToShape(v0)[2][0]
#        inf1 = c.distToShape(v1)[2][0]
#        #print(inf0)
#        #print(inf1)
#        if inf0[3] == 'Edge' and inf1[3] == 'Edge':
#            inter.add(v,(inf0[5],inf1[5]))
    edges = list()
    for tu in zip(inter.param,inter.value):
        print(tu)
        l = Part.makeLine(v0.valueAt(tu[1][0]), v1.valueAt(tu[1][1]))
        edges.append(l)

    newc0 = Part.BSplineCurve()
    pts_0 = [v0.valueAt(v[0]) for v in inter.value]
    newc0.interpolate(Points = pts_0,Parameters=inter.param)
    Part.show(newc0.toShape())

    newc1 = Part.BSplineCurve()
    pts_1 = [v1.valueAt(v[1]) for v in inter.value]
    newc1.interpolate(Points = pts_1,Parameters=inter.param)
    Part.show(newc1.toShape())

    Part.show(Part.Compound(edges))
        
    
        



def test():
    i = interp()
    i.add(0,5)
    i.add(2,6)
    i.add(3,12)
    i.valueAt(1)
    i.valueAt(2.5)
    i.valueAt(3.5)
    i.paramAt(5)
    i.paramAt(7)
    print("---")
    
    i = interp()
    i.add(0,(5,23))
    i.add(2,(6,36))
    i.add(3,(12,80))
    i.valueAt(1)
    i.valueAt(2.5)
    i.valueAt(3.5)
    i.paramAt((7,40))
    i.paramAt((9,50))

if __name__ == '__main__':
    main()



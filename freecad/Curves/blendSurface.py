# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part
from freecad.Curves.curveOnSurface import curveOnSurface
from freecad.Curves import nurbs_tools


class blendSurface:
    def __init__(self, o1, o2):

        e1 = self.getEdge(o1)
        e2 = self.getEdge(o2)
        f1 = self.getFace(o1)
        f2 = self.getFace(o2)

        self.cos1 = curveOnSurface(e1, f1)
        self.cos2 = curveOnSurface(e2, f2)
        if o1.Reverse:
            self.cos1.reverse()
        if o2.Reverse:
            self.cos2.reverse()

        self.cont1 = 2
        self.cont2 = 2
        self.scale1 = 1.0
        self.scale2 = 1.0
        self.var_scale1 = None
        self.var_scale2 = None

        # self.cos1.reverseTangent =  o1.ReverseTangent
        # self.cos1.reverseNormal =   o1.ReverseNormal
        # self.cos1.reverseBinormal = o1.ReverseBinormal

        # self.cos2.reverseTangent =  o2.ReverseTangent
        # self.cos2.reverseNormal =   o2.ReverseNormal
        # self.cos2.reverseBinormal = o2.ReverseBinormal

        self.railSamples = 20
        self.profSamples = 20
        self.untwist = False
        self.curves = []

    def buildCurves(self):  # -----------------------DEPRECATED ---------------------
        for i in range(self.railSamples):
            t1 = self.cos1.firstParameter + (1.0 * i * self.paramRange(self.cos1) / (self.railSamples - 1))
            if not self.untwist:
                t2 = self.cos2.firstParameter + (1.0 * i * self.paramRange(self.cos2) / (self.railSamples - 1))
            else:
                t2 = self.cos2.lastParameter - (1.0 * i * self.paramRange(self.cos2) / (self.railSamples - 1))
            pt1 = self.cos1.valueAt(t1)
            pt2 = self.cos2.valueAt(t2)
            chord = pt2.sub(pt1).Length
        #    ip1 = cos1.tangentTo(t1,pt2)[0]
        #    ip2 = cos2.tangentTo(t2,pt1)[0]
            ip1 = self.cos1.binormalAt(t1)
            ip2 = self.cos2.binormalAt(t2)
            ip1.normalize().multiply(chord / 3.0)
            ip2.normalize().multiply(chord / 3.0)
            poles = [pt1, pt1.add(ip1), pt2.add(ip2), pt2]
            bz = Part.BezierCurve()
            bz.setPoles(poles)
            self.curves.append(bz)

    def compute_scale(self, sc, edge):
        if sc is None:
            return(False)
        if isinstance(sc, (list, tuple)):
            res = list()
            ei = nurbs_tools.EdgeInterpolator(edge)
            for v in sc:
                ei.add_data(v.x, v)
            # ei.add_mult_data(sc)
            ei.interpolate()
            for i in range(self.railSamples):
                p = float(i) / (self.railSamples - 1)
                res.append(ei.valueAt(p))
            return(res)
        elif isinstance(sc, (float, int)):
            return([float(sc)] * self.railSamples)
        else:
            FreeCAD.Console.PrintError("BlendSurface : failed to compute scale\n{}\n".format(sc))
            return(None)

    def cross_curves2(self):
        self.curves = list()
        # params1 = self.cos1.build_param_list(self.railSamples)
        # params2 = self.cos2.build_param_list(self.railSamples)
        if self.untwist:
            self.cos2.param_list.reverse()
        sc1 = self.compute_scale(self.var_scale1, self.cos1.edge)
        sc2 = self.compute_scale(self.var_scale2, self.cos2.edge)
        # if self.untwist:
        #   c2 = self.cos2.get_cross_curves(self.railSamples, 1.0, True)
        #   sc2.reverse()
        blends = list()
        for i in range(self.railSamples):
            pt1 = self.cos1.edgeOnFace.valueAt(self.cos1.param_list[i])
            pt2 = self.cos2.edgeOnFace.valueAt(self.cos2.param_list[i])
            c1 = self.cos1.get_cross_curve_toward_point(self.cos1.param_list[i],
                                                        pt2, 1e-1, False)
            c2 = self.cos2.get_cross_curve_toward_point(self.cos2.param_list[i],
                                                        pt1, 1e-1, False)
            b = nurbs_tools.blendCurve(c1, c2)
            b.cont1 = self.cont1
            b.cont2 = self.cont2
            if sc1:
                b.scale1 = sc1[i].y
            else:
                b.scale1 = self.scale1
            if sc2:
                b.scale2 = sc2[i].y
            else:
                b.scale2 = self.scale2
            b.compute()
            blends.append(b.shape())
            self.curves.append(b)
        return(blends)

    def cross_curves(self):
        self.curves = list()
        c1 = self.cos1.get_cross_curves(self.railSamples, 1.0)
        c2 = self.cos2.get_cross_curves(self.railSamples, 1.0)
        sc1 = self.compute_scale(self.var_scale1, self.cos1.edge)
        sc2 = self.compute_scale(self.var_scale2, self.cos2.edge)
        if self.untwist:
            c2 = self.cos2.get_cross_curves(self.railSamples, 1.0, True)
            sc2.reverse()
        blends = list()
        for i in range(self.railSamples):
            b = nurbs_tools.blendCurve(c1[i], c2[i])
            b.cont1 = self.cont1
            b.cont2 = self.cont2
            if sc1:
                b.scale1 = sc1[i].y
            else:
                b.scale1 = self.scale1
            if sc2:
                b.scale2 = sc2[i].y
            else:
                b.scale2 = self.scale2
            b.compute()
            blends.append(b.shape())
            self.curves.append(b)
        return(blends)

    def blend_curves(self):
        blend_curves = list()
        offset_curve_1 = self.cos1.get_offset_curve2d(0.1)
        offset_curve_2 = self.cos2.get_offset_curve2d(0.1)
        sc1 = self.compute_scale(self.var_scale1, self.cos1.edge)
        sc2 = self.compute_scale(self.var_scale2, self.cos2.edge)
        self.cos1.build_param_list(self.railSamples)
        self.cos2.build_param_list(self.railSamples)
        if self.untwist:
            self.cos2.param_list.reverse()
            sc2.reverse()
        for i in range(self.railSamples):
            c1 = self.cos1.get_cross_curve(offset_curve_1,
                                           self.cos1.param_list[i])
            c2 = self.cos2.get_cross_curve(offset_curve_2,
                                           self.cos2.param_list[i])
            b = nurbs_tools.blendCurve(c1, c2)
            b.cont1 = self.cont1
            b.cont2 = self.cont2
            b.param1 = b.edge1.LastParameter
            b.param2 = b.edge2.LastParameter
            if sc1:
                b.scale1 = sc1[i].y
            else:
                b.scale1 = self.scale1
            if sc2:
                b.scale2 = sc2[i].y
            else:
                b.scale2 = self.scale2
            b.compute()
            blend_curves.append(b.shape())
            self.curves.append(b)
        return(blend_curves)

    def get_gordon_shapes(self, curvetype=0):
        com1 = Part.Compound([self.cos1.edge, self.cos2.edge])
        com2 = Part.Compound(self.blend_curves())
        if curvetype == 1:
            com2 = Part.Compound(self.cross_curves2())
        return(Part.Compound([com1, com2]))

    def getPoints(self):
        pts = []
        for c in self.curves:
            e = c.toShape()
            pts.append(e.discretize(self.profSamples))
        return(pts)

    def getEdge(self, obj):
        res = None
        if hasattr(obj, "InputEdge"):
            o = obj.InputEdge[0]
            ss = obj.InputEdge[1][0]
            n = eval(ss.lstrip('Edge'))
            if len(o.Shape.Edges) >= n:
                res = o.Shape.Edges[n - 1]
        return(res)

    def getFace(self, obj):
        res = None
        if hasattr(obj, "Face"):
            o = obj.Face[0]
            ss = obj.Face[1][0]
            n = eval(ss.lstrip('Face'))
            if len(o.Shape.Faces) >= n:
                res = o.Shape.Faces[n - 1]
        return(res)

    def paramRange(self, cos):
        return(cos.lastParameter - cos.firstParameter)


def main():
    import FreeCADGui
    s = FreeCADGui.Selection.getSelection()

    o1 = s[0]
    o2 = s[1]

    bs = blendSurface(o1, o2)
    bs.railSamples = 32
    bs.profSamples = 16
    bs.untwist = False

    bs.buildCurves()
    pts = bs.getPoints()


if __name__ == '__main__':
    main()

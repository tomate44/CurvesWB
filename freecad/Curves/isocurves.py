# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "isoCurves for FreeCAD"
__author__ = "Chris_G"
__license__ = "LGPL 2.1"
__doc__ = '''
import isocurves
single = isocurves.isoCurve(face,'U',0.5)
Part.show(single.toShape())
multi  = isocurves.multiIso(face,10,20)
Part.show(multi.toShape())
'''

# from operator import itemgetter
import FreeCAD
from FreeCAD import Base
import Part
from freecad.Curves import _utils
from . import TOL3D


class curve(object):
    '''Base class of nurbs curves'''

    def __init__(self, edge=None):
        if edge is None:
            v1 = FreeCAD.Vector(0, 0, 0)
            v2 = FreeCAD.Vector(1, 0, 0)
            b = Part.BezierCurve()
            b.setPoles([v1, v2])
            self.curve = b
        elif isinstance(edge, Part.Edge):
            c = edge.Curve
            if isinstance(c, (Part.BezierCurve, Part.BSplineCurve)):
                self.curve = c
            else:
                bs = c.toBSpline()
                self.curve = bs
        elif isinstance(edge, (Part.BezierCurve, Part.BSplineCurve)):
            self.curve = edge

    def length(self):
        return self.curve.length()


class curveOnSurface(curve):
    '''defines a curve on a surface'''


class isoCurve:
    '''isoCurve of a surface'''

    def __init__(self, face, direc='U', param=0):
        self.face = None
        self.direction = 'U'
        self.parameter = 0
        if not isinstance(face, Part.Face):
            FreeCAD.Console.PrintMessage("Error. Not a face")
        else:
            self.bounds = face.ParameterRange
            self.face = face
        if direc not in 'UV':
            FreeCAD.Console.PrintMessage("Direction error")
        else:
            self.direction = direc
        if not isinstance(param, (float, int)):
            FreeCAD.Console.PrintMessage("Parameter error")
        else:
            self.parameter = param

    def faceBounds2d(self):
        edges2d = []
        for edge3d in self.face.OuterWire.Edges:
            if edge3d.isSeam(self.face):
                for pc in _utils.get_pcurves(edge3d):
                    s = pc[1]
                    s.transform(pc[2].Matrix)
                    match_surf = _utils.geom_equal(s, self.face.Surface)
                    if match_surf:
                        edges2d.append((pc[0], pc[-2], pc[-1]))
            else:
                edges2d.append(self.face.curveOnSurface(edge3d))
        # print(edges2d)
        return edges2d

    def getIntersectionPoints(self, l2d, bounds):
        pts = []
        for c2d in bounds:
            try:
                inter = l2d.intersectCC(c2d[0])
                pts.extend(inter)
            except RuntimeError:
                pass
        return pts

    def toShape(self):
        ext = 0.00
        bounds = self.faceBounds2d()
        prange = [0, 1]
        if self.direction == 'U':
            prange = self.bounds[2:]
            self.curve = self.face.Surface.uIso(self.parameter)
            v1 = Base.Vector2d(self.parameter, self.bounds[2] - ext)
            v2 = Base.Vector2d(self.parameter, self.bounds[3] + ext)
            l2d = Part.Geom2d.Line2dSegment(v1, v2)
            pts = self.getIntersectionPoints(l2d, bounds)
            if pts:
                sortedPts = sorted(pts, key=lambda v: v.y)
                prange = [l2d.parameter(sortedPts[0]), l2d.parameter(sortedPts[-1])]
            # else:
            #     FreeCAD.Console.PrintMessage("No intersection points\n")
        elif self.direction == 'V':
            prange = self.bounds[:2]
            self.curve = self.face.Surface.vIso(self.parameter)
            v1 = Base.Vector2d(self.bounds[0] - ext, self.parameter)
            v2 = Base.Vector2d(self.bounds[1] + ext, self.parameter)
            l2d = Part.Geom2d.Line2dSegment(v1, v2)
            pts = self.getIntersectionPoints(l2d, bounds)
            if pts:
                sortedPts = sorted(pts, key=lambda v: v.x)
                prange = [l2d.parameter(sortedPts[0]), l2d.parameter(sortedPts[-1])]
            # else:
            #     FreeCAD.Console.PrintMessage("No intersection points\n")
        e = None
        if (prange[1] - prange[0]) > 1e-9:
            e = l2d.toShape(self.face, prange[0], prange[1])
        if isinstance(e, Part.Edge):
            return e
        # else:
        #     FreeCAD.Console.PrintMessage("Failed to create isoCurve shape\n")
        #     return l2d.toShape(self.face)


class multiIso:
    '''defines a set of multiple iso curves on a face'''

    def __init__(self, face, numu=0, numv=0):
        self.face = None
        self.paramu = []
        self.paramv = []
        self.uiso = []
        self.viso = []
        if not isinstance(face, Part.Face):
            FreeCAD.Console.PrintMessage("Error. Not a face")
        else:
            self.bounds = face.ParameterRange
            self.face = face
        if numu:
            self.setNumberU(numu)
        if numv:
            self.setNumberV(numv)

    def computeU(self):
        self.uiso = []
        for u in self.paramu:
            self.uiso.append(isoCurve(self.face, 'U', u))

    def computeV(self):
        self.viso = []
        for v in self.paramv:
            self.viso.append(isoCurve(self.face, 'V', v))

    # def compute(self):
        # self.computeU()
        # self.computeV()

    def toShape(self):
        c = []
        for u in self.uiso:
            c.append(u.toShape())
        for v in self.viso:
            c.append(v.toShape())
        return Part.Compound(c)

    def paramList(self, n, fp, lp):
        par_range = lp - fp
        params = []
        if n == 1:
            params = [fp + par_range / 2.0]
        elif n == 2:
            params = [fp, lp]
        elif n > 2:
            for i in range(n):
                params.append(fp + 1.0 * i * par_range / (n - 1))
        return params

    def setNumberU(self, n):
        fp = self.bounds[0]
        lp = self.bounds[1]
        u0, u1, v0, v1 = self.face.Surface.bounds()
        uperiod = u1 - u0
        closed = False
        if self.face.Surface.isUClosed():
            if (abs(lp - fp - uperiod) < TOL3D):
                closed = True
                # print("U Closed")
        if closed:
            self.paramu = self.paramList(n + 1, fp, lp)[:-1]
        else:
            self.paramu = self.paramList(n, fp, lp)
        self.computeU()

    def setNumberV(self, n):
        fp = self.bounds[2]
        lp = self.bounds[3]
        u0, u1, v0, v1 = self.face.Surface.bounds()
        vperiod = v1 - v0
        closed = False
        if self.face.Surface.isVClosed():
            if (abs(lp - fp - vperiod) < TOL3D):
                closed = True
                # print("V Closed")
        if closed:
            self.paramv = self.paramList(n + 1, fp, lp)[:-1]
        else:
            self.paramv = self.paramList(n, fp, lp)
        self.computeV()

    def setNumbers(self, nu, nv):
        self.setNumberU(nu)
        self.setNumberV(nv)

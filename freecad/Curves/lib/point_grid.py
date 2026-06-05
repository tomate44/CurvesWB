# SPDX-License-Identifier: LGPL-2.1-or-later

from FreeCAD import Vector
import Part

from math import pi
from freecad.Curves.lib.point_list import PointList
from freecad.Curves.lib.precision import tol3d
from freecad.Curves.lib.timer import cls_timer
from freecad.Curves.lib.logger import FCLogger
from freecad.Curves.lib.math_util import float_range


class PointGrid:
    '''
    NxM point grid object
    '''

    def __init__(self, points=None, tol=tol3d):
        self.log = FCLogger("Debug", "PointGrid")
        if points is None:
            self.Points = self.debug_points()
        else:
            self.Points = []
            for row in points:
                if isinstance(row[0], Part.Vertex):
                    self.Points.append([Vector(v.Point) for v in row])
                else:
                    self.Points.append([Vector(v) for v in row])
        self.Tolerance = tol
        self.AverageParams = True

    def __str__(self):
        return f"Point Grid {self.NbU}x{self.NbV}"

    def __repr__(self):
        return str(self)

    def deepcopy(self):
        pg = PointGrid(self.Points, self.Tolerance)
        pg.AverageParams = self.AverageParams
        return pg

    @property
    def NbU(self):
        'Number of U lines'
        return len(self.Points)

    @property
    def NbV(self):
        'Number of V lines'
        return len(self.Points[0])

    def debug_points(self):
        'Returns a 6x4 point grid sample'
        sph = Part.Sphere()
        samplesU = [0.0, pi/6, pi/4, 3*pi/4, 5*pi/6, pi]
        samplesV = [0.0, 0.2, 0.8, 1.0]
        pts = []
        for u in samplesU:
            uiso = sph.uIso(u)
            pts.append([uiso.value(pow(v, 1.2)) for v in samplesV])
        return pts

    def discretize(self, surf, nbu, nbv):
        '''
        Sets the point grid by discretizing the surface.

        Arguments:
            surf: Part.Surface or Part.Face
            nbu: number of points in the U directions
            nbv: number of points in the V direction
        '''
        if isinstance(surf, Part.Face):
            u0, u1, v0, v1 = surf.ParameterRange
            s = surf.Surface
        else:
            u0, u1, v0, v1 = surf.bounds()
            s = surf
        pts = []
        for u in float_range(u0, u1, nbu):
            row = []
            for v in float_range(v0, v1, nbv):
                row.append(s.value(u, v))
            pts.append(row)
        self.Points = pts

    def rowU(self, idx):
        'Returns the row of U points at idx'
        return self.Points[idx]

    def rowV(self, idx):
        'Returns the row of V points at idx'
        return [self.Points[i][idx] for i in range(self.NbU)]

    def pointsU(self):
        for i in range(self.NbU):
            yield self.rowU(i)

    def pointsV(self):
        for i in range(self.NbV):
            yield self.rowV(i)

    def swapUV(self):
        'Swap U and V directions of the grid'
        self.Points = list(zip(*self.Points))

    # *** Shapes

    @property
    def ShapePoints(self):
        'Returns a coumpound of vertexes'
        comp = Part.Compound()
        for col in self.Points:
            comp.add(Part.Compound([Part.Vertex(p) for p in col]))
        return comp

    @property
    def ShapeLinesU(self):
        'Returns a compound of U polylines'
        comp = Part.Compound()
        for col in self.Points:
            comp.add(Part.makePolygon(col))
        return comp

    @property
    def ShapeLinesV(self):
        'Returns a compound of V polylines'
        comp = Part.Compound()
        for pts in self.pointsV():
            comp.add(Part.makePolygon(pts))
        return comp

    @property
    def ShapePolygon(self):
        'Returns a compound of U and V polylines'
        comp = Part.Compound()
        comp.add(self.ShapeLinesU)
        comp.add(self.ShapeLinesV)
        return comp

    # *** U Closed

    def is_Uclosed(self):
        closed = True
        for p1, p2 in list(zip(self.Points[0], self.Points[-1])):
            if p1.distanceToPoint(p2) > self.Tolerance:
                closed = False
        return closed

    def set_Uclosed(self):
        if not self.is_Uclosed():
            self.Points.append(self.Points[0])

    def set_Uopen(self):
        if self.is_Uclosed():
            self.Points = self.Points[:-1]

    # *** V Closed

    def is_Vclosed(self):
        closed = True
        for col in self.Points:
            if col[0].distanceToPoint(col[-1]) > self.Tolerance:
                closed = False
        return closed

    def set_Vclosed(self):
        if not self.is_Vclosed():
            pts = []
            for i in range(self.NbU):
                pts.append(self.Points[i] + [self.Points[i][0]])
            self.Points = pts

    def set_Vopen(self):
        if self.is_Vclosed():
            for i in range(self.NbU):
                self.Points[i] = self.Points[i][:-1]

    def compute_Uparams(self, factor=1.0):
        par = []
        for col in self.pointsU():
            pl = PointList(col, self.Tolerance)
            par.append(pl.compute_params(factor, [0.0, 1 / self.NbU]))
        average = [sum(pars) for pars in list(zip(*par))]
        return average

    def compute_Vparams(self, factor=1.0):
        par = []
        for col in self.pointsV():
            pl = PointList(col, self.Tolerance)
            par.append(pl.compute_params(factor, [0.0, 1 / self.NbV]))
        average = [sum(pars) for pars in list(zip(*par))]
        return average

    def interpolate_Ucurves(self, factor=1.0, periodic=False, average=True):
        # if periodic:
        #     self.set_Uclosed()
        if average:
            uparams = self.compute_Uparams(factor)
            # print(len(pts), uparams)
            curves = []
            for pts in self.pointsU():
                pl = PointList(pts, self.Tolerance)
                c = pl.interpolate(uparams, periodic, 3)
                curves.append(c.toShape())
            return Part.Compound(curves)
        curves = []
        for pts in self.pointsU():
            pl = PointList(pts, self.Tolerance)
            c = pl.interpolate(factor, periodic, 3)
            # print(len(pts), len(pl.Parameters))
            curves.append(c.toShape())
        return Part.Compound(curves)

    def interpolate_Vcurves(self, factor=1.0, periodic=False, average=True):
        pg = self.deepcopy()
        pg.swapUV()
        comp = pg.interpolate_Ucurves(factor, periodic, average)
        return comp

    @cls_timer
    def interpolate_surface(self, factors=[1.0, 1.0], periodic=[False, False], average=[True, True]):
        pg = self.deepcopy()
        if periodic[0]:
            pg.set_Uclosed()
        if periodic[1]:
            pg.set_Vclosed()

        comp = pg.interpolate_Ucurves(factors[1], periodic[1], average[1])
        c = comp.Edge1.Curve
        vdegree = c.Degree
        vknots = c.getKnots()
        vmults = c.getMultiplicities()
        vperiodic = c.isPeriodic()

        pg.Points = [e.Curve.getPoles() for e in comp.Edges]
        pg.swapUV()
        comp = pg.interpolate_Ucurves(factors[0], periodic[0], average[0])
        c = comp.Edge1.Curve
        udegree = c.Degree
        uknots = c.getKnots()
        umults = c.getMultiplicities()
        uperiodic = c.isPeriodic()

        pg.Points = [e.Curve.getPoles() for e in comp.Edges]
        pg.swapUV()
        poles = pg.Points

        bs = Part.BSplineSurface()
        print(f"{len(poles)}x{len(poles[0])}", umults, vmults, uknots, vknots, uperiodic, vperiodic, udegree, vdegree)
        bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots, uperiodic, vperiodic, udegree, vdegree)
        return bs

    @cls_timer
    def fc_interpolate(self):
        bs = Part.BSplineSurface()
        bs.interpolate(self.Points)
        return bs


'''
from importlib import reload
from freecad.Curves.lib import point_grid
reload(point_grid)

pg = point_grid.PointGrid()
Part.show(pg.ShapePolygon)
s = pg.interpolate_surface([1,1], [True, True])
Part.show(s.toShape())

'''

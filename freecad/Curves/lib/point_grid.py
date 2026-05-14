import FreeCAD
import Part

from math import pi
from freecad.Curves.lib.point_list import PointList
from freecad.Curves.lib.precision import tol3d
from freecad.Curves.lib.logger import FCLogger


class PointGrid:
    '''
    NxM point grid object
    '''

    def __init__(self, points=None, tol=tol3d):
        if points is None:
            self.pts = self.debug_points()
        else:
            self.pts = points
        self.tol = tol
        self.AverageParams = True

    def __str__(self):
        return f"Point Grid {self.NbU}x{self.NbV}"

    def __repr__(self):
        return str(self)

    def deepcopy(self):
        pts = [list(row) for row in self.pts]
        pg = PointGrid(pts, self.tol)
        pg.AverageParams = self.AverageParams
        return pg

    @property
    def NbU(self):
        'Number of U lines'
        return len(self.pts)

    @property
    def NbV(self):
        'Number of V lines'
        return len(self.pts[0])

    def debug_points(self):
        'Returns a 4x4 point grid sample'
        sph = Part.Sphere()
        samplesU = [0.0, pi/6, pi/4, 3*pi/4, 5*pi/6, pi]
        samplesV = [0.0, 0.2, 0.8, 1.0]
        pts = []
        for u in samplesU:
            uiso = sph.uIso(u)
            pts.append([uiso.value(pow(v, 1.2)) for v in samplesV])
        return pts

    def rowU(self, idx):
        'Returns the row of U points at idx'
        return self.pts[idx]

    def rowV(self, idx):
        'Returns the row of V points at idx'
        return [self.pts[i][idx] for i in range(self.NbU)]

    def pointsU(self):
        for i in range(self.NbU):
            yield self.rowU(i)

    def pointsV(self):
        for i in range(self.NbV):
            yield self.rowV(i)

    def swapUV(self):
        'Swap U and V directions of the grid'
        self.pts = list(zip(*self.pts))

    # *** Shapes

    @property
    def ShapePoints(self):
        'Returns a coumpound of vertexes'
        comp = Part.Compound()
        for col in self.pts:
            comp.add(Part.Compound([Part.Vertex(p) for p in col]))
        return comp

    @property
    def ShapeLinesU(self):
        'Returns a compound of U polylines'
        comp = Part.Compound()
        for col in self.pts:
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
        for p1, p2 in list(zip(self.pts[0], self.pts[-1])):
            if p1.distanceToPoint(p2) > self.tol:
                closed = False
        return closed

    def set_Uclosed(self):
        if not self.is_Uclosed():
            self.pts.append(self.pts[0])

    def set_Uopen(self):
        if self.is_Uclosed():
            self.pts = self.pts[:-1]

    # *** V Closed

    def is_Vclosed(self):
        closed = True
        for col in self.pts:
            if col[0].distanceToPoint(col[-1]) > self.tol:
                closed = False
        return closed

    def set_Vclosed(self):
        if not self.is_Vclosed():
            pts = []
            for i in range(self.NbU):
                pts.append(self.pts[i] + [self.pts[i][0]])
            self.pts = pts

    def set_Vopen(self):
        if self.is_Vclosed():
            for i in range(self.NbU):
                self.pts[i] = self.pts[i][:-1]

    def compute_Uparams(self, factor=1.0):
        par = []
        for col in self.pointsU():
            pl = PointList(col, self.tol)
            par.append(pl.compute_params(factor, [0.0, 1 / self.NbU]))
        average = [sum(pars) for pars in list(zip(*par))]
        return average

    def compute_Vparams(self, factor=1.0):
        par = []
        for col in self.pointsV():
            pl = PointList(col, self.tol)
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
                pl = PointList(pts, self.tol)
                c = pl.interpolate(uparams, periodic, 3)
                curves.append(c.toShape())
            return Part.Compound(curves)
        curves = []
        for pts in self.pointsU():
            pl = PointList(pts, self.tol)
            c = pl.interpolate(factor, periodic, 3)
            # print(len(pts), len(pl.Parameters))
            curves.append(c.toShape())
        return Part.Compound(curves)

    def interpolate_Vcurves(self, factor=1.0, periodic=False, average=True):
        pg = self.deepcopy()
        pg.swapUV()
        comp = pg.interpolate_Ucurves(factor, periodic, average)
        return comp

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
        pts = [e.Curve.getPoles() for e in comp.Edges]
        pg = PointGrid(pts, self.tol)
        comp = pg.interpolate_Vcurves(factors[0], periodic[0], average[0])
        pts = [e.Curve.getPoles() for e in comp.Edges]
        pg = PointGrid(pts, self.tol)
        # print(pg)
        pg.swapUV()
        poles = pg.pts
        c = comp.Edge1.Curve
        udegree = c.Degree
        uknots = c.getKnots()
        umults = c.getMultiplicities()
        uperiodic = c.isPeriodic()
        bs = Part.BSplineSurface()
        print(f"{len(poles)}x{len(poles[0])}", umults, vmults, uknots, vknots, uperiodic, vperiodic, udegree, vdegree)
        bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots, uperiodic, vperiodic, udegree, vdegree)
        return bs


'''
from importlib import reload
from freecad.Curves.lib import point_grid
reload(point_grid)

pg = point_grid.PointGrid()
Part.show(pg.ShapePolygon)
s = pg.interpolate_surface([1,1], [False, True], [False, False])
Part.show(s.toShape())

'''

# SPDX-License-Identifier: LGPL-2.1-or-later

from FreeCAD import Vector
import Part

from freecad.Curves.lib.precision import tol3d


class PointParameters(list):
    def __init__(self, params=[]):
        super().__init__(params)
    
    def __add__(self, other):
        if isinstance(other, (int, float)):
            return PointParameters([self[i] + other for i in range(len(self))])
        if not self.__len__() == other.__len__():
            raise ValueError("The two lists must have the same length")
        return PointParameters([self[i] + other[i] for i in range(len(self))])
    
    def __radd__(self, other):
        return self + other
    
    def __iadd__(self, other):
        if not self.__len__() == other.__len__():
            raise ValueError("The two lists must have the same length")
        for i in range(len(self)):
            self[i] += other[i]
        return self
    
    def __mul__(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f"numeric value expected, got {type(value).__name__}")
        return PointParameters([item * value for item in self])
    
    def __rmul__(self, value):
        return self * value
    
    def __truediv__(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f"numeric value expected, got {type(value).__name__}")
        return PointParameters([item / value for item in self])
    
    def scale_to_bounds(self, a, b):
        fac = (b - a) / (self[-1] - self[0])
        return PointParameters([a + fac * (val - self[0]) for val in self])
    
    def set_bounds(self, a, b):
        fp = self[0]
        lp = self[-1]
        fac = (b - a) / (lp - fp)
        for i in range(len(self)):
            nval = a + fac * (self[i] - fp)
            self[i] = nval
    
    def normalized(self):
        return self.scale_to_bounds(0.0, 1.0)
    
    def normalize(self):
        self.set_bounds(0.0, 1.0)




class PointList:
    '''
    PointList object (mainly for interpolation)

    Attributes:
        Points: a list of consecutive FreeCAD.Vector
        Tolerance: geometric tolerance
    '''

    def __init__(self, pts=None, tol=tol3d):
        '''
        Initialisation of the PointList.

        Arguments:
            pts: list of FreeCAD.Vector(or Part.Vertex) or None
                  if None, a default list is created (see method debug_points)
            tol: geometric tolerance
        '''
        if isinstance(pts, PointList):
            self._pts = pts.Points
            self.Tolerance = pts.Tolerance
        else:
            self.Points = pts
            self.Tolerance = tol

    def __str__(self):
        closed = ""
        if self.is_closed():
            closed = " Closed"
        return f"Point List : {self.Nb} points{closed}"

    def __repr__(self):
        return str(self)

    @property
    def Points(self):
        return self._pts

    @Points.setter
    def Points(self, pts):
        if isinstance(pts[0], Part.Vertex):
            self._pts = [Vector(v.Point) for v in pts]
        else:
            self._pts = [Vector(p) for p in pts]

    @property
    def Nb(self):
        'Number of Points'
        return len(self.Points)

    def deepcopy(self):
        return PointList(self.Points, self.Tolerance)

    # *** Shapes

    @property
    def ShapePoints(self):
        'Returns a coumpound of vertexes'
        return Part.Compound([Part.Vertex(p) for p in self.Points])

    @property
    def ShapePolygon(self):
        'Returns a polygon wire of the points'
        if not self.has_duplicates():
            return Part.makePolygon(self.Points)
        return Part.Shape()

    # *** Closedness

    def is_closed(self):
        'Returns True if first and last points are identical'
        return self.Points[0].distanceToPoint(self.Points[-1]) < self.Tolerance

    def set_closed(self):
        'If Point List is not closed, append first point'
        if not self.is_closed():
            # print(self.Points)
            self.Points.append(self.Points[0])

    def set_open(self):
        'If Point List is closed, remove last point'
        if self.is_closed():
            self.Points = self.Points[:-1]

    # *** Other methods

    def has_duplicates(self):
        for i in range(1, self.Nb):
            d = self.Points[i].distanceToPoint(self.Points[i - 1])
            if d < self.Tolerance:
                return True
        return False

    def compute_params(self, param_factor=1.0):
        '''
        Computes a list of parameters from the points
        param_factor (float) : parameterization factor, usually between 0.0 and 1.0
            0.0 -> Uniform / 0.5 -> Centripetal / 1.0 -> Chord-Length
        Returns a list of floats
        '''
        pl = [0.0]
        for i in range(1, len(self.Points)):
            p = self.Points[i] - self.Points[i - 1]
            span = pow(p.Length, param_factor)
            pl.append(pl[-1] + span)
        self.Parameters = pl
        return pl


class PointListSample:
    '''
    Create various PointList objects for testing purpose
    '''

    def __init__(self):
        return

    def duplicate_points(self, nb=10):
        '''
        Create an list of nb duplicate points
        '''
        pts = [Vector()] * nb
        return PointList(pts)

    def oscillating_circle(self, nb=10):
        '''
        Returns an open list of nb points around a circle
        with alternating Z height.
        Useful to test periodic interpolation
        '''
        ci = Part.Circle(Vector(0, 0, 0), Vector(0, 0, 1), 1.0)
        pts = ci.discretize(nb + 1)[:-1]
        offsetZ = 1
        for p in pts:
            p.z += offsetZ
            offsetZ = -offsetZ
        return PointList(pts)

    def square(self, nb=3):
        '''
        Returns an open list of 4 * nb points on a square
        Useful to test Akima interpolation
        '''
        pts = []
        vl = [[Vector(-1, -1, -1), Vector(-1, 1, -1)],
              [Vector(-1, 1, 1), Vector(1, 1, 1)],
              [Vector(1, 1, -1), Vector(1, -1, -1)],
              [Vector(1, -1, 1), Vector(-1, -1, 1)]]
        for p1, p2 in vl:
            li = Part.makeLine(p1, p2)
            pts.extend(li.discretize(nb + 2)[1:-1])
        return PointList(pts)


'''
from importlib import reload
from freecad.Curves.lib import point_list
reload(point_list)

pls = point_list.PointListSample()
pl1 = pls.duplicate_points(10)
pl2 = pls.oscillating_circle(10)
pl3 = pls.square(10)

for pl in [pl1, pl2, pl3]:
    print(pl)
    Part.show(pl.ShapePoints, "Points")
    Part.show(pl.ShapePolygon, "Polyline")
    pars = pl.compute_params(1.0)
    print(pars)


'''

import FreeCAD
import Part


"""
from freecad.Curves.lib.point_array import PointArray
pa = PointArray(f1.Surface.getPoles())
pa.extend(0.2, 0.3, 0.4, 0.5)
# pa.multi_extend(5,5,5,5,2)
Part.show(pa.Shape)
bs = Part.BSplineSurface()
bs.interpolate(pa.pts)
Part.show(bs.toShape())
"""


class PointArray:
    "NxM point array"

    def __init__(self, array=[]):
        self.pts = array

    def __repr__(self):
        return f"PointArray ({len(self.pts)}x{len(self.pts[0])})"

    @property
    def Shape(self):
        comp = Part.Compound()
        for row in self.pts:
            comp.add(Part.Compound([Part.Vertex(p) for p in row]))
        return comp

    def multi_extend(self, u0=1, u1=1, v0=1, v1=1, order=1):
        """
        Extend the array in U and / or V direction
        u0, u1, v0, v1 (int) : number of rows / cols to add in each direction
        order (int) : 1 = linear / 2 = 2nd order
        """
        for u in range(u0):
            for i in range(len(self.pts)):
                pt1 = self.pts[i][1]
                pt0 = self.pts[i][0]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[i][2]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                npt = pt0 + vec
                self.pts[i].insert(0, npt)
        for u in range(u1):
            for i in range(len(self.pts)):
                pt1 = self.pts[i][-2]
                pt0 = self.pts[i][-1]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[i][-3]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                npt = pt0 + vec
                self.pts[i].append(npt)
        for v in range(v0):
            pl = []
            for i in range(len(self.pts[0])):
                pt1 = self.pts[1][i]
                pt0 = self.pts[0][i]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[2][i]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                npt = pt0 + vec
                pl.append(npt)
            self.pts.insert(0, pl)
        for v in range(v1):
            pl = []
            for i in range(len(self.pts[0])):
                pt1 = self.pts[-2][i]
                pt0 = self.pts[-1][i]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[-3][i]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                npt = pt0 + vec
                pl.append(npt)
            self.pts.append(pl)


    def extend(self, u0=1, u1=1, v0=1, v1=1, order=1, num=1):
        """
        Extend the array in U and / or V direction
        u0, u1, v0, v1 (float) : length of extension in each direction
        order (int) : 1 = linear / 2 = 2nd order
        num (int) : number of points to add
        """
        for n in range(num):
            for i in range(len(self.pts)):
                pt1 = self.pts[i][1]
                pt0 = self.pts[i][0]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[i][2]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                vec.normalize()
                npt = pt0 + vec * u0 / num
                self.pts[i].insert(0, npt)
        for n in range(num):
            for i in range(len(self.pts)):
                pt1 = self.pts[i][-2]
                pt0 = self.pts[i][-1]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[i][-3]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                vec.normalize()
                npt = pt0 + vec * u1 / num
                self.pts[i].append(npt)
        for n in range(num):
            pl = []
            for i in range(len(self.pts[0])):
                pt1 = self.pts[1][i]
                pt0 = self.pts[0][i]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[2][i]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                vec.normalize()
                npt = pt0 + vec * v0 / num
                pl.append(npt)
            self.pts.insert(0, pl)
        for n in range(num):
            pl = []
            for i in range(len(self.pts[0])):
                pt1 = self.pts[-2][i]
                pt0 = self.pts[-1][i]
                vec = pt0 - pt1
                if order == 2:
                    pt2 = self.pts[-3][i]
                    v2 = pt1 - pt2
                    rot = FreeCAD.Rotation(v2, vec)
                    vec = rot.multVec(vec)
                vec.normalize()
                npt = pt0 + vec * v1 / num
                pl.append(npt)
            self.pts.append(pl)


# -*- coding: utf-8 -*-

__title__ = ""
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """"""

# from time import time
# from math import pi
# from operator import itemgetter

import FreeCAD
import FreeCADGui
import Part
# import numpy as np
# from scipy.linalg import solve

# from .. import _utils
# from .. import curves_to_surface
# from ..nurbs_tools import nurbs_quad


def printError(string):
    FreeCAD.Console.PrintError(str(string) + "\n")

# def vec3_to_string(v):
#     return f"Vector({v.x:6.2f}, {v.y:6.2f}, {v.z:6.2f})"


class ProfileWire:
    def __init__(self, shape):
        self.Shape = shape
        self.XYShape = shape
        self.Matrix = FreeCAD.Matrix()
        self.Normal = self.get_normal()
        self.Center = self.Shape.CenterOfGravity
        self.AxisX = None
        # self._default_indices = list(range(len(shape.Edges)))
        # self._edgeid = self._default_indices

    def get_normal(self):
        pl = self.Shape.findPlane()
        if pl is not None:
            return pl.Axis
        pts = self.Shape.discretize(4)
        tn = FreeCAD.Vector()
        for i in range(1, len(pts)):
            v1 = pts[i - 1] - self.Center
            v2 = pts[i] - self.Center
            tn += v1.cross(v2)
        if tn.Length > 1e-5:
            return tn.normalize()

    def normal_line(self):
        if self.Normal:
            return Part.Line(self.Center, self.Normal)

    def transform(self):
        self.Matrix.setCol(0, self.AxisX)
        self.Matrix.setCol(1, self.Normal.cross(self.AxisX))
        self.Matrix.setCol(3, self.Normal)
        self.Matrix.setCol(4, self.Center)
        self.XYShape = self.Shape.transformGeometry(self.Matrix)

    def normalize_size(self):
        bb = self.XYShape.BoundBox
        xfac, yfac = 1.0, 1.0
        if bb.XLength > 1e-5:
            xfac = 1 / bb.XLength
        if bb.YLength > 1e-5:
            yfac = 1 / bb.YLength
        m = FreeCAD.Matrix()
        m.move(-bb.Center)
        m.scale(xfac, yfac, 1.0)
        self.XYShape = self.Shape.transformGeometry(m)

    def toShape(self):
        return self.Shape


class ProfileWires:
    def __init__(self, shape):
        self.Shape = shape
        self.WireProfiles = [ProfileWire(w) for w in shape.Wires]
        self._default_indices = list(range(len(shape.Wires)))
        self._wireid = self.default_indices

    def Wires(self, idx):
        assert (sorted(self._wireid) == self._default_indices)
        return self.Shape.WireProfiles[self._wireid[idx]]

    def toShape(self):
        wires = [wp.toShape() for wp in self.WireProfiles]
        return Part.Compound(wires)


class ProfileFace(ProfileWires):
    def __init__(self, shape):
        super().__init__(shape)

    def toShape(self):
        wires = [wp.toShape() for wp in self.WireProfiles]
        f = Part.Face(self.Shape.Face1.Surface, wires)
        return f


class ProfileMatcher:
    def __init__(self, shapes, verttol=0.1, removeC1=True, angtol=0.1):
        print(self.__class__.__name__)
        self.Profiles = []
        self.VertexTol = verttol
        self.AngTol = angtol
        self.AutoOrient = True
        self.RemoveC1 = removeC1
        for sh in shapes:
            prof = self.create_profile(sh)
            print(f"Adding {prof.__class__.__name__}")
            self.Profiles.append(prof)
        # print(self.Profiles)

    @property
    def Shape(self):
        return Part.Compound([p.toShape() for p in self.Profiles])

    def create_profile(self, shape):
        if isinstance(shape, Part.Face):
            return ProfileFace(shape)
        elif len(shape.Wires) > 1:
            return ProfileWires(shape)
        elif len(shape.Wires) == 1:
            return ProfileWire(shape)

    def compatible_profiles(self):
        numlist = [len(p.Shape.Edges) for p in self.Profiles]
        reduced = list(set(numlist))
        if len(reduced) == 1:
            return True
        return False

    def auto_orient(self):
        for i in range(len(self.Profiles) - 1):
            pro1 = self.Profiles[i]
            pro2 = self.Profiles[i + 1]
            if pro1.Normal and pro2.Normal:
                if pro1.normal_line().parameter(pro2.Center) < 0.0:
                    pro1.Normal.reverse()
                pl1 = Part.Plane(pro1.Center, pro1.Normal)
                pl2 = Part.Plane(pro2.Center, pro2.Normal)
                inters = pl1.intersectSS(pl2)
                if inters:
                    pro1.AxisX = inters[0].Direction
                    pro2.AxisX = inters[0].Direction
        return

    def find_C1_vertexes(self):
        return

    def match_vertexes(self):
        return

    def insert_extra_vertexes(self):
        return

    def remove_C1_vertexes(self):
        return

    def match(self):
        if self.AutoOrient:
            self.auto_orient()
        if self.compatible_profiles():
            return
        if self.RemoveC1:
            self.find_C1_vertexes()
        self.match_vertexes()
        self.insert_extra_vertexes()
        if self.RemoveC1:
            self.remove_C1_vertexes()


def test():
    sel = FreeCADGui.Selection.getSelection()
    return ProfileMatcher([o.toShape() for o in sel])



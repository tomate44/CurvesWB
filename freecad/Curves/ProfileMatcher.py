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

from . import nurbs_tools
# from .. import curves_to_surface
# from ..nurbs_tools import nurbs_quad


def printError(string):
    FreeCAD.Console.PrintError(str(string) + "\n")

# def vec3_to_string(v):
#     return f"Vector({v.x:6.2f}, {v.y:6.2f}, {v.z:6.2f})"


class Profile:
    def __init__(self, shape):
        self.Shape = shape  # self.cleanup(shape)
        self.XYShape = self.Shape
        self.Matrix = FreeCAD.Matrix()
        self.Normal = self.get_normal()
        self.Center = self.Shape.CenterOfGravity
        self._axisX = None

    @property
    def AxisX(self):
        return self._axisX

    @AxisX.setter
    def AxisX(self, val):
        self._axisX = val
        if isinstance(self._axisX, FreeCAD.Vector):
            self._axisX.normalize()

    def get_normal(self):
        pl = self.Shape.findPlane()
        if pl is not None:
            return pl.Axis

    def normal_line(self):
        return Part.Line(self.Center, self.Normal)

    def transform(self, normalize=False):
        self.Matrix.setCol(1, self.AxisX)
        self.Matrix.setCol(0, self.Normal.cross(self.AxisX))
        self.Matrix.setCol(2, self.Normal)
        self.Matrix.setCol(3, self.Center)
        self.XYShape = self.Shape.transformGeometry(self.Matrix.inverse())
        if normalize:
            self.normalize_size()

    def normalize_size(self):
        bb = self.XYShape.BoundBox
        xfac, yfac = 1.0, 1.0
        if bb.XLength > 1e-5:
            xfac = 1 / bb.XLength
        if bb.YLength > 1e-5:
            yfac = 1 / bb.YLength
        m = FreeCAD.Matrix()
        # m.move(-bb.Center)
        m.scale(xfac, yfac, 1.0)
        self.XYShape = self.XYShape.transformGeometry(m)


class ProfileWire(Profile):
    def __init__(self, shape):
        super().__init__(shape)
        if self.Normal is None:
            self.Normal = self.get_normal()
        if not self.Shape.isClosed():
            pts = self.XYShape.discretize(2)
            self._axisX = pts[1] - pts[0]
        # self._default_indices = list(range(len(self.Shape.Edges)))
        # self._edgeid = self._default_indices

    def transform(self, normalize=False):
        super().transform(normalize)
        self.XYShape = self.XYShape.Wire1

    def normalize_size(self):
        super().normalize_size()
        self.XYShape = self.XYShape.Wire1

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
        print("Failed to get a normal vector")

    def set_normals_towards(self, other):
        if self.Normal:
            if self.normal_line().parameter(other.Center) < 0.0:
                self.Normal = -self.Normal
            if other.normal_line().parameter(self.Center) < 0.0:
                other.Normal = -other.Normal
            return
        ml = Part.makeLine(self.Center, other.Center)
        self.Normal = ml.Curve.Direction

    def set_xaxis_with(self, other):
        pl1 = Part.Plane(self.Center, self.Normal)
        pl2 = Part.Plane(other.Center, other.Normal)
        inters = pl1.intersectSS(pl2)
        axis = self.Normal.cross(other.Normal)

        if inters:
            axis = inters[0].Direction
        else:  # profiles have parallel normals
            if pl1.normal(0, 0).dot(FreeCAD.Vector(1, 0, 0)) < 0.5:
                axis = pl1.normal(0, 0).cross(FreeCAD.Vector(1, 0, 0))
            else:
                axis = pl1.normal(0, 0).cross(FreeCAD.Vector(0, 1, 0))
        self.AxisX = axis
        other.AxisX = axis

    def shift_origin(self, other=None):
        self.transform(True)
        if not self.Shape.isClosed():
            return
        if other is None:
            v = Part.Vertex(FreeCAD.Vector(1, 0, 0))
            d, pts, info = self.XYShape.distToShape(v)
            idx = 0
            if info[0][0] == "Edge":
                idx = info[0][1]
            elif info[0][0] == "Vertex":
                # A more robust method is needed here
                idx = info[0][1]
            print(f"Shifting origin to edge {idx}")
            edges = self.Shape.Edges[idx:] + self.Shape.Edges[:idx]
            self.Shape = Part.Wire(edges)
            self.transform(True)
            return

        v = other.XYShape.Edge1.firstVertex()
        comp = Part.Compound([e.firstVertex() for e in self.XYShape.Edges])
        d, pts, info = comp.distToShape(v)
        new_origin = info[0][1]
        if new_origin > 0:
            print(f"Shifting origin to vertex {new_origin}")
            edges = self.Shape.Edges[new_origin:] + self.Shape.Edges[:new_origin]
            self.Shape = Part.Wire(edges)
            self.transform(True)

    def orient(self):
        if not self.Shape.isClosed():
            pts = self.XYShape.discretize(2)
            # print(pts)
            rev = pts[0].y > pts[1].y
        else:
            pts = self.XYShape.discretize(5)
            rev = pts[1].y < pts[3].y
        if rev:
            print("Reversing profile")
            edges = []
            for e in self.Shape.Edges[::-1]:
                e.reverse()
                edges.append(e)
            self.Shape = Part.Wire(edges)
            self.transform(True)

    def orient_with_openwire(self, other):
        v = other.XYShape.Edge1.Vertex1
        comp = Part.Compound([self.XYShape.Edges[0].Vertexes[0], self.XYShape.Edges[-1].Vertexes[-1]])
        d, pts, info = comp.distToShape(v)
        new_origin = info[0][1]
        print(new_origin)
        if new_origin == 1:
            print(f"Reversing open profile")
            self.Shape = Part.Wire(self.Shape.Edges[::-1])
            self.transform(True)

    def match_points(self, pts1, pts2):
        idx = []
        vl = Part.Compound([Part.Vertex(p) for p in pts2])
        for p in pts1:
            v = Part.Vertex(p)
            d, pts, info = vl.distToShape(v)
            idx.append(info[0][1])
        return idx

    def match_with(self, other):
        self.transform(True)
        other.transform(True)
        if self.Shape.isClosed() and other.Shape.isClosed():
            self.shift_origin(other)
            pts1 = self.XYShape.discretize(5)[1:-1]
            pts2 = other.XYShape.discretize(5)[1:-1]
            idx = self.match_points(pts1, pts2)
            if idx == [3, 2, 1]:
                print(f"Reversing closed profile")
                self.Shape = Part.Wire(self.Shape.Edges[::-1])
                self.transform(True)
        else:
            self.orient_with_openwire(other)

    def LCS_Shape(self):
        l1 = Part.makeLine(self.Center, self.Center + self.Normal * 20)
        l2 = Part.makeLine(self.Center, self.Center + self.AxisX * 40)
        return Part.Compound([l1, l2])

    def toShape(self, xy=False):
        if xy:
            self.transform(True)
            return self.XYShape
        return self.Shape


class ProfileWires(Profile):
    def __init__(self, shape):
        super().__init__(shape)
        self.WireProfiles = [ProfileWire(w) for w in shape.Wires]
        self._default_indices = list(range(len(shape.Wires)))
        self._wireid = self._default_indices

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
        # return self.CompoundLCS()
        return Part.Compound([p.toShape(False) for p in self.Profiles])

    def CompoundLCS(self):
        return Part.Compound([p.LCS_Shape() for p in self.Profiles])

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

    def all_normals_defined(self):
        nl = [isinstance(p.Normal, FreeCAD.Vector) for p in self.Profiles]
        return all(nl)

    def cog_interpolation(self):
        """Returns the curve interpolating the profiles Centers of gravity,
        and the corresponding parameters"""
        pts = [p.Center for p in self.Profiles]
        params = nurbs_tools.parameterization(pts, 0.5)
        for i in range(len(self.Profiles)):
            self.Profiles[i].Parameter = params[i]
        bs = Part.BSplineCurve()
        bs.interpolate(Points=pts, Parameters=params)
        return bs, params

    def harmonize_normals(self):
        bs, params = self.cog_interpolation()
        for i in range(len(self.Profiles)):
            dot = self.Profiles[i].Normal.dot(bs.tangent(params[i])[0])
            if dot < 0:
                print(f"Reversing normal of profile {i}")
                self.Profiles[i].Normal = -self.Profiles[i].Normal
                # self.Profiles[i].transform()

    def set_binormals(self):
        print("setting binormals")
        found = 0
        last_axis = None
        for i in range(len(self.Profiles) - 1):
            if not isinstance(self.Profiles[i].AxisX, FreeCAD.Vector):
                n = self.Profiles[i].Normal.cross(self.Profiles[i + 1].Normal)
                if n.Length > 1e-5:
                    self.Profiles[i].AxisX = n
            if isinstance(self.Profiles[i].AxisX, FreeCAD.Vector):
                found += 1
                last_axis = self.Profiles[i].AxisX

        if found == 0:
            pl1 = Part.Plane(self.Profiles[0].Center, self.Profiles[0].Normal)
            binor = pl1.tangent(0, 0)[0]
            for p in self.Profiles:
                p.AxisX = binor
            return

        if found == 1:
            for p in self.Profiles:
                p.AxisX = last_axis
            return

    def orient_binormals(self):
        old_binor = self.Profiles[0].AxisX
        for i in range(1, len(self.Profiles)):
            pro1 = self.Profiles[i]
            if (old_binor is not None) and (pro1.AxisX is not None):
                dot = old_binor.dot(pro1.AxisX)
                if dot < 0:
                    pro1.AxisX = -pro1.AxisX
                    old_binor = pro1.AxisX
            if (old_binor is None) and (pro1.AxisX is not None):
                old_binor = pro1.AxisX

        # populate binormals at the end of profiles list
        old_binor = None
        for p in self.Profiles:
            if p.AxisX is not None:
                old_binor = p.AxisX
            if (p.AxisX is None) and (old_binor is not None):
                p.AxisX = old_binor

        # populate binormals at the beginning of profiles list
        old_binor = None
        for p in self.Profiles[::-1]:
            if p.AxisX is not None:
                old_binor = p.AxisX
            if (p.AxisX is None) and (old_binor is not None):
                p.AxisX = old_binor

        # interpolate existing binormals
        pts = []
        params = []
        for p in self.Profiles:
            if p.AxisX is not None:
                pts.append(p.AxisX + p.Center)
                params.append(p.Parameter)
        bs = Part.BSplineCurve()
        print(pts, params)
        bs.interpolate(Points=pts, Parameters=params)

        # populate remaining binormals
        for p in self.Profiles:
            if p.AxisX is None:
                p.AxisX = bs.value(p.Parameter) - p.Center

    def auto_orient(self):
        for i, p in enumerate(self.Profiles):
            print(f"shift origin profile {i}")
            p.shift_origin()
            p.orient()
        return
        # for i in range(len(self.Profiles) - 1):
        #     print(f"Orienting profile {i + 1}")
        #     pro1 = self.Profiles[i]
        #     pro2 = self.Profiles[i + 1]
        #     pro1.set_normals_towards(pro2)
        #     pro1.set_xaxis_with(pro2)
        #     pro2.match_with(pro1)
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
        self.harmonize_normals()
        self.set_binormals()
        self.orient_binormals()
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



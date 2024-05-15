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


class Profile:
    def __init__(self, shape, matrix=None):
        self.Shape = shape
        self.Matrix = matrix
        self.ShapeType = "Wires"
        if len(self.Shape.Faces) > 1:
            printError("Profile with multiple faces not supported. Taking 1st face")
        if self.Shape.Faces:
            self.Shape = self.Shape.Face1
            self.ShapeType = "Face"
            self.WireProfiles = [self.__class__(w, self.Matrix) for w in self.Shape.Wires]
        elif len(self.Shape.Wires) == 0:
            printError("Profile : wires required")
            sortedges = Part.sortEdges(self.Shape.Edges)
            if len(sortedges) == 1:
                self.Shape = Part.Wire(sortedges[0])
                self.ShapeType = "Wire"
                self.WireProfiles = [self.__class__(self.Shape.Wire1, self.Matrix)]
        elif len(self.Shape.Wires) == 1:
            self.ShapeType = "Wire"
            self.WireProfiles = [self]  # .__class__(self.Shape.Wire1, self.Matrix)]
        else:
            self.WireProfiles = [self.__class__(w, self.Matrix) for w in self.Shape.Wires]
        self.COG = self.Shape.CenterOfGravity

    def toShape(self):
        if self.ShapeType == "Face":
            wires = [wp.toShape() for wp in self.WireProfiles]
            f = Part.Face(self.Shape.Face1.Surface, wires)
            return f
        elif self.ShapeType == "Wires":
            wires = [wp.toShape() for wp in self.WireProfiles]
            comp = Part.Compound(wires)
            return comp
        elif self.ShapeType == "Wire":
            wire = self.WireProfiles[0].toShape()
            return wire


class ProfileMatcher:
    def __init__(self, shapes):
        self.Profiles = []
        for sh in shapes:
            if hasattr(sh, "WireProfiles"):
                self.Profiles.append(sh)
            elif hasattr(sh, "Solids"):
                self.Profiles.append(Profile(sh))

def test():
    sel = FreeCADGui.Selection.getSelection()
    return ProfileMatcher([o.Shape for o in sel])



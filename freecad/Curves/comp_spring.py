# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Compression Spring"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Parametric Compression Spring"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import os
import FreeCAD
import FreeCADGui
import Part
from Part import Geom2d
from math import pi
from freecad.Curves import ICONPATH
Vector = FreeCAD.Base.Vector
Vector2d = FreeCAD.Base.Vector2d


TOOL_ICON = os.path.join(ICONPATH, 'spring.svg')
# debug = _utils.debug
# debug = _utils.doNothing


class CompSpring(object):
    def __init__(self, length=10, turns=8, wireDiam=0.5, diameter=4.0, flatness=100, reverse=False):
        self.length = length
        self.turns = turns
        self.wire_diam = wireDiam
        self.diameter = diameter
        self.flatness = flatness
        self.reverse = reverse

    def compute_path_cp(self):
        skew = Part.LineSegment(Vector(2 * pi, self.wire_diam, 0), Vector((self.turns - 1) * 2 * pi, self.length - self.wire_diam, 0))
        tan = skew.tangent(skew.FirstParameter)[0]
        tan.normalize()
        tan.multiply(self.wire_diam / 2.0)
        p1 = Vector(-tan.y, tan.x, 0)
        ls = Part.Line(skew.StartPoint + p1, skew.EndPoint - p1)
        h1 = Part.Line(Vector(0, self.wire_diam / 2.0, 0), Vector(1, self.wire_diam / 2.0, 0))
        h2 = Part.Line(Vector(0, self.length - self.wire_diam / 2.0, 0), Vector(1, self.length - self.wire_diam / 2.0, 0))
        pts = [Vector2d(0, self.wire_diam / 2.0)]
        i1 = h1.intersect(ls)[0]
        i2 = h2.intersect(ls)[0]
        pts.append(Vector2d(i1.X, i1.Y))
        pts.append(Vector2d(i2.X, i2.Y))
        pts.append(Vector2d(self.turns * 2 * pi, self.length - self.wire_diam / 2.0))
        return pts

    def path2d(self):
        poles = self.compute_path_cp()
        bs = Geom2d.BSplineCurve2d()
        bs.buildFromPoles(poles)
        bs.setWeight(2, self.flatness)
        bs.setWeight(3, self.flatness)
        return bs

    def path3d(self):
        cyl = Part.makeCylinder((self.diameter - self.wire_diam) / 2.0, self.length - self.wire_diam, Vector(), Vector(0, 0, 1)).Face1
        if self.reverse:
            reflxz = FreeCAD.Matrix()
            reflxz.A22 = -1
            surf = cyl.transformed(reflxz, copy=True).Surface
        else:
            surf = cyl.Surface
        return self.path2d().toShape(surf)

    def min_length(self):
        return (self.turns + 1) * self.wire_diam

    def shape(self):
        path = Part.Wire(self.path3d())
        c = Part.Circle(path.Edges[0].valueAt(path.Edges[0].FirstParameter), path.Edges[0].tangentAt(path.Edges[0].FirstParameter), self.wire_diam / 2.0)
        pro = Part.Wire([c.toShape()])
        ps = Part.BRepOffsetAPI.MakePipeShell(path)
        ps.setFrenetMode(True)
        # ps.setForceApproxC1(True)
        ps.setTolerance(1e-2, 1e-2, 0.1)
        ps.setMaxDegree(5)
        ps.setMaxSegments(999)
        ps.add(pro)
        if ps.isReady():
            ps.build()
            ps.makeSolid()
            return ps.shape()
        return None


class CompSpringFP:
    """Creates a Parametric Compression Spring"""

    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyFloat", "Length", "CompSpring", "Spring Length").Length = 10.0
        obj.addProperty("App::PropertyInteger", "Turns", "CompSpring", "Number of turns").Turns = 5
        obj.addProperty("App::PropertyFloat", "WireDiameter", "CompSpring", "Diameter of the spring wire").WireDiameter = 0.5
        obj.addProperty("App::PropertyFloat", "Diameter", "CompSpring", "Diameter of the spring").Diameter = 4.0
        obj.addProperty("App::PropertyInteger", "Flatness", "Setting", "Flatness of spring extremities from 0 to 4").Flatness = 0
        obj.addProperty("App::PropertyBool", "WireOutput", "Setting", "Output a wire shape").WireOutput = True
        obj.addProperty("App::PropertyBool", "ReverseHelix", "CompSpring", "Left hand if true").ReverseHelix = False
        obj.Proxy = self

    def spring(self, obj):
        try:
            f = pow(10, obj.Flatness - 1)
            return CompSpring(obj.Length, obj.Turns, obj.WireDiameter, obj.Diameter, f, obj.ReverseHelix)
        except AttributeError:
            return None

    def execute(self, obj):
        cs = self.spring(obj)
        if not cs:
            return
        if obj.WireOutput:
            obj.Shape = cs.path3d()
        else:
            obj.Shape = cs.shape()
        return cs

    def onChanged(self, obj, prop):
        if prop in ("Length", "Turns", "WireDiameter"):
            cs = self.spring(obj)
            if cs:
                if obj.Length < cs.min_length():
                    obj.Length = cs.min_length()
        if prop == "Flatness":
            if obj.Flatness < 0:
                obj.Flatness = 0
            elif obj.Flatness > 4:
                obj.Flatness = 4


class CompSpringVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None


class CompSpringCommand:
    """Creates a Parametric Compression Spring"""

    def makeFeature(self):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "CompSpring")
        CompSpringFP(fp)
        CompSpringVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        self.makeFeature()

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('comp_spring', CompSpringCommand())

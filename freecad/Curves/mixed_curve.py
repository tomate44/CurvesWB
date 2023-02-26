# -*- coding: utf-8 -*-

__title__ = "Mixed curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Builds a 3D curve as the intersection of 2 projected curves."
__usage__ = """Select two objects or shapes, and activate tool.
The camera direction is saved during each shape selection, and will be used as projection direction.
Set these directions to (0,0,0) to use the placement of each shape as projection direction."""

import os
import FreeCAD
import FreeCADGui
import Part
from . import approximate_extension
from . import _utils
from . import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'mixed_curve.svg')
debug = _utils.debug
# debug = _utils.doNothing


class MixedCurve:
    """Builds a 3D curve as the intersection of 2 projected curves."""
    def __init__(self, sh1, sh2, dir1, dir2):
        self.shape1 = sh1
        self.shape2 = sh2
        if not dir1.Length == 0:
            self.dir1 = dir1
        else:
            raise ValueError("Vector is null")
        if not dir2.Length == 0:
            self.dir2 = dir2
        else:
            raise ValueError("Vector is null")

    def shape(self):
        proj1 = self.shape1.toNurbs().extrude(self.dir1)
        proj2 = self.shape2.toNurbs().extrude(self.dir2)
        curves = list()
        for f1 in proj1.Faces:
            for f2 in proj2.Faces:
                curves += f1.Surface.intersectSS(f2.Surface)
        intersect = [c.toShape() for c in curves]
        edges = []
        for sh in intersect:
            if isinstance(sh, Part.Edge) and sh.Length > 1e-7:
                edges.append(sh)
        se = Part.sortEdges(edges)
        wires = []
        for el in se:
            wires.append(Part.Wire(el))
        if len(wires) == 1:
            return wires[0]
        return Part.Compound(wires)


class MixedCurveFP:
    """Builds a 3D curve as the intersection of 2 projected curves."""
    def __init__(self, obj, s1, s2, d1, d2):
        obj.addProperty("App::PropertyLink", "Shape1", "Mixed Curve", "First shape").Shape1 = s1
        obj.addProperty("App::PropertyLink", "Shape2", "Mixed Curve", "Second shape").Shape2 = s2
        obj.addProperty("App::PropertyVector", "Direction1", "Mixed Curve",
                        "Projection direction of the first shape.\nIf vector is null, shape's placement is used.").Direction1 = d1
        obj.addProperty("App::PropertyVector", "Direction2", "Mixed Curve",
                        "Projection direction of the second shape.\nIf vector is null, shape's placement is used.").Direction2 = d2
        obj.addProperty("App::PropertyBool", "FillFace1", "Mixed Curve",
                        "Build ruled surfaces between Shape1 and resulting Mixed-Curve").FillFace1 = False
        obj.addProperty("App::PropertyBool", "FillFace2", "Mixed Curve",
                        "Build ruled surfaces between Shape2 and resulting Mixed-Curve").FillFace2 = False
        obj.Proxy = self

    def execute(self, obj):
        s1 = obj.Shape1.Shape
        s2 = obj.Shape2.Shape
        if obj.Direction1.Length < 1e-7:
            d1 = obj.Shape1.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, -1))
        else:
            d1 = obj.Direction1
        if obj.Direction2.Length < 1e-7:
            d2 = obj.Shape2.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, -1))
        else:
            d2 = obj.Direction2
        cc = MixedCurve(s1, s2, d1, d2)

        if hasattr(obj, "ExtensionProxy"):
            mixed = obj.ExtensionProxy.approximate(obj, cc.shape())
        else:
            mixed = cc.shape()
        if not hasattr(obj, "FillFace1"):
            obj.Shape = mixed
            return
        # print(s1, s2, mixed.Wires)
        trimshape1, trimshape2 = Part.Shape(), Part.Shape()
        if obj.FillFace1:
            trimshape1 = _utils.ruled_surface(s1, mixed.Wires[0], normalize=False)
            # print(trimshape1)
        if obj.FillFace2:
            trimshape2 = _utils.ruled_surface(s2, mixed.Wires[0], normalize=False)
            # print(trimshape2)
        faces = trimshape1.Faces + trimshape2.Faces
        if faces:
            shell = Part.Shell(faces)
            if shell.Faces:
                obj.Shape = shell
                return
        obj.Shape = mixed

    def onChanged(self, fp, prop):
        if hasattr(fp, "ExtensionProxy"):
            fp.ExtensionProxy.onChanged(fp, prop)


class MixedCurveVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        return [self.Object.Shape1, self.Object.Shape2]


class MixedCurveCmd:
    """Splits the selected edges."""
    def makeCPCFeature(self, o1, o2, d1, d2):
        cc = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Mixed curve")
        MixedCurveFP(cc, o1, o2, d1, d2)
        approximate_extension.ApproximateExtension(cc)
        cc.Active = False
        MixedCurveVP(cc.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        vd = [FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 0)]
        try:
            sel = FreeCADGui.activeWorkbench().Selection
            vd = FreeCADGui.activeWorkbench().View_Directions
        except AttributeError:
            sel = FreeCADGui.Selection.getSelectionEx()
        if not len(sel) == 2:
            FreeCAD.Console.PrintError("Select 2 objects !\n")
            return
        for selobj in sel:
            selobj.Object.ViewObject.Visibility = False
        if len(vd) == 2 and vd[0].dot(vd[1]) < 0.999:
            d1, d2 = vd
        else:
            d1, d2 = [FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 0)]
        self.makeCPCFeature(sel[0].Object, sel[1].Object, d1, d2)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Mixed curve',
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('mixed_curve', MixedCurveCmd())

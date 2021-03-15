# -*- coding: utf-8 -*-

__title__ = "Face Map"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Flat map of a 3D face"""

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves.nurbs_tools import nurbs_quad
from freecad.Curves import ICONPATH

vec2 = FreeCAD.Base.Vector2d
TOOL_ICON = os.path.join(ICONPATH, 'face_map.svg')
# debug = _utils.debug
# debug = _utils.doNothing


def get_dual_curveOnSurface(face, e):
    cos_list = []
    for c2d in _utils.get_pcurves(e):
        s = c2d[1]
        s.transform(c2d[2].toMatrix())
        surf_test = _utils.geom_equal(face.Surface, s)
        if surf_test:
            cos_list.append((c2d[0], c2d[3], c2d[4]))
    if len(cos_list) < 2:
        FreeCAD.Console.PrintError("Failed to extract pcurves of seam edge\n")
    return cos_list


def face_bounding_box_2d(face):
    u0, u1, v0, v1 = face.ParameterRange
    line_top = Part.Geom2d.Line2dSegment(vec2(u0, v1), vec2(u1, v1))
    line_bottom = Part.Geom2d.Line2dSegment(vec2(u0, v0), vec2(u1, v0))
    line_right = Part.Geom2d.Line2dSegment(vec2(u0, v0), vec2(u0, v1))
    line_left = Part.Geom2d.Line2dSegment(vec2(u1, v0), vec2(u1, v1))
    return line_bottom, line_top, line_left, line_right


def face_bounding_box_3d(face):
    bot, top, lef, rig = face_bounding_box_2d(face)
    bot3d = bot.toShape(face.Surface)
    top3d = top.toShape(face.Surface)
    lef3d = lef.toShape(face.Surface)
    rig3d = rig.toShape(face.Surface)
    return bot3d, top3d, lef3d, rig3d


class FaceMapFP:
    """Creates a flat map of a face"""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Source",
                        "Base", "Input face")
        obj.addProperty("App::PropertyFloat", "SizeU",
                        "Dimensions", "Size of the map in the U direction")
        obj.addProperty("App::PropertyFloat", "SizeV",
                        "Dimensions", "Size of the map in the V direction")
        obj.addProperty("App::PropertyBool", "AddBounds",
                        "Settings", "Add the bounding box of the face")
        obj.addProperty("App::PropertyEnumeration", "SizeMode",
                        "Settings", "The method used to set the size of the face map")
        obj.addProperty("App::PropertyFloat", "ExtendFactor",
                        "Settings", "Set the size factor of the underlying surface")
        obj.SizeMode = ["Average3D", "Average2D", "Manual"]
        obj.SizeMode = "Manual"
        obj.SizeU = 1.0
        obj.SizeV = 1.0
        obj.ExtendFactor = 10.0
        obj.setEditorMode("SizeU", 0)
        obj.setEditorMode("SizeV", 0)
        obj.setEditorMode("ExtendFactor", 2)
        obj.Proxy = self

    def get_face(self, obj):
        if hasattr(obj, "Source"):
            if obj.Source[1]:
                return obj.Source[0].Shape.getElement(obj.Source[1][0])
            else:
                return obj.Source[0].Shape.Face1

    def execute(self, obj):
        face = self.get_face(obj)
        if not isinstance(face, Part.Face):
            obj.Shape = None
            return
        outer_wire = None
        inner_wires = []
        poles = [[FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, obj.SizeV, 0)],
                 [FreeCAD.Vector(obj.SizeU, 0, 0), FreeCAD.Vector(obj.SizeU, obj.SizeV, 0)]]
        quad = nurbs_quad(poles, face.ParameterRange, obj.ExtendFactor)
        for w in face.Wires:
            el = []
            for e in w.Edges:
                if e.isSeam(face):
                    cos_list = get_dual_curveOnSurface(face, e)
                    el.append(cos_list[0][0].toShape(quad, cos_list[0][1], cos_list[0][2]))
                    el.append(cos_list[1][0].toShape(quad, cos_list[1][1], cos_list[1][2]))
                else:
                    cos, fp, lp = face.curveOnSurface(e)
                    el.append(cos.toShape(quad, fp, lp))
            flat_wire = Part.Wire(Part.sortEdges(el)[0])
            if w.isSame(face.OuterWire):
                outer_wire = flat_wire
            else:
                inner_wires.append(flat_wire)
        mapface = Part.Face(quad, outer_wire)
        if inner_wires:
            mapface.validate()
            mapface.cutHoles(inner_wires)
        mapface.validate()
        obj.Shape = mapface

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return
        if prop == "SizeMode":
            if obj.SizeMode == "Average3D":
                face = self.get_face(obj)
                bb = face_bounding_box_3d(face)
                obj.SizeU = 0.5 * (bb[0].Length + bb[1].Length)
                obj.SizeV = 0.5 * (bb[2].Length + bb[3].Length)
                obj.setEditorMode("SizeU", 1)
                obj.setEditorMode("SizeV", 1)
            elif obj.SizeMode == "Average2D":
                face = self.get_face(obj)
                bb = face_bounding_box_2d(face)
                obj.SizeU = 0.5 * (bb[0].length() + bb[1].length())
                obj.SizeV = 0.5 * (bb[2].length() + bb[3].length())
                obj.setEditorMode("SizeU", 1)
                obj.setEditorMode("SizeV", 1)
            elif obj.SizeMode == "Manual":
                obj.setEditorMode("SizeU", 0)
                obj.setEditorMode("SizeV", 0)
        if prop in ["SizeU", "SizeV"]:
            if obj.SizeU <= 0.0:
                obj.SizeU = 1.0
            if obj.SizeV <= 0.0:
                obj.SizeV = 1.0
            self.execute(obj)


class FaceMapVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None


class CurvesCmd_FlatMap:
    """Creates a flat map of a face"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Face Map")
        FaceMapFP(fp)
        FaceMapVP(fp.ViewObject)
        fp.Source = (sel[0].Object, (sel[0].SubElementNames[0]))
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('CurvesCmd_FlatMap', CurvesCmd_FlatMap())

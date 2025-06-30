# -*- coding: utf-8 -*-

__title__ = 'MapOnFace'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = '''Map objects on a target face.
This will replace SketchOnSurface.
Work In Progress. Do Not Use.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ShapeMapper
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')


# Reminder : Available properties
"""
obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "FeaturePython")
for prop in obj.supportedProperties():
    print(prop)

"""

def error(obj, msg):
    FreeCAD.Console.PrintError(f"{obj.Label}: {msg}\n")



class MapOnFaceFP:
    "MapOnFace Feature Python Proxy"

    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList", "Sources", "BaseObjects",
                        "Tooltip")
        obj.addProperty("App::PropertyLinkSub", "TargetFace", "BaseObjects",
                        "Tooltip")
        obj.addProperty("App::PropertyLink", "TargetFlatMap", "BaseObjects",
                        "Tooltip")
        obj.addProperty("App::PropertyBool", "FillFaces", "MainSettings",
                        "Make faces from closed wires").FillFaces = True
        obj.addProperty("App::PropertyBool", "FillExtrusion", "MainSettings",
                        "Add extrusion faces").FillExtrusion = True
        obj.addProperty("App::PropertyFloat", "Offset", "MainSettings",
                        "Offset distance of mapped sketch").Offset = 0.0
        obj.addProperty("App::PropertyFloat", "Thickness", "MainSettings",
                        "Extrusion thickness").Thickness = 0.0
        obj.addProperty("App::PropertyBool", "ReverseU", "Orientation",
                        "Reverse U direction").ReverseU = False
        obj.addProperty("App::PropertyBool", "ReverseV", "Orientation",
                        "Reverse V direction").ReverseV = False
        obj.addProperty("App::PropertyBool", "SwapUV", "Orientation",
                        "Swap U and V directions").ReverseV = False
        obj.Proxy = self

    def execute(self, obj):
        source = Part.Compound([o.Shape for o in obj.Sources])
        if len(source.Vertexes) == 0:
            error(obj, "No source shapes")
            return
        target = _utils.getShape(obj, "TargetFace", "Face")
        if not target:
            error(obj, "No source shapes")
            return
        if not hasattr(obj.TargetFlatMap, "Shape"):
            error(obj, "No transfer object")
            return
        transfer_shape = obj.TargetFlatMap.Shape
        bb = transfer_shape.BoundBox
        transfer = ShapeMapper.Quad([bb.XMin, bb.XMax, bb.YMin, bb.YMax], target.ParameterRange)
        if obj.ReverseU:
            transfer.reverseU()
        if obj.ReverseV:
            transfer.reverseV()
        if obj.SwapUV:
            transfer.swapUV()

        sm = ShapeMapper.ShapeMapper(source, target, transfer.Face)
        if (not obj.FillExtrusion) or (obj.Thickness == 0.0):
            faces, wires = sm.get_shapes(obj.Offset, obj.FillFaces)
            comp = Part.Compound([faces, wires])
            if not obj.Thickness == 0.0:
                faces, wires = sm.get_shapes(obj.Offset + obj.Thickness, obj.FillFaces)
                comp.add(faces)
                comp.add(wires)
            obj.Shape = comp
            return
        if not obj.FillFaces:
            obj.Shape = sm.get_extrusion(obj.Offset, obj.Offset + obj.Thickness)
            return
        obj.Shape = sm.get_solids(obj.Offset, obj.Offset + obj.Thickness)

    def onChanged(self, obj, prop):
        return False


class MapOnFaceVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

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


class MapOnFaceCommand:
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "MapOnFace")
        MapOnFaceFP(fp)
        MapOnFaceVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
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


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Curves_MapOnFace', MapOnFaceCommand())

# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'MapOnFace'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = '''Map objects on a target face.
This will replace SketchOnSurface.
WORK IN PROGRESS. USE AT YOUR OWN RISKS.
Three objects must be provided in sequence:
- the source shapes to map on the target face
- the target face on which the source shapes will be mapped
- the object that represent the flat bounding box of the target face'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ShapeMapper
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'map_on_face.svg')


# Reminder : Available properties
"""
obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "FeaturePython")
for prop in obj.supportedProperties():
    print(prop)

"""


def error(obj, msg):
    FreeCAD.Console.PrintError(f"{obj.Label}: {msg}\n")


class MofProxyBase:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkList", "Sources", "BaseObjects",
                        "Source shapes that will be mapped on target face")
        obj.addProperty("App::PropertyLinkSub", "TargetFace", "BaseObjects",
                        "Target face of the mapping operation")
        obj.addProperty("App::PropertyLink", "TargetFlatMap", "BaseObjects",
                        """Shape (usually a sketcher rectangle) that represent
                        the flat bounding box of the target face""")
        obj.addProperty("App::PropertyFloat", "Thickness", "MainSettings",
                        "Extrusion thickness").Thickness = 0.0
        obj.addProperty("App::PropertyBool", "ReverseU", "Orientation",
                        "Reverse U direction").ReverseU = False
        obj.addProperty("App::PropertyBool", "ReverseV", "Orientation",
                        "Reverse V direction").ReverseV = False
        obj.addProperty("App::PropertyBool", "SwapUV", "Orientation",
                        "Swap U and V directions").ReverseV = False

    def get_shapeMapper(self, obj):
        source = Part.Compound([o.Shape for o in obj.Sources])
        if len(source.Vertexes) == 0:
            error(obj, "No source shapes")
            return
        target = _utils.getShape(obj, "TargetFace", "Face")
        if not target:
            error(obj, "No target face")
            return
        if not hasattr(obj.TargetFlatMap, "Shape"):
            error(obj, "No transfer object. Using Source face")
            return ShapeMapper.ShapeMapper(source, target)
        transfer_shape = obj.TargetFlatMap.Shape
        if len(transfer_shape.Faces) == 1:
            transfer = ShapeMapper.TransferSurface(transfer_shape.Face1)
        else:
            bb = transfer_shape.BoundBox
            transfer = ShapeMapper.Quad([bb.XMin, bb.XMax, bb.YMin, bb.YMax],
                                        target.ParameterRange)
            numU = 1 + source.BoundBox.XLength / bb.XLength
            numV = 1 + source.BoundBox.YLength / bb.YLength
            transfer.extend(numU, numV)
        print(transfer.get_center())
        if obj.ReverseU:
            transfer.reverseU()
        if obj.ReverseV:
            transfer.reverseV()
        if obj.SwapUV:
            transfer.swapUV()

        return ShapeMapper.ShapeMapper(source, target, transfer.Face)


class MapOnFaceFP(MofProxyBase):
    "MapOnFace Feature Python Proxy"

    def __init__(self, obj):
        """Add the properties"""
        super(MapOnFaceFP, self).__init__(obj)
        obj.addProperty("App::PropertyBool", "FillFaces", "MainSettings",
                        "Make faces from closed wires").FillFaces = True
        obj.addProperty("App::PropertyBool", "FillExtrusion", "MainSettings",
                        "Add extrusion faces").FillExtrusion = True
        obj.addProperty("App::PropertyFloat", "Offset", "MainSettings",
                        "Offset distance of mapped sketch").Offset = 0.0
        obj.Proxy = self

    @ShapeMapper.timer
    def execute(self, obj):
        sm = self.get_shapeMapper(obj)
        if (not obj.FillExtrusion) or (obj.Thickness == 0.0):
            faces, wires = sm.get_shapes(obj.Offset, obj.FillFaces)
            comp = Part.Compound([faces, wires])
            if not obj.Thickness == 0.0:
                faces, wires = sm.get_shapes(obj.Offset + obj.Thickness, obj.FillFaces)
                comp.add(faces)
                comp.add(wires)
            obj.Shape = comp
            _ = [print(mes) for mes in sm.Messages]
            return
        if not obj.FillFaces:
            obj.Shape = sm.get_extrusion(obj.Offset, obj.Offset + obj.Thickness)
            _ = [print(mes) for mes in sm.Messages]
            return
        obj.Shape = sm.get_solids(obj.Offset, obj.Offset + obj.Thickness)
        _ = [print(mes) for mes in sm.Messages]

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return


class MapOnFacePDFP(MofProxyBase):
    "MapOnFace Part Design Proxy"

    def __init__(self, obj):
        """Add the properties"""
        super(MapOnFacePDFP, self).__init__(obj)
        obj.addProperty("App::PropertyBool", "Refine", "PartDesign",
                        "Refine shape (clean up redundant edges) after operations")
        obj.Thickness = 1.0
        obj.Proxy = self

    @ShapeMapper.timer
    def execute(self, obj):
        offset = 0.0
        sm = self.get_shapeMapper(obj)
        result = sm.get_solids(-offset, obj.Thickness + offset)
        base = obj.BaseFeature.Shape
        if obj.Thickness == 0.0:
            obj.Shape = base
            error(obj, "Null thickness")
            return
        if obj.Thickness < 0.0:
            bop = base.cut(result.Solids)
        else:
            bop = base.fuse(result.Solids)
        if obj.Refine:
            bop = bop.removeSplitter()
        obj.Shape = bop

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return


class MapOnFaceVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object
        children = self.claimChildren()
        for child in children:
            child.ViewObject.Visibility = False

    def claimChildren(self):
        ol = self.Object.Sources
        ol.append(self.Object.TargetFlatMap)
        return ol

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
    def makeFeature(self, sel=[], body=None):
        if body is None:
            fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "MapOnFace")
            MapOnFaceFP(fp)
        else:
            fp = body.newObject("PartDesign::FeaturePython", "MapOnFace")
            MapOnFacePDFP(fp)
        props = ["Sources", "TargetFace", "TargetFlatMap"]
        for i, link in enumerate(sel):
            setattr(fp, props[i], link)
        MapOnFaceVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def get_body(self, sel):
        parents = [o.Object.getParent() for o in sel]
        parents = list(set(parents))
        if (len(parents) == 1) and (getattr(parents[0], "TypeId", "") == "PartDesign::Body"):
            return parents[0]

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        links = []
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        if len(sel) >= 1:
            links.append(sel[0].Object)
        if len(sel) >= 2:
            links.append((sel[1].Object, sel[1].SubElementNames))
        if len(sel) >= 3:
            links.append(sel[2].Object)
        self.makeFeature(links, self.get_body(sel))

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

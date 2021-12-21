# -*- coding: utf-8 -*-

__title__ = "Face Map"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Flat map of a 3D face"""

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import face_map_wrap
# from freecad.Curves.nurbs_tools import nurbs_quad
from freecad.Curves import ICONPATH

vec2 = FreeCAD.Base.Vector2d
TOOL_ICON = os.path.join(ICONPATH, 'face_map.svg')
# debug = _utils.debug
# debug = _utils.doNothing


class FaceMapFP:
    """Creates a flat map of a face"""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Source",
                        "Base", "Input face")
        obj.addProperty("App::PropertyLinkList", "ExtraObjects",
                        "Base", "External objects to project on face")
        obj.addProperty("App::PropertyFloat", "SizeU",
                        "Dimensions", "Size of the map in the U direction")
        obj.addProperty("App::PropertyFloat", "SizeV",
                        "Dimensions", "Size of the map in the V direction")
        obj.addProperty("App::PropertyBool", "AddBounds",
                        "Settings", "Add the bounding box of the face")
        obj.addProperty("App::PropertyBool", "FillFace",
                        "Settings", "Generate a face, or simply wires").FillFace = True
        obj.addProperty("App::PropertyEnumeration", "SizeMode",
                        "Dimensions", "The method used to set the size of the face map")
        obj.addProperty("App::PropertyFloat", "ExtendFactor",
                        "Settings", "Set the size factor of the underlying surface")
        # obj.addProperty("App::PropertyBool", "ReverseU", "Touchup",
                        # "Reverse U direction").ReverseU = False
        # obj.addProperty("App::PropertyBool", "ReverseV", "Touchup",
                        # "Reverse V direction").ReverseV = False
        obj.addProperty("App::PropertyBool", "SwapUV", "Touchup",
                        "Swap U and V directions").SwapUV = False
        obj.SizeMode = ["Average3D", "Bounds2D", "Manual"]
        obj.SizeMode = "Manual"
        obj.SizeU = 1.0
        obj.SizeV = 1.0
        obj.ExtendFactor = 10.0
        obj.setEditorMode("SizeU", 0)
        obj.setEditorMode("SizeV", 0)
        obj.setEditorMode("ExtendFactor", 2)
        obj.Proxy = self

    @staticmethod
    def get_face(obj):
        if hasattr(obj, "Source") and isinstance(obj.Source, (list, tuple)):
            if len(obj.Source) == 2:
                return obj.Source[0].Shape.getElement(obj.Source[1][0])
            elif len(obj.Source) == 1:
                return obj.Source[0].Shape.Face1

    def execute(self, obj):
        save_placement = obj.Placement
        face = self.get_face(obj)
        if not isinstance(face, Part.Face):
            # obj.Shape = None
            return

        mapper = face_map_wrap.FaceMapper(face)
        su = False
        sv = False
        if obj.SizeMode == "Average3D":
            bb = mapper.boundbox_on_face()
            su = 0.5 * (bb.Edges[0].Length + bb.Edges[2].Length)
            sv = 0.5 * (bb.Edges[1].Length + bb.Edges[3].Length)
        elif obj.SizeMode == "Bounds2D":
            u0, u1, v0, v1 = face.ParameterRange
            su = u1 - u0
            sv = v1 - v0
        if (su is not False) and (not obj.SizeU == su):
            obj.SizeU = su
        if (sv is not False) and (not obj.SizeV == sv):
            obj.SizeV = sv

        if obj.SwapUV:
            mapper.set_quad([0, obj.SizeV, 0, obj.SizeU], obj.ExtendFactor)
        else:
            mapper.set_quad([0, obj.SizeU, 0, obj.SizeV], obj.ExtendFactor)
        # mapper.reverseU(obj.ReverseU)
        # mapper.reverseV(obj.ReverseV)
        mapper.swapUV(obj.SwapUV)
        shapes = [mapper.flatFace(None, obj.FillFace)]

        if obj.AddBounds:
            shapes.append(mapper.boundbox_flat())
        if len(obj.ExtraObjects) > 0:
            proj = face.project([o.Shape for o in obj.ExtraObjects])
            shapes.append(mapper.flatShape(proj, obj.FillFace))
        if len(shapes) > 1:
            obj.Shape = Part.Compound(shapes)
        else:
            obj.Shape = shapes[0]
        obj.Placement = save_placement

    def setSize(self, obj):
        face = self.get_face(obj)
        if not isinstance(face, Part.Face):
            return
        if obj.SizeMode == "Average3D":
            mapper = face_map_wrap.FaceMapper(face)
            bb = mapper.boundbox_on_face()
            obj.SizeU = 0.5 * (bb.Edges[0].Length + bb.Edges[2].Length)
            obj.SizeV = 0.5 * (bb.Edges[1].Length + bb.Edges[3].Length)
        elif obj.SizeMode == "Bounds2D":
            u0, u1, v0, v1 = face.ParameterRange
            obj.SizeU = u1 - u0
            obj.SizeV = v1 - v0

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return
        #if prop == "Source":
            #self.setSize(obj)
        if prop == "SizeMode":
            if obj.SizeMode in ["Average3D", "Bounds2D"]:
                #self.setSize(obj)
                obj.setEditorMode("SizeU", 1)
                obj.setEditorMode("SizeV", 1)
            else:
                obj.setEditorMode("SizeU", 0)
                obj.setEditorMode("SizeV", 0)
        if prop == "SizeU":
            if abs(obj.SizeU) < 1e-5:
                obj.SizeU = 1e-5
        if prop == "SizeV":
            if abs(obj.SizeV) < 1e-5:
                obj.SizeV = 1e-5
        if prop in ["Source", "SizeU", "SizeV", "AddBounds", "FillFace", "ExtendFactor", "SwapUV"]:
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


def isCylinder(lnk=None):
    try:
        f = lnk[0].getSubObject(lnk[1])
        if isinstance(f.Surface, Part.Cylinder):
            return True
    except Exception as e:
        print(f"Selection error : {e} - {lnk}")
    return False


class CurvesCmd_FlatMap:
    """Creates a flat map of a face"""

    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Face Map")
        FaceMapFP(fp)
        FaceMapVP(fp.ViewObject)
        fp.Source = sel
        # FreeCAD.ActiveDocument.recompute()
        if isCylinder(sel):
            print("Average3D")
            fp.SizeMode = "Average3D"
        FreeCAD.ActiveDocument.recompute()
        return fp

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select a face in the 3D view before activation.\n")
        else:
            self.makeFeature([sel[0].Object, sel[0].SubElementNames[0]])

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

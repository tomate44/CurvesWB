# -*- coding: utf-8 -*-

__title__ = 'Wrap on face'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Wrap objects on a face'

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'wrap_on_face.svg')
# debug = _utils.debug
# debug = _utils.doNothing

props = """
App::PropertyBool
App::PropertyBoolList
App::PropertyFloat
App::PropertyFloatList
App::PropertyFloatConstraint
App::PropertyQuantity
App::PropertyQuantityConstraint
App::PropertyAngle
App::PropertyDistance
App::PropertyLength
App::PropertySpeed
App::PropertyAcceleration
App::PropertyForce
App::PropertyPressure
App::PropertyInteger
App::PropertyIntegerConstraint
App::PropertyPercent
App::PropertyEnumeration
App::PropertyIntegerList
App::PropertyIntegerSet
App::PropertyMap
App::PropertyString
App::PropertyUUID
App::PropertyFont
App::PropertyStringList
App::PropertyLink
App::PropertyLinkSub
App::PropertyLinkList
App::PropertyLinkSubList
App::PropertyMatrix
App::PropertyVector
App::PropertyVectorList
App::PropertyPlacement
App::PropertyPlacementLink
App::PropertyColor
App::PropertyColorList
App::PropertyMaterial
App::PropertyPath
App::PropertyFile
App::PropertyFileIncluded
App::PropertyPythonObject
Part::PropertyPartShape
Part::PropertyGeometryList
Part::PropertyShapeHistory
Part::PropertyFilletEdges
Sketcher::PropertyConstraintList
"""


class WrapOnFaceFP:
    """Create a ..."""
    def __init__(self, fp):
        """Add the properties"""
        fp.addProperty("App::PropertyLinkList", "Sources",
                       "Group", "List of objects to be wrapped on target face")
        fp.addProperty("App::PropertyLink", "FaceMap",
                       "Group", "Flat representation of a face")
        fp.addProperty("App::PropertyBool", "FillFaces", "Settings",
                       "Make faces from closed wires").FillFaces = False
        fp.addProperty("App::PropertyBool", "FillExtrusion", "Settings",
                       "Add extrusion faces").FillExtrusion = True
        fp.addProperty("App::PropertyFloat", "Offset", "Settings",
                       "Offset distance of mapped sketch").Offset = 0.0
        fp.addProperty("App::PropertyFloat", "Thickness", "Settings",
                       "Extrusion thickness").Thickness = 0.0
        fp.addProperty("App::PropertyBool", "ReverseU", "Touchup",
                       "Reverse U direction").ReverseU = False
        fp.addProperty("App::PropertyBool", "ReverseV", "Touchup",
                       "Reverse V direction").ReverseV = False
        fp.addProperty("App::PropertyBool", "SwapUV", "Touchup",
                       "Swap U and V directions").ReverseV = False
        fp.Proxy = self

    def execute(self, fp):
        quad = fp.FaceMap.Shape.Face1.Surface.toShape()
        face = fp.FaceMap.Proxy.get_face(fp.FaceMap)

    def onChanged(self, fp, prop):
        return False


class WrapOnFaceVP:
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

    def claimChildren(self):
        objs = [o[0] for o in self.Object.Sources]
        return [self.Object.FaceMap] + objs


class CurvesCmd_WrapOnFace:
    """Create a ... feature"""
    def makeFeature(self, facemap, not_facemap=[]):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "WrapOnFace")
        WrapOnFaceFP(fp)
        WrapOnFaceVP(fp.ViewObject)
        fp.FaceMap = facemap
        fp.Sources = not_facemap
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        facemap = None
        not_facemap = []
        for selobj in sel:
            # print(str(selobj.Object.Proxy.__class__))
            if hasattr(selobj.Object, "Proxy") and ("FaceMapFP" in str(selobj.Object.Proxy.__class__)):
                facemap = selobj.Object
            elif hasattr(selobj.Object, "Shape"):
                not_facemap.append(selobj.Object)
        if facemap is not None:
            self.makeFeature(facemap, not_facemap)
            return
        # No FaceMap FeaturePython object in the selection
        # The first selected face will be used to create a FaceMap object
        not_facemap = []
        for selobj in sel:
            if facemap is None:
                for subname in selobj.SubElementNames:
                    if "Face" in subname and facemap is None:
                        from .FaceMapFP import CurvesCmd_FlatMap
                        facemap = CurvesCmd_FlatMap.makeFeature((selobj.Object, (subname, )))
            elif hasattr(selobj.Object, "Shape"):
                not_facemap.append(selobj.Object)
        if facemap is not None:
            self.makeFeature(facemap, not_facemap)
            return
        FreeCAD.Console.PrintError("Select a target face in 3D view, or a FaceMap object.\n")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('CurvesCmd_WrapOnFace', CurvesCmd_WrapOnFace())

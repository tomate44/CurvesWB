# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Rectangular face'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Create a rectangular trimmed face'

import os
import FreeCAD
import FreeCADGui
# import Part
from freecad.Curves.BaseProxy import BaseFPOProxy, BaseFPOViewProxy
# from freecad.Curves.lib import bspline_surface
from freecad.Curves import ICONPATH
from freecad.Curves.lib.trimmed_surface import TrimmedSurface

TOOL_ICON = os.path.join(ICONPATH, 'rectangular_face.svg')


class RectangularFaceFP(BaseFPOProxy):
    def __init__(self, obj):
        super().__init__(obj)
        obj.addProperty("App::PropertyLinkSub", "Face",
                        "Input", "Source face")
        obj.addProperty("App::PropertyFloat", "UMin",
                        "Extend", "Extend value on the UMin side (percent of the parameter range)")
        obj.addProperty("App::PropertyFloat", "UMax",
                        "Extend", "Extend value on the UMax side (percent of the parameter range)")
        obj.addProperty("App::PropertyFloat", "VMin",
                        "Extend", "Extend value on the VMin side (percent of the parameter range)")
        obj.addProperty("App::PropertyFloat", "VMax",
                        "Extend", "Extend value on the VMax side (percent of the parameter range)")
        obj.addProperty("App::PropertyBool", "BSpline",
                        "BSpline", "Convert surface to BSpline")
        obj.UMin = 0.0
        obj.UMax = 0.0
        obj.VMin = 0.0
        obj.VMax = 0.0
        obj.Proxy = self

    def execute(self, obj):
        o, subname = obj.Face
        f = o.getSubObject(subname)[0]
        if not hasattr(f, "Face1"):
            raise ValueError(
                f"{obj.Label}: Face property is not pointing to a valid face")
        ts = TrimmedSurface(f)
        ts.extend(obj.UMin / 100,
                  obj.UMax / 100,
                  obj.VMin / 100,
                  obj.VMax / 100,
                  Relative=True)
        if obj.BSpline:
            s = ts.Surface.toBSpline()
            obj.Shape = s.toShape()
        else:
            obj.Shape = ts.Face

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return
        if prop in ["UMin", "UMax", "VMin", "VMax"]:
            obj.recompute()
        return False

    def onDocumentRestored(self, obj):
        pass


class RectangularFaceVP(BaseFPOViewProxy):
    def __init__(self, viewobj):
        viewobj.addProperty("App::PropertyBool", "ClaimChildren",
                            "Display Options",
                            "Claim input face objects as children ?")
        viewobj.ClaimChildren = True
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def claimChildren(self):
        if self.Object.ViewObject.ClaimChildren:
            ol = [self.Object.Face[0]]
            return ol
        return []

    def onChanged(self, obj, prop):
        if prop == "ClaimChildren":
            self.Object.recompute()
        return False


class RectangularFaceCmd:
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "Rectangular Face")
        RectangularFaceFP(fp)
        RectangularFaceVP(fp.ViewObject)
        fp.Face = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select a face in 3D view.\n")
            return
        for so in sel:
            for sn in so.SubElementNames:
                if "Face" in sn:
                    self.makeFeature((so.Object, sn))
        #     else:
        #         faces.append(so.Object)
        # # print(faces)
        # self.makeFeature(faces)

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
    FreeCADGui.addCommand('Curves_RectangularFace', RectangularFaceCmd())

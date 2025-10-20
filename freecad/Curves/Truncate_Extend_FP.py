# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Truncate Extend'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = '''Cut a shape with a plane and truncate or extend it by a given distance.
In a PartDesign body, select only the cutting plane.
Otherwise, select the shape to modify, and the cutting plane.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import Truncate_Extend
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'truncate_extend.svg')


class TruncateExtendFP:
    """Proxy of the Truncate_Extend feature.
    Cut a shape with a plane and truncate or extend it by a given distance."""

    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLink", "Source",
                        "InputObjects", "The object that will be truncated or extended")
        obj.addProperty("App::PropertyLink", "Cutter",
                        "InputObjects", "The planar object that cuts the Source object")
        obj.addProperty("App::PropertyDistance", "Distance",
                        "Settings", "The distance to truncate (if negative) or extend (if positive)")
        obj.addProperty("App::PropertyBool", "Refine",
                        "Settings", "Refine shape (clean up redundant edges)")
        obj.addProperty("App::PropertyBool", "Reverse",
                        "Settings", "Reverse cutter plane normal")
        obj.Distance = 10.0
        obj.Proxy = self

    def execute(self, obj):
        if not obj.Cutter:
            return
        if obj.Source is None:
            solids = obj.BaseFeature.Shape.Solids
        else:
            solids = obj.Source.Shape.Solids
        cutter = obj.Cutter.Shape.Face1
        extends = []
        for solid in solids:
            extender = Truncate_Extend.TruncateExtend(solid, cutter, obj.Distance, obj.Reverse)
            extends.append(extender.Shape)
        if len(extends) == 1:
            sh = extends[0]
        else:
            sh = Part.Compound(extends)
        if obj.Refine:
            sh = sh.removeSplitter()
        obj.Shape = sh


class TruncateExtendVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

    def claimChildren(self):
        if self.Object.Source is None:
            return [self.Object.Cutter]
        else:
            return [self.Object.Source, self.Object.Cutter]

    if (FreeCAD.Version()[0] + '.' + FreeCAD.Version()[1]) >= '0.22':
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


class TruncateExtendCommand:
    """Command that creates the Truncate_Extend feature"""

    def makePDFeature(self, body, plane):
        FreeCAD.ActiveDocument.openTransaction("Truncate_Extend")
        fp = body.newObject("PartDesign::FeaturePython", "Truncate_Extend")
        TruncateExtendFP(fp)
        TruncateExtendVP(fp.ViewObject)
        fp.setEditorMode("Source", 2)
        fp.Source = None
        fp.Cutter = plane
        plane.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()

    def makePartFeature(self, sel=None):
        FreeCAD.ActiveDocument.openTransaction("Truncate_Extend")
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Truncate_Extend")
        TruncateExtendFP(fp)
        TruncateExtendVP(fp.ViewObject)
        if len(sel) == 2:
            fp.Source, fp.Cutter = sel
            fp.Source.ViewObject.Visibility = False
            fp.Cutter.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            t1 = sel[0].TypeId
            if hasattr(sel[0], "getParentGeoFeatureGroup"):
                parent = sel[0].getParentGeoFeatureGroup()
                if parent and (parent.TypeId == "PartDesign::Body") and (t1 == "PartDesign::Plane"):
                    self.makePDFeature(parent, sel[0])
        elif len(sel) == 2:
            self.makePartFeature(sel)
        else:
            FreeCAD.Console.PrintError("Wrong Selection\n")

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curve_TruncateExtendCmd', TruncateExtendCommand())

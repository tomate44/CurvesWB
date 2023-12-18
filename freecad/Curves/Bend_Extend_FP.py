# -*- coding: utf-8 -*-

__title__ = 'Bend Extend'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = '''Cut a shape with a plane and bend it by a given angle.
In a PartDesign body, select only the rotation axis edge of the cutting plane.
Otherwise, select the shape to modify, and the rotation axis edge of the cutting plane.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import Truncate_Extend
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'truncate_extend.svg')


class BendExtendFP:
    """Proxy of the Bend_Extend feature.
    Cut a shape with a plane and bend it by a given angle."""

    def __init__(self, obj):
        obj.addProperty("App::PropertyLink", "Source",
                        "InputObjects", "The object that will be bent")
        obj.addProperty("App::PropertyLinkSub", "Cutter",
                        "InputObjects", "The edge of the cutter plane that represent the rotation axis")
        obj.addProperty("App::PropertyAngle", "Angle",
                        "Settings", "The angle of the bent extension")
        obj.addProperty("App::PropertyBool", "Refine",
                        "Settings", "Refine shape (clean up redundant edges)")
        obj.addProperty("App::PropertyBool", "Reverse",
                        "Settings", "Reverse cutter plane normal")
        obj.Angle = 90.0
        obj.Proxy = self

    def execute(self, obj):
        if not obj.Cutter:
            return
        if obj.Source is None:
            solids = obj.BaseFeature.Shape.Solids
        else:
            solids = obj.Source.Shape.Solids
        cutter = obj.Cutter[0].Shape.Face1
        axis = obj.Cutter[0].getSubObject(obj.Cutter[1])[0]
        extends = []
        for solid in solids:
            extender = Truncate_Extend.BendExtend(solid, cutter, axis, obj.Angle, obj.Reverse)
            extends.append(extender.Shape)
        if len(extends) == 1:
            sh = extends[0]
        else:
            sh = Part.Compound(extends)
        if obj.Refine:
            sh = sh.removeSplitter()
        obj.Shape = sh


class BendExtendVP:
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


class BendExtendCommand:
    """Command that creates the Bend_Extend feature"""

    def makePDFeature(self, body, plane):
        FreeCAD.ActiveDocument.openTransaction("Bend_Extend")
        fp = body.newObject("PartDesign::FeaturePython", "Bend Extend")
        BendExtendFP(fp)
        BendExtendVP(fp.ViewObject)
        fp.setEditorMode("Source", 2)
        fp.Source = None
        fp.Cutter = plane
        plane.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()

    def makePartFeature(self, sel=None):
        FreeCAD.ActiveDocument.openTransaction("Bend_Extend")
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Bend Extend")
        BendExtendFP(fp)
        BendExtendVP(fp.ViewObject)
        if len(sel) == 2:
            fp.Source = sel[0].Object
            fp.Cutter = (sel[1].Object, sel[1].SubElementNames[0])
            fp.Source.ViewObject.Visibility = False
            fp.Cutter[0].ViewObject.Visibility = False
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 1:
            t1 = sel[0].Object.TypeId
            parent = sel[0].Object.getParentGeoFeatureGroup()
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


FreeCADGui.addCommand('Curve_BendExtendCmd', BendExtendCommand())

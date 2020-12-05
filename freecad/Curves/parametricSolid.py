# -*- coding: utf-8 -*-

__title__   = "Parametric solid"
__author__  = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__     = "Make a parametric solid from selected faces."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'solid.svg')


class solid:
    """Make a parametric solid from selected faces"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList",
                        "Faces",
                        "Solid",
                        "List of faces to build the solid")
        obj.Proxy = self

    def execute(self, obj):
        faces = _utils.getShape(obj, "Faces", "Face")
        shell = Part.Shell(faces)
        solid = Part.Solid(shell)
        if solid.isValid():
            obj.Shape = solid
        elif shell.isValid():
            obj.Shape = shell
        else:
            obj.Shape = Part.Compound(faces)


class solidVP:
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

    # def claimChildren(self):
        # return None #[self.Object.Base, self.Object.Tool]


class solidCommand:
    """Make a parametric solid from selected faces"""
    def makeSolidFeature(self, source):
        solidFP = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                                   "Solid")
        solid(solidFP)
        solidVP(solidFP.ViewObject)
        solidFP.Faces = source
        FreeCAD.ActiveDocument.recompute()
        # solidFP.ViewObject.LineWidth = 2.0
        # solidFP.ViewObject.LineColor = (0.3,0.5,0.5)

    def Activated(self):
        faces = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select some faces first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Face):
                        faces.append((selobj.Object,
                                      selobj.SubElementNames[i]))
            elif selobj.Object.Shape.Faces:
                for i in range(len(selobj.Object.Shape.Faces)):
                    faces.append((selobj.Object, "Face{}".format(i+1)))
                selobj.Object.ViewObject.Visibility = False
        if faces:
            self.makeSolidFeature(faces)

    def IsActive(self):
        if FreeCADGui.Selection.getSelectionEx():
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Make Solid',
                'ToolTip': 'Make a parametric solid from selected faces'}

FreeCADGui.addCommand('solid', solidCommand())

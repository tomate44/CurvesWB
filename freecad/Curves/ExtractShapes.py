# -*- coding: utf-8 -*-

__title__ = "Extract subshape"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Extract selected subshapes from objects."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, '/extract.svg')

class extract:
    """Extract the selected shapes from objects"""
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        for o in s:
            objName = o.ObjectName
            sh = o.Object.Shape.copy()
            if hasattr(o.Object, "getGlobalPlacement"):
                gpl = o.Object.getGlobalPlacement()
                sh.Placement = gpl
            for name in o.SubElementNames:
                fullname = objName+"_"+name
                newobj = o.Document.addObject("Part::Feature",fullname)
                newobj.Shape = sh.getElement(name)
            o.Object.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Extract', 'ToolTip': 'Extract selected subshapes from objects'}

FreeCADGui.addCommand('extract', extract()) 

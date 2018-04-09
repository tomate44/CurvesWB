# -*- coding: utf-8 -*-

__title__ = "Extract subshape"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Extract selected subshapes from objects."

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/extract.svg'

class extract:
    """Extract the selected shapes from objects"""
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        for o in s:
            objName = o.ObjectName
            for so,name in zip(o.SubObjects,o.SubElementNames):
                fullname = objName+"_"+name
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature",fullname)
                newobj.Shape = so
            o.Object.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Extract', 'ToolTip': 'Extract selected subshapes from objects'}

FreeCADGui.addCommand('extract', extract()) 

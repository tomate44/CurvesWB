# -*- coding: utf-8 -*-

__title__ = "Reflect Lines"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Creates the reflect lines on a shape, according to a view direction"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/icon.svg'

class ReflectLinesFP:
    """Creates the reflect lines on a shape, according to a view direction"""
    def __init__(self, obj, src):
        """Add the properties"""
        obj.addProperty("App::PropertyLink",   "Source",  "ReflectLines", "Source object").Source = src
        obj.addProperty("App::PropertyVector", "ViewPos", "ReflectLines", "View position")
        obj.addProperty("App::PropertyVector", "ViewDir", "ReflectLines", "View direction")
        obj.addProperty("App::PropertyVector", "UpDir",   "ReflectLines", "Up direction")
        obj.ViewPos = FreeCAD.Vector(0,0,0)
        obj.ViewDir = FreeCAD.Vector(0,0,1)
        obj.UpDir   = FreeCAD.Vector(0,1,0)
        obj.Proxy = self

    def execute(self, obj):
        obj.Shape = obj.Source.Shape.reflectLines(obj.ViewDir, obj.ViewPos, obj.UpDir)

    #def onChanged(self, obj, prop):
        #return(False)

class ReflectLinesVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class ReflectLinesCommand:
    """Creates the reflect lines on a shape, according to a view direction"""
    def makeFeature(self, s):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","ReflectLines")
        ReflectLinesFP(fp,s)
        ReflectLinesVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel[0])

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

def run():
    ReflectLinesCommand().Activated()

FreeCADGui.addCommand('ReflectLines', ReflectLinesCommand())

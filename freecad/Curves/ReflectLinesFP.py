# -*- coding: utf-8 -*-

__title__   = "Reflect Lines"
__author__  = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__     = "Creates the reflect lines on a shape, according to a view direction"

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import os
import FreeCAD
import FreeCADGui
import Part

from freecad.Curves import nurbs_tools
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join( ICONPATH, 'reflectLines.svg')

class ReflectLinesFP:
    """Creates the reflect lines on a shape, according to a view direction"""
    def __init__(self, obj, src):
        """Add the properties"""
        obj.addProperty("App::PropertyLink",   "Source",  "ReflectLines", "Source object")
        obj.addProperty("App::PropertyLinkSubList","IndivFaces","ReflectLines", "Individual faces")
        obj.addProperty("App::PropertyVector", "ViewPos", "ReflectLines", "View position")
        obj.addProperty("App::PropertyVector", "ViewDir", "ReflectLines", "View direction")
        obj.addProperty("App::PropertyVector", "UpDir",   "ReflectLines", "Up direction")
        obj.addProperty("App::PropertyBool",   "ShapeCleaning","ReflectLines", "Remove duplicate edges").ShapeCleaning = False
        obj.addProperty("App::PropertyInteger", "Samples","CleaningOptions", "Number of edge samples").Samples = 10
        obj.addProperty("App::PropertyQuantity", "Tolerance","CleaningOptions", "Tolerance for duplicate detection").Tolerance = 1e-3
        #obj.Samples = [10,3,999,1]
        obj.ViewPos = FreeCAD.Vector(0,0,0)
        obj.ViewDir = FreeCAD.Vector(0,0,1)
        obj.UpDir   = FreeCAD.Vector(0,1,0)
        obj.setEditorMode("Samples",2)
        obj.setEditorMode("Tolerance",2)
        if isinstance(src,(list,tuple)):
            obj.IndivFaces = src
        else:
            obj.Source = src
        obj.Proxy = self

    def execute(self, obj):
        sh = None
        rl = False
        if len(obj.IndivFaces) > 0:
            faces = _utils.getShape(obj, "IndivFaces", "Face")
            sh = Part.Compound(faces)
        elif hasattr(obj.Source,"Shape"):
            sh = obj.Source.Shape
        try:
            rl = sh.reflectLines(obj.ViewDir, obj.ViewPos, obj.UpDir)
        except AttributeError:
            pass
        if rl and obj.ShapeCleaning:
            edges = rl.Edges
            rl = Part.Compound(nurbs_tools.remove_subsegments(edges, num=obj.Samples, tol=obj.Tolerance))
        if rl:
            obj.Shape = rl

    def onChanged(self, obj, prop):
        if prop in ("Source","ViewPos","ViewDir","UpDir"):
            self.execute(obj)
        if prop == "ShapeCleaning":
            if obj.ShapeCleaning:
                obj.setEditorMode("Samples",0)
                obj.setEditorMode("Tolerance",0)
            else:
                obj.setEditorMode("Samples",2)
                obj.setEditorMode("Tolerance",2)

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
        return fp

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select an object first !\n")
        else:
            rot = FreeCADGui.ActiveDocument.ActiveView.getCameraOrientation()
            vdir = FreeCAD.Vector(0,0,-1)
            vdir = rot.multVec(vdir)
            udir = FreeCAD.Vector(0,1,0)
            udir = rot.multVec(udir)
            pos = FreeCADGui.ActiveDocument.ActiveView.getCameraNode().position.getValue().getValue()
            pos = FreeCAD.Vector(*pos)
            facelist = []
            for so in sel:
                o = so.Object
                if so.HasSubObjects:
                    facelist.append((o,so.SubElementNames))
                elif hasattr(o,"Proxy") and isinstance(o.Proxy,ReflectLinesFP):
                    o.ViewPos = pos
                    o.ViewDir = vdir
                    o.UpDir = udir
                else:
                    fp = self.makeFeature(o)
                    fp.ViewPos = pos
                    fp.ViewDir = vdir
                    fp.UpDir = udir
            if facelist:
                fp = self.makeFeature(facelist)
                fp.ViewPos = pos
                fp.ViewDir = vdir
                fp.UpDir = udir

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__
        }

def run():
    ReflectLinesCommand().Activated()

FreeCADGui.addCommand('ReflectLines', ReflectLinesCommand())

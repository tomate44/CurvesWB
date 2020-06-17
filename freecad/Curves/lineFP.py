# -*- coding: utf-8 -*-

__title__ = "Parametric line"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Parametric line between two vertexes."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, "line.svg")
debug = _utils.debug
debug = _utils.doNothing

class line:
    """Creates a parametric line between two vertexes"""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Vertex1", "Line", "First Vertex")
        obj.addProperty("App::PropertyLinkSub", "Vertex2", "Line", "Second Vertex")
        obj.Proxy = self

    def execute(self, obj):
        v1 = _utils.getShape(obj, "Vertex1", "Vertex")
        v2 = _utils.getShape(obj, "Vertex2", "Vertex")
        if v1 and v2:
            l = Part.LineSegment(v1.Point, v2.Point)
            obj.Shape = l.toShape()
        else:
            FreeCAD.Console.PrintError("%s broken !\n"%obj.Label)

class lineVP:
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

class lineCommand:
    """Creates a parametric line between two vertexes"""
    def makeLineFeature(self,source):
        lineObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Line")
        line(lineObj)
        lineVP(lineObj.ViewObject)
        lineObj.Vertex1 = source[0]
        lineObj.Vertex2 = source[1]
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        verts = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select 2 vertexes !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Vertex):
                        verts.append((selobj.Object, selobj.SubElementNames[i]))
        if len(verts) == 2:
            self.makeLineFeature(verts)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Vertex COUNT 2")
            return f.match()
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Line', 'ToolTip': 'Creates a line between 2 vertexes'}

FreeCADGui.addCommand('line', lineCommand())

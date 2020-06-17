# -*- coding: utf-8 -*-

__title__ = "Curve extend"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Extend an edge by a given distance."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH
from freecad.Curves import curveExtend

TOOL_ICON = os.path.join(ICONPATH, 'extendcurve.svg')
debug = _utils.debug
debug = _utils.doNothing

class extend:
    """Extends the selected edge"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSub",      "Edge",       "Base", "Input edge to extend")
        obj.addProperty("App::PropertyEnumeration",  "Output",     "Base", "Output shape").Output = ["SingleEdge","Wire"]

        obj.addProperty("App::PropertyFloat",        "LengthStart","Beginning", "Start Extension Length").LengthStart=10.0
        obj.addProperty("App::PropertyEnumeration",  "TypeStart",  "Beginning", "Start Extension type").TypeStart = ["Straight","G2 curve"]

        obj.addProperty("App::PropertyFloat",        "LengthEnd",  "End", "End Extension Length").LengthEnd=10.0
        obj.addProperty("App::PropertyEnumeration",  "TypeEnd",    "End", "End Extension type").TypeEnd = ["Straight","G2 curve"]
        
        obj.TypeStart = "Straight"
        obj.TypeEnd = "Straight"
        obj.Output = "SingleEdge"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if prop == "LengthStart":
            if fp.LengthStart < 0:
                fp.LengthStart = 0
        elif prop == "LengthEnd":
            if fp.LengthEnd < 0:
                fp.LengthEnd = 0

    def execute(self, obj):
        edge = _utils.getShape(obj, "Edge", "Edge")
        curve = curveExtend.getTrimmedCurve(edge)

        cont_start = 1
        if hasattr(obj, "TypeStart"):
            if obj.TypeStart == "G2 curve":
                cont_start = 2
        cont_end = 1
        if hasattr(obj, "TypeEnd"):
            if obj.TypeEnd == "G2 curve":
                cont_end = 2

        ext = []
        if obj.LengthStart > 0:
            ext.append(curveExtend.extendCurve( curve, 0, obj.LengthStart, cont_start))
        if obj.LengthEnd > 0:
            ext.append(curveExtend.extendCurve( curve, 1, obj.LengthEnd, cont_end))
        if not ext == []:
            if hasattr(obj, "Output"):
                if obj.Output == "SingleEdge":
                    for c in ext:
                        curve.join(c.toBSpline())
                    obj.Shape = curve.toShape()
                else:
                    ext.append(curve)
                    edges = []
                    for c in ext:
                        edges.append(Part.Edge(c))
                    w = Part.Wire(Part.__sortEdges__(edges))
                    w.fixWire()
                    obj.Shape = w


class extendVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def claimChildren(self):
        return [self.Object.Edge[0]]
        
    def onDelete(self, feature, subelements):
        return True

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class extendCommand:
    """Extends the selected edge"""
    def makeExtendFeature(self,source):
        if source is not []:
            for o in source:
                extCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","ExtendedCurve")
                extend(extCurve)
                extCurve.Edge = o
                extendVP(extCurve.ViewObject)
                extCurve.ViewObject.LineWidth = 2.0
                extCurve.ViewObject.LineColor = (0.5,0.0,0.3)
            FreeCAD.ActiveDocument.recompute()
        

    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select the edges to extend first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        edges.append((selobj.Object, selobj.SubElementNames[i]))
                        selobj.Object.ViewObject.Visibility=False
        if edges:
            self.makeExtendFeature(edges)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            #return f.match()
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Extend Curve', 'ToolTip': 'Extends the selected edge'}

FreeCADGui.addCommand('extend', extendCommand())

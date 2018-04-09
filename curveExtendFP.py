# -*- coding: utf-8 -*-

__title__ = "Curve extend"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Extend an edge by a given distance."

import FreeCAD
import FreeCADGui
import Part
import _utils
import curveExtend

TOOL_ICON = _utils.iconsPath() + '/extendcurve.svg'
debug = _utils.debug
debug = _utils.doNothing

class extend:
    """Extends the selected edge"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSub",      "Edge",       "Extend", "Input edge to extend")
        obj.addProperty("App::PropertyFloat",        "Length",     "Extend", "Extension Length").Length=1.0
        obj.addProperty("App::PropertyEnumeration",  "Location",   "Extend", "Edge extremity to extend").Location = ["Start","End","Both"]
        obj.addProperty("App::PropertyEnumeration",  "Type",       "Extend", "Extension type").Type = ["Straight","G2 curve"]
        obj.addProperty("App::PropertyEnumeration",  "Output",     "Extend", "Output shape").Output = ["SingleEdge","Wire"]
        obj.Location = "Start"
        obj.Type = "Straight"
        obj.Output = "SingleEdge"
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if prop == "Length":
            if fp.Length < 0:
                fp.Length = 0

    def execute(self, obj):
        edge = _utils.getShape(obj, "Edge", "Edge")
        if hasattr(obj, "Length"):
            if obj.Length <= 0:
                obj.Shape = edge
                return()
        curve = curveExtend.getTrimmedCurve(edge)
        cont = 1
        if hasattr(obj, "Type"):
            if obj.Type == "G2 curve":
                cont = 2
        ext = []
        if hasattr(obj, "Location"):
            if obj.Location in ["Start","Both"]:
                ext.append(curveExtend.extendCurve( curve, 0, obj.Length, cont))
            if obj.Location in ["End","Both"]:
                ext.append(curveExtend.extendCurve( curve, 1, obj.Length, cont))
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

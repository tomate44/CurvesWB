# -*- coding: utf-8 -*-

__title__ = "Split curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Splits the selected edge."

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/splitcurve.svg'
debug = _utils.debug
#debug = _utils.doNothing

class split:
    """Splits the selected edge."""
    def __init__(self, obj, e):
        obj.addProperty("App::PropertyLinkSub",      "Edge",     "Split",  "Edge to split").Edge = e
        obj.addProperty("App::PropertyEnumeration",  "Method",   "Split",  "Splitting method").Method = ['Parameter','Distance','Percent']
        obj.addProperty("App::PropertyFloat",        "Value",    "Split",  "Split at given parameter")
        obj.addProperty("App::PropertyFloat",        "Param",    "Split",  "Parameter")
        obj.setEditorMode("Param", 2)
        obj.Method = 'Percent'
        obj.Value = 50.0
        obj.Proxy = self

    def onChanged(self, fp, prop):
        e = _utils.getShape(fp, "Edge", "Edge")
        if not e:
            return
        if prop == "Edge":
            debug("Split : Edge changed")
        if prop == "Method":
            debug("Split : Method changed")
            if fp.Method == "Percent":
                fp.Value = self.ParamToPercent(e, fp.Param)
            elif fp.Method == "Distance":
                fp.Value = self.ParamToDistance(e, fp.Param)
            else:
                fp.Value = fp.Param
        if prop == "Value":
            if fp.Method == "Percent":
                if fp.Value < 0:
                    fp.Value = 0
                elif fp.Value > 100:
                    fp.Value = 100
                fp.Param = self.PercentToParam(e, fp.Value)
            elif fp.Method == "Distance":
                if fp.Value < -e.Length:
                    fp.Value = -e.Length
                elif fp.Value > e.Length:
                    fp.Value = e.Length
                fp.Param = self.DistanceToParam(e, fp.Value)
            else: # fp.Method == "Parameter"
                if fp.Value < e.FirstParameter:
                    fp.Value = e.FirstParameter
                elif fp.Value > e.LastParameter:
                    fp.Value = e.LastParameter
                fp.Param = fp.Value
            self.execute(fp)

    def PercentToParam(self, e, per):
        prange = e.LastParameter - e.FirstParameter
        return (e.FirstParameter + 0.01*per*prange)

    def DistanceToParam(self, e, dis):
        prange = e.LastParameter - e.FirstParameter
        if dis >= e.Length:
            return(e.LastParameter)
        elif dis <= -e.Length:
            return(e.FirstParameter)
        else:
            return (e.getParameterByLength(dis))

    def ParamToPercent(self, e, par):
        prange = e.LastParameter - e.FirstParameter
        return (100.0*(par-e.FirstParameter)/prange)

    def ParamToDistance(self, e, par):
        #prange = e.LastParameter - e.FirstParameter
        dis = Part.Edge(e.Curve,e.FirstParameter,par).Length
        return (dis)

    def execute(self, obj):
        e = _utils.getShape(obj, "Edge", "Edge")
        p = obj.Value
        if   obj.Method == "Percent":
            p = self.PercentToParam(e, obj.Value)
        elif obj.Method == "Distance":
            p = self.DistanceToParam(e, obj.Value)
        if p > e.FirstParameter and p < e.LastParameter:
            obj.Shape = e.split(p)
        else:
            obj.Shape = e
        obj.Placement = e.Placement

class splitVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def claimChildren(self):
        return [self.Object.Edge[0]]

class splitCommand:
    """Splits the selected edges."""
    def makeSplitFeature(self,e):
        splitCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","SplitCurve")
        split(splitCurve, e)
        splitVP(splitCurve.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        splitCurve.Value = 50.0
        splitCurve.ViewObject.PointSize = 5.0

    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select the edges to split first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        self.makeSplitFeature((selobj.Object, selobj.SubElementNames[i]))
                        if selobj.Object.Shape:
                            if len(selobj.Object.Shape.Edges) == 1:
                                selobj.Object.ViewObject.Visibility = False
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            return f.match()
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Split Curve', 'ToolTip': 'Splits the selected edge'}

FreeCADGui.addCommand('split', splitCommand())

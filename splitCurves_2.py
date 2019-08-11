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
        obj.Proxy = self
        obj.addProperty("App::PropertyLinkSub",
                        "Source",
                        "Split",
                        "Edge to split").Source = e
        obj.addProperty("App::PropertyStringList",
                        "Values",
                        "Split",
                        "List of splitting locations\n% and units are allowed\nNegative values are computed from edge end")
        #obj.addProperty("App::PropertyFloatList",
                        #"Parameters",
                        #"Split",
                        #"Parameter list")
        #obj.setEditorMode("Parameters",2)

    def parse_values(self, edge, values):
        #edge = _utils.getShape(fp, "Source", "Edge")
        if not edge:
            return
        l = edge.Length
        parameters = []
        for v in values:
            num_val = None
            par = None
            if "%" in v:
                num_val = float(v.split("%")[0]) * l / 100
            else:
                num_val = FreeCAD.Units.parseQuantity(v).Value
            if num_val < 0:
                par = edge.Curve.parameterAtDistance(num_val, edge.LastParameter)
            else:
                par = edge.Curve.parameterAtDistance(num_val, edge.FirstParameter)
            if par > edge.FirstParameter and par < edge.LastParameter :
                parameters.append(par)
        parameters.sort()
        return parameters

    def onChanged(self, fp, prop):
        e = None
        if hasattr(fp, "Source"):
            e = _utils.getShape(fp, "Source", "Edge")
        if not e:
            return
        if prop == "Source":
            debug("Split : Source changed")
            self.execute(fp)
        if prop == "Values":
            debug("Split : Values changed")
            self.execute(fp)

    def execute(self, obj):
        e = _utils.getShape(obj, "Source", "Edge")
        params = []
        if hasattr(obj, "Values"):
            params = self.parse_values(e, obj.Values)
        if params == []:
            obj.Shape = e
            return
        if params[0] > e.FirstParameter:
            params.insert(0, e.FirstParameter)
        if params[-1] < e.LastParameter:
            params.append(e.LastParameter)
        edges = []
        for i in range(len(params)-1):
            c = e.Curve.trim(params[i], params[i+1])
            edges.append(c.toShape())
        w = Part.Wire(edges)
        if w.isValid():
            obj.Shape = w
        else:
            FreeCAD.Console.PrintError("Split curve : Invalid Wire !")
            obj.Shape = e

    #def onDocumentRestored(self, fp):
        #fp.setEditorMode("Param", 2)

class splitVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

    def claimChildren(self):
        return [self.Object.Source[0]]

class splitCommand:
    """Splits the selected edges."""
    def makeSplitFeature(self,e):
        splitCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","SplitCurve")
        split(splitCurve, e)
        splitVP(splitCurve.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        splitCurve.Values = ["50%"]
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

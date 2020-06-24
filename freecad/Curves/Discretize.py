# -*- coding: utf-8 -*-

__title__ = "Discretize"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Discretize an edge or a wire."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'discretize.svg')
debug = _utils.debug
debug = _utils.doNothing

class Discretization:
    def __init__(self, obj , edge):
        debug("Discretization class Init")
        obj.addProperty("App::PropertyLinkSub",      "Edge",      "Discretization",   "Edge").Edge = edge
        obj.addProperty("App::PropertyEnumeration",  "Target",    "Discretization",   "Tool target").Target=["Edge","Wire"]
        obj.addProperty("App::PropertyEnumeration",  "Algorithm", "Method",   "Discretization Method").Algorithm=["Number","QuasiNumber","Distance","Deflection","QuasiDeflection","Angular-Curvature"]
        obj.addProperty("App::PropertyInteger",      "Number",    "Method",   "Number of edge points").Number = 100
        obj.addProperty("App::PropertyFloat",        "Distance",  "Method",   "Distance between edge points").Distance=1.0
        obj.addProperty("App::PropertyFloat",        "Deflection","Method",   "Distance for deflection Algorithm").Deflection=1.0
        obj.addProperty("App::PropertyFloat",        "Angular",   "Method",   "Angular value for Angular-Curvature Algorithm").Angular=0.1
        obj.addProperty("App::PropertyFloat",        "Curvature", "Method",   "Curvature value for Angular-Curvature Algorithm").Curvature=0.1
        obj.addProperty("App::PropertyInteger",      "Minimum",   "Method",   "Minimum Number of points").Minimum = 2
        obj.addProperty("App::PropertyFloat",        "ParameterFirst",     "Parameters",   "Start parameter")
        obj.addProperty("App::PropertyFloat",        "ParameterLast",      "Parameters",   "End parameter")
        obj.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
        obj.Proxy = self
        self.obj = obj
        obj.Algorithm = "Number"
        obj.Target = "Edge"
        edge = self.getTarget(obj, False)
        obj.ParameterFirst = edge.FirstParameter
        obj.ParameterLast = edge.LastParameter
        self.execute(obj)

    def edgeBounds(self, obj):
        o = obj.Edge[0]
        e = obj.Edge[1][0]
        n = eval(e.lstrip('Edge'))
        try:
            edge = o.Shape.Edges[n-1]
            return edge.FirstParameter, edge.LastParameter
        except:
            return 0,1

    def getTarget( self, obj, typ):
        o = obj.Edge[0]
        e = obj.Edge[1][0]
        n = eval(e.lstrip('Edge'))
        try:
            edge = o.Shape.Edges[n-1]
            obj.setEditorMode("Target", 2)
            for w in o.Shape.Wires:
                for e in w.Edges:
                    if edge.isSame(e):
                        debug("found matching edge")
                        debug("wire has %d edges"%len(w.Edges))
                        obj.setEditorMode("Target", 0)
                        if typ:
                            return w
            return edge
        except:
            return None

    def buildPoints(self, obj):
        if obj.Target == "Wire":
            target = self.getTarget(obj, True)
            if not target:
                debug("Failed to get wire")
                return False
            if   obj.Algorithm == "Number":
                obj.Points = target.discretize( Number = obj.Number)
            elif obj.Algorithm == "QuasiNumber":
                obj.Points = target.discretize( QuasiNumber = obj.Number)
            elif obj.Algorithm == "Distance":
                obj.Points = target.discretize( Distance = obj.Distance)
            elif obj.Algorithm == "Deflection":
                obj.Points = target.discretize( Deflection = obj.Deflection)
            elif obj.Algorithm == "QuasiDeflection":
                obj.Points = target.discretize( QuasiDeflection = obj.Deflection)
            elif obj.Algorithm == "Angular-Curvature":
                obj.Points = target.discretize( Angular = obj.Angular, Curvature = obj.Curvature, Minimum = obj.Minimum)
        else:
            target = self.getTarget(obj, False)
            if not target:
                debug("Failed to get edge")
                return False
            if   obj.Algorithm == "Number":
                obj.Points = target.discretize( Number = obj.Number,         First = obj.ParameterFirst, Last = obj.ParameterLast)
            elif obj.Algorithm == "QuasiNumber":
                obj.Points = target.discretize( QuasiNumber = obj.Number,    First = obj.ParameterFirst, Last = obj.ParameterLast)
            elif obj.Algorithm == "Distance":
                obj.Points = target.discretize( Distance = obj.Distance,     First = obj.ParameterFirst, Last = obj.ParameterLast)
            elif obj.Algorithm == "Deflection":
                obj.Points = target.discretize( Deflection = obj.Deflection, First = obj.ParameterFirst, Last = obj.ParameterLast)
            elif obj.Algorithm == "QuasiDeflection":
                obj.Points = target.discretize( QuasiDeflection = obj.Deflection, First = obj.ParameterFirst, Last = obj.ParameterLast)
            elif obj.Algorithm == "Angular-Curvature":
                obj.Points = target.discretize( Angular = obj.Angular, Curvature = obj.Curvature, Minimum = obj.Minimum, First = obj.ParameterFirst, Last = obj.ParameterLast)

        return True

    def execute(self, obj):
        debug("* Discretization : execute *")
        if self.buildPoints( obj):
            obj.Shape = Part.Compound([Part.Vertex(i) for i in obj.Points])

    def onChanged(self, fp, prop):
        #print fp
        if not fp.Edge:
            return
        if prop == "Edge":
            debug("Discretization : Edge changed")
            #self.setEdge( fp)
        if prop == "Target":
            debug("Discretization : Target changed")
            #self.setEdge( fp)
            if fp.Target == "Wire":
                fp.setEditorMode("ParameterFirst", 2)
                fp.setEditorMode("ParameterLast", 2)
            else:
                fp.setEditorMode("ParameterFirst", 0)
                fp.setEditorMode("ParameterLast", 0)
                
        if prop == "Algorithm":
            debug("Discretization : Algorithm changed")
            if fp.Algorithm in ("Number","QuasiNumber"):
                fp.setEditorMode("Number", 0)
                fp.setEditorMode("Distance", 2)
                fp.setEditorMode("Deflection", 2)
                fp.setEditorMode("Angular", 2)
                fp.setEditorMode("Curvature", 2)
                fp.setEditorMode("Minimum", 2)
            elif fp.Algorithm == "Distance":
                fp.setEditorMode("Number", 2)
                fp.setEditorMode("Distance", 0)
                fp.setEditorMode("Deflection", 2)
                fp.setEditorMode("Angular", 2)
                fp.setEditorMode("Curvature", 2)
                fp.setEditorMode("Minimum", 2)
            elif fp.Algorithm in ("Deflection","QuasiDeflection"):
                fp.setEditorMode("Number", 2)
                fp.setEditorMode("Distance", 2)
                fp.setEditorMode("Deflection", 0)
                fp.setEditorMode("Angular", 2)
                fp.setEditorMode("Curvature", 2)
                fp.setEditorMode("Minimum", 2)
            elif fp.Algorithm == "Angular-Curvature":
                fp.setEditorMode("Number", 2)
                fp.setEditorMode("Distance", 2)
                fp.setEditorMode("Deflection", 2)
                fp.setEditorMode("Angular", 0)
                fp.setEditorMode("Curvature", 0)
                fp.setEditorMode("Minimum", 0)
        if prop == "Number":
            if fp.Number <= 1:
                fp.Number = 2
            debug("Discretization : Number changed to %s"%str(fp.Number))
        if prop == "Distance":
            if fp.Distance <= 0.0:
                fp.Distance = 0.0001
            debug("Discretization : Distance changed to %s"%str(fp.Distance))
        if prop == "Deflection":
            if fp.Deflection <= 0.0:
                fp.Deflection = 0.0001
            debug("Discretization : Deflection changed to %s"%str(fp.Deflection))
        if prop == "Angular":
            if fp.Angular <= 0.0:
                fp.Angular = 0.0001
            debug("Discretization : Angular changed to %s"%str(fp.Angular))
        if prop == "Curvature":
            if fp.Curvature <= 0.0:
                fp.Curvature = 0.0001
            debug("Discretization : Curvature changed to %s"%str(fp.Curvature))
        if prop == "Minimum":
            if fp.Minimum < 2:
                fp.Minimum = 2
            debug("Discretization : Minimum changed to %s"%str(fp.Minimum))
        if prop == "ParameterFirst":
            if fp.ParameterFirst < self.edgeBounds(fp)[0]:
                fp.ParameterFirst = self.edgeBounds(fp)[0]
            debug("Discretization : ParameterFirst changed to %s"%str(fp.ParameterFirst))
        if prop == "ParameterLast":
            if fp.ParameterLast > self.edgeBounds(fp)[1]:
                fp.ParameterLast = self.edgeBounds(fp)[1]
            debug("Discretization : ParameterLast changed to %s"%str(fp.ParameterLast))
            
    def __getstate__(self):
        out = {"name": self.obj.Name,
               "algo": self.obj.Algorithm,
               "target": self.obj.Target}
        return out

    def __setstate__(self,state):
        self.obj = FreeCAD.ActiveDocument.getObject(state["name"])
        if not "Algorithm" in self.obj.PropertiesList:
            self.obj.addProperty("App::PropertyEnumeration",  "Algorithm", "Method",   "Discretization Method").Algorithm=["Number","QuasiNumber","Distance","Deflection","QuasiDeflection","Angular-Curvature"]
        if not "Target" in self.obj.PropertiesList:
            self.obj.addProperty("App::PropertyEnumeration",  "Target",    "Discretization",   "Tool target").Target=["Edge","Wire"]
        self.obj.Algorithm = state["algo"]
        self.obj.Target = state["target"]
        return None

class ViewProviderDisc:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        return [self.Object.Edge[0]]
        
    def onDelete(self, feature, subelements):
        try:
            self.Object.Edge[0].ViewObject.Visibility=True
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: {0} \n".format(err))
        return True

class discretize:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                subobj = obj.SubObjects[0]
                if issubclass(type(subobj),Part.Edge):
                    res.append((obj.Object,[obj.SubElementNames[0]]))
            else:
                res.append((obj.Object,["Edge1"]))
        return res

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = self.parseSel(s)
        FreeCADGui.doCommand("from freecad.Curves import Discretize")
        for e in edges:
            FreeCADGui.doCommand('obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Discretized_Edge")')
            FreeCADGui.doCommand('Discretize.Discretization(obj, (FreeCAD.ActiveDocument.getObject("%s"),"%s"))'%(e[0].Name,e[1][0]))
            FreeCADGui.doCommand('Discretize.ViewProviderDisc(obj.ViewObject)')
            FreeCADGui.doCommand('obj.ViewObject.PointSize = 3')
            #obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Discretized_Edge")
            #Discretization(obj,e)
            #ViewProviderDisc(obj.ViewObject)
            #obj.ViewObject.PointSize = 3.00000
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            #return f.match()
            return True
        else:
            return False


    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Discretize', 'ToolTip': 'Discretize an edge or a wire'}

FreeCADGui.addCommand('Discretize', discretize())




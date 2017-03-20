from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class Discretization:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        debug("\nDiscretization class Init\n")
        obj.addProperty("App::PropertyLinkSub",      "Edge",      "Discretization",   "Edge").Edge = edge
        obj.addProperty("App::PropertyEnumeration",  "Target",    "Discretization",   "Tool target").Target=["Edge","Wire"]
        obj.addProperty("App::PropertyEnumeration",  "Algorithm", "Method",   "Discretization Method").Algorithm=["Number","QuasiNumber","Distance","Deflection","QuasiDeflection","Angular-Curvature"]
        obj.addProperty("App::PropertyInteger",      "Number",    "Method",   "Number of edge points").Number = 10
        obj.addProperty("App::PropertyFloat",        "Distance",  "Method",   "Distance between edge points").Distance=1.0
        obj.addProperty("App::PropertyFloat",        "Deflection","Method",   "Distance for deflection Algorithm").Deflection=1.0
        obj.addProperty("App::PropertyFloat",        "Angular",   "Method",   "Angular value for Angular-Curvature Algorithm").Angular=0.1
        obj.addProperty("App::PropertyFloat",        "Curvature", "Method",   "Curvature value for Angular-Curvature Algorithm").Curvature=0.1
        obj.addProperty("App::PropertyInteger",      "Minimum",   "Method",   "Minimum Number of points").Minimum = 2
        obj.addProperty("App::PropertyFloat",        "ParameterFirst",     "Parameters",   "Start parameter")
        obj.addProperty("App::PropertyFloat",        "ParameterLast",      "Parameters",   "End parameter")
        obj.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
        #obj.addProperty("App::PropertyVectorList",   "Tangents",   "Discretization",   "Tangents")
        #obj.addProperty("App::PropertyVectorList",   "Normals",    "Discretization",   "Normals")
        #obj.addProperty("Part::PropertyPartShape",   "Shape",     "Discretization",   "Shape")
        obj.Proxy = self
        self.obj = obj
        obj.Points = []
        obj.Algorithm = "Number"
        obj.Target = "Edge"
        #self.edge = None
        #self.wire = None
        #self.target = None
        #self.setEdge(obj)
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
            return(edge.FirstParameter, edge.LastParameter)
        except:
            return(0,1)

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
                            return(w)
            return(edge)
        except:
            return(None)

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
        debug("\n* Discretization : execute *\n")
        #self.setEdge( obj)
        if self.buildPoints( obj):
            obj.Shape = Part.Compound([Part.Vertex(i) for i in obj.Points])
            #self.obj = obj

    def onChanged(self, fp, prop):
        #print fp
        if not fp.Edge:
            return
        if prop == "Edge":
            debug("Discretization : Edge changed\n")
            #self.setEdge( fp)
        if prop == "Target":
            debug("Discretization : Target changed\n")
            #self.setEdge( fp)
            if fp.Target == "Wire":
                fp.setEditorMode("ParameterFirst", 2)
                fp.setEditorMode("ParameterLast", 2)
            else:
                fp.setEditorMode("ParameterFirst", 0)
                fp.setEditorMode("ParameterLast", 0)
                
        if prop == "Algorithm":
            debug("Discretization : Algorithm changed\n")
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
            debug("Discretization : Number changed to "+str(fp.Number)+"\n")
        if prop == "Distance":
            if fp.Distance <= 0.0:
                fp.Distance = 0.0001
            debug("Discretization : Distance changed to "+str(fp.Distance)+"\n")
        if prop == "Deflection":
            if fp.Deflection <= 0.0:
                fp.Deflection = 0.0001
            debug("Discretization : Deflection changed to "+str(fp.Deflection)+"\n")
        if prop == "Angular":
            if fp.Angular <= 0.0:
                fp.Angular = 0.0001
            debug("Discretization : Angular changed to "+str(fp.Angular)+"\n")
        if prop == "Curvature":
            if fp.Curvature <= 0.0:
                fp.Curvature = 0.0001
            debug("Discretization : Curvature changed to "+str(fp.Curvature)+"\n")
        if prop == "Minimum":
            if fp.Minimum < 2:
                fp.Minimum = 2
            debug("Discretization : Minimum changed to "+str(fp.Minimum)+"\n")
        if prop == "ParameterFirst":
            if fp.ParameterFirst < self.edgeBounds(fp)[0]:
                fp.ParameterFirst = self.edgeBounds(fp)[0]
            debug("Discretization : ParameterFirst changed to "+str(fp.ParameterFirst)+"\n")
        if prop == "ParameterLast":
            if fp.ParameterLast > self.edgeBounds(fp)[1]:
                fp.ParameterLast = self.edgeBounds(fp)[1]
            debug("Discretization : ParameterLast changed to "+str(fp.ParameterLast)+"\n")
        #self.execute(fp) # Infinite loop
            
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
        return (path_curvesWB_icons+'/discretize.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def claimChildren(self):
        return [self.Object.Edge[0]]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            self.Object.Edge[0].ViewObject.Visibility=True
            #self.Object.Tool.ViewObject.show()
        except Exception as err:
            App.Console.PrintError("Error in onDelete: " + err.message)
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
        for e in edges:
            obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Discretized_Edge") #add object to document
            Discretization(obj,e)
            ViewProviderDisc(obj.ViewObject)
            obj.ViewObject.PointSize = 3.00000
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/discretize.svg', 'MenuText': 'Discretize', 'ToolTip': 'Discretizes edge or wire'}

FreeCADGui.addCommand('Discretize', discretize())




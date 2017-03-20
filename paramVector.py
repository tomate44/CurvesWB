 
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


class paramVector:
    def __init__(self, obj):
        ''' Add the properties '''
        debug("\paramVector class Init\n")
        obj.addProperty("App::PropertyVector",       "Origin",      "Vector",   "Origin point")
        obj.addProperty("App::PropertyVector",       "Direction",   "Vector",   "Direction vector")
        obj.Proxy = self

    def execute(self, obj):
        debug("\n* paramVector : execute *\n")

    def onChanged(self, fp, prop):
        pass

    def __getstate__(self):
        #out = {"name": self.obj.Name,
               #"algo": self.obj.Algorithm,
               #"target": self.obj.Target}
        #return out
        return None

    def __setstate__(self,state):
        #self.obj = FreeCAD.ActiveDocument.getObject(state["name"])
        #if not "Algorithm" in self.obj.PropertiesList:
            #self.obj.addProperty("App::PropertyEnumeration",  "Algorithm", "Method",   "Discretization Method").Algorithm=["Number","QuasiNumber","Distance","Deflection","QuasiDeflection","Angular-Curvature"]
        #if not "Target" in self.obj.PropertiesList:
            #self.obj.addProperty("App::PropertyEnumeration",  "Target",    "Discretization",   "Tool target").Target=["Edge","Wire"]
        #self.obj.Algorithm = state["algo"]
        #self.obj.Target = state["target"]
        return None

class paramVectorVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/discretize.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def updateData(self, fp, prop):
        if (prop == "Origin") or (prop == "Direction"):
            # update coordinates
            pass
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

class vector:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                p = obj.PickedPoints[0]
                return (p)
        return(None)

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        p = self.parseSel(s)
        obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Vector") #add object to document
        paramVector(obj)
        paramVectorVP(obj.ViewObject)
        if p:
            obj.Origin = p
        else:
            obj.Origin = FreeCAD.Vector(0,0,0)
        obj.Direction = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/discretize.svg', 'MenuText': 'Direction Vector', 'ToolTip': 'Creates a direction vector'}

FreeCADGui.addCommand('Vector', vector())




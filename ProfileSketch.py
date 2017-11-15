import os
import FreeCAD, FreeCADGui
import Part, Sketcher
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class profile:
    "creates a profile sketch"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub",  "Edge1",        "Profile",   "First support edge")
        obj.addProperty("App::PropertyLinkSub",  "Edge2",        "Profile",   "Second support edge")
        obj.addProperty("App::PropertyFloat",    "Parameter1",   "Profile",   "Parameter on first edge")
        obj.addProperty("App::PropertyFloat",    "Parameter2",   "Profile",   "Parameter on second edge")
        obj.addProperty("App::PropertyVector",   "MainAxis",     "Profile",   "Main axis of the sketch")
        obj.addProperty("Part::PropertyPartShape","Shape",       "Profile",   "Shape of the object")
        obj.Proxy = self

    def getEdges(self, obj):
        res = []
        if hasattr(obj, "Edge1"):
            n = eval(obj.Edge1[1][0].lstrip('Edge'))
            res.append(obj.Edge1[0].Shape.Edges[n-1])
        if hasattr(obj, "Edge2"):
            n = eval(obj.Edge2[1][0].lstrip('Edge'))
            res.append(obj.Edge2[0].Shape.Edges[n-1])
        return(res)

    def execute(self, obj):
        e1,e2 = self.getEdges(obj)
        ls = Part.LineSegment(e1.valueAt(obj.Parameter1),e2.valueAt(obj.Parameter2))
        debug(ls)
        obj.Shape = ls.toShape()
        return()
    
    def onChanged(self, fp, prop):
        if prop in ["Edge1","Edge2","Parameter1","Parameter2","MainAxis"]:
            self.execute(fp)

class profileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/joincurve.svg')

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

    #def claimChildren(self):
        #return None #[self.Object.Base, self.Object.Tool]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        return True


class profileCommand:
    "creates a profile sketch"
    def makeProfileFeature(self, shapes, params):
        prof = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','Profile')
        profile(prof)
        profileVP(prof.ViewObject)
        if isinstance(shapes,list):
            prof.Edge1 = shapes[0]
            prof.Edge2 = shapes[1]
            prof.Parameter1 = params[0]
            prof.Parameter2 = params[1]
            prof.MainAxis = FreeCAD.Vector(0,0,1)
        else:
            prof.Base = source
        FreeCAD.ActiveDocument.recompute()
        prof.ViewObject.LineWidth = 2.0
        prof.ViewObject.LineColor = (0.5,0.0,0.5)

    def Activated(self):
        shapes = []
        params = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select 2 edges or vertexes first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        shapes.append((selobj.Object, selobj.SubElementNames[i]))
                        p = selobj.PickedPoints[i]
                        poe = selobj.SubObjects[i].distToShape(Part.Vertex(p))
                        par = poe[2][0][2]
                        params.append(par)
                    elif isinstance(selobj.SubObjects[i], Part.Vertex):
                        shapes.append((selobj.Object, selobj.SubElementNames[i]))
                        #p = selobj.PickedPoints[i]
                        #poe = so.distToShape(Part.Vertex(p))
                        #par = poe[2][0][2]
                        params.append(0)
            else:
                FreeCAD.Console.PrintError("Select 2 edges or vertexes first !\n")
        if shapes:
            self.makeProfileFeature(shapes, params)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/joincurve.svg', 'MenuText': 'Create profile sketch', 'ToolTip': 'creates a profile sketch'}

FreeCADGui.addCommand('profile', profileCommand())

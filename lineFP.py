import os
import FreeCAD, FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

class line:
    "Creates a line between 2 vertexes"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub",  "Vertex1",  "Line",   "First Vertex")
        obj.addProperty("App::PropertyLinkSub",  "Vertex2",  "Line",   "Second Vertex")
        obj.Proxy = self

    def getVerts(self, obj):
        res = []
        if hasattr(obj, "Vertex1"):
            n = eval(obj.Vertex1[1][0].lstrip('Vertex'))
            res.append(obj.Vertex1[0].Shape.Vertexes[n-1])
        if hasattr(obj, "Vertex2"):
            n = eval(obj.Vertex2[1][0].lstrip('Vertex'))
            res.append(obj.Vertex2[0].Shape.Vertexes[n-1])
        return(res)

    def execute(self, obj):
        verts = self.getVerts(obj)
        if isinstance(verts[0],Part.Vertex) and isinstance(verts[1],Part.Vertex):
            l = Part.LineSegment(verts[0].Point, verts[1].Point)
            obj.Shape = l.toShape()

class lineVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/line.svg')

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


class lineCommand:
    "joins the selected edges into a single BSpline Curve"
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
        if verts:
            self.makeLineFeature(verts)

        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Vertex COUNT 2")
            return f.match()
            #return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/line.svg', 'MenuText': 'Line', 'ToolTip': 'Creates a line between 2 vertexes'}

FreeCADGui.addCommand('line', lineCommand())

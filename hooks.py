 
from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin
import CoinNodes

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class hook:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        debug("\Hook class Init\n")
        obj.addProperty("App::PropertyLinkSub",      "Edge",          "Base",     "Support edge").Edge = edge
        obj.addProperty("App::PropertyEnumeration",  "Method",        "Position", "Position").Method=["Fixed","Parameter","Distance-From-Start","Distance-From-End"]
        obj.addProperty("App::PropertyFloat",        "X",             "Value", "X coordinate")
        obj.addProperty("App::PropertyFloat",        "Y",             "Value", "Y coordinate")
        obj.addProperty("App::PropertyFloat",        "Z",             "Value", "Z coordinate")
        obj.addProperty("App::PropertyFloat",        "Parameter",     "Value", "Parameter value")
        obj.addProperty("App::PropertyFloat",        "StartDistance", "Value", "Distance from edge start")
        obj.addProperty("App::PropertyFloat",        "EndDistance",   "Value", "Distance to edge end")
        obj.addProperty("App::PropertyVector",       "Center",        "Position", "Center")
        #obj.Method = "Parameter"
        obj.Proxy = self

    def getEdge(self, obj):
        if obj.Edge:
            o = obj.Edge[0]
            e = obj.Edge[1][0]
            n = eval(e.lstrip('Edge'))
            return o.Shape.Edges[n-1]
        else:
            debug("getEdge failed")
            return None

    def execute(self, obj):
        debug("* Hook : execute *\n")
        e = self.getEdge(obj)
        if e == None:
            return
        #center = FreeCAD.Vector(0,0,0)
        if obj.Method == "Fixed":
            p = FreeCAD.Vector(obj.X, obj.Y, obj.Z)
            v = Part.Vertex(p)
            obj.Center = v.distToShape(e)[1][0][1]
        elif obj.Method == "Parameter":
            obj.Center = e.valueAt(obj.Parameter)
        elif obj.Method == "Distance-From-Start":
            par = e.getParameterByLength(obj.StartDistance)
            obj.Center = e.valueAt(par)
        elif obj.Method == "Distance-From-End":
            par = e.getParameterByLength(e.Length - obj.EndDistance)
            obj.Center = e.valueAt(par)
        #radius = 1.0 * e.Length / 100.0
        #sphere = Part.Sphere()
        #sphere.Radius = radius
        #sphere.Center = obj.Center
        obj.Shape = Part.Vertex(obj.Center)

    def setEditormode(self, fp, l):
        if not len(l) == 6:
            return
        i = 0
        for prop in ["X","Y","Z","Parameter","StartDistance","EndDistance"]:
            fp.setEditorMode(prop, l[i])
            i += 1

    def onChanged(self, fp, prop):
        debug("Hook : onChanged -> %s"%str(prop))
        #print fp
        if not fp.Edge:
            return
        else:
            e = self.getEdge( fp)
        #if prop == "Edge":
            #self.setEdge( fp)

        if prop == "Method":
            if fp.Method == "Fixed":
                self.setEditormode(fp, [0,0,0,2,2,2])
                fp.X = fp.Center.x
                fp.Y = fp.Center.y
                fp.Z = fp.Center.z
                
            elif fp.Method == "Parameter":
                self.setEditormode(fp, [2,2,2,0,2,2])
                v = Part.Vertex( fp.Center )
                try:
                    fp.Parameter = e.Curve.parameter(fp.Center)
                except:
                    pass
            elif fp.Method == "Distance-From-Start":
                self.setEditormode(fp, [2,2,2,2,0,2])
                par = e.getParameterByLength(fp.StartDistance)
                fp.Center = e.valueAt(par)
            elif fp.Method == "Distance-From-End":
                self.setEditormode(fp, [2,2,2,2,2,0])
                par = e.getParameterByLength(e.Length - fp.EndDistance)
                fp.Center = e.valueAt(par)
        if prop in ['X','Y','Z']:
            p = FreeCAD.Vector(fp.X, fp.Y, fp.Z)
            v = Part.Vertex(p)
            center = v.distToShape(e)[1][0][1]
            fp.Center = center
        if prop == "Parameter":
            if fp.Parameter < e.FirstParameter:
                fp.Parameter = e.FirstParameter
            elif fp.Parameter > e.LastParameter:
                fp.Parameter = e.LastParameter
            debug("Hook : Parameter changed to %f"%(fp.Parameter))
            fp.Center = e.valueAt(fp.Parameter)
        if prop == "StartDistance":
            if fp.StartDistance < 0.0:
                fp.StartDistance = 0.0
            elif fp.StartDistance > e.Length:
                fp.StartDistance = e.Length
            par = e.getParameterByLength(fp.StartDistance)
            fp.Center = e.valueAt(par)
            debug("Hook : StartDistance changed to %f"%(fp.StartDistance))
        if prop == "EndDistance":
            if fp.EndDistance < 0:
                fp.EndDistance = 0
            elif fp.EndDistance > e.Length:
                fp.EndDistance = e.Length
            par = e.getParameterByLength(e.Length - fp.EndDistance)
            fp.Center = e.valueAt(par)
            debug("Hook : EndDistance changed to %f"%(fp.EndDistance))


class ViewProviderHook:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/discretize.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        
        #self.selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        #self.selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        #self.selectionNode.objectName.setValue(vobj.Object.Name) # here obj is the ViewObject, we need its associated App Object
        #self.selectionNode.subElementName.setValue("Vertex")
        
        
        #self.node = coin.SoSeparator()
        #self.node.setName("Hook")
        #self.coord = coin.SoCoordinate3()
        #self.marker = coin.SoSphere() #coin.SoMarkerSet() #((1,0,0),coin.SoMarkerSet.DIAMOND_FILLED_9_9)
        ##self.marker.markerIndex = coin.SoMarkerSet.DIAMOND_FILLED_9_9
        #self.color = coin.SoBaseColor()
        #self.color.rgb = (1,0,0)
        
        
        ##self.node.addChild(self.color)
        ##self.node.addChild(self.coord)
        ##self.node.addChild(self.marker)
        #self.selectionNode.addChild(self.color)
        #self.selectionNode.addChild(self.coord)
        #self.selectionNode.addChild(self.marker)
        
        #vobj.addDisplayMode(self.selectionNode,"Wireframe")

    #def updateData(self, fp, prop):
        #if prop == "Center":
            #vec = coin.SbVec3f(fp.Center.x, fp.Center.y, fp.Center.z)
            #self.coord.point.setValue(vec)
            ##self.coord.point.setValues(0,len([vec]),[vec])

    #def getDisplayModes(self,obj):
         #"Return a list of display modes."
         #modes=[]
         #modes.append("Wireframe")
         #return modes

    #def getDefaultDisplayMode(self):
         #'''Return the name of the default display mode. It must be defined in getDisplayModes.'''
         #return "Wireframe"

    #def setDisplayMode(self,mode):
         #return mode
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    #def claimChildren(self):
        #return None #[self.Object.Edge[0]]
        
    #def onDelete(self, feature, subelements): # subelements is a tuple of strings
        #try:
            #self.Object.Edge[0].ViewObject.Visibility=True
            ##self.Object.Tool.ViewObject.show()
        #except Exception as err:
            #FreeCAD.Console.PrintError("Error in onDelete: {0} \n".format(err))
        #return True


class hookCmd:
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
            obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython",u"Hook") #add object to document
            hook(obj,e)
            ViewProviderHook(obj.ViewObject)
            obj.ViewObject.PointSize = 5
            obj.Method = "Parameter"
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/discretize.svg', 'MenuText': 'Hook', 'ToolTip': 'Creates a hook on edge'}

FreeCADGui.addCommand('hook', hookCmd())




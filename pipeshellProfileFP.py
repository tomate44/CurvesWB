import os
import FreeCAD
import FreeCADGui
import Part
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 0

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

class profile:
    "Profile object for PipeShell"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSubList",  "Profile",    "Profile", "SubShapes of the profile")
        obj.addProperty("App::PropertyLinkSub",      "Location",   "Profile", "Vertex location on spine")
        obj.addProperty("App::PropertyBool",         "Contact",    "Profile", "Translate profile to contact spine").Contact = False
        obj.addProperty("App::PropertyBool",         "Correction", "Profile", "Rotate profile to be orthogonal to spine").Correction = False
        obj.Proxy = self

    def getEdgeList(self, obj, prop):
        res = []
        if hasattr(obj, prop):
            content = obj.getPropertyByName(prop)
            for l in content:
                o = l[0]
                for ss in l[1]:
                    n = eval(ss.lstrip('Edge'))
                    res.append(o.Shape.Edges[n-1])
        else:
            FreeCAD.Console.PrintError("\n%s object has no property %s\n"%(obj.Label, prop))
        return(res)

    def getVertex(self, obj, prop):
        res = []
        content = False
        if hasattr(obj, prop):
            content = obj.getPropertyByName(prop)
            if not content:
                return(res)
            o = content[0]
            for ss in content[1]:
                n = eval(ss.lstrip('Vertex'))
                res.append(o.Shape.Vertexes[n-1])
        else:
            FreeCAD.Console.PrintError("\n%s object has no property %s\n"%(obj.Label, prop))
        return(res)


    def onChanged(self, fp, prop):
        debug("%s changed"%prop)

    def execute(self, obj):
        #curvesWB = FreeCADGui.activeWorkbench()
        edges = self.getEdgeList( obj, "Profile")
        vert = self.getVertex( obj, "Location")
        if edges:
            w = Part.Wire(Part.__sortEdges__(edges))
            obj.Shape = Part.Compound([w]+vert)
        else:
            FreeCAD.Console.PrintError("\nFailed to build wire\n")

class profileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/profile.svg')

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
        #return None #[self.Object.Edge[0]]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        return True


class profileCommand:
    "creates a profile feature python object"
    def makeProfileFeature(self,edges,verts):
        if edges is not []:
            proffp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Profile")
            profile(proffp)
            proffp.Profile = edges
            if verts:
                proffp.Location = verts
            profileVP(proffp.ViewObject)
            proffp.ViewObject.LineWidth = 2.0
            proffp.ViewObject.LineColor = (0.1,0.1,0.8)
            FreeCAD.ActiveDocument.recompute()
        

    def Activated(self):
        edges = []
        verts = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select at least 1 edge !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        edges.append((selobj.Object, selobj.SubElementNames[i]))
                        selobj.Object.ViewObject.Visibility=False
                    elif isinstance(selobj.SubObjects[i], Part.Vertex):
                        verts=(selobj.Object, selobj.SubElementNames[i])
                        #selobj.Object.ViewObject.Visibility=False
            else:
                for i in range(len(selobj.Object.Shape.Edges)):
                    edges.append((selobj.Object, "Edge"+str(i+1)))
                selobj.Object.ViewObject.Visibility=False
        if edges:
            self.makeProfileFeature(edges,verts)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            #return f.match()
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/profile.svg', 'MenuText': 'Profile object', 'ToolTip': 'Creates a Profile object for PipeShell'}

FreeCADGui.addCommand('profile', profileCommand())

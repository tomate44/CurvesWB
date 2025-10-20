# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Pipeshell profile'
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = 'Creates a Profile object for PipeShell'

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join( ICONPATH, 'profile.svg')
DEBUG = False

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

class profile:
    "Profile object for PipeShell"
    def __init__(self, obj, source):
        ''' Add the properties '''
        if isinstance(source,(list,tuple)):
            obj.addProperty("App::PropertyLinkSubList",  "Profile",    "Profile", "SubShapes of the profile")
        else:
            obj.addProperty("App::PropertyLink",  "Profile",    "Profile", "source object of the profile")
        obj.Profile = source
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
        proptype = obj.getTypeIdOfProperty("Profile")
        if proptype == 'App::PropertyLink':
            sh = obj.Profile.Shape.copy()
            mat = obj.Profile.Shape.Placement.toMatrix()
            obj.Shape = sh.transformGeometry(mat)
        elif proptype == 'App::PropertyLinkSubList':
            edges = self.getEdgeList( obj, "Profile")
            #vert = self.getVertex( obj, "Location")
            if edges:
                w = Part.Wire(Part.__sortEdges__(edges))
                if w:
                    obj.Shape = w
                else:
                    FreeCAD.Console.PrintError("\nFailed to build wire\n")
            else:
                FreeCAD.Console.PrintError("\nFailed to extract edges\n")

class profileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return None

        def loads(self, state):
            return None

    else:
        def __getstate__(self):
            return None

        def __setstate__(self, state):
            return None

    #def claimChildren(self):
        #return None #[self.Object.Edge[0]]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        return True


class profileCommand:
    "creates a profile feature python object"
    def makeProfileFeature(self,source,verts):
        if source:
            proffp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Profile")
            profile(proffp,source)
            #proffp.Profile = edges
            if verts:
                proffp.Location = verts
            profileVP(proffp.ViewObject)
            proffp.ViewObject.LineWidth = 2.0
            proffp.ViewObject.LineColor = (0.1,0.1,0.8)
            FreeCAD.ActiveDocument.recompute()
        

    def Activated(self):
        edges = []
        verts = []
        source = None
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
                source = selobj.Object
                selobj.Object.ViewObject.Visibility=False
        if source:
            self.makeProfileFeature(source, verts)
        elif edges:
            self.makeProfileFeature(edges, verts)
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            #return f.match()
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}

FreeCADGui.addCommand('profile', profileCommand())

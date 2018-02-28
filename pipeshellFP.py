import os
import FreeCAD
import FreeCADGui
import Part
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

class pipeShell:
    "PipeShell featurePython object"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLink",       "Spine",       "PipeShell", "Sweep path")
        obj.addProperty("App::PropertyLinkList",   "Profiles",    "PipeShell", "Profiles that are swept along spine")
        obj.addProperty("App::PropertyEnumeration","Mode",        "PipeShell", "PipeShell mode").Mode = ["Frenet","DiscreteTrihedron","FixedTrihedron","Binormal","ShapeSupport","AuxiliarySpine"]
        obj.addProperty("App::PropertyBool",       "Preview",     "PipeShell", "Preview mode").Preview = True
        obj.addProperty("App::PropertyBool",       "Solid",       "Settings",  "Make solid object").Solid = False
        obj.addProperty("App::PropertyInteger",    "MaxDegree",   "Settings",  "Maximum degree of the generated surface").MaxDegree = 5
        obj.addProperty("App::PropertyInteger",    "MaxSegments", "Settings",  "Maximum number of segments of the generated surface").MaxSegments = 32
        obj.addProperty("App::PropertyInteger",    "Samples",     "Settings",  "Number of samples for preview").Samples = 20
        obj.Mode = "DiscreteTrihedron"
        obj.Proxy = self

    def getWires(self, obj, prop):
        res = []
        if hasattr(obj, prop):
            content = obj.getPropertyByName(prop)
            if isinstance(content,(list,tuple)):
                for l in content:
                    res.append(l.Shape.Wires[0])
                return(res)
            else:
                if content.Shape.Wires:
                    return(content.Shape.Wires[0])
                elif content.Shape.Edges:
                    return(Part.Wire([content.Shape.Edges[0]]))
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

    def add(self, ps, p):
        contact = False
        correction = False
        if hasattr(p, "Contact"):
            contact = p.Contact
        if hasattr(p, "Correction"):
            correction = p.Correction
        loc = self.getVertex(p,"Location")
        if p.Shape.Wires:
            shape = p.Shape.Wires[0]
        debug("Adding Profile %s"%p.Label)
        if not loc == []:
            ps.add(shape, loc, contact, correction)
        else:
            ps.add(shape, contact, correction)

    def execute(self, obj):
        #curvesWB = FreeCADGui.activeWorkbench()
        path = None
        profs = []
        if hasattr(obj, "Spine"):
            path =  self.getWires( obj, "Spine")
        if hasattr(obj, "Profiles"):
            profs = obj.Profiles
        if not (path and profs):
            return(None)
        debug("Creating PipeShell")
        ps = Part.BRepOffsetAPI.MakePipeShell(path)
        for p in profs:
            self.add(ps,p)
        
        if ps.isReady():
            if not obj.Preview:
                ps.build()
                obj.Shape = ps.shape()
            else:
                nb = 20
                if hasattr(obj, "Samples"):
                    nb = obj.Samples
                c = Part.Compound(ps.simulate(nb))
                obj.Shape = c
        else:
            FreeCAD.Console.PrintError("\nFailed to create shape\n")

class pipeShellVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/pipeshell.svg')

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


class pipeShellCommand:
    "creates a PipeShell feature python object"
    def makePipeShellFeature(self,path,profs):
        if path and profs:
            psfp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PipeShell")
            pipeShell(psfp)
            psfp.Spine = path
            psfp.Profiles = profs
            pipeShellVP(psfp.ViewObject)
            #psfp.ViewObject.LineWidth = 2.0
            #psfp.ViewObject.LineColor = (0.5,0.8,0.3)
            FreeCAD.ActiveDocument.recompute()
        

    def Activated(self):
        path = None
        profs = []
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select at least 1 path object and 1 profile object !\n")
        for selobj in sel:
            if hasattr(selobj,'Proxy'):
                if selobj.Proxy.__module__ == 'pipeshellProfileFP':
                    profs.append(selobj)
                elif selobj.Shape.Wires or selobj.Shape.Edges:
                    path = selobj
            elif selobj.Shape.Wires or selobj.Shape.Edges:
                path = selobj
        if path and profs:
            self.makePipeShellFeature(path,profs)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/pipeshell.svg', 'MenuText': 'PipeShell object', 'ToolTip': 'Creates a PipeShell object'}

FreeCADGui.addCommand('pipeshell', pipeShellCommand())

 
 
from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin
try:
    import BOPTools.SplitAPI
except ImportError:
    FreeCAD.Console.PrintError("Failed importing BOPTools. Fallback to Part API\n")

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class trimFace:
    def __init__(self, obj):
        ''' Add the properties '''
        debug("\ntrimFace init")
        obj.addProperty("App::PropertyLinkSub",    "Face",          "TrimFace",   "Input face")
        obj.addProperty("App::PropertyVector",     "PickedPoint",   "TrimFace",   "Picked point in parametric space of the face (u,v,0)")
        obj.addProperty("App::PropertyLinkSubList","Tool",          "TrimFace",   "Trimming curve")
        obj.addProperty("App::PropertyLink",       "DirVector",     "TrimFace",   "Trimming Vector")
        obj.addProperty("App::PropertyVector",     "Direction",     "TrimFace",   "Trimming direction")
        obj.Proxy = self

    def getFace( self, link):
        o = link[0]
        shapelist = link[1]
        for s in shapelist:
            if 'Face' in s:
                n = eval(s.lstrip('Face'))
                debug("Face %d"%n)
                return(o.Shape.Faces[n-1])
        return(None)

    def getEdges( self, link):
        res = []
        for l in link:
            o = l[0]
            shapelist = l[1]
            for s in shapelist:
                if 'Edge' in s:
                    n = eval(s.lstrip('Edge'))
                    debug("Edge %d"%n)
                    res.append(o.Shape.Edges[n-1])
        return(res)

    def getVector( self, obj):
        if hasattr(obj,"DirVector"):
            if obj.DirVector:
                v = FreeCAD.Vector(obj.DirVector.Direction)
                debug("choosing DirVector : %s"%str(v))
                if v.Length > 1e-6:
                    return(v)
        if hasattr(obj,"Direction"):
            if obj.Direction:
                v = FreeCAD.Vector(obj.Direction)
                debug("choosing Direction : %s"%str(v))
                if v.Length > 1e-6:
                    return(v)
        debug("choosing (0,0,-1)")
        return(FreeCAD.Vector(0,0,-1))

    def execute(self, obj):
        debug("* trimFace execute *")
        if not obj.Tool:
            debug("No tool")
            return
        if not obj.PickedPoint:
            debug("No PickedPoint")
            return
        if not obj.Face:
            debug("No Face")
            return
        if not (obj.DirVector or obj.Direction):
            debug("No Direction")
            return
        scale = 10000
        
        v = self.getVector(obj)
        v.normalize().multiply(scale)
        debug("Vector : %s"%str(v))
        try:
            edges = [Part.Wire(self.getEdges(obj.Tool))]
            debug("Wire upgrade success")
        except:
            edges = self.getEdges(obj.Tool)
        cuttool = []
        for edge in edges:
            edge.translate(v)
            cuttool.append(edge.extrude(v.multiply(-2)))
        #Part.show(cuttool)
        face = self.getFace(obj.Face)
        #return
        try:
            bf = BOPTools.SplitAPI.slice(face, cuttool, "Split", 1e-6)
        except:
            bf = Part.BOPTools.SplitAPI.slice(face, cuttool, "Split", 1e-6)
        debug("shape has %d faces"%len(bf.Faces))
        
        u = obj.PickedPoint.x
        v = obj.PickedPoint.y
        for f in bf.Faces:
            if f.isPartOfDomain(u,v):
                obj.Shape = f
                return
        
        #vert = Part.Vertex(obj.PickedPoint)
        #min = 1e6
        #index = 0
        #for i in range(len(bf.Faces)):
            #dts = vert.distToShape(bf.Faces[i])[0]
            #if dts < min:
                #min = dts
                #index = i
        #if bf.Faces:
            #obj.Shape = bf.Faces[index]

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

class trimFaceVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/trimFace.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def updateData(self, fp, prop):
        if (prop == "Origin") or (prop == "Direction"):
            # update coordinates
            pass

    def doubleClicked(self,vobj):
        if hasattr(self.Object,"Direction"):
            d = self.Object.Direction
            FreeCADGui.ActiveDocument.ActiveView.setViewDirection((d.x,d.y,d.z))
            return True
  
    def claimChildren(self):
        l=[]
        if hasattr(self.Object,"DirVector"):
            if self.Object.DirVector:
                l.append(self.Object.DirVector)
        if hasattr(self.Object,"Face"):
            if self.Object.Face:
                l.append(self.Object.Face[0])
        if hasattr(self.Object,"Tool"):
            if self.Object.Tool:
                l.append(self.Object.Tool[0])
        #for o in l:
            #o.ViewObject.Visibility=False
        return(l)
  
    #def setEdit(self,vobj,mode):
        #return False
    
    #def unsetEdit(self,vobj,mode):
        #return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

class trim:
    def findVector(self, selectionObject):
        res = selectionObject[:]
        i = 0
        for obj in selectionObject:
            if hasattr(obj.Object,"Direction") and hasattr(obj.Object,"Origin"):
                v = obj.Object
                res.pop(i)
                return (v,res)
            i += 1
        return(None,selectionObject)

    def findCurve(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj),Part.Edge):
                        #res.pop(i)
                        res.append((obj.Object,obj.SubElementNames[i]))
                    i += 1
        return(res,selectionObject)

    def findFaces(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj),Part.Face):
                        f = (obj.Object ,[obj.SubElementNames[i]])
                        p = obj.PickedPoints[i]
                        u,v = subobj.Surface.parameter(p)
                        res.append((f,FreeCAD.Vector(u,v,0)))
                    i += 1
        return(res)

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        vector, selObj1 = self.findVector(s)
        trimmingCurve, selObj2 = self.findCurve(selObj1[::-1])
        faces = self.findFaces(selObj2)
        
        if trimmingCurve and faces:
            for f in faces:
                obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","TrimmedFace") #add object to document
                trimFace(obj)
                trimFaceVP(obj.ViewObject)
                obj.Face = f[0]
                obj.Face[0].ViewObject.Visibility=False
                obj.PickedPoint = f[1]
                obj.Tool = trimmingCurve
                #obj.Tool[0].ViewObject.Visibility=False
                if vector:
                    obj.DirVector = vector
                    obj.DirVector.ViewObject.Visibility=False
                else:
                    obj.Direction = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/trimFace.svg', 'MenuText': 'Trim face', 'ToolTip': 'Trim a face with a projected curve'}

FreeCADGui.addCommand('Trim', trim())




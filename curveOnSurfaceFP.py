import os
import FreeCAD
import FreeCADGui
import Part
import dummy
import curveOnSurface
import CoinNodes
from pivy import coin
from FreeCAD import Base

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class cosFP:
    "joins the selected edges into a single BSpline Curve"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub",    "InputEdge",      "CurveOnSurface",   "Input edge")
        obj.addProperty("App::PropertyLinkSub",    "Face",           "CurveOnSurface",   "Support face")
        #obj.addProperty("App::PropertyFloat",      "Tolerance",      "CurveOnSurface",   "Tolerance").Tolerance=0.001
        obj.addProperty("App::PropertyBool",       "ReverseTangent", "CurveOnSurface",   "Reverse tangent").ReverseTangent = False
        obj.addProperty("App::PropertyBool",       "ReverseNormal",  "CurveOnSurface",   "Reverse normal").ReverseNormal = False
        obj.addProperty("App::PropertyBool",       "ReverseBinormal","CurveOnSurface",   "Reverse binormal").ReverseBinormal = False
        obj.addProperty("Part::PropertyPartShape", "Shape",          "Base",   "Shape")
        obj.Proxy = self

    def getEdge(self, obj):
        res = None
        if hasattr(obj, "InputEdge"):
            o = obj.InputEdge[0]
            ss = obj.InputEdge[1][0]
            n = eval(ss.lstrip('Edge'))
            res = o.Shape.Edges[n-1]
        return(res)

    def getFace(self, obj):
        res = None
        if hasattr(obj, "Face"):
            o = obj.Face[0]
            ss = obj.Face[1][0]
            n = eval(ss.lstrip('Face'))
            res = o.Shape.Faces[n-1]
        return(res)

    def execute(self, obj):
        edge = self.getEdge(obj)
        face = self.getFace(obj)
        cos = curveOnSurface.curveOnSurface(edge, face)
        cos.reverseTangent = obj.ReverseTangent
        cos.reverseNormal = obj.ReverseNormal
        cos.reverseBinormal = obj.ReverseBinormal
        #e2d = cos.curve2D
        obj.Shape = cos.edgeOnFace

class cosVP:
    def __init__(self,vobj):
        vobj.addProperty("App::PropertyInteger", "Samples", "CurveOnSurface", "Samples").Samples=64
        vobj.addProperty("App::PropertyFloat",   "Scale",   "CurveOnSurface", "Scale").Scale=1.0
        vobj.Proxy = self

    def getEdge(self, obj):
        res = None
        try:
            o = obj.InputEdge[0]
            ss = obj.InputEdge[1][0]
            n = eval(ss.lstrip('Edge'))
            res = o.Shape.Edges[n-1]
        except:
            pass
        return(res)

    def getFace(self, obj):
        res = None
        try:
            o = obj.Face[0]
            ss = obj.Face[1][0]
            n = eval(ss.lstrip('Face'))
            res = o.Shape.Faces[n-1]
        except:
            pass
        return(res)

    def getIcon(self):
        return (path_curvesWB_icons+'/curveOnSurface.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        #self.wireframeDM = coin.SoGroup()
        self.normalDM = coin.SoGroup()
        self.binormalDM = coin.SoGroup()
        self.bothDM = coin.SoGroup()
        
        self.normCoords = CoinNodes.coordinate3Node()
        self.binormCoords = CoinNodes.coordinate3Node()
        self.curveCoords = CoinNodes.coordinate3Node()
        
        self.normComb = CoinNodes.combComb(color = (0.,0.3,0.), lineWidth = 1.0)
        self.normCurve = CoinNodes.combCurve(color = (0.,0.7,0.), lineWidth = 1.0)
        
        self.binormComb = CoinNodes.combComb(color = (0.,0.,0.3), lineWidth = 1.0)
        self.binormCurve = CoinNodes.combCurve(color = (0.,0.,0.7), lineWidth = 1.0)
        
        self.curve = CoinNodes.polygonNode(color = (0.,0.,0.), lineWidth = 1.0)
        
        self.normComb.linkTo(self.normCoords)
        self.normCurve.linkTo(self.normCoords)
        
        self.binormComb.linkTo(self.binormCoords)
        self.binormCurve.linkTo(self.binormCoords)
        
        #self.wireframeDM.addChild(self.curveCoords)
        #self.wireframeDM.addChild(self.curve)
        self.normalDM.addChild(self.curveCoords)
        self.normalDM.addChild(self.curve)
        self.binormalDM.addChild(self.curveCoords)
        self.binormalDM.addChild(self.curve)
        
        self.normalDM.addChild(self.normCoords)
        self.normalDM.addChild(self.normComb)
        self.normalDM.addChild(self.normCurve)
        
        self.binormalDM.addChild(self.binormCoords)
        self.binormalDM.addChild(self.binormComb)
        self.binormalDM.addChild(self.binormCurve)
        
        self.bothDM.addChild(self.normalDM)
        self.bothDM.addChild(self.binormalDM)
        
        #vobj.addDisplayMode(self.wireframeDM,"Wireframe")
        vobj.addDisplayMode(self.normalDM,   "Normal")
        vobj.addDisplayMode(self.binormalDM, "Binormal")
        vobj.addDisplayMode(self.bothDM,     "Normal Binormal")

    def updateData(self, fp, prop):
        edge = self.getEdge(self.Object)
        face = self.getFace(self.Object)
        #if edge == None or face == None:
            #return
        cos = curveOnSurface.curveOnSurface(edge, face)
        if True: #cos.isValid:
            cos.reverseTangent = fp.ReverseTangent
            cos.reverseNormal = fp.ReverseNormal
            cos.reverseBinormal = fp.ReverseBinormal
            ParamRange = cos.lastParameter - cos.firstParameter
            val = []
            nor = []
            bino = []
            for i in range(self.ViewObject.Samples):
                t = cos.firstParameter + (1.0 * i * ParamRange / (self.ViewObject.Samples - 1))
                v = cos.valueAt(t)
                val.append(v)
                nor.append(v)
                nor.append(v.add(cos.normalAt(t).multiply(self.ViewObject.Scale)))
                bino.append(v)
                bino.append(v.add(cos.binormalAt(t).multiply(self.ViewObject.Scale)))
            self.curveCoords.points = val
            self.curve.vertices = val
            self.normCoords.points = nor
            self.binormCoords.points = bino

  
    def getDisplayModes(self,obj):
         "Return a list of display modes."
         modes=[]
         #modes.append("Wireframe")
         modes.append("Normal")
         modes.append("Binormal")
         modes.append("Normal Binormal")
         return modes

    def getDefaultDisplayMode(self):
         "Return the name of the default display mode. It must be defined in getDisplayModes."
         return "Normal Binormal"

    def setDisplayMode(self,mode):
         return mode

    def onChanged(self, vp, prop):
        "Here we can do something when a single property got changed"
        if prop == "Samples":
            debug("vp detected a Samples change")
            if vp.Samples < 2:
                vp.Samples = 2
            elif vp.Samples > 1000:
                vp.Samples = 1000
        if prop == "Scale":
            debug("vp detected a Scale change")
            if vp.Scale <= 0.0:
                vp.Scale = 0.0001
            elif vp.Scale > 1000:
                vp.Scale = 1000
        self.updateData(vp.Object,"Scale")

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    #def claimChildren(self):
        #return([self.Object.InputEdge[0], self.Object.Face[0]])
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        #try:
            #self.Object.Base.ViewObject.show()
            #self.Object.Tool.ViewObject.show()
        #except Exception as err:
            #App.Console.PrintError("Error in onDelete: " + err.message)
        return True


class cosCommand:
    "joins the selected edges into a single BSpline Curve"
    def Activated(self):
        edge = None
        face = None
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select an edge and its supporting face \n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        edge = (selobj.Object, selobj.SubElementNames[i])
                    elif isinstance(selobj.SubObjects[i], Part.Face):
                        face = (selobj.Object, selobj.SubElementNames[i])
        print(edge)
        print(face)
        if edge and face:
            cos = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CurveOnSurface")
            cosFP(cos)
            cosVP(cos.ViewObject)
            cos.InputEdge = edge
            cos.Face = face
            cos.Placement = edge[0].Placement
            FreeCAD.ActiveDocument.recompute()
            
            #cos.ViewObject.DrawStyle = "Dashed"
            #cos.ViewObject.LineColor = (1.0,0.67,0.0)
            #cos.ViewObject.LineWidth = 3.0
        else:
            FreeCAD.Console.PrintError("Select an edge and its supporting face \n")


    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/curveOnSurface.svg', 'MenuText': 'CurveOnSurface', 'ToolTip': 'Create a curve on surface object'}

FreeCADGui.addCommand('cos', cosCommand())

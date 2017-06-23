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


class cosFP:
    "joins the selected edges into a single BSpline Curve"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub",  "Edge",           "CurveOnSurface",   "Edge")
        obj.addProperty("App::PropertyLinkSub",  "Face",           "CurveOnSurface",   "Support face")
        #obj.addProperty("App::PropertyFloat",    "Tolerance",      "CurveOnSurface",   "Tolerance").Tolerance=0.001
        obj.addProperty("App::PropertyBool",     "ReverseTangent", "CurveOnSurface",   "Reverse tangent").ReverseTangent = False
        obj.addProperty("App::PropertyBool",     "ReverseNormal",  "CurveOnSurface",   "Reverse normal").ReverseNormal = False
        obj.addProperty("App::PropertyBool",     "ReverseBinormal","CurveOnSurface",   "Reverse binormal").ReverseBinormal = False
        obj.Proxy = self

    def getEdge(self, obj):
        res = None
        if hasattr(obj, "Edge"):
            o = obj.Edge[0]
            ss = obj.Edge[1][0]
            n = eval(ss.lstrip('Edge'))
            res = o.Shape.Edges[n-1]
        return(res)

    def execute(self, obj):
        edge = self.getEdge(obj)
        obj.Shape = edge

class cosVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/curveOnSurface.svg')

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
            cos.Edge = edge
            cos.Face = face
            FreeCAD.ActiveDocument.recompute()
            cos.ViewObject.DrawStyle = "Dashed"
            cos.ViewObject.LineColor = (1.0,0.67,0.0)
            cos.ViewObject.LineWidth = 3.0
        else:
            FreeCAD.Console.PrintError("Select an edge and its supporting face \n")


    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/curveOnSurface.svg', 'MenuText': 'CurveOnSurface', 'ToolTip': 'Create a curve on surface object'}

FreeCADGui.addCommand('cos', cosCommand())

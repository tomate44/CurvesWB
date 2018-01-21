import os
import FreeCAD
import FreeCADGui
import Part
import dummy
import curveExtend

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

class extend:
    "extends the selected edge"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub",      "Edge",       "Extend", "Input edge to extend")
        obj.addProperty("App::PropertyFloat",        "Length",     "Extend", "Extension Length").Length=1.0
        obj.addProperty("App::PropertyEnumeration",  "Location",   "Extend", "Edge extremity to extend").Location = ["Start","End","Both"]
        obj.addProperty("App::PropertyEnumeration",  "Type",       "Extend", "Extension type").Type = ["Straight","G2 curve"]
        obj.addProperty("App::PropertyEnumeration",  "Output",     "Extend", "Output shape").Output = ["SingleEdge","Wire"]
        obj.Location = "Start"
        obj.Type = "Straight"
        obj.Output = "SingleEdge"
        obj.Proxy = self

    def getEdges(self, obj):
        res = []
        if hasattr(obj, "Edge"):
            o = obj.Edge[0]
            ss = obj.Edge[1][0]
            n = eval(ss.lstrip('Edge'))
            res.append(o.Shape.Edges[n-1])
        return(res)

    def onChanged(self, fp, prop):
        if prop == "Length":
            if fp.Length < 0:
                fp.Length = 0

    def execute(self, obj):
        edge = self.getEdges(obj)[0]
        if hasattr(obj, "Length"):
            if obj.Length <= 0:
                obj.Shape = edge
                return()
        curve = curveExtend.getTrimmedCurve(edge)
        cont = 1
        if hasattr(obj, "Type"):
            if obj.Type == "G2 curve":
                cont = 2
        ext = []
        if hasattr(obj, "Location"):
            if obj.Location in ["Start","Both"]:
                ext.append(curveExtend.extendCurve( curve, 0, obj.Length, cont))
            if obj.Location in ["End","Both"]:
                ext.append(curveExtend.extendCurve( curve, 1, obj.Length, cont))
        if not ext == []:
            if hasattr(obj, "Output"):
                if obj.Output == "SingleEdge":
                    for c in ext:
                        curve.join(c.toBSpline())
                    obj.Shape = curve.toShape()
                else:
                    ext.append(curve)
                    edges = []
                    for c in ext:
                        edges.append(Part.Edge(c))
                    w = Part.Wire(Part.__sortEdges__(edges))
                    w.fixWire()
                    obj.Shape = w


class extendVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/extendcurve.svg')

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

    def claimChildren(self):
        return [self.Object.Edge[0]]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        return True


class extendCommand:
    "extendss the selected edges"
    def makeExtendFeature(self,source):
        if source is not []:
            for o in source:
                extCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","ExtendedCurve")
                extend(extCurve)
                extCurve.Edge = o
                extendVP(extCurve.ViewObject)
                extCurve.ViewObject.LineWidth = 2.0
                extCurve.ViewObject.LineColor = (0.5,0.0,0.3)
            FreeCAD.ActiveDocument.recompute()
        

    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select the edges to extend first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        edges.append((selobj.Object, selobj.SubElementNames[i]))
                        selobj.Object.ViewObject.Visibility=False
            #else:
                #self.makeJoinFeature(selobj.Object)
                #selobj.Object.ViewObject.Visibility=False
        if edges:
            self.makeExtendFeature(edges)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            #return f.match()
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/extendcurve.svg', 'MenuText': 'Extend Curve', 'ToolTip': 'Extends the selected edge'}

FreeCADGui.addCommand('extend', extendCommand())

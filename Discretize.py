from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')


def getEdgeParamList(edge, start = None, end = None, num = 64):
    res = []
    if num <= 1:
        num = 2
    if not start:
        start = edge.FirstParameter
    if not end:
        end = edge.LastParameter
    step = (end - start) / (num-1)
    for i in range(num):
        res.append(start + i * step)
    return res


def getEdgePointList(edge, paramList):
    res = []
    for p in paramList:
        res.append(edge.valueAt(p))
    return res


def getEdgeCurvatureList(edge, paramList):
    res = []
    for p in paramList:
        res.append(edge.curvatureAt(p))
    return res


def getEdgeNormalList(edge, paramList):
    res = []
    for p in paramList:
        try:
            res.append(edge.normalAt(p))
        except:
            FreeCAD.Console.PrintMessage("Normal error\n")
            res.append(FreeCAD.Vector(1e-3,1e-3,1e-3))
    return res



def getEdgePointCurvNormList(edge, paramList):
    ''' No perf gain '''
    pts = []
    cur = []
    nor = []
    for p in paramList:
        pts.append(edge.valueAt(p))
        cur.append(edge.curvatureAt(p))
        nor.append(edge.normalAt(p))
    return [pts,cur,nor]


def getEdgeData(edge, paramList):
    pts = getEdgePointList(edge, paramList)
    cur = getEdgeCurvatureList(edge, paramList)
    nor = getEdgeNormalList(edge, paramList)
    return [pts,cur,nor]

def getCombPoints(data, scale):
    pts = []
    for i in range(len(data[0])):
        v = FreeCAD.Vector(data[2][i]).multiply(data[1][i]*scale)
        pts.append(data[0][i].add(v))
    return pts

def getSoPoints(data , scale):
    pts = []
    for i in range(len(data[0])):
        v = FreeCAD.Vector(data[2][i]).multiply(data[1][i]*scale)
        w = data[0][i].add(v.negative())
        pts.append((data[0][i].x,data[0][i].y,data[0][i].z))
        pts.append((w.x,w.y,w.z))
    return pts

def getCombCoords(fp):
    coords = []
    n = 0.5 * len(fp.CombPoints) / fp.Samples
    for r in range(int(n)):
        for i in range(fp.Samples):
            c = 2*r*fp.Samples + i*2
            coords += [c, c+1, -1]
    return coords

def getCurveCoords(fp):
    coords = []
    n = 0.5 * len(fp.CombPoints) / fp.Samples
    for r in range(int(n)):
        for i in range(fp.Samples):
            coords.append(2*r*fp.Samples + i*2 + 1)
        coords.append(-1)
    return coords


class Discretization:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nDiscretization class Init\n")
        obj.addProperty("App::PropertyLinkSub",      "Edge",      "Discretization",   "Edge").Edge = edge
        obj.addProperty("App::PropertyEnumeration",  "AMethod",    "Discretization",   "Discretization Method").AMethod=["Number","Distance","Deflection"]
        obj.addProperty("App::PropertyInteger",      "Number",    "Discretization",   "Number of edge points").Number = 10
        obj.addProperty("App::PropertyFloat",        "Distance",  "Discretization",   "Distance between edge points").Distance=1.0
        obj.addProperty("App::PropertyFloat",        "Deflection","Discretization",   "Distance for deflection AMethod").Deflection=1.0
        obj.addProperty("App::PropertyFloat",        "ParameterFirst",     "Discretization",   "Start parameter").ParameterFirst=0.0
        obj.addProperty("App::PropertyFloat",        "ParameterLast",      "Discretization",   "End parameter").ParameterLast=1.0
        obj.addProperty("App::PropertyVectorList",   "Points",    "Discretization",   "Points")
        obj.addProperty("Part::PropertyPartShape",   "Shape",     "Discretization",   "Shape")
        obj.Proxy = self
        #obj.Samples = (20,2,1000,10)
        obj.Points = []
        self.edge = None
        self.setEdge(obj)
        self.execute(obj)

        
    def selectedEdgesToProperty(self, obj, edge):
        objs = []
        for o in edge:
            if isinstance(o,tuple) or isinstance(o,list):
                if o[0].Name != obj.Name:
                    objs.append(tuple(o))
            else:
                for el in o.SubElementNames:
                    if "Edge" in el:
                        if o.Object.Name != obj.Name:
                            objs.append((o.Object,el))
        if objs:
            obj.Edge = objs
            FreeCAD.Console.PrintMessage(str(edge) + "\n")
            FreeCAD.Console.PrintMessage(str(obj.Edge) + "\n")


    def setEdge( self, obj):
        o = obj.Edge[0]
        e = obj.Edge[1][0]
        n = eval(e.lstrip('Edge'))
        self.edge = o.Shape.Edges[n-1]
        obj.ParameterFirst = self.edge.FirstParameter
        obj.ParameterLast = self.edge.LastParameter

    def buildPoints(self, obj):
        if   obj.AMethod == "Number":
            obj.Points = self.edge.discretize( Number = obj.Number,         First = obj.ParameterFirst, Last = obj.ParameterLast)
        elif obj.AMethod == "Distance":
            obj.Points = self.edge.discretize( Distance = obj.Distance,     First = obj.ParameterFirst, Last = obj.ParameterLast)
        elif obj.AMethod == "Deflection":
            obj.Points = self.edge.discretize( Deflection = obj.Deflection, First = obj.ParameterFirst, Last = obj.ParameterLast)
        #FreeCAD.Console.PrintMessage(str(len(obj.CombPoints))+" Comb points\n")   #+str(obj.CombPoints)+"\n\n")

    def execute(self, obj):
        FreeCAD.Console.PrintMessage("\n* Discretization : execute *\n")
        self.setEdge( obj)
        self.buildPoints( obj)
        obj.Shape = Part.Compound([Part.Vertex(i) for i in obj.Points])

    def onChanged(self, fp, prop):
        #print fp
        if not fp.Edge:
            return
        if prop == "Edge":
            FreeCAD.Console.PrintMessage("Discretization : Edge changed\n")
            self.setEdge( fp)
        if prop == "AMethod":
            FreeCAD.Console.PrintMessage("Discretization : AMethod changed\n")
        if prop == "Number":
            if fp.Number <= 1:
                fp.Number = 2
            FreeCAD.Console.PrintMessage("Discretization : Number changed to "+str(fp.Number)+"\n")
        if prop == "Distance":
            if fp.Distance <= 0.0:
                fp.Distance = 0.001
            FreeCAD.Console.PrintMessage("Discretization : Distance changed to "+str(fp.Distance)+"\n")
        if prop == "Deflection":
            if fp.Deflection <= 0.0:
                fp.Deflection = 0.001
            FreeCAD.Console.PrintMessage("Discretization : Deflection changed to "+str(fp.Deflection)+"\n")
        if prop == "ParameterFirst":
            if fp.ParameterFirst < self.edge.FirstParameter:
                fp.ParameterFirst = self.edge.FirstParameter
            FreeCAD.Console.PrintMessage("Discretization : ParameterFirst changed to "+str(fp.ParameterFirst)+"\n")
        if prop == "ParameterLast":
            if fp.ParameterLast > self.edge.LastParameter:
                fp.ParameterLast = self.edge.LastParameter
            FreeCAD.Console.PrintMessage("Discretization : ParameterLast changed to "+str(fp.ParameterLast)+"\n")
        #self.execute(fp) # Infinite loop
            
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None




class ViewProviderDiscretization:
    def __init__(self, obj):
        "Set this object to the proxy object of the actual view provider"
        obj.addProperty("App::PropertyColor","CurveColor","Comb","Color of the curvature curve").CurveColor=(0.8,0.0,0.0)
        obj.addProperty("App::PropertyColor","CombColor","Comb","Color of the curvature comb").CombColor=(0.0,0.8,0.0)
        # TODO : add transparency property
        obj.Proxy = self
            
    def createNodes(self, fp):
        self.nodes = []
        for e in self.edges:
            node = SoComb(e)
            if not (node in self.nodes):
                self.nodes.append(node)
                self.wireframe.addChild(node)

    def attach(self, obj):
        #FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.attach \n")

        self.wireframe = coin.SoGroup()

        self.combColor  =  coin.SoBaseColor()
        self.curveColor =  coin.SoBaseColor()
        self.combColor.rgb  = (obj.CombColor[0],obj.CombColor[1],obj.CombColor[2])
        self.curveColor.rgb = (obj.CurveColor[0],obj.CurveColor[1],obj.CurveColor[2])
        self.points = coin.SoCoordinate3()
        self.combLines = coin.SoIndexedLineSet()
        self.curveLines = coin.SoIndexedLineSet()
        self.wireframe.addChild(self.points)
        self.wireframe.addChild(self.combColor)
        self.wireframe.addChild(self.combLines)
        self.wireframe.addChild(self.curveColor)
        self.wireframe.addChild(self.curveLines)
        
        #self.selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        #self.selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        #self.selectionNode.objectName.setValue(obj.Object.Name) # here obj is the ViewObject, we need its associated App Object
        #self.selectionNode.subElementName.setValue("Comb")
        #self.selectionNode.addChild(self.curveLines)
            

        #self.wireframe.addChild(self.selectionNode)
        obj.addDisplayMode(self.wireframe,"Wireframe")
        #self.onChanged(obj,"Color")

    def updateData(self, fp, prop):
        self.combLines.coordIndex.setValue(0)
        self.curveLines.coordIndex.setValue(0)
        self.points.point.setValues(0,0,[])
        
        p = fp.CombPoints
        self.points.point.setValues(0,len(p),p)
        
        i1 = getCombCoords(fp)
        self.combLines.coordIndex.setValues(0,len(i1),i1)
        #FreeCAD.Console.PrintMessage("\n\n"+str(i1)+"\n")
        
        i2 = getCurveCoords(fp)
        self.curveLines.coordIndex.setValues(0,len(i2),i2)
        #FreeCAD.Console.PrintMessage("\n\n"+str(i2)+"\n")

    def getDisplayModes(self,obj):
         "Return a list of display modes."
         modes=[]
         modes.append("Wireframe")
         return modes

    def getDefaultDisplayMode(self):
         "Return the name of the default display mode. It must be defined in getDisplayModes."
         return "Wireframe"

    def setDisplayMode(self,mode):
         return mode

    def onChanged(self, vp, prop):
        "Here we can do something when a single property got changed"
        if prop == "Edge":
            FreeCAD.Console.PrintMessage("\n\n\nvp detected a Edge change\n\n\n")
        if prop == "CurveColor":
            self.curveColor.rgb = (vp.CurveColor[0],vp.CurveColor[1],vp.CurveColor[2])
        elif prop == "CombColor":
            self.combColor.rgb  = (vp.CombColor[0],vp.CombColor[1],vp.CombColor[2])
        return
        
    def getIcon(self):
        return (path_curvesWB_icons+'/comb.svg')

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

class discretize:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                subobj = obj.SubObjects[0]
                if issubclass(type(subobj),Part.Edge):
                    res=(obj.Object,[obj.SubElementNames[0]])
            else:
                res=(obj.Object,["Edge1"])
        return res

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = self.parseSel(s)
        #FreeCAD.Console.PrintMessage(str(edges) + "\n")
        #combSelected = self.findComb(s)
        #if not combSelected:
            #obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython","Comb") #add object to document
            #Comb(obj,edges)
            #ViewProviderComb(obj.ViewObject)
        #else:
            #self.appendEdges(combSelected, edges)
        obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","EdgePoints") #add object to document
        Discretization(obj,edges)
        obj.ViewObject.Proxy = 0
        obj.ViewObject.PointSize = 4.00000
        #ViewProviderDiscretization(obj.ViewObject)
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/discretize.svg', 'MenuText': 'Discretize', 'ToolTip': 'Discretizes edge or wire'}

FreeCADGui.addCommand('Discretize', discretize())




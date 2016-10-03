from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')


def getEdgeParamList(edge, start = None, end = None, num = 64):
    res = []
    if num <= 0:
        num = 1
    if not start:
        start = edge.FirstParameter
    if not end:
        end = edge.LastParameter
    step = (end - start) / num
    for i in range(num+1):
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
        res.append(edge.normalAt(p))
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
    pts = coin.SoCoordinate3()
    for i in range(len(data[0])):
        v = FreeCAD.Vector(data[2][i]).multiply(data[1][i]*scale)
        w = data[0][i].add(v)
        pts.append((data[0][i].x,data[0][i].y,data[0][i].z))
        pts.append((w.x,w.y,w.z))
    return pts

def getCombCoords(samples):
    coords = []
    for i in range(samples):
        coords += [i*2, 1+i*2, -1]
    return coords

def getCurveCoords(samples):
    coords = []
    for i in range(samples):
        coords.append(1+i*2)
    coords.append(-1)
    return coords


class Comb:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nComb class Init\n")
        obj.addProperty("App::PropertyLinkSubList","Edge","Comb","Edge")
        obj.addProperty("App::PropertyEnumeration","Type","Comb","Comb Type").Type=["Curvature","Unit Normal"]
        obj.addProperty("App::PropertyFloat","Scale","Comb","Scale (%)").Scale=100.0
        obj.addProperty("App::PropertyBool","ScaleAuto","Comb","Automatic Scale").ScaleAuto = True
        obj.addProperty("App::PropertyInteger","Samples","Comb","Number of samples").Samples=128
        obj.addProperty("App::PropertyFloat","TotalLength","Comb","Total length of edges")
        #obj.addProperty("App::PropertyVectorList","CombPoints","Comb","CombPoints")
        obj.addProperty("Part::PropertyPartShape","Shape","Comb", "Shape of comb plot")
        obj.Proxy = self
        
        #self.selectedEdgesToProperty( obj, edge)
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

    def computeTotalLength(self, obj):
        totalLength = 0
        for e in obj.Edge:
            o = e[0]
            #FreeCAD.Console.PrintMessage(str(o) + " - ")
            for f in e[1]:
                n = eval(f.lstrip('Edge'))
                #FreeCAD.Console.PrintMessage(str(n) + "\n")
                g = o.Shape.Edges[n-1]
                totalLength += g.Length
        obj.TotalLength = totalLength


    def execute(self, obj):
        self.selectedEdgesToProperty( obj, obj.Edge)
        self.computeTotalLength(obj)

    def onChanged(self, fp, prop):
        #print fp
        if not fp.Edge:
            return
        if prop == "Edge":
            FreeCAD.Console.PrintMessage("\nComb : Edge changed\n")
            print fp.Edge
            self.execute(fp)
        if prop == "Type" or prop == "Scale" or prop == "Samples":
            FreeCAD.Console.PrintMessage("\nComb : Propery changed\n")
            #self.execute(fp)

class SoComb(coin.SoSeparator):
    def __init__(self, edge):
        super(SoComb, self).__init__()
        self.edge = edge
        self.combColor  =  coin.SoBaseColor()
        self.curveColor =  coin.SoBaseColor()
        self.combColor.rgb  = (0,0.8,0)
        self.curveColor.rgb = (0.8,0,0)
        self.points = coin.SoCoordinate3()
        self.combLines = coin.SoIndexedLineSet()
        self.curveLines = coin.SoIndexedLineSet()
        self.addChild(self.points)
        self.addChild(self.combColor)
        self.addChild(self.combLines)
        self.addChild(self.curveColor)
        self.addChild(self.curveLines)

class ViewProviderComb:
    def __init__(self, obj):
        "Set this object to the proxy object of the actual view provider"
        obj.addProperty("App::PropertyColor","CurveColor","Comb","Color of the curvature curve").CurveColor=(0.8,0.0,0.0)
        obj.addProperty("App::PropertyColor","CombColor","Comb","Color of the curvature comb").CombColor=(0.0,0.8,0.0)
        # TODO : add transparency property
        obj.Proxy = self
        self.maxCurv = 0.001
        self.factor = 1.0
        #self.setEdgeList(obj)

    def setEdgeList( self, obj):
        edgeList = []
        for e in obj.Edge:
            o = e[0]
            FreeCAD.Console.PrintMessage(str(o) + " - ")
            for f in e[1]:
                n = eval(f.lstrip('Edge'))
                FreeCAD.Console.PrintMessage(str(n) + "\n")
                edgeList.append(o.Shape.Edges[n-1])
        self.edges = edgeList
        
    def getMaxCurv(self, samples):
        self.maxCurv = 0.001
        for e in self.edges:
            pl = getEdgeParamList(e, num = samples)
            cl = getEdgeCurvatureList(e, pl)
            m = max(cl)
            if self.maxCurv < m:
                self.maxCurv = m
                
    def getCurvFactor(self, obj):
        if obj.ScaleAuto:
            self.factor = 0.5 * obj.TotalLength / self.maxCurv
        else:
            self.factor = obj.Scale / 100
            
    def createNodes(self, fp):
        self.nodes = []
        for e in self.edges:
            node = SoComb(e)
            self.nodes.append(node)
            self.wireframe.addChild(node)

    def attach(self, obj):
        #FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.attach \n")

        self.wireframe = coin.SoGroup()

        #self.selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        #self.selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        #self.selectionNode.objectName.setValue(obj.Object.Name) # here obj is the ViewObject, we need its associated App Object
        #self.selectionNode.subElementName.setValue("Comb")
        #self.selectionNode.addChild(self.curveLines)
            

        #self.wireframe.addChild(self.selectionNode)
        obj.addDisplayMode(self.wireframe,"Wireframe")
        #self.onChanged(obj,"Color")

    def updateData(self, fp, prop):
        self.setEdgeList( fp )
        self.createNodes(fp)
        #FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.updateData \n")
        #if fp.Type == "Curvature":
            #self.combColor.rgb  = (0,0.6,0)
        #elif fp.Type == "Radius":
            #self.combColor.rgb  = (0,0.8,0.8)
        #elif fp.Type == "Unit Normal":
            #self.combColor.rgb  = (0.8,0.8,0)
        self.getMaxCurv(fp.Samples)
        self.getCurvFactor(fp)
        for n in self.nodes:
            pl = getEdgeParamList(n.edge, fp.Samples)
            data = getEdgeData(n.edge, pl)
            n.points = getSoPoints(data , self.factor)
            ci = getCombCoords(fp.Samples)
            n.combLines.coordIndex.setValues(0,len(ci),ci)
            di = getCurveCoords(fp.Samples)
            n.curveLines.coordIndex.setValues(0,len(di),di)

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
        #FreeCAD.Console.PrintMessage("Comb : Change property: " + str(prop) + "\n")
        return
        
    def getIcon(self):
        return """
            /* XPM */
            static const char * ViewProviderBox_xpm[] = {
            "16 16 6 1",
            "    c None",
            ".   c #141010",
            "+   c #615BD2",
            "@   c #C39D55",
            "#   c #000000",
            "$   c #57C355",
            "        ........",
            "   ......++..+..",
            "   .@@@@.++..++.",
            "   .@@@@.++..++.",
            "   .@@  .++++++.",
            "  ..@@  .++..++.",
            "###@@@@ .++..++.",
            "##$.@@$#.++++++.",
            "#$#$.$$$........",
            "#$$#######      ",
            "#$$#$$$$$#      ",
            "#$$#$$$$$#      ",
            "#$$#$$$$$#      ",
            " #$#$$$$$#      ",
            "  ##$$$$$#      ",
            "   #######      "};
            """

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

class ParametricComb:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj),Part.Edge):
                        res.append((obj.Object,[obj.SubElementNames[i]]))
                        #res.append(obj.SubElementNames[i])
                    i += 1
            else:
                i = 0
                for e in obj.Object.Shape.Edges:
                    n = "Edge"+str(i)
                    res.append((obj.Object,[n]))
                    #res.append(n)
                    i += 1
        return res
    
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = self.parseSel(s)
        FreeCAD.Console.PrintMessage(str(edges) + "\n")
        obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython","Comb") #add object to document
        Comb(obj,edges)
        ViewProviderComb(obj.ViewObject)
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/comb.svg', 'MenuText': 'ParametricComb', 'ToolTip': 'Creates a parametric Comb plot on selected edges'}

FreeCADGui.addCommand('ParametricComb', ParametricComb())




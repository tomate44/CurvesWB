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


class Comb:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nComb class Init\n")
        obj.addProperty("App::PropertyLinkSubList","Edge","Comb","Edge").Edge = edge
        obj.addProperty("App::PropertyEnumeration","Type","Comb","Comb Type").Type=["Curvature","Unit Normal"]
        obj.addProperty("App::PropertyFloat","Scale","Comb","Scale (%)").Scale=100.0
        obj.addProperty("App::PropertyBool","ScaleAuto","Comb","Automatic Scale").ScaleAuto = True
        obj.addProperty("App::PropertyIntegerConstraint","Samples","Comb","Number of samples").Samples = 20
        #obj.addProperty("App::PropertyFloat","TotalLength","Comb","Total length of edges")
        obj.addProperty("App::PropertyVectorList","CombPoints","Comb","CombPoints")
        obj.addProperty("Part::PropertyPartShape","Shape","Comb", "Shape of comb plot")
        obj.Proxy = self
        #obj.Samples = (20,2,1000,10)
        obj.CombPoints = []
        self.edges = []
        self.TotalLength = 0.0
        self.factor = 1.0
        #self.selectedEdgesToProperty( obj, edge)
        #self.setEdgeList( obj)
        self.execute(obj)
        obj.Scale = self.factor * 100
        
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
        totalLength = 0.0
        for e in obj.Edge:
            o = e[0]
            FreeCAD.Console.PrintMessage(str(o) + " - ")
            for f in e[1]:
                n = eval(f.lstrip('Edge'))
                FreeCAD.Console.PrintMessage(str(n) + "\n")
                if o.Shape.Edges:
                    g = o.Shape.Edges[n-1]
                    totalLength += g.Length
        self.TotalLength = totalLength
        FreeCAD.Console.PrintMessage("Total Length : " + str(self.TotalLength) + "\n")

    def setEdgeList( self, obj):
        edgeList = []
        FreeCAD.Console.PrintMessage(str(obj.Edge) + "\n")
        for e in obj.Edge:
            o = e[0]
            FreeCAD.Console.PrintMessage(str(o.Name) + " - ")
            for f in e[1]:
                n = eval(f.lstrip('Edge'))
                FreeCAD.Console.PrintMessage(str(n) + "\n")
                FreeCAD.Console.PrintMessage(str(o.Shape) + "\n")
                if o.Shape.Edges:
                    edgeList.append(o.Shape.Edges[n-1])
        self.edges = edgeList
        
    def getMaxCurv(self, obj):
        self.maxCurv = 0.001
        for e in self.edges:
            pl = getEdgeParamList(e, None, None, obj.Samples)
            cl = getEdgeCurvatureList(e, pl)
            m = max(cl)
            if self.maxCurv < m:
                self.maxCurv = m
        FreeCAD.Console.PrintMessage("max curvature : "+str(self.maxCurv)+"\n")
                
    def getCurvFactor(self, obj):
        self.factor = 100
        if hasattr(obj, "Scale"):
            self.factor = obj.Scale / 100
        if hasattr(obj, "ScaleAuto"):
            if obj.ScaleAuto:
                self.factor = 0.5 * self.TotalLength / self.maxCurv
        FreeCAD.Console.PrintMessage("Curvature Factor : "+str(self.factor)+"\n")

    def buildPoints(self, obj):
        obj.CombPoints = []
        pts = []
        for e in self.edges:
            pl = getEdgeParamList(e, None, None, obj.Samples)
            data = getEdgeData(e, pl)
            pts += getSoPoints(data , self.factor)
        obj.CombPoints = pts
        FreeCAD.Console.PrintMessage(str(len(obj.CombPoints))+" Comb points\n")   #+str(obj.CombPoints)+"\n\n")

    def execute(self, obj):
        FreeCAD.Console.PrintMessage("\n***** execute *****\n")
        #self.selectedEdgesToProperty( obj, edge)
        self.setEdgeList( obj)
        self.computeTotalLength( obj)
        self.getMaxCurv( obj)
        self.getCurvFactor( obj)
        self.buildPoints( obj)
        FreeCAD.Console.PrintMessage("\n----- execute -----\n")

    def onChanged(self, fp, prop):
        #print fp
        if not fp.Edge:
            return
        if prop == "Edge":
            FreeCAD.Console.PrintMessage("\nComb : Edge changed\n")
            #self.setEdgeList( fp)
            self.execute(fp)
        if prop == "Type":
            FreeCAD.Console.PrintMessage("\nComb : Type Property changed\n")
        if prop == "Scale":
            FreeCAD.Console.PrintMessage("\nComb : Scale Property changed\n")
        if prop == "Samples":
            FreeCAD.Console.PrintMessage("\nComb : Samples Property changed\n")
            self.execute(fp)
        if prop == "ScaleAuto":
            FreeCAD.Console.PrintMessage("\nComb : ScaleAuto Property changed\n")
            if fp.ScaleAuto:
                self.execute(fp)
                fp.Scale = self.factor * 100
            
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None




class ViewProviderComb:
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




from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 0

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


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
            debug("Normal error")
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
        debug("Comb class Init")
        obj.addProperty("App::PropertyLinkSubList","Edge","Comb","Edge").Edge = edge
        #obj.addProperty("App::PropertyEnumeration","Type","Comb","Comb Type").Type=["Curvature","Unit Normal"]
        obj.addProperty("App::PropertyFloat","Scale","Comb","Scale (%). 0 for AutoScale").Scale=0.0
        #obj.addProperty("App::PropertyBool","ScaleAuto","Comb","Automatic Scale").ScaleAuto = True
        obj.addProperty("App::PropertyIntegerConstraint","Samples","Comb","Number of samples").Samples = 64
        obj.addProperty("App::PropertyInteger","SurfaceSamples","Comb","Number of surface samples").SurfaceSamples = 3
        obj.addProperty("App::PropertyEnumeration","SurfaceOrientation","Comb","Surface Comb Orientation").SurfaceOrientation=["U","V"]
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
        obj.Scale = self.factor
        
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
            debug(str(edge) + "")
            debug(str(obj.Edge) + "")

    def computeTotalLength(self, obj):
        totalLength = 0.0
        for e in obj.Edge:
            o = e[0]
            debug(str(o) + " - ")
            for f in e[1]:
                if 'Edge' in f:
                    n = eval(f.lstrip('Edge'))
                    debug(str(n) + "")
                    if o.Shape.Edges:
                        g = o.Shape.Edges[n-1]
                        totalLength += g.Length
                elif 'Face' in f:
                    n = eval(f.lstrip('Face'))
                    debug(str(n) + "")
                    if o.Shape.Faces:
                        g = o.Shape.Faces[n-1]
                        try:
                            if obj.SurfaceOrientation == 'U':
                                bounds = g.Surface.bounds()
                                midParam = bounds[0] + (bounds[1] - bounds[0]) / 2
                                iso = g.Surface.uIso(midParam).toShape()
                            else:
                                bounds = g.Surface.bounds()
                                midParam = bounds[2] + (bounds[3] - bounds[2]) / 2
                                iso = g.Surface.vIso(midParam).toShape()
                            totalLength += iso.Length
                        except:
                            debug("Surface Error")
 
 
        self.TotalLength = totalLength
        debug("Total Length : " + str(self.TotalLength) + "")

    def setEdgeList( self, obj):
        edgeList = []
        debug(str(obj.Edge) + "")
        for e in obj.Edge:
            o = e[0]
            debug(str(o.Name) + " - ")
            for f in e[1]:
                if 'Edge' in f:
                    n = eval(f.lstrip('Edge'))
                    debug('Edge ' + str(n) + "")
                    debug(str(o.Shape) + "")
                    if o.Shape.Edges:
                        edgeList.append(o.Shape.Edges[n-1])
                elif 'Face' in f:
                    n = eval(f.lstrip('Face'))
                    debug('Face ' + str(n) + "")
                    debug(str(o.Shape) + "")
                    if o.Shape.Faces:
                        g = o.Shape.Faces[n-1]
                        #try:
                        if obj.SurfaceOrientation == 'U':
                            iso = self.getuIsoEdges(g,obj.SurfaceSamples)
                        else:
                            iso = self.getvIsoEdges(g,obj.SurfaceSamples)
                        edgeList += iso
                        #except:
                            #debug("Surface Error")
        self.edges = edgeList
 
 
    def getuIsoEdges(self, face, samples):
        res = []
        n = []
        bounds = face.Surface.bounds()
        if samples <= 1:
            midParam = bounds[0] + (bounds[1] - bounds[0]) / 2
            n = [midParam]
        elif samples == 2:
            n = [bounds[0],bounds[1]]
        else :
            brange = bounds[1] - bounds[0]
            for  i in range(samples-1):
                n.append(bounds[0] + brange*i/(samples-1))
            n.append(bounds[1])
        for t in n:
            res.append(face.Surface.uIso(t).toShape())
        debug("U Iso curves :")
        debug(str(res))
        return res


    def getvIsoEdges(self, face, samples):
        res = []
        n = []
        bounds = face.Surface.bounds()
        if samples <= 1:
            midParam = bounds[2] + (bounds[3] - bounds[2]) / 2
            n = [midParam]
        elif samples == 2:
            n = [bounds[2], bounds[3]]
        else :
            brange = bounds[3] - bounds[2]
            for  i in range(samples-1):
                n.append(bounds[2] + brange*i/(samples-1))
            n.append(bounds[3])
        for t in n:
            res.append(face.Surface.vIso(t).toShape())
        debug("V Iso curves :")
        debug(str(res))
        return res
    
    
    def getMaxCurv(self, obj):
        self.maxCurv = 0.001
        for e in self.edges:
            pl = getEdgeParamList(e, None, None, obj.Samples)
            cl = getEdgeCurvatureList(e, pl)
            m = max(cl)
            if self.maxCurv < m:
                self.maxCurv = m
        debug("max curvature : "+str(self.maxCurv)+"")
                
    def getCurvFactor(self, obj):
        self.factor = 1.0
        if hasattr(obj, "Scale"):
            if obj.Scale == 0.0:
                self.factor = 0.5 * self.TotalLength / self.maxCurv
            else:
                self.factor = obj.Scale
        #if hasattr(obj, "ScaleAuto"):
            #if obj.ScaleAuto:
                #self.factor = 0.5 * self.TotalLength / self.maxCurv
        debug("Curvature Factor : "+str(self.factor)+"")

    def buildPoints(self, obj):
        obj.CombPoints = []
        pts = []
        for e in self.edges:
            pl = getEdgeParamList(e, None, None, obj.Samples)
            data = getEdgeData(e, pl)
            pts += getSoPoints(data , self.factor)
        obj.CombPoints = pts
        debug(str(len(obj.CombPoints))+" Comb points")   #+str(obj.CombPoints)+"")

    def execute(self, obj):
        debug("***** execute *****")
        #self.selectedEdgesToProperty( obj, edge)
        self.setEdgeList( obj)
        self.computeTotalLength( obj)
        self.getMaxCurv( obj)
        self.getCurvFactor( obj)
        self.buildPoints( obj)
        debug("----- execute -----")

    def onChanged(self, fp, prop):
        #print fp
        if not fp.Edge:
            return
        if prop == "Edge":
            debug("Comb : Edge changed")
            #self.setEdgeList( fp)
            self.execute(fp)
        if prop == "Type":
            debug("Comb : Type Property changed")
        if prop == "Scale":
            if fp.Scale <= 0.0:
                self.factor = 0.5 * self.TotalLength / self.maxCurv
                fp.Scale = self.factor
            debug("Comb : Scale Property changed to "+str(fp.Scale)+"")
        if prop == "Samples":
            debug("Comb : Samples Property changed")
            self.execute(fp)
        #if prop == "ScaleAuto":
            #debug("Comb : ScaleAuto Property changed")
            #if fp.ScaleAuto:
                #self.execute(fp)
                #fp.Scale = self.factor * 100
            
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
        #debug("Comb : ViewProviderComb.attach ")

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
        #debug(""+str(i1)+"")
        
        i2 = getCurveCoords(fp)
        self.curveLines.coordIndex.setValues(0,len(i2),i2)
        #debug(""+str(i2)+"")

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
            debug("vp detected a Edge change")
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
                    if issubclass(type(subobj),Part.Face):
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
                for f in obj.Object.Shape.Faces:
                    n = "Face"+str(i)
                    res.append((obj.Object,[n]))
                    #res.append(n)
                    i += 1
        return res
    
    def findComb(self, sel):
        res = None
        module = None
        for obj in sel:
            debug("-- Parsing Object : "+str(obj.Object.Label)+"")
            try:
                module = obj.Object.Proxy.__module__
                if module == 'ParametricComb':
                    res = obj.Object
                    debug("Found active Comb : "+str(res.Label)+"")
            except:
                debug("No module found")

        return res
    
    def appendEdges(self, comb, edges):
        existingEdges = comb.Edge
        newEdges = existingEdges + edges
        comb.Edge = newEdges
    
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = self.parseSel(s)
        #debug(str(edges) + "")
        combSelected = self.findComb(s)
        if not combSelected:
            obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython","Comb") #add object to document
            Comb(obj,edges)
            ViewProviderComb(obj.ViewObject)
        else:
            self.appendEdges(combSelected, edges)
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/comb.svg', 'MenuText': 'ParametricComb', 'ToolTip': 'Creates a parametric Comb plot on selected edges'}

FreeCADGui.addCommand('ParametricComb', ParametricComb())




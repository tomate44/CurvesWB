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



class Comb:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nComb class Init\n")
        obj.addProperty("App::PropertyLinkSubList","Edge","Comb","Edge")
        obj.addProperty("App::PropertyEnumeration","Type","Comb","Comb Type").Type=["Curvature","Unit Normal"]
        obj.addProperty("App::PropertyFloat","Scale","Comb","Scale (%)").Scale=100.0
        obj.addProperty("App::PropertyBool","ScaleAuto","Comb","Automatic Scale").ScaleAuto = True
        obj.addProperty("App::PropertyInteger","Samples","Comb","Number of samples").Samples=128
        #obj.addProperty("App::PropertyVectorList","CurvePoints","Comb","CurvePoints")
        #obj.addProperty("App::PropertyVectorList","CombPoints","Comb","CombPoints")
        obj.addProperty("Part::PropertyPartShape","Shape","Comb", "Shape of comb plot")
        objs = []
        obj.Proxy = self
        
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
            self.execute(obj)

    def execute(self, fp):
        #FreeCAD.Console.PrintMessage("\nComb : computeComb\n")
        #num = fp.Samples
        lines = []
        maxCur = 0.01
        minCur = 1e10
        pts = []
        edges =  []
        params = []
        datas =  []
        totalLength = 0
        for e in fp.Edge:
            o = e[0]
            FreeCAD.Console.PrintMessage(str(o) + " - ")
            for f in e[1]:
                n = eval(f.lstrip('Edge'))
                FreeCAD.Console.PrintMessage(str(n) + "\n")
                g = o.Shape.Edges[n-1]
                totalLength += g.Length
                edges.append(g)
                p = getEdgeParamList(g, num = fp.Samples)
                params.append(p)
                d = getEdgeData(g, p)
                datas.append(d)
                if maxCur < max(d[1]):
                    maxCur = max(d[1])
                # computation of min value is not needed
                #if minCur > min(d[1]):
                #    minCur = min(d[1])
        if fp.ScaleAuto:
            fp.Scale = 0.4 * totalLength
            if fp.Type == "Curvature":
                fp.Scale = fp.Scale / maxCur

        self.CurvePoints = []
        self.CombPoints  = []
        
        for d in datas:
            self.CurvePoints.append(d[0])
            
        
        
                firstParameter = o.Shape.Edges[n-1].FirstParameter
                lastParameter = o.Shape.Edges[n-1].LastParameter
                parameterRange = lastParameter - firstParameter


                for i in range(num+1):
                    t = firstParameter + parameterRange * i / num
                    v0 = bs_1.value(t)
                    pts.append(v0)
                    c = bs_1.toShape().curvatureAt(t)
                    if c:
                        v1 = bs_1.toShape().centerOfCurvatureAt(t)
                    else:
                        v1 = v0
                    v2 = v0.sub(v1)
                    
                    lines.append([v0,v2,c])
                    if c > max:
                        max  = c
                    if c < min:
                        min = c
        fp.CurvePoints = pts
        #fp.Shape = Part.makePolygon(pts)
        #print str(min)
        #print str(max)
        #print fp.CurvePoints

        curvatureScale = fp.Scale
        if fp.Relative and fp.Type == "Curvature":
            curvatureScale *= o.Shape.Edges[n-1].Length / max
        #if fp.Relative and fp.Type == "Radius":
            #curvatureScale *= o.Shape.Edges[n-1].Length * min
        if fp.Relative and fp.Type == "Unit Normal":
            curvatureScale *= o.Shape.Edges[n-1].Length
        combpts = []
        for l in lines:
            curvature = l[2]
            if curvature != 0:
                if fp.Type == "Curvature":
                    newVec = FreeCAD.Vector(l[1]).normalize().multiply(curvature * curvatureScale / 100)
                elif fp.Type == "Radius":
                    newVec = FreeCAD.Vector(l[1]).multiply(curvatureScale / 100)
                else:
                    newVec = FreeCAD.Vector(l[1]).normalize().multiply(curvatureScale / 100)
                y = l[0].add(newVec)
                combpts.append(y)
                #print str(y.Length)
            else:
                combpts.append(l[0])
                #print "  0"
        fp.CombPoints = combpts

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
            self.execute(fp)



class ViewProviderComb:
    def __init__(self, obj):
        "Set this object to the proxy object of the actual view provider"
        obj.addProperty("App::PropertyColor","CurveColor","Comb","Color of the curvature curve").Color=(0.8,0.0,0.0)
        obj.addProperty("App::PropertyColor","CombColor","Comb","Color of the curvature comb").Color=(0.0,0.8,0.0)
        # TODO : add transparency property
        obj.Proxy = self

    def attach(self, obj):
        #FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.attach \n")

        self.wireframe = coin.SoGroup()

        self.combColor  =  coin.SoBaseColor()
        self.curveColor =  coin.SoBaseColor()
        self.combColor.rgb  = (0,0.8,0)
        self.curveColor.rgb = (0.8,0,0)

        self.combPts =  coin.SoCoordinate3()
        self.curvePts = coin.SoCoordinate3()
        self.combLines= coin.SoIndexedLineSet()
        self.curveLines=coin.SoIndexedLineSet()

        self.selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        self.selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        self.selectionNode.objectName.setValue(obj.Object.Name) # here obj is the ViewObject, we need its associated App Object
        self.selectionNode.subElementName.setValue("Comb")
        self.selectionNode.addChild(self.curveLines)

        self.wireframe.addChild(self.combColor)
        self.wireframe.addChild(self.combPts)
        self.wireframe.addChild(self.combLines)
        self.wireframe.addChild(self.curveColor)
        self.wireframe.addChild(self.curvePts)
        self.wireframe.addChild(self.curveLines)
        self.wireframe.addChild(self.selectionNode)
        obj.addDisplayMode(self.wireframe,"Wireframe")
        self.onChanged(obj,"Color")

    def updateData(self, fp, prop):
        #FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.updateData \n")
        if fp.Type == "Curvature":
            self.combColor.rgb  = (0,0.6,0)
        #elif fp.Type == "Radius":
            #self.combColor.rgb  = (0,0.8,0.8)
        elif fp.Type == "Unit Normal":
            self.combColor.rgb  = (0.8,0.8,0)

        pts1 = []
        cnt1 = 0
        ptsIndex1 = []
        for pt in fp.CombPoints:
            pts1.append([pt.x,pt.y,pt.z])
            ptsIndex1.append(cnt1)
            cnt1 += 1
        ptsIndex1.append(-1)

        #print "Number of Curve points : "+str(len(pts1))
        #print ptsIndex1
        
        pts2 = []
        cnt2 = 0
        ptsIndex2 = []
        for i in range(len(fp.CombPoints)):
            p0 = [fp.CurvePoints[i].x,fp.CurvePoints[i].y,fp.CurvePoints[i].z]
            p1 = [fp.CombPoints[i].x,fp.CombPoints[i].y,fp.CombPoints[i].z]
            pts2.append(p0)
            pts2.append(p1)
            ptsIndex2.append(i*2)
            ptsIndex2.append(1+i*2)
            ptsIndex2.append(-1)

        #print "Number of Comb points : "+str(len(pts2))

        self.curvePts.point.setValue(0,0,0)
        self.curveLines.coordIndex.setValue(0)
        self.curvePts.point.setValues(0,len(pts1),pts1)
        self.curveLines.coordIndex.setValues(0,len(ptsIndex1),ptsIndex1)

        self.combPts.point.setValue(0,0,0)
        self.combLines.coordIndex.setValue(0)
        self.combPts.point.setValues(0,len(pts2),pts2)
        self.combLines.coordIndex.setValues(0,len(ptsIndex2),ptsIndex2)

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




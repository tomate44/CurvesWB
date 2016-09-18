from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class Comb:
    def __init__(self, obj , edge):
        ''' Add the properties '''
        FreeCAD.Console.PrintMessage("\nComb class Init\n")
        obj.addProperty("App::PropertyLinkSub","Edge","Comb","Edge").Edge = edge
        obj.addProperty("App::PropertyEnumeration","Type","Comb","Comb Type").Type=["Curvature","Radius","Unit Normal"]
        obj.addProperty("App::PropertyFloat","Scale","Comb","Scale (%)").Scale=100.0
        obj.addProperty("App::PropertyBool","Relative","Comb","Scale is relative to edge length").Relative = False
        obj.addProperty("App::PropertyInteger","Samples","Comb","Number of samples").Samples=128
        obj.addProperty("App::PropertyVectorList","CurvePoints","Comb","CurvePoints")
        obj.addProperty("App::PropertyVectorList","CombPoints","Comb","CombPoints")
        obj.addProperty("Part::PropertyPartShape","Shape","Comb", "Shape of comb plot")
        obj.Proxy = self
        self.execute(obj)

    def computeComb(self, fp):
        FreeCAD.Console.PrintMessage("\nComb : computeComb\n")
        num = fp.Samples
        lines = []
        o = fp.Edge[0]
        #print o
        n = eval(fp.Edge[1][0].lstrip('Edge'))
        #print n
        bs_1 = o.Shape.Edges[n-1].Curve
        firstParameter = o.Shape.Edges[n-1].FirstParameter
        lastParameter = o.Shape.Edges[n-1].LastParameter
        parameterRange = lastParameter - firstParameter
        max = 0
        min = 1e10
        pts = []
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
        fp.Shape = Part.makePolygon(pts)
        #print str(min)
        #print str(max)
        #print fp.CurvePoints

        curvatureScale = fp.Scale
        if fp.Relative and fp.Type == "Curvature":
            curvatureScale *= o.Shape.Edges[n-1].Length / max
        if fp.Relative and fp.Type == "Radius":
            curvatureScale *= o.Shape.Edges[n-1].Length * min
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

    def execute(self, fp):
        FreeCAD.Console.PrintMessage("\nComb : execute\n")
        self.computeComb(fp)



class ViewProviderComb:
    def __init__(self, obj):
        "Set this object to the proxy object of the actual view provider"
        obj.Proxy = self

    def attach(self, obj):
        FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.attach \n")

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
        FreeCAD.Console.PrintMessage("\nComb : ViewProviderComb.updateData \n")
        if fp.Type == "Curvature":
            self.combColor.rgb  = (0,0.8,0)
        elif fp.Type == "Radius":
            self.combColor.rgb  = (0,0.8,0.8)
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
        FreeCAD.Console.PrintMessage("Comb : Change property: " + str(prop) + "\n")
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
                        res.append([obj.Object,obj.SubElementNames[i]])
                    i += 1
            else:
                i = 0
                for e in obj.Object.Shape.Edges:
                    n = "Edge"+str(i)
                    res.append([obj.Object,n])
                    i += 1
        return res
    
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = self.parseSel(s)

        for e in edges:
            obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython","Comb") #add object to document
            Comb(obj,e)
            ViewProviderComb(obj.ViewObject)
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/comb.svg', 'MenuText': 'ParametricComb', 'ToolTip': 'Creates a parametric Comb plot on selected edges'}

FreeCADGui.addCommand('ParametricComb', ParametricComb())




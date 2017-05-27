import os
import FreeCAD, FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

def increaseContinuity(c,tol):
    #oc = c.Continuity
    mults = [int(m) for m in c.getMultiplicities()]
    #knots = c.getKnots()
    for i in range(len(mults))[1:-1]:
        rk = c.removeKnot(i+1,mults[i]-1,tol)
    return(c.Continuity)    

def alignedTangents(c0, c1, Tol):
    t0 = c0.tangent(c0.LastParameter)[0]
    t1 = c1.tangent(c1.FirstParameter)[0]
    t0.normalize()
    t1.negative()
    t1.normalize()
    v = t0.sub(t1)
    if v.Length < Tol:
        return(True)
    else:
        return(False)
    


class join:
    "joins the selected edges into a single BSpline Curve"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSubList",  "Edges",        "Join",   "Edges")
        obj.addProperty("App::PropertyFloat",        "Tolerance",    "Join",   "Tolerance").Tolerance=0.001
        obj.addProperty("App::PropertyBool",         "CornerBreak",  "Join",   "Break on corners").CornerBreak = False
        #obj.addProperty("App::PropertyBool",         "BadContinuity","Join",   "Break On Bad C0 Continuity").BadContinuity = False
        obj.Proxy = self

    def getEdges(self, obj):
        res = []
        if hasattr(obj, "Edges"):
            for l in obj.Edges:
                o = l[0]
                for ss in l[1]:
                    n = eval(ss.lstrip('Edge'))
                    res.append(o.Shape.Edges[n-1])
        return(res)

    def execute(self, obj):
        edges = self.getEdges(obj)
        curves = []
        for e in edges:
            c = e.Curve
            if not isinstance(c,Part.BSplineCurve):
                c = e.Curve.toBSpline()
            c.segment(e.FirstParameter,e.LastParameter)
            curves.append(c)

        c0 = curves[0].copy()
        if not isinstance(c0,Part.BSplineCurve):
            #FreeCAD.Console.PrintMessage("\nConverting c0 to BSplineCurve\n")
            c0 = c0.toBSpline()
        outcurves = []
        for c in curves[1:]:
            i = False
            tempCurve = c0.copy()
            tan = alignedTangents(c0,c,obj.Tolerance)
            if (tan is False) & obj.CornerBreak:
                outcurves.append(c0)
                c0 = c.copy()
                debug("No tangency on edge #"+str(curves[1:].index(c)+2)+"\n")
            else:
                r = c0.join(c) #.toBSpline())
                if r is False:  #  join operation failed
                    outcurves.append(c0)
                    c0 = c.copy()
                    debug("Failed to join edge #"+str(curves[1:].index(c)+2)+"\n")
                else:
                    i = increaseContinuity(c0,obj.Tolerance)
                    if (not (i == 'C1')) & obj.CornerBreak:
                        outcurves.append(tempCurve)
                        c0 = c.copy()
                        debug("Failed to smooth edge #"+str(curves[1:].index(c)+2)+"\n")

        outcurves.append(c0)

        outEdges = [Part.Edge(c) for c in outcurves]
        obj.Shape = Part.Wire(outEdges)
        #for selobj in sel:
            #if selobj.Object:                
                #selobj.Object.ViewObject.Visibility = False



class joinCommand:
    "joins the selected edges into a single BSpline Curve"
    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select the edges to join first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        edges.append((selobj.Object, selobj.SubElementNames[i]))
            else:
                for i in range(len(selobj.Object.Shape.Edges)):
                    name = "Edge%d"%(i+1)
                    edges.append((selobj.Object, name))
        
        joinCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","JoinCurve")
        join(joinCurve)
        joinCurve.ViewObject.Proxy=0
        joinCurve.Edges = edges
        FreeCAD.ActiveDocument.recompute()
        
        
        #curves = []
        #for e in edges:
            #c = e.Curve
            #if not isinstance(c,Part.BSplineCurve):
                #c = e.Curve.toBSpline()
            #c.segment(e.FirstParameter,e.LastParameter)
            #curves.append(c)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/joincurve.svg', 'MenuText': 'Join Curves', 'ToolTip': 'Joins the selected edges into BSpline Curves'}

FreeCADGui.addCommand('join', joinCommand())

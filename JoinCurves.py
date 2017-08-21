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
    try:
        for i in range(len(mults))[1:-1]:
            rk = c.removeKnot(i+1,mults[i]-1,tol)
    except Part.OCCError:
        debug('failed to increase continuity.')
        debug("curve has %d poles."%len(c.getPoles()))
    return(c)    

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
        tmp = []
        for e in edges:
            #c = e.Curve
            #if not isinstance(c,Part.BSplineCurve):
                #c = e.Curve.toBSpline()
            #c.segment(e.FirstParameter,e.LastParameter)
            #tmp.append(c)
            tmp += e.toNurbs().Edges

        curves = []
        for e in tmp:
            c = e.Curve
            if not isinstance(c,Part.BSplineCurve):
                c = e.Curve.toBSpline()
            c.segment(e.FirstParameter,e.LastParameter)
            curves.append(c)

        debug("Edges : \n%s"%str(curves))
        c0 = curves[0].copy()
        if not isinstance(c0,Part.BSplineCurve):
            #FreeCAD.Console.PrintMessage("\nConverting c0 to BSplineCurve\n")
            c0 = c0.toBSpline()
        outcurves = []
        for n,c in enumerate(curves[1:]):
            debug("joining edge #%d"%(n+2))
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
                    if (not (i.Continuity == 'C1')) & obj.CornerBreak:
                        outcurves.append(tempCurve)
                        c0 = c.copy()
                        debug("Failed to smooth edge #"+str(curves[1:].index(c)+2)+"\n")
        outcurves.append(c0)

        outEdges = [Part.Edge(c) for c in outcurves]
        obj.Shape = Part.Wire(outEdges)
        #for selobj in sel:
            #if selobj.Object:                
                #selobj.Object.ViewObject.Visibility = False

class joinVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/joincurve.svg')

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
        return True


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
        joinVP(joinCurve.ViewObject)
        joinCurve.Edges = edges
        FreeCAD.ActiveDocument.recompute()
        joinCurve.ViewObject.LineWidth = 2.0
        joinCurve.ViewObject.LineColor = (0.3,0.0,0.5)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            #return f.match()
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/joincurve.svg', 'MenuText': 'Join Curves', 'ToolTip': 'Joins the selected edges into BSpline Curves'}

FreeCADGui.addCommand('join', joinCommand())

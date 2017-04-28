import os
import FreeCAD, FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1
Tol = 0.001
BreakOnBadTangents = True
BreakOnBadContinuity = True

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

def alignedTangents(c0,c1):
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
    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.HasSubObjects:                
                edges += selobj.SubObjects
            else:
                edges += selobj.Object.Shape.Edges
        curves = []
        for e in edges:
            c = e.Curve
            if not isinstance(c,Part.BSplineCurve):
                c = e.Curve.toBSpline()
            c.segment(e.FirstParameter,e.LastParameter)
            curves.append(c)

        #print(curves)
        #success = True
        c0 = curves[0].copy()
        if not isinstance(c0,Part.BSplineCurve):
            #FreeCAD.Console.PrintMessage("\nConverting c0 to BSplineCurve\n")
            c0 = c0.toBSpline()
        outcurves = []
        for c in curves[1:]:
            i = False
            tempCurve = c0.copy()
            tan = alignedTangents(c0,c)
            if (tan is False) & BreakOnBadTangents:
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
                    i = increaseContinuity(c0,Tol)
                    if (not (i == 'C1')) & BreakOnBadContinuity:
                        outcurves.append(tempCurve)
                        c0 = c.copy()
                        debug("Failed to smooth edge #"+str(curves[1:].index(c)+2)+"\n")
            #success = False
            #FreeCAD.Console.PrintMessage("Failed to join edge #"+str(curves[1:].index(c)+2)+"\n")
        outcurves.append(c0)
            #c0 = c.copy()
        if 1:
            #increaseContinuity(c0,1e-3)
            obj = FreeCAD.ActiveDocument.addObject("Part::Spline","Spline")
            outEdges = [Part.Edge(c) for c in outcurves]
            obj.Shape = Part.Wire(outEdges)
            for selobj in sel:
                if selobj.Object:                
                    selobj.Object.ViewObject.Visibility = False
        else:
            FreeCAD.Console.PrintMessage("Join operation failed !\n")

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/joincurve.svg', 'MenuText': 'Join Curves', 'ToolTip': 'Joins the selected edges into a single BSpline Curve'}
FreeCADGui.addCommand('join', join())

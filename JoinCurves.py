import os
import FreeCAD, FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

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
        curves = [e.Curve for e in edges]

        #print(curves)
        success = True
        c0 = curves[0].copy()
        if not isinstance(c0,Part.BSplineCurve):
            #FreeCAD.Console.PrintMessage("\nConverting c0 to BSplineCurve\n")
            c0 = c0.toBSpline()
        for c in curves[1:]:
            r = c0.join(c.toBSpline())
            if not r:
                success = False
                FreeCAD.Console.PrintMessage("Failed to join edge #"+str(curves[1:].index(c)+2)+"\n")

        if success:
            obj = FreeCAD.ActiveDocument.addObject("Part::Spline","Spline")
            obj.Shape = c0.toShape()
            for selobj in sel:
                if selobj.Object:                
                    selobj.Object.ViewObject.Visibility = False
        else:
            FreeCAD.Console.PrintMessage("Join operation failed !\n")

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/joincurve.svg', 'MenuText': 'Join Curves', 'ToolTip': 'Joins the selected edges into a single BSpline Curve'}
FreeCADGui.addCommand('join', join())

#import FreeCADGui
import os, sys
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
sys.path.append(path_curvesWB + '/Gui')
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class CurvesWorkbench (Workbench):
   MenuText = "Curves"
   def Initialize(self):
       import line
       import bezierCurve
       import editableSpline
       import ParametricBlendCurve
       import ParametricComb
       import ZebraTool
       import SurfaceEdit
       import GeomInfo
       import ExtractShapes
       import IsoCurve
       import JoinCurves
       import Discretize
       import Sketch_On_Surface
       commandslist = ["line","bezierCurve","editableSpline","ParametricBlendCurve","ParametricComb","ZebraTool","SurfaceEditTool","GeomInfo","extract","IsoCurve","join","Discretize","SoS"]
       #FreeCADGui.addIconPath( ':/CurvesWB/icons' )
       self.appendToolbar("Curves",commandslist)
Gui.addWorkbench(CurvesWorkbench())




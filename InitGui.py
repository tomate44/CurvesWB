#import FreeCADGui
import os, sys
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
sys.path.append(path_curvesWB + '/Gui')
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class CurvesWorkbench (Workbench):
   MenuText = "Curves"
   def Initialize(self):
       import bezierCurve
       import editableSpline
       import JoinCurves
       import Discretize
       import approximate
       import ParametricBlendCurve
       import ParametricComb
       import ZebraTool
       import SurfaceEdit
       import GeomInfo
       import ExtractShapes
       import IsoCurve
       import Sketch_On_Surface
       import Sw2R

       commandslist = ["bezierCurve","editableSpline","join","Discretize","Approximate","ParametricBlendCurve","ParametricComb","ZebraTool","SurfaceEditTool","GeomInfo","extract","IsoCurve","SoS","sw2r"]
       #FreeCADGui.addIconPath( ':/CurvesWB/icons' )
       self.appendToolbar("Curves",commandslist)
Gui.addWorkbench(CurvesWorkbench())




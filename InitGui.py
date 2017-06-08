#import FreeCADGui
import os, sys
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
sys.path.append(path_curvesWB + '/Gui')
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class CurvesWorkbench (Workbench):
    MenuText = "Curves"
    def Initialize(self):
        "This function is executed when FreeCAD starts"
        import bezierCurve
        import paramVector
        import editableSpline
        import JoinCurves
        import Discretize
        import approximate
        import ParametricBlendCurve
        import ParametricComb
        import ZebraTool
        import SurfaceEdit
        import TrimFace
        import GeomInfo
        import ExtractShapes
        import IsoCurve
        import Sketch_On_Surface
        #import Sw2R
        import PlateSurface
        #import Birail
        import Sweep2Rails
        import hooks

        stablelist = ["bezierCurve","editableSpline","join","Discretize","Approximate","ParametricBlendCurve","ParametricComb","ZebraTool","SurfaceEditTool","Trim","GeomInfo","extract","IsoCurve","SoS","sw2r","hook"]
        #devellist = ["Vector","Plate"]
        #FreeCADGui.addIconPath( ':/CurvesWB/icons' )
        self.appendToolbar("Curves",stablelist)
        #self.appendToolbar("Devel",devellist)

    def Activated(self):
        "This function is executed when the workbench is activated"
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return

    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        # FreeCAD.Console.PrintMessage(recipient)
        if recipient == "View":
            contextlist = ["ParametricComb","ZebraTool","GeomInfo","extract"]
            self.appendContextMenu("Curves",contextlist) # add commands to the context menu
        elif recipient == "Tree":
            contextlist = ["ZebraTool"]
            self.appendContextMenu("Curves",contextlist) # add commands to the context menu

    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"
        
Gui.addWorkbench(CurvesWorkbench())




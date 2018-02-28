#import FreeCADGui
import os, sys
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
sys.path.append(os.path.join(path_curvesWB, 'Gui'))
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')
global main_CurvesWB_Icon
main_CurvesWB_Icon = os.path.join( path_curvesWB_icons , 'blendSurf.svg')

class CurvesWorkbench (Workbench):
    MenuText = "Curves"
    global main_CurvesWB_Icon
    Icon = main_CurvesWB_Icon
    def Initialize(self):
        "This function is executed when FreeCAD starts"
        import lineFP
        import bezierCurve
        import paramVector
        import editableSpline
        import curveExtendFP
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
        import curveOnSurfaceFP
        import blendSurfaceFP
        import parametricSolid
        import ProfileSketch
        import splitCurves
        import pasteSVG
        import pipeshellProfileFP
        import pipeshellFP

        stablelist = ["line","bezierCurve","editableSpline","extend","join","split","Discretize","Approximate","ParametricBlendCurve","ParametricComb","ZebraTool","SurfaceEditTool","Trim","GeomInfo","extract","solid","IsoCurve","SoS","sw2r","profileSupportCmd","cos","blendSurface","pasteSVG","profile","pipeshell"]
        #devellist = ["Vector","Plate"]
        #FreeCADGui.addIconPath( ':/CurvesWB/icons' )
        self.appendToolbar("Curves",stablelist)
        #self.appendToolbar("Devel",devellist)
        

    def Activated(self):
        "This function is executed when the workbench is activated"
        if FreeCAD.GuiUp:
            self.isObserving = True
            self.Selection = []
            FreeCADGui.Selection.addObserver(self)
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        if self.isObserving:
            FreeCADGui.Selection.removeObserver(self)
            self.isObserving = False
        return

    def addSelection(self,doc,obj,sub,pnt):               # Selection object
        #self.Selection.append((doc,obj,sub,pnt))
        self.Selection.append(Gui.Selection.getSelectionObject(doc,obj,sub,pnt))

    def removeSelection(self,doc,obj,sub):                # Delete the selected object
        #FreeCAD.Console.PrintMessage("removeSelection"+ "\n")
        nl = []
        for o in self.Selection:
            if not o == Gui.Selection.getSelectionObject(doc,obj,sub):
                nl.append(o)
        self.Selection= nl
                
    #def setSelection(self,doc):                           # Selection in ComboView
        #FreeCAD.Console.PrintMessage("setSelection"+ "\n")
        #self.Selection.append((doc,None,None,None))
    def clearSelection(self,doc):                         # If click on the screen, clear the selection
        #FreeCAD.Console.PrintMessage("clearSelection"+ "\n")
        self.Selection = []


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




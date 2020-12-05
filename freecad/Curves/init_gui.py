# -*- coding: utf-8 -*-

__title__   = "init_gui.py"
__author__  = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__     = ""

import os
import FreeCADGui as Gui
import FreeCAD as App
from freecad.Curves import ICONPATH

class CurvesWorkbench(Gui.Workbench):
    """FreeCAD workbench that offers a collection of tools mainly related to Nurbs curves and surfaces."""
    MenuText = "Curves"
    ToolTip = "A workbench dedicated to curves and surfaces"
    Icon = os.path.join(ICONPATH, "blendSurf.svg")
    toolbox = []
    
    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        
        #import Sw2R
        #import PlateSurface
        #import Birail
        #import paramVector
        #import SurfaceEdit

        # TODO changes module names to lower_with_underscore

        #import lineFP # cleaned
        #import bezierCurve
        stablelist = list()
        try:
            from freecad.Curves import graphics
            marker = graphics.Marker([App.Vector()])
            from freecad.Curves import gordon_profile_FP
            stablelist = []
            App.Console.PrintMessage("Pivy.graphics interaction library enabled\n")
        except:
            App.Console.PrintWarning("Pivy.graphics interaction library is not available on this computer\n")

        from freecad.Curves import lineFP # cleaned
        from freecad.Curves import curveExtendFP # TODO use basisSpline
        from freecad.Curves import JoinCurves
        from freecad.Curves import splitCurves_2 # cleaned
        from freecad.Curves import Discretize # cleaned
        from freecad.Curves import approximate
        from freecad.Curves import ParametricBlendCurve # cleaned
        from freecad.Curves import ParametricComb
        from freecad.Curves import ZebraTool
        from freecad.Curves import TrimFace
        from freecad.Curves import GeomInfo
        from freecad.Curves import ExtractShapes # cleaned
        from freecad.Curves import IsoCurve
        from freecad.Curves import Sketch_On_Surface
        from freecad.Curves import Sweep2Rails
        #from freecad.Curves import hooks
        from freecad.Curves import curveOnSurfaceFP
        from freecad.Curves import blendSurfaceFP
        from freecad.Curves import parametricSolid # cleaned
        from freecad.Curves import ProfileSketch
        from freecad.Curves import pasteSVG
        from freecad.Curves import pipeshellProfileFP
        from freecad.Curves import pipeshellFP
        from freecad.Curves import gordonFP
        from freecad.Curves import toConsole
        from freecad.Curves import mixed_curve
        from freecad.Curves import curve_to_script
        from freecad.Curves import sublink_edit
        from freecad.Curves import adjacent_faces
        from freecad.Curves import interpolate
        from freecad.Curves import comp_spring
        from freecad.Curves import ReflectLinesFP
        from freecad.Curves import segmentSurfaceFP
        #from freecad.Curves import OrientedSketchFP
        #from freecad.Curves import HQRuledSurfaceFP
        from freecad.Curves import multiLoftFP
        #from freecad.Curves import HelicalSweepFP
        #import sectionSketch
        #if hasattr(Part.BezierSurface,"extendByLength"):
            #import ExtendSurfaceFP

        stablelist.extend(["line","gordon_profile","mixed_curve","extend","join","split","Discretize",
                           "Approximate","Interpolate","ParametricBlendCurve","ParametricComb","ZebraTool",
                           "Trim","GeomInfo","extract","solid","IsoCurve","SoS","sw2r","profileSupportCmd",
                           "cos","blendSurface","pasteSVG","profile","pipeshell","gordon","segment_surface",
                           "to_console","SublinkEditor","comp_spring","ReflectLines",
                           "MultiLoft"]) # "hq_ruled_surface","HelicalSweep"])
        
        #if hasattr(Part.BezierSurface,"extendByLength"):
            #stablelist.append("extend_surface")
            
        self.appendToolbar("Curves",stablelist)
        self.appendMenu("Curves",stablelist)
        self.appendMenu("Curves",["bspline_to_console"])
        

    def Activated(self):
        """This function is executed when the workbench is activated"""
        if App.GuiUp:
            self.isObserving = True
            self.Selection = []
            self.View_Directions = []
            Gui.Selection.addObserver(self)
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        if self.isObserving:
            Gui.Selection.removeObserver(self)
            self.isObserving = False
        return

    def addSelection(self,doc,obj,sub,pnt):
        """Custom selection observer that keeps selection order."""
        #direction = None
        rot = Gui.getDocument(doc).ActiveView.getCameraOrientation()
        direction = rot.multVec(App.Vector(0,0,-1))
        self.View_Directions.append(direction)
        self.Selection.append(Gui.Selection.getSelectionObject(doc,obj,sub,pnt))

    def removeSelection(self,doc,obj,sub):
        nl = []
        cl = []
        for i in range(len(self.Selection)):
            if not self.Selection[i] == Gui.Selection.getSelectionObject(doc,obj,sub):
                nl.append(self.Selection[i])
                cl.append(self.View_Directions[i])
        self.Selection= nl

    def clearSelection(self,doc):
        self.Selection = []
        self.View_Directions = []

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen.
        recipient" will be either 'view' or 'tree'"""
        if recipient == "View":
            contextlist = ["adjacent_faces","bspline_to_console"] # list of commands
            self.appendContextMenu("Curves",contextlist)
        elif recipient == "Tree":
            contextlist = [] # list of commands
            self.appendContextMenu("Curves",contextlist)

    def GetClassName(self): 
        """This function is mandatory if this is a full python workbench"""
        return "Gui::PythonWorkbench"
        
Gui.addWorkbench(CurvesWorkbench())

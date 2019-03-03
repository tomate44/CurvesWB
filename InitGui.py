# -*- coding: utf-8 -*-

__title__ = "Curves workbench"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "FreeCAD workbench that offers a collection of tools mainly related to Nurbs curves and surfaces."

import os
import sys
import _utils

path_curvesWB = os.path.dirname(_utils.__file__)
sys.path.append(os.path.join(path_curvesWB, 'Gui'))
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')
_utils.setIconsPath(path_curvesWB_icons)
global main_CurvesWB_Icon
main_CurvesWB_Icon = os.path.join( path_curvesWB_icons , 'blendSurf.svg')

class CurvesWorkbench(Workbench):
    """FreeCAD workbench that offers a collection of tools mainly related to Nurbs curves and surfaces."""
    MenuText = "Curves"
    global main_CurvesWB_Icon
    Icon = main_CurvesWB_Icon
    
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
            import gordon_profile_FP
            stablelist = ["gordon_profile"]
        except:
            pass
        import curveExtendFP # TODO use basisSpline
        import JoinCurves
        import splitCurves # cleaned
        import Discretize # cleaned
        import approximate
        import ParametricBlendCurve # cleaned
        import ParametricComb
        import ZebraTool
        import TrimFace
        import GeomInfo
        import ExtractShapes # cleaned
        import IsoCurve
        import Sketch_On_Surface
        import Sweep2Rails
        import hooks
        import curveOnSurfaceFP
        import blendSurfaceFP
        import parametricSolid # cleaned
        import ProfileSketch
        import pasteSVG
        import pipeshellProfileFP
        import pipeshellFP
        import gordonFP
        import toConsole
        import combined_curve
        import curve_to_script
        import sublink_edit
        import adjacent_faces
        import interpolate
        import comp_spring
        import ReflectLinesFP
        #import sectionSketch
        #if hasattr(Part.BezierSurface,"extendByLength"):
            #import ExtendSurfaceFP

        stablelist.extend(["combined_projection","extend","join","split","Discretize","Approximate","Interpolate","ParametricBlendCurve","ParametricComb","ZebraTool","Trim","GeomInfo","extract","solid","IsoCurve","SoS","sw2r","profileSupportCmd","cos","blendSurface","pasteSVG","profile","pipeshell","gordon","to_console","SublinkEditor","comp_spring","ReflectLines"])
        
        #if hasattr(Part.BezierSurface,"extendByLength"):
            #stablelist.append("extend_surface")
            
        self.appendToolbar("Curves",stablelist)
        self.appendMenu("Curves",stablelist)
        self.appendMenu("Curves",["bspline_to_console"])
        

    def Activated(self):
        """This function is executed when the workbench is activated"""
        if FreeCAD.GuiUp:
            self.isObserving = True
            self.Selection = []
            FreeCADGui.Selection.addObserver(self)
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        if self.isObserving:
            FreeCADGui.Selection.removeObserver(self)
            self.isObserving = False
        return

    def addSelection(self,doc,obj,sub,pnt):
        """Custom selection observer that keeps selection order."""
        self.Selection.append(Gui.Selection.getSelectionObject(doc,obj,sub,pnt))

    def removeSelection(self,doc,obj,sub):
        nl = []
        for o in self.Selection:
            if not o == Gui.Selection.getSelectionObject(doc,obj,sub):
                nl.append(o)
        self.Selection= nl

    def clearSelection(self,doc):
        self.Selection = []

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




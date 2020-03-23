# -*- coding: utf-8 -*-

__title__ = "Curves workbench"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "FreeCAD workbench that offers a collection of tools mainly related to Nurbs curves and surfaces."

import os
import sys
import _utils
import FreeCAD

FreeCAD.addImportType("3DM (*.3dm)","import3DM")
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
            import graphics
            marker = graphics.Marker([FreeCAD.Vector()])
            import gordon_profile_FP
            stablelist = []
            FreeCAD.Console.PrintMessage("Pivy.graphics interaction library enabled\n")
        except:
            FreeCAD.Console.PrintWarning("Pivy.graphics interaction library is not available on this computer\n")

        import lineFP # cleaned
        import curveExtendFP # TODO use basisSpline
        import JoinCurves
        import splitCurves_2 # cleaned
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
        import mixed_curve
        import curve_to_script
        import sublink_edit
        import adjacent_faces
        import interpolate
        import comp_spring
        import ReflectLinesFP
        import segmentSurfaceFP
        import OrientedSketchFP
        import HQRuledSurfaceFP
        import multiLoftFP
        #import sectionSketch
        #if hasattr(Part.BezierSurface,"extendByLength"):
            #import ExtendSurfaceFP

        stablelist.extend(["line","gordon_profile","mixed_curve","extend","join","split","Discretize","Approximate","Interpolate","ParametricBlendCurve","ParametricComb","ZebraTool","Trim","GeomInfo","extract","solid","IsoCurve","SoS","sw2r","profileSupportCmd","cos","blendSurface","pasteSVG","profile","pipeshell","gordon","segment_surface","to_console","SublinkEditor","comp_spring","ReflectLines","oriented_sketch","hq_ruled_surface","MultiLoft"])
        
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
            self.View_Directions = []
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
        #direction = None
        rot = FreeCADGui.getDocument(doc).ActiveView.getCameraOrientation()
        direction = rot.multVec(FreeCAD.Vector(0,0,-1))
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




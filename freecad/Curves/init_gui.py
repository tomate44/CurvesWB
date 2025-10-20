# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import FreeCADGui as Gui
import FreeCAD as App
from . import ICONPATH


class CurvesWorkbench(Gui.Workbench):
    """FreeCAD workbench that offers a collection of tools mainly related to Nurbs curves and surfaces."""
    MenuText = "Curves"
    ToolTip = "a workbench dedicated to curves and surfaces"
    Icon = os.path.join(ICONPATH, "blendSurf.svg")
    toolbox = []

    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        # TODO changes module names to lower_with_underscore

        try:
            from . import graphics
            graphics.Marker([App.Vector()])
            # App.Console.PrintMessage("Pivy.graphics interaction library enabled\n")
        except Exception as exc:
            App.Console.PrintWarning(str(exc) + "\nPivy.graphics interaction library is not available on this computer\n")

        from . import lineFP # cleaned
        from . import gordon_profile_FP
        from . import curveExtendFP # TODO use basisSpline
        from . import JoinCurves
        from . import splitCurves_2 # cleaned
        from . import Discretize # cleaned
        from . import approximate
        from . import ParametricBlendCurve # cleaned
        from . import ParametricComb
        from . import ZebraTool
        from . import TrimFace
        from . import GeomInfo
        from . import ExtractShapes # cleaned
        from . import IsoCurve
        from . import Sketch_On_Surface
        from . import Sweep2Rails
        from . import curveOnSurfaceFP
        from . import blendSurfaceFP
        from . import parametricSolid # cleaned
        from . import ProfileSketch
        from . import pasteSVG
        from . import pipeshellProfileFP
        from . import pipeshellFP
        from . import gordonFP
        from . import toConsole
        from . import mixed_curve
        from . import curve_to_script
        from . import sublink_edit
        from . import adjacent_faces
        from . import interpolate
        from . import comp_spring
        from . import ReflectLinesFP
        from . import segmentSurfaceFP
        from . import multiLoftFP
        from . import blendSurfaceFP_new
        from . import blendSolidFP
        from . import FlattenFP
        from . import RotationSweepFP
        from . import SurfaceAnalysisFP
        from . import DraftAnalysisFP
        from . import Truncate_Extend_FP
        from . import WaterLineFP
        from . import MapOnFaceFP
        # from . import ProfileSupportFP
        # from . import Sweep2RailsFP
        # from . import HQRuledSurfaceFP
        # from . import HelicalSweepFP
        # import sectionSketch

        curvelist = ["Curves_line", "gordon_profile", "mixed_curve", "extend", "join", "split",
                     "Discretize", "Approximate", "Interpolate", "ParametricBlendCurve",
                     "ParametricComb", "cos"]

        surflist = ["ZebraTool", "Trim", "IsoCurve", "SoS", "Curves_MapOnFace", "sw2r", "profileSupportCmd",
                    "profile", "pipeshell", "gordon", "segment_surface", "comp_spring",
                    "ReflectLines", "MultiLoft", "Curves_BlendSurf2", "Curves_BlendSolid",
                    "Curves_FlattenFace", "Curves_RotationSweep", 'Curves_SurfaceAnalysis',
                    'Curves_DraftAnalysis', "Curve_TruncateExtendCmd", "Curves_WaterlineCurves"]  # ,"Curves_ProfileSupport", "Curves_Sweep2Rails"]
        misclist = ["GeomInfo", "extract", "solid", "pasteSVG", "to_console", "Curves_adjacent_faces",
                    "Curves_bspline_to_console"]

        self.appendToolbar("Curves", curvelist)
        self.appendToolbar("Surfaces", surflist)
        self.appendToolbar("Misc.", misclist)
        self.appendMenu("Curves", curvelist)
        self.appendMenu("Surfaces", surflist)
        self.appendMenu("Misc.", misclist)

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

    def addSelection(self, doc, obj, sub, pnt):
        """Custom selection observer that keeps selection order."""
        try:
            rot = Gui.getDocument(doc).ActiveView.getCameraOrientation()
            direction = rot.multVec(App.Vector(0, 0, -1))
            self.View_Directions.append(direction)
        except AttributeError:  # When ActiveView has no camera (TechDraw)
            pass
        self.Selection.append(Gui.Selection.getSelectionObject(doc, obj, sub, pnt))

    def removeSelection(self, doc, obj, sub):
        nl = []
        cl = []
        for i in range(len(self.Selection)):
            doc_match = (doc == self.Selection[i].Document.Name)
            obj_match = (obj == self.Selection[i].Object.Name)
            sub_match = (len(sub) == 0) or (sub in self.Selection[i].SubElementNames)
            if doc_match and obj_match and sub_match:
                continue
            nl.append(self.Selection[i])
            cl.append(self.View_Directions[i])
        self.Selection = nl

    def clearSelection(self, doc):
        self.Selection = []
        self.View_Directions = []

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen.
        recipient" will be either 'view' or 'tree'"""
        if recipient == "View":
            contextlist = ["Curves_adjacent_faces", "Curves_bspline_to_console"]  # list of commands
            self.appendContextMenu("Curves", contextlist)
        elif recipient == "Tree":
            contextlist = ["join", "split", "Discretize", "Approximate", "Interpolate"]  # list of commands
            self.appendContextMenu("Curves", contextlist)

    def GetClassName(self):
        """This function is mandatory if this is a full python workbench"""
        return "Gui::PythonWorkbench"


Gui.addWorkbench(CurvesWorkbench())

# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
from pivy import coin
from os import path
from freecad.Curves import ICONPATH
from freecad.Curves.Zebra_shaders.Zebra_shader import SurfaceAnalysisShader

TOOL_ICON = path.join(ICONPATH, 'zebra.svg')
# debug = _utils.debug
# debug = _utils.doNothing


props = """
App::PropertyBool
App::PropertyBoolList
App::PropertyFloat
App::PropertyFloatList
App::PropertyFloatConstraint
App::PropertyQuantity
App::PropertyQuantityConstraint
App::PropertyAngle
App::PropertyDistance
App::PropertyLength
App::PropertySpeed
App::PropertyAcceleration
App::PropertyForce
App::PropertyPressure
App::PropertyInteger
App::PropertyIntegerConstraint
App::PropertyPercent
App::PropertyEnumeration
App::PropertyIntegerList
App::PropertyIntegerSet
App::PropertyMap
App::PropertyString
App::PropertyUUID
App::PropertyFont
App::PropertyStringList
App::PropertyLink
App::PropertyLinkSub
App::PropertyLinkList
App::PropertyLinkSubList
App::PropertyMatrix
App::PropertyVector
App::PropertyVectorList
App::PropertyPlacement
App::PropertyPlacementLink
App::PropertyColor
App::PropertyColorList
App::PropertyMaterial
App::PropertyPath
App::PropertyFile
App::PropertyFileIncluded
App::PropertyPythonObject
Part::PropertyPartShape
Part::PropertyGeometryList
Part::PropertyShapeHistory
Part::PropertyFilletEdges
Sketcher::PropertyConstraintList
"""


class SurfaceAnalysisProxyFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList", "Sources",
                        "Group", "Tooltip")
        obj.Proxy = self

    def execute(self, obj):
        return False  # obj.Shape = None

    def onChanged(self, obj, prop):
        return False


class SurfaceAnalysisProxyVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object
        self.Active = False
        self.rootnodes = []
        self.surf_analyze = SurfaceAnalysisShader(1, 0)
        self.load_shader()

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def updateData(self, fp, prop):
        if prop == "Sources":
            self.remove_shader()
            self.load_shader()

    def onChanged(self, viewobj, prop):
        if prop == "Visibility":
            if viewobj.Visibility and not self.Active:
                self.load_shader()
            if (not viewobj.Visibility) and self.Active:
                self.remove_shader()

    def onDelete(self, viewobj, sub):
        self.remove_shader()
        return True

    def load_shader(self):
        if self.Active:
            return
        if len(self.Object.Sources) == 0:
            view = FreeCADGui.ActiveDocument.ActiveView
            self.rootnodes = [view.getViewer().getSceneGraph(), ]
        else:
            self.rootnodes = [o.ViewObject.RootNode for o in self.Object.Sources]
        for rn in self.rootnodes:
            rn.insertChild(self.surf_analyze.Shader, 0)
        self.Active = True
        FreeCADGui.Selection.addObserver(self)

    def remove_shader(self):
        if not self.Active:
            return
        for rn in self.rootnodes:
            rn.removeChild(self.surf_analyze.Shader)
        self.Active = False
        FreeCADGui.Selection.removeObserver(self)

    def addSelection(self, doc, obj, sub, pnt):  # Selection
        # FreeCAD.Console.PrintMessage("addSelection %s %s\n" % (obj, str(sub)))
        names = [o.Name for o in self.Object.Sources]
        if self.Active and obj in names:
            if "Face" in sub:
                o = FreeCAD.getDocument(doc).getObject(obj)
                surf = o.Shape.getElement(sub).Surface
                u, v = surf.parameter(FreeCAD.Vector(pnt))
                n = surf.normal(u, v)
                direc = FreeCAD.Vector(self.surf_analyze.AnalysisDirection)
                angle = n.getAngle(direc)
                FreeCAD.Console.PrintMessage(f"{obj}, {sub}, {pnt}, Angle: {angle} to {direc}\n")


    def removeSelection(self, doc, obj, sub):  # Delete selected object
        # FreeCAD.Console.PrintMessage("removeSelection %s %s\n" % (obj, str(sub)))
        pass

    def setPreselection(self, doc, obj, sub):
        pass

    def clearSelection(self, doc):  # If screen is clicked, delete selection
        # FreeCAD.Console.PrintMessage("clearSelection\n")
        pass

class SurfaceAnalysisCommand:
    """Create a ... feature"""
    def makeFeature(self, sel=[]):
        fp = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "SurfaceAnalysis")
        SurfaceAnalysisProxyFP(fp)
        SurfaceAnalysisProxyVP(fp.ViewObject)
        fp.Sources = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        self.makeFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curves_SurfaceAnalysis', SurfaceAnalysisCommand())

# -*- coding: utf-8 -*-

__title__ = 'Draft Analysis'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Draft Analysis for injection molding'

# import os
import FreeCAD
import FreeCADGui
# from pivy import coin
from os import path
from math import pi
from freecad.Curves import ICONPATH
from freecad.Curves.DraftAnalysis_shaders.DraftAnalysis_shader import DraftAnalysisShader

TOOL_ICON = path.join(ICONPATH, 'draft_analysis.svg')
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


class DraftAnalysisProxyFP:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLink", "Source", "Base", "Object on which the analysis is performed")
        obj.Proxy = self

    def execute(self, obj):
        return False  # obj.Shape = None

    def onChanged(self, obj, prop):
        return False


class DraftAnalysisProxyVP:
    def __init__(self, viewobj):
        viewobj.addProperty("App::PropertyVector", "Direction",
                            "AnalysisOptions", "Pull direction")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftAngle1",
                            "AnalysisOptions", "Positive draft angle")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftAngle2",
                            "AnalysisOptions", "Negative draft angle")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftTol1",
                            "AnalysisOptions", "Positive draft tolerance")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftTol2",
                            "AnalysisOptions", "Negative draft tolerance")
        viewobj.addProperty("App::PropertyColor", "ColorInDraft1",
                            "Colors", "Color of the positive in-draft area")
        viewobj.addProperty("App::PropertyColor", "ColorInDraft2",
                            "Colors", "Color of the negative in-draft area")
        viewobj.addProperty("App::PropertyColor", "ColorOutOfDraft",
                            "Colors", "Color of the out-of-draft area")
        viewobj.addProperty("App::PropertyColor", "ColorTolDraft1",
                            "Colors", "Color of the positive tolerance area")
        viewobj.addProperty("App::PropertyColor", "ColorTolDraft2",
                            "Colors", "Color of the negative tolerance area")
        viewobj.addProperty("App::PropertyFloatConstraint", "Opacity",
                            "AnalysisOptions", "Opacity of the analysis overlay")

        viewobj.DraftAngle1 = (1.0, 0.0, 90.0, 0.1)
        viewobj.DraftAngle2 = (1.0, 0.0, 90.0, 0.1)
        viewobj.DraftTol1 = (0.05, 0.0, 90.0, 0.05)
        viewobj.DraftTol2 = (0.05, 0.0, 90.0, 0.05)
        viewobj.ColorInDraft1 = (0.0, 0.0, 1.0)
        viewobj.ColorInDraft2 = (0.0, 1.0, 0.0)
        viewobj.ColorOutOfDraft = (1.0, 0.0, 0.0)
        viewobj.ColorTolDraft1 = (0.0, 1.0, 1.0)
        viewobj.ColorTolDraft2 = (1.0, 1.0, 0.0)
        viewobj.Opacity = (0.8, 0.0, 1.0, 0.05)
        viewobj.Proxy = self
        viewobj.Direction = (0, 0, 1)

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object
        self.Active = False
        self.rootnode = None
        self.draft_analyzer = DraftAnalysisShader()
        self.load_shader()

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def updateData(self, fp, prop):
        if prop == "Source":
            self.remove_shader()
            self.load_shader()

    def onChanged(self, viewobj, prop):
        if prop == "Visibility":
            if viewobj.Visibility and not self.Active:
                self.load_shader()
            if (not viewobj.Visibility) and self.Active:
                self.remove_shader()
        if prop == "Direction":
            pl = self.Object.Source.Placement
            inv = pl.inverse()
            d = inv.multVec(viewobj.Direction)
            self.draft_analyzer.AnalysisDirection = d
            print(d)
        if hasattr(self.draft_analyzer, prop):
            setattr(self.draft_analyzer, prop, getattr(viewobj, prop))

    def onDelete(self, viewobj, sub):
        self.remove_shader()
        return True

    def load_shader(self):
        o = self.Object.Source
        if self.Active or (o is None):
            return
        sw = o.ViewObject.SwitchNode
        if sw.getNumChildren() == 4:  # Std object with 4 DisplayModes
            self.rootnode = sw.getChild(1)  # This should be the Shaded node
        else:
            self.rootnode = o.ViewObject.RootNode
        self.rootnode.insertChild(self.draft_analyzer.Shader, 0)
        self.Active = True
        FreeCADGui.Selection.addObserver(self)

    def remove_shader(self):
        if not self.Active:
            return
        self.rootnode.removeChild(self.draft_analyzer.Shader)
        self.Active = False
        FreeCADGui.Selection.removeObserver(self)

    def addSelection(self, doc, obj, sub, pnt):  # Selection
        # FreeCAD.Console.PrintMessage("addSelection %s %s\n" % (obj, str(sub)))
        o = self.Object.Source
        if self.Active and (obj == o.Name):
            if "Face" in sub:
                o = FreeCAD.getDocument(doc).getObject(obj)
                surf = o.Shape.getElement(sub).Surface
                u, v = surf.parameter(FreeCAD.Vector(pnt))
                n = surf.normal(u, v)
                direc = FreeCAD.Vector(self.draft_analyzer.Direction)
                angle = n.getAngle(direc) * 180 / pi
                FreeCAD.Console.PrintMessage(f"{obj}.{sub} Normal Angle: {angle}\n")
                # da = self.Object.ViewObject.DraftAngles
                # da.insert(0, angle)
                # self.Object.ViewObject.DraftAngles = da[:16]

    def removeSelection(self, doc, obj, sub):  # Delete selected object
        # FreeCAD.Console.PrintMessage("removeSelection %s %s\n" % (obj, str(sub)))
        pass

    def setPreselection(self, doc, obj, sub):
        pass

    def clearSelection(self, doc):  # If screen is clicked, delete selection
        # FreeCAD.Console.PrintMessage("clearSelection\n")
        pass  # self.Object.ViewObject.DraftAngles = []

class DraftAnalysisCommand:
    def makeFeature(self, sel):
        fp = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "DraftAnalysis")
        DraftAnalysisProxyFP(fp)
        DraftAnalysisProxyVP(fp.ViewObject)
        fp.Source = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        for so in sel:
            self.makeFeature(so)

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curves_DraftAnalysis', DraftAnalysisCommand())

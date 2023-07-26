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
        obj.addProperty("App::PropertyLink", "Source",
                        "AnalysisOptions", "Object on which the analysis is performed")
        obj.addProperty("App::PropertyVector", "Direction",
                        "AnalysisOptions", "Pull direction")
        obj.addProperty("App::PropertyFloatConstraint", "DraftAngle1",
                        "AnalysisOptions", "Positive draft angle")
        obj.addProperty("App::PropertyFloatConstraint", "DraftAngle2",
                        "AnalysisOptions", "Negative draft angle")
        obj.addProperty("App::PropertyFloatConstraint", "DraftTol1",
                        "AnalysisOptions", "Positive draft tolerance")
        obj.addProperty("App::PropertyFloatConstraint", "DraftTol2",
                        "AnalysisOptions", "Negative draft tolerance")
        obj.DraftAngle1 = (1.0, 0.0, 90.0, 0.1)
        obj.DraftAngle2 = (1.0, 0.0, 90.0, 0.1)
        obj.DraftTol1 = (0.05, 0.0, 90.0, 0.05)
        obj.DraftTol2 = (0.05, 0.0, 90.0, 0.05)
        obj.Direction = (0, 0, 1)
        obj.Proxy = self

    def execute(self, obj):
        sh = obj.Source.Shape
        pl = obj.Source.Placement
        nsh = sh.transformGeometry(pl.Matrix)
        nsh.Placement = FreeCAD.Placement()
        obj.Shape = nsh

    def onChanged(self, obj, prop):
        return False


class DraftAnalysisProxyVP:
    def __init__(self, viewobj):
        viewobj.addProperty("App::PropertyColor", "ColorInDraft1",
                            "Colors1PositiveDraft", "Color of the positive in-draft area")
        viewobj.addProperty("App::PropertyColor", "ColorInTolerance1",
                            "Colors1PositiveDraft", "Color of the positive tolerance area")
        viewobj.addProperty("App::PropertyColor", "ColorOutOfDraft1",
                            "Colors1PositiveDraft", "Color of the positive out-of-draft area")
        viewobj.addProperty("App::PropertyColor", "ColorInDraft2",
                            "Colors2NegativeDraft", "Color of the negative in-draft area")
        viewobj.addProperty("App::PropertyColor", "ColorInTolerance2",
                            "Colors2NegativeDraft", "Color of the negative tolerance area")
        viewobj.addProperty("App::PropertyColor", "ColorOutOfDraft2",
                            "Colors2NegativeDraft", "Color of the negative out-of-draft area")
        viewobj.addProperty("App::PropertyFloatConstraint", "Shading",
                            "AnalysisOptions", "Amount of shading on the analysis overlay")

        viewobj.ColorInDraft1 = (0.0, 0.0, 1.0)
        viewobj.ColorInDraft2 = (0.0, 1.0, 0.0)
        viewobj.ColorOutOfDraft1 = (1.0, 0.0, 0.0)
        viewobj.ColorOutOfDraft2 = (1.0, 0.0, 1.0)
        viewobj.ColorInTolerance1 = (0.0, 1.0, 1.0)
        viewobj.ColorInTolerance2 = (1.0, 1.0, 0.0)
        viewobj.Shading = (0.2, 0.0, 1.0, 0.05)
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def claimChildren(self):
        return [self.Object.Source, ]

    def onDelete(self, feature, subelements):
        self.remove_shader()
        if not self.Object.Source.ViewObject.Visibility:
            self.Object.Source.ViewObject.Visibility = True
        return True

    def attach(self, viewobj):
        self.Object = viewobj.Object
        self.Active = False
        self.rootnode = None
        self.draft_analyzer = DraftAnalysisShader()
        self.load_shader(viewobj)

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def updateData(self, fp, prop):
        if prop == "Source":
            self.remove_shader()
            self.load_shader(fp.ViewObject)
        elif prop == "Direction" and (fp.Source is not None):
            self.draft_analyzer.Direction = fp.Direction
        elif hasattr(self.draft_analyzer, prop):
            setattr(self.draft_analyzer, prop, getattr(fp, prop))

    def onChanged(self, viewobj, prop):
        # if prop == "Visibility":
        #     if viewobj.Visibility and not self.Active:
        #         self.load_shader(viewobj)
        #     if (not viewobj.Visibility) and self.Active:
        #         self.remove_shader()
        if hasattr(self.draft_analyzer, prop):
            setattr(self.draft_analyzer, prop, getattr(viewobj, prop))

    def load_shader(self, vo):
        if self.Active or (self.Object.Source is None):
            return
        sw = vo.SwitchNode
        if sw.getNumChildren() == 4:  # Std object with 4 DisplayModes
            self.rootnode = sw.getChild(1)  # This should be the Shaded node
        else:
            self.rootnode = vo.RootNode
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
        o = self.Object
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
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "DraftAnalysis")
        DraftAnalysisProxyFP(fp)
        DraftAnalysisProxyVP(fp.ViewObject)
        fp.Source = sel
        sel.ViewObject.Visibility = False
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

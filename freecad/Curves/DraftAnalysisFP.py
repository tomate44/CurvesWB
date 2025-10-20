# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Draft Analysis'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = '''Create a colored overlay on an object to visualize draft angles.
Tool options are in the View tab.
Mouse clics in the colored areas print measured draft angle in the Report View.'''

import FreeCAD
import FreeCADGui
import Part
from os import path
from math import pi
from freecad.Curves import ICONPATH
from freecad.Curves.DraftAnalysis_shaders.DraftAnalysis_shader import DraftAnalysisShader

TOOL_ICON = path.join(ICONPATH, 'draft_analysis.svg')


class DraftAnalysisProxyFP:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLink", "Source",
                        "AnalysisOptions", "Object on which the analysis is performed")
        obj.Proxy = self

    def execute(self, obj):
        if hasattr(obj.Source, "Shape"):
            sh = obj.Source.Shape.copy()
            pl = obj.Source.Placement
            sh.transformShape(pl.Matrix, True, False)
            sh.Placement = FreeCAD.Placement()
            obj.Shape = sh
        else:
            obj.Shape = Part.Shape()

    def onChanged(self, obj, prop):
        if prop == "Source" and (obj.Source is not None):
            obj.Label = f"DraftAnalysis - {obj.Source.Label}"
            obj.Source.ViewObject.Visibility = False
            obj.recompute()


class DraftAnalysisProxyVP:
    def __init__(self, viewobj):
        viewobj.addProperty("App::PropertyVector", "Direction",
                            "AnalysisOptions", "Anaysis direction")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftAngle1",
                            "AnalysisOptions", "Positive draft angle")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftAngle2",
                            "AnalysisOptions", "Negative draft angle")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftTol1",
                            "AnalysisOptions", "Positive draft tolerance")
        viewobj.addProperty("App::PropertyFloatConstraint", "DraftTol2",
                            "AnalysisOptions", "Negative draft tolerance")
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
        viewobj.DraftAngle1 = (1.0, 0.0, 90.0, 0.1)
        viewobj.DraftAngle2 = (1.0, 0.0, 90.0, 0.1)
        viewobj.DraftTol1 = (0.05, 0.0, 90.0, 0.05)
        viewobj.DraftTol2 = (0.05, 0.0, 90.0, 0.05)
        viewobj.Direction = (0, 0, 1)
        viewobj.ColorInDraft1 = (0.0, 0.0, 1.0)
        viewobj.ColorInDraft2 = (0.0, 1.0, 0.0)
        viewobj.ColorOutOfDraft1 = (1.0, 0.0, 0.0)
        viewobj.ColorOutOfDraft2 = (1.0, 0.0, 0.0)
        viewobj.ColorInTolerance1 = (0.0, 1.0, 1.0)
        viewobj.ColorInTolerance2 = (1.0, 1.0, 0.0)
        viewobj.Shading = (0.2, 0.0, 1.0, 0.05)
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def claimChildren(self):
        return []  # [self.Object.Source, ]

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

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    def updateData(self, fp, prop):
        if prop == "Source":
            self.remove_shader()
            self.load_shader(fp.ViewObject)

    def onChanged(self, viewobj, prop):
        mod_prop = "badname"
        if prop == "Direction" and (self.Object.Source is not None):
            self.draft_analyzer.Direction = viewobj.Direction
        elif prop == "Shading":
            self.draft_analyzer.Shading = viewobj.Shading
        elif prop[-1] == "1":
            mod_prop = prop[:-1] + "Pos"
        elif prop[-1] == "2":
            mod_prop = prop[:-1] + "Neg"
        # print(f"setting {prop} - {mod_prop}")
        if hasattr(self.draft_analyzer, mod_prop):
            if "Color" in mod_prop:
                setattr(self.draft_analyzer, mod_prop, getattr(viewobj, prop)[:3])
            else:
                setattr(self.draft_analyzer, mod_prop, getattr(viewobj, prop))

    def load_shader(self, vo):
        if self.Active or (self.Object.Source is None):
            return
        sw = vo.SwitchNode
        if sw.getNumChildren() == 4:  # Std object with 4 DisplayModes
            self.rootnode = sw.getChild(1)  # This should be the "Shaded" node
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
                FreeCAD.Console.PrintMessage(f"{obj}.{sub} Normal={angle:3.2f}° Draft={(90-angle):3.2f}°\n")


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

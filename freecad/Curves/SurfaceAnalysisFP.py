# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

# import os
import FreeCAD
import FreeCADGui
# from pivy import coin
from os import path
from math import pi
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
        viewobj.addProperty("App::PropertyVector", "Direction",
                            "AnalysisMode", "Analysis Direction")
        viewobj.addProperty("App::PropertyEnumeration", "Mode",
                            "AnalysisMode", "Analysis Mode")
        viewobj.addProperty("App::PropertyBool", "Fixed",
                            "AnalysisMode", "Fix analysis direction to global coordinate system")
        viewobj.addProperty("App::PropertyInteger", "StripesNumber",
                            "AnalysisOptions", "Number of stripes (Zebra, Rainbow)")
        viewobj.addProperty("App::PropertyFloatConstraint", "StripesRatio",
                            "AnalysisOptions", "Relative width of stripes (Zebra)")
        viewobj.addProperty("App::PropertyColor", "Color1",
                            "AnalysisOptions", "First color (Zebra, Rainbow, Isophote)")
        viewobj.addProperty("App::PropertyColor", "Color2",
                            "AnalysisOptions", "Second color (Zebra, Rainbow, Isophote)")
        viewobj.addProperty("App::PropertyFloatConstraint", "RainbowAngle1",
                            "AnalysisOptions", "Start angle of the rainbow")
        viewobj.addProperty("App::PropertyFloatConstraint", "RainbowAngle2",
                            "AnalysisOptions", "End angle of the rainbow")
        viewobj.addProperty("App::PropertyFloatList", "IsoAngles",
                            "AnalysisOptions", "Angles of isophote curves")
        viewobj.addProperty("App::PropertyFloat", "IsoTolerance",
                            "AnalysisOptions", "Angular tolerance of isophote curves")
        viewobj.addProperty("App::PropertyFloatConstraint", "Shading",
                            "AnalysisMode", "Amount of shading on the analysis overlay")
        viewobj.Direction = (1, 0, 0)
        viewobj.Mode = ["Zebra", "Rainbow", "Isophote"]
        viewobj.Mode = "Zebra"
        viewobj.Fixed = False
        viewobj.Proxy = self
        viewobj.StripesNumber = 12
        viewobj.StripesRatio = (0.5, 0.0, 1.0, 0.05)
        viewobj.Color1 = (1.0, 1.0, 1.0)
        viewobj.Color2 = (0.0, 0.0, 0.0)
        viewobj.RainbowAngle1 = (0.0, 0.0, 180.0, 5.0)
        viewobj.RainbowAngle2 = (180.0, 0.0, 180.0, 5.0)
        viewobj.IsoAngles = [45.0, 90.0, 135.0]
        viewobj.IsoTolerance = 0.5
        viewobj.Shading = (0.2, 0.0, 1.0, 0.05)

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object
        self.Active = False
        self.rootnodes = []
        self.surf_analyze = SurfaceAnalysisShader(0, 0)
        self.load_shader()

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
        if prop == "Sources":
            self.remove_shader()
            self.load_shader()

    def onChanged(self, viewobj, prop):
        if prop == "Visibility":
            if viewobj.Visibility and not self.Active:
                self.load_shader()
            if (not viewobj.Visibility) and self.Active:
                self.remove_shader()
        if prop == "Direction":
            self.surf_analyze.AnalysisDirection = viewobj.Direction
        if prop == "Mode":
            modes = {"Zebra": 0, "Rainbow": 1, "Isophote": 2}
            self.surf_analyze.Mode = modes[viewobj.Mode]
        if prop == "Fixed":
            if viewobj.Fixed:
                self.surf_analyze.Fixed = 1
            else:
                self.surf_analyze.Fixed = 0
        if prop == "StripesNumber":
            self.surf_analyze.StripesNumber = viewobj.StripesNumber
        if prop == "StripesRatio":
            self.surf_analyze.StripesRatio = viewobj.StripesRatio
        if prop == "Color1":
            self.surf_analyze.Color1 = viewobj.Color1[:3]
        if prop == "Color2":
            self.surf_analyze.Color2 = viewobj.Color2[:3]
        if prop == "RainbowAngle1":
            self.surf_analyze.RainbowAngle1 = viewobj.RainbowAngle1
        if prop == "RainbowAngle2":
            self.surf_analyze.RainbowAngle2 = viewobj.RainbowAngle2
        if prop == "IsoAngles":
            self.surf_analyze.CurvesAngles = viewobj.IsoAngles
        if prop == "IsoTolerance":
            self.surf_analyze.CurvesTolerance = viewobj.IsoTolerance
        if prop == "Shading":
            self.surf_analyze.Shading = viewobj.Shading

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
        if self.Object.ViewObject.Fixed and self.Active and obj in names:
            if "Face" in sub:
                o = FreeCAD.getDocument(doc).getObject(obj)
                surf = o.Shape.getElement(sub).Surface
                u, v = surf.parameter(FreeCAD.Vector(pnt))
                n = surf.normal(u, v)
                direc = FreeCAD.Vector(self.surf_analyze.AnalysisDirection)
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

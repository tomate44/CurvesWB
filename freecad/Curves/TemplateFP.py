# -*- coding: utf-8 -*-

__title__ = ""
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """doc"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/icon.svg'
#debug = _utils.debug
#debug = _utils.doNothing

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

class TemplateFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList", "Sources", "Gordon", "Curve network")
        obj.addProperty("App::PropertyFloat", "Tol3D", "Gordon", "3D tolerance").Tol3D = 1e-5
        obj.addProperty("App::PropertyFloat", "Tol2D", "Gordon", "Parametric tolerance").Tol2D = 1e-8
        obj.Proxy = self

    def execute(self, obj):
        obj.Shape = None

    def onChanged(self, obj, prop):
        return(False)

class TemplateVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class ToolCommand:
    """Creates a ..."""
    def makeFeature(self):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","")
        TemplateFP(fp)
        TemplateVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('tool_name', ToolCommand())

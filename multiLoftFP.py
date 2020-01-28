# -*- coding: utf-8 -*-

__title__ = "MultiLoft"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Loft profile objects made of multiple faces in parallel"""


import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/multiLoft.svg'
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

class MultiLoftFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList", "Sources", "Multiloft", "Objects to loft")
        obj.addProperty("App::PropertyBool", "Ruled", "Multiloft", "Ruled Loft").Ruled = False
        obj.addProperty("App::PropertyBool", "Closed", "Multiloft", "Close loft").Closed = False
        obj.addProperty("App::PropertyInteger", "MaxDegree", "Multiloft", "Max Bspline degree").MaxDegree = 5
        obj.Proxy = self

    def execute(self, obj):
        if not hasattr(obj, "Sources"):
            return
        solids = []
        num_faces = len(obj.Sources[0].Shape.Faces)
        for i in range(num_faces):
            faces = [obj.Sources[0].Shape.Faces[i], obj.Sources[-1].Shape.Faces[i]]
            loft = []
            num_wires = len(faces[0].Wires)
            for j in range(num_wires):
                wires = []
                for o in obj.Sources:
                    wires.append(o.Shape.Faces[i].Wires[j])
                loft = Part.makeLoft(wires, False, obj.Ruled, obj.Closed, obj.MaxDegree)
                faces.extend(loft.Faces)
            shell = Part.Shell(faces)
            solids.append(Part.Solid(shell))
        obj.Shape = Part.Compound(solids)

    def onChanged(self, obj, prop):
        if prop == "MaxDegree":
            if obj.MaxDegree < 1:
                obj.MaxDegree = 1
            if obj.MaxDegree > 25:
                obj.MaxDegree = 25
        if prop in ["Ruled","Closed","MaxDegree"]:
            self.execute(obj)
        return

class MultiLoftVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        return self.Object.Sources

    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        for c in self.Object.Sources:
            if hasattr(c,"ViewObject"):
                c.ViewObject.Visibility = True
        return True

class MultiLoftCommand:
    """Creates a MultiLoft"""
    def makeFeature(self, sel):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","MultiLoft")
        MultiLoftFP(fp)
        MultiLoftVP(fp.ViewObject)
        fp.Sources = sel
        for c in sel:
            if hasattr(c,"ViewObject"):
                c.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('MultiLoft', MultiLoftCommand())

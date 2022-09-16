# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
# import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')
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


class RotationSweep:
    def __init__(self, path, profiles, closed=False):
        self.path = path
        self.profiles = profiles
        self.closed = closed

    def getCenter(self):
        if len(self.profiles) == 1:
            dist, pts, info = self.path.toShape.distToShape(self.profiles[0].toShape())
            par = self.profiles[0].parameter(pts[0][1])
            if abs(par - self.profiles[0].FirstParameter) > abs(par - self.profiles[0].LastParameter):
                return self.profiles[0].value(self.profiles[0].FirstParameter)
            else:
                return self.profiles[0].value(self.profiles[0].LastParameter)

        center = FreeCAD.Vector()
        for p in self.profiles[1:]:
            dist, pts, info = p.toShape.distToShape(self.profiles[0].toShape())
            center += pts[0][1]
        return center / (len(self.profiles) - 1)

    def loftProfiles(self):
        wl = [Part.Wire([c.toShape()]) for c in self.profiles]
        loft = Part.makeLoft(wl, False, False, self.closed, 3)
        return loft.Face1.Surface

    def ruledToCenter(self):




class RotsweepProxyFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Profiles",
                        "InputShapes", "The list of profiles to sweep")
        obj.addProperty("App::PropertyLinkSub", "Path",
                        "InputShapes", "The sweep path")
        obj.addProperty("App::PropertyBool", "Closed",
                        "Settings", "Close the sweep shape")
        obj.Proxy = self

    def getCurve(self, prop):
        edges = []
        po, psn = prop
        for sn in psn:
            edges.append(po.getSubObject(sn))
        if len(edges) == 0:
            edges = po.Shape.Edges
        if len(edges) == 1:
            return edges[0].Curve
        soed = Part.SortEdges(edges)
        w = Part.Wire(soed[0])
        return w.approximate(1e-10, 1e-7, 10000, 3)

    def execute(self, obj):
        path = self.getCurve(obj.Path)[0]
        profiles = [self.getCurve(l) for l in obj.Profiles]
        rs = RotationSweep(path, profiles, obj.Closed)
        obj.Shape = rs.Face

    def onChanged(self, obj, prop):
        return False


class RotsweepProxyVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None


class RotsweepFPCommand:
    """Create a ... feature"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Rotation Sweep")
        RotsweepProxyFP(fp)
        fp.Path = sel[0]
        fp.Profiles = sel[1:]
        RotsweepProxyVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        links = []
        sel = FreeCADGui.Selection.getSelectionEx('',0)
        for so in sel:
            if so.HasSubObjects:
                links.append((so.Object, so.SubElementNames))
            else:
                links.append((so.Object, [""]))
        if len(links) < 2:
            FreeCAD.Console.PrintError("Select Path and Profiles first !\n")
        else:
            self.makeFeature(links)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('tool_name', ToolCommand())

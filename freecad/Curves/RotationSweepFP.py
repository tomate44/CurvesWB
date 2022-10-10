# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import SweepPath
from freecad.Curves import ICONPATH

err = FreeCAD.Console.PrintError
warn = FreeCAD.Console.PrintWarning
message = FreeCAD.Console.PrintMessage
TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')
# debug = _utils.debug
# debug = _utils.doNothing


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
        obj.addProperty("App::PropertyBool", "AddProfiles",
                        "Settings", "Add profiles to the sweep shape")
        obj.addProperty("App::PropertyInteger", "AddSamples",
                        "Settings", "Number of additional profiles")
        obj.setEditorMode("AddProfiles", 2)
        obj.Proxy = self

    def getCurve(self, lo):
        edges = []
        po, psn = lo
        # print(psn)
        for sn in psn:
            if "Edge" in sn:
                edges.append(po.getSubObject(sn))
        if len(edges) == 0:
            edges = po.Shape.Edges
        bsedges = []
        for e in edges:
            if isinstance(e.Curve, Part.BSplineCurve):
                bsedges.append(e)
            else:
                c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
                bsedges.append(c.toShape())
        return bsedges

    def getCurves(self, prop):
        edges = []
        for p in prop:
            edges.extend(self.getCurve(p))
        return edges

    def execute(self, obj):
        path = self.getCurve(obj.Path)[0]
        profiles = self.getCurves(obj.Profiles)
        rs = SweepPath.RotationSweep(path, profiles, obj.Closed)
        rs.insert_profiles(obj.AddSamples)
        if obj.AddProfiles:
            obj.Shape = Part.Compound([rs.Face] + rs.profiles)
        else:
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
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                              "Rotation Sweep")
        RotsweepProxyFP(fp)
        fp.Path = sel[0]
        fp.Profiles = sel[1:]
        RotsweepProxyVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        links = []
        sel = FreeCADGui.Selection.getSelectionEx('', 0)
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


FreeCADGui.addCommand('Curves_RotationSweep', RotsweepFPCommand())

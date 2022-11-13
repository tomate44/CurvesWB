# -*- coding: utf-8 -*-

__title__ = 'Rotation Sweep'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Sweep some profiles along a path, and around a point'
__usage__ = """Select a sweep path and some profiles in the 3D View.
If TrimPath is False, the Sweep surface will be extrapolated to fit the whole path."""

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import SweepPath
from freecad.Curves import ICONPATH

err = FreeCAD.Console.PrintError
warn = FreeCAD.Console.PrintWarning
message = FreeCAD.Console.PrintMessage
TOOL_ICON = os.path.join(ICONPATH, 'sweep_around.svg')
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
        obj.addProperty("App::PropertyLinkSub", "FaceSupport",
                        "InputShapes", "Face support of the sweep path")
        obj.addProperty("App::PropertyBool", "TrimPath",
                        "Settings", "Trim the sweep shape").TrimPath = True
        obj.addProperty("App::PropertyBool", "AddProfiles",
                        "Settings", "Add profiles to the sweep shape")
        obj.addProperty("App::PropertyInteger", "AddSamples",
                        "Settings", "Number of additional profiles")
        obj.addProperty("App::PropertyBool", "Stretch",
                        "Settings", "Stretch or scale additional profiles")
        obj.setEditorMode("AddProfiles", 2)
        # obj.setEditorMode("AddSamples", 2)
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
        fc = None
        if obj.FaceSupport is not None:
            fc = obj.FaceSupport[0].getSubObject(obj.FaceSupport[1])[0]
            FreeCAD.Console.PrintMessage(fc)
        rs = SweepPath.RotationSweep(path, profiles)  # , obj.TrimPath, fc)
        # rs.stretch = obj.Stretch
        # rs.insert_profiles(obj.AddSamples)
        if obj.AddProfiles:
            shapes = [p.Shape for p in rs.profiles] + [rs.Face]
            if rs.interpolator is not None:
                shapes.append(rs.interpolator.localLoft.toShape())
            comp = Part.Compound(shapes)
            obj.Shape = comp
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
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('Curves_RotationSweep', RotsweepFPCommand())

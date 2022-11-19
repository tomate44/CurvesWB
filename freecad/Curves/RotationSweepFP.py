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
from importlib import reload
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
                        "ExtraProfiles", "Face support of the sweep path")
        obj.addProperty("App::PropertyBool", "TrimPath",
                        "Settings", "Trim the sweep shape").TrimPath = True
        obj.addProperty("App::PropertyBool", "ViewProfiles",
                        "Settings", "Add profiles to the sweep shape")
        obj.addProperty("App::PropertyInteger", "ExtraProfiles",
                        "ExtraProfiles", "Number of extra profiles")
        obj.addProperty("App::PropertyBool", "SmoothTop",
                        "Settings", "Build a smooth top with extra profiles")
        obj.setEditorMode("ViewProfiles", 2)
        # obj.setEditorMode("ExtraProfiles", 2)
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
        reload(SweepPath)
        rs = SweepPath.RotationSweep(path, profiles, obj.TrimPath)
        rs.set_curves()
        inter = None
        if obj.ExtraProfiles or (not obj.TrimPath) or (len(profiles) < 2) or obj.SmoothTop:
            inter = SweepPath.SweepAroundInterpolator(rs)
            inter.Extend = (not obj.TrimPath) or (len(profiles) < 2)
            inter.NumExtra = obj.ExtraProfiles
            if obj.SmoothTop:
                inter.setSmoothTop()
            if obj.FaceSupport is not None:
                fs = obj.FaceSupport[0].getSubObject(obj.FaceSupport[1])[0]
                # FreeCAD.Console.PrintMessage(fs)
                inter.FaceSupport = fs
            inter.compute()
        f = rs.Face
        if obj.SmoothTop:
            s = f.Surface
            pl = Part.Plane(s.value(0, 0), inter.TopNormal)
            for i, pt in enumerate(s.getPoles()[1]):
                npt = pl.projectPoint(pt)
                s.setPole(2, i + 1, npt)
            f = s.toShape()
        if obj.ViewProfiles:
            shl = [f] + [p.Shape for p in rs.Profiles]
            obj.Shape = Part.Compound(shl)
        else:
            obj.Shape = f

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return
        if prop == "Profiles":
            edges = self.getCurves(obj.Profiles)
            if len(edges) == 1:
                obj.ExtraProfiles = 1


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

# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Segment surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Segment a surface on isocurves"""
__usage__ = """Select a face in the 3D view and activate tool.
The face will be converted to a BSpline surface.
In Auto mode, the surface will be segmented along isocurves of highest multiplicity.
In Custom mode, it will be segmented along isocurves of specified parameters.
These parameters can be provided by an external object that have a NormalizedParameters property,
like the Discretize, or the SplitCurve tools."""

import os

import FreeCAD
import FreeCADGui
import Part
from . import ICONPATH
from .nurbs_tools import KnotVector

TOOL_ICON = os.path.join(ICONPATH, 'segment_surface.svg')


class SegmentSurface:
    """SegmentSurface feature proxy"""

    def __init__(self, obj, face):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Source", "Base", "Initial Face").Source = face
        obj.addProperty("App::PropertyEnumeration", "Option", "Base", "Option list").Option = ["Auto", "Custom"]
        obj.addProperty("App::PropertyEnumeration", "Direction", "OptionAuto", "Segmenting direction").Direction = ["U", "V", "Both"]
        obj.addProperty("App::PropertyFloatList", "KnotsU", "UDirection", "Splitting parameters in U direction")
        obj.addProperty("App::PropertyFloatList", "KnotsV", "VDirection", "Splitting parameters in V direction")
        obj.addProperty("App::PropertyInteger", "NumberU", "UDirection", "Split the U parameter range in the given number of segments").NumberU = 2
        obj.addProperty("App::PropertyInteger", "NumberV", "VDirection", "Split the V parameter range in the given number of segments").NumberV = 2
        obj.addProperty("App::PropertyLink", "KnotsUProvider", "UDirection", "Object generating normalized parameters in U direction")
        obj.addProperty("App::PropertyLink", "KnotsVProvider", "VDirection", "Object generating normalized parameters in V direction")
        obj.Proxy = self
        obj.Option = "Custom"

    def get_intervals(self, knots, mults):
        ml = list(set(mults))
        ml.sort()
        if len(ml) == 1:
            return mults
        target = ml[-2]
        cutknots = list()
        for i, m in enumerate(mults):
            if m >= target:
                cutknots.append(knots[i])
        return cutknots

    def get_normalized_params(self, obj, prop):
        if not hasattr(obj, prop):
            return False
        lnk = obj.getPropertyByName(prop)
        if not hasattr(lnk, 'NormalizedParameters'):
            return False
        params = lnk.getPropertyByName('NormalizedParameters')
        return params

    def execute(self, obj):
        f = obj.Source[0].getSubObject(obj.Source[1][0])
        # mat = obj.Source[0].Placement.Matrix
        u0, u1, v0, v1 = f.ParameterRange
        # print("Face parameters : {}".format(f.ParameterRange))
        trim = Part.RectangularTrimmedSurface(f.Surface, u0, u1, v0, v1)
        bs = trim.toBSpline()
        u0, u1, v0, v1 = bs.bounds()
        cutKnotsU = [u0, u1]
        cutKnotsV = [v0, v1]
        # print("bs parameters : {}".format(bs.bounds()))
        if obj.Option == "Auto":
            if obj.Direction in ["U", "Both"]:
                knots = bs.getUKnots()
                mults = bs.getUMultiplicities()
                cutKnotsU = self.get_intervals(knots, mults)
            if obj.Direction in ["V", "Both"]:
                knots = bs.getVKnots()
                mults = bs.getVMultiplicities()
                cutKnotsV = self.get_intervals(knots, mults)

        elif obj.Option == "Custom":
            knots = self.get_normalized_params(obj, 'KnotsUProvider')
            if knots:
                knots = KnotVector(knots)
                uknots = knots.transpose(u0, u1)
            else:
                uknots = obj.KnotsU

            knots = self.get_normalized_params(obj, 'KnotsVProvider')
            if knots:
                knots = KnotVector(knots)
                vknots = knots.transpose(v0, v1)
            else:
                vknots = obj.KnotsV

            for k in uknots:
                if (k > u0) and (k < u1):
                    cutKnotsU.append(k)
            for k in vknots:
                if (k > v0) and (k < v1):
                    cutKnotsV.append(k)

            if hasattr(obj, "NumberU") and (obj.NumberU > 1):
                par_range = u1 - u0
                uk = [(u0 + i * par_range / obj.NumberU) for i in range(1, obj.NumberU)]
                cutKnotsU.extend(uk)
            if hasattr(obj, "NumberV") and (obj.NumberV > 1):
                par_range = v1 - v0
                vk = [(v0 + i * par_range / obj.NumberV) for i in range(1, obj.NumberV)]
                cutKnotsV.extend(vk)

            cutKnotsU = list(set(cutKnotsU))
            cutKnotsV = list(set(cutKnotsV))
            cutKnotsU.sort()
            cutKnotsV.sort()

        # print(cutKnotsU)
        # print(cutKnotsV)
        if len(cutKnotsU) < 3 and len(cutKnotsV) < 3:
            # f.transformShape(mat)
            obj.Shape = bs.toShape()
            return

        faces = list()
        for i in range(len(cutKnotsU) - 1):
            for j in range(len(cutKnotsV) - 1):
                s = bs.copy()
                s.segment(cutKnotsU[i], cutKnotsU[i + 1], cutKnotsV[j], cutKnotsV[j + 1])
                # print(f"Surface segmented to {s.bounds()}")
                nf = s.toShape()
                if f.Orientation == "Reversed":
                    nf.reverse()
                faces.append(nf)
        if faces:
            shell = Part.Shell(faces)
            if shell.isValid():
                obj.Shape = shell
            else:
                obj.Shape = Part.Compound(faces)
            return
        # f.transformShape(mat)
        obj.Shape = bs.toShape()

    def onChanged(self, obj, prop):
        if prop == "Option":
            grp1 = [p for p in obj.PropertiesList if "Direction" in obj.getGroupOfProperty(p)]
            if obj.Option == "Auto":
                for p in grp1:
                    obj.setEditorMode(p, 2)
                obj.setEditorMode("Direction", 0)
            elif obj.Option == "Custom":
                for p in grp1:
                    obj.setEditorMode(p, 0)
                obj.setEditorMode("Direction", 2)


class SegmentSurfaceVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        if len(self.Object.Source) > 0:
            if len(self.Object.Source[0].Shape.Faces) == 1:
                self.Object.Source[0].ViewObject.Visibility = False
                return [self.Object.Source[0]]
        return []

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


class SegSurfCommand:
    """SegmentSurface command"""

    def makeFeature(self, s):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Segment_Surface")
        SegmentSurface(fp, (s.Object, s.SubElementNames[0]))
        SegmentSurfaceVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))
        else:
            self.makeFeature(sel[0])

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('segment_surface', SegSurfCommand())

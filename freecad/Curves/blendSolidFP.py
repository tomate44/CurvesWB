# -*- coding: utf-8 -*-

__title__ = "BlendSolid"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Create a solid between two faces with some continuity with their support shapes"
__usage__ = """You must select at least 2 faces in the 3D View.
Additionally, in order to prevent twisting, you can also select 1, or 2 consecutive edges or vertexes, on each face."""

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import blend_curve as bc
from freecad.Curves import ICONPATH
from freecad.Curves import blendSolids

TOOL_ICON = os.path.join(ICONPATH, 'blendSurf.svg')
# debug = _utils.debug
# debug = _utils.doNothing


class BlendSolidProxy:
    """Proxy of a BlendSolid FeaturePython object"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList", "Sources",
                        "Base", "Faces to join")
        obj.addProperty("App::PropertyInteger", "Samples",
                        "Settings", "Number of samples to generate each surface")
        obj.addProperty("App::PropertyEnumeration", "Algo",
                        "Untwist", "Method used to untwist the wires")
        obj.addProperty("App::PropertyLinkSubList", "MatchingShapes",
                        "Untwist", "User selected matching edges or vertexes")
        obj.addProperty("App::PropertyIntegerList", "Offset",
                        "Untwist", "Offset edge indices, negative values also untwist the wires")
        obj.addProperty("App::PropertyInteger", "Continuity1",
                        "Continuity", "Continuity level with shape 1")
        obj.addProperty("App::PropertyInteger", "Continuity2",
                        "Continuity", "Continuity level with shape 2")
        obj.addProperty("App::PropertyEnumeration", "AutoScale",
                        "Scale", "Compute scales to get regular poles, or minimal curvature")
        obj.addProperty("App::PropertyInteger", "ScaleSamples",
                        "Scale", "Number of samples for auto scaling")
        obj.addProperty("App::PropertyFloatList", "Scale1",
                        "Scale", "Scale values along face 1")
        obj.addProperty("App::PropertyFloatList", "Scale2",
                        "Scale", "Scale values along face 2")
        obj.addProperty("App::PropertyString", "ShapeType",
                        "Status", "Status of the created shape")
        obj.ShapeType = ""
        obj.setEditorMode("ShapeType", 1)
        obj.ScaleSamples = 3
        obj.Samples = 20
        obj.Continuity1 = 2
        obj.Continuity2 = 2
        obj.AutoScale = ["RegularPoles", "MinimizeCurvature", "Manual"]
        obj.AutoScale = "RegularPoles"
        obj.setEditorMode("Scale1", 2)
        obj.setEditorMode("Scale2", 2)
        obj.Algo = ["ManualMatch", "ManualValues"]
        obj.Algo = "ManualValues"
        obj.Proxy = self

    def get_input_shapes(self, obj):
        if hasattr(obj, "Sources"):
            s1 = obj.Sources[0]
            s2 = obj.Sources[1]
            f1 = s1[0].getSubObject(s1[1][0])
            f2 = s2[0].getSubObject(s2[1][0])
            if isinstance(f1, Part.Face) and isinstance(f2, Part.Face):
                return f1, f2, s1[0].Shape, s2[0].Shape
        return None, None, None, None

    def get_untwist_shapes(self, obj):
        pairs = []
        if hasattr(obj, "MatchingShapes") and len(obj.MatchingShapes) > 1:
            s1 = obj.MatchingShapes[0]
            s2 = obj.MatchingShapes[1]
            if s1[0] == obj.Sources[1][0]:
                s1 = obj.MatchingShapes[1]
                s2 = obj.MatchingShapes[0]
            for n1, n2 in zip(s1[1], s2[1]):
                sh1 = s1[0].getSubObject(n1)
                sh2 = s2[0].getSubObject(n2)
                if sh1.__class__ == sh2.__class__:
                    pairs.append([sh1, sh2])
        return pairs

    def other_face(self, sh, f, e):
        anc = sh.ancestorsOfType(e, Part.Face)
        for af in anc:
            if not af.isPartner(f):
                return af

    def execute(self, obj):
        blso = blendSolids.BlendSolid(*self.get_input_shapes(obj))
        if obj.Algo == "ManualMatch" and len(obj.MatchingShapes) > 1:
            blso.match_shapes(self.get_untwist_shapes(obj))
            obj.Offset = blso.offset
        else:
            blso.offset = obj.Offset

        if obj.AutoScale == "Manual":
            blso.set_size(obj.Scale1, obj.Scale2)
        else:
            if obj.AutoScale == "RegularPoles":
                blso.auto_scale(obj.ScaleSamples)
            elif obj.AutoScale == "MinimizeCurvature":
                blso.minimize_curvature(obj.ScaleSamples)
        blso.update_surfaces(obj.Samples)
        obj.Scale1 = blso.surfaces()[0].edge1.size.values
        obj.Scale2 = blso.surfaces()[0].edge2.size.values
        shape = blso.Shape
        if isinstance(shape, Part.Solid):  # and shape.isValid():
            obj.ShapeType = "Solid"
        elif isinstance(shape, Part.Shell):  # and shape.isValid():
            obj.ShapeType = "Shell"
        else:
            obj.ShapeType = "Compound"
        obj.Shape = shape  # Part.Compound(edges + [shape])

    def onChanged(self, obj, prop):
        if prop == "AutoScale":
            if obj.AutoScale == "Manual":
                obj.setEditorMode("ScaleSamples", 2)
                obj.setEditorMode("Scale1", 0)
                obj.setEditorMode("Scale2", 0)
            else:
                obj.setEditorMode("ScaleSamples", 0)
                obj.setEditorMode("Scale1", 2)
                obj.setEditorMode("Scale2", 2)
        if prop == "Algo":
            if obj.Algo == "ManualMatch":
                obj.setEditorMode("Offset", 1)
                obj.setEditorMode("MatchingShapes", 0)
            else:
                obj.setEditorMode("Offset", 0)
                obj.setEditorMode("MatchingShapes", 2)
        if prop == "Offset":
            self.execute(obj)


class BlendSolidViewProxy:
    """Proxy of a BlendSolid FeaturePython ViewObject"""
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


class BlendSolidCommand:
    """Create a BlendSurface FeaturePython object"""
    def makeFeature(self, sel=[], untwist=[]):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Blend Solid")
        BlendSolidProxy(fp)
        BlendSolidViewProxy(fp.ViewObject)
        fp.Sources = sel
        FreeCAD.ActiveDocument.recompute()
        if untwist:
            fp.Algo = "ManualMatch"
            fp.MatchingShapes = untwist

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        sources = []
        untwist = []
        for selobj in sel:
            for sen in selobj.SubElementNames:
                if ("Edge" in sen) or ("Vertex" in sen):
                    untwist.append((selobj.Object, sen))
                elif "Face" in sen:
                    sources.append((selobj.Object, sen))
        if len(sources) == 2:
            self.makeFeature(sources, untwist)
        else:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}\n\n{}\n\n{}".format(__title__, __doc__, __usage__)}


FreeCADGui.addCommand('Curves_BlendSolid', BlendSolidCommand())

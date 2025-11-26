# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "BlendSolid"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Create a solid between two faces with some continuity with their support shapes"
__usage__ = "Select a face on each of the two solids to blend, in the 3D View."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import ICONPATH
from freecad.Curves import blendSolids

TOOL_ICON = os.path.join(ICONPATH, 'blendSolid.svg')
# debug = _utils.debug
# debug = _utils.doNothing


class BlendSolidProxy:
    """Proxy of a BlendSolid FeaturePython object"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList", "Sources",
                        "Base", "Faces to join")
        obj.addProperty("App::PropertyInteger", "Samples",
                        "Settings", "Number of samples to generate each surface")
        obj.addProperty("App::PropertyBool", "Fuse",
                        "Settings", "Fuse the 3 solids together")
        # obj.addProperty("App::PropertyEnumeration", "Algo",
        #                 "Untwist", "Method used to untwist the wires")
        # obj.addProperty("App::PropertyLinkSubList", "MatchingShapes",
        #                 "Untwist", "User selected matching edges or vertexes")
        # obj.addProperty("App::PropertyVectorList", "Offset",
        #                 "Untwist", "Offset edge indices")
        obj.addProperty("App::PropertyInteger", "Continuity1",
                        "Continuity", "Continuity order G... with shape 1")
        obj.addProperty("App::PropertyInteger", "Continuity2",
                        "Continuity", "Continuity order G... with shape 2")
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
        obj.ScaleSamples = 6
        obj.Samples = 20
        obj.Continuity1 = 2
        obj.Continuity2 = 2
        obj.Fuse = False
        obj.AutoScale = ["RegularPoles", "MinimizeCurvature", "Manual"]
        obj.AutoScale = "RegularPoles"
        obj.setEditorMode("Scale1", 2)
        obj.setEditorMode("Scale2", 2)
        # obj.Algo = ["ManualMatch", "ManualValues"]
        # obj.Algo = "ManualValues"
        obj.Proxy = self

    def get_input_shapes(self, obj):
        if hasattr(obj, "Sources") and len(obj.Sources) > 1:
            s1 = obj.Sources[0]
            s2 = obj.Sources[1]
            f1 = s1[0].getSubObject(s1[1][0])
            f2 = s2[0].getSubObject(s2[1][0])
            if isinstance(f1, Part.Face) and isinstance(f2, Part.Face):
                return f1, f2, s1[0].Shape, s2[0].Shape
        return None, None, None, None

    # def get_orientation_shapes(self, obj):
    #     vl1 = []
    #     vl2 = []
    #     if hasattr(obj, "MatchingShapes") and len(obj.MatchingShapes) > 1:
    #         s1 = obj.MatchingShapes[0]
    #         s2 = obj.MatchingShapes[1]
    #         if s1[0] == obj.Sources[1][0]:
    #             s1 = obj.MatchingShapes[1]
    #             s2 = obj.MatchingShapes[0]
    #         for n1 in s1[1]:
    #             sh1 = s1[0].getSubObject(n1)
    #             vl1.append(sh1)
    #         for n2 in s2[1]:
    #             sh2 = s2[0].getSubObject(n2)
    #             vl2.append(sh2)
    #     return vl1, vl2

    def other_face(self, sh, f, e):
        anc = sh.ancestorsOfType(e, Part.Face)
        for af in anc:
            if not af.isPartner(f):
                return af

    def execute(self, obj):
        f1, f2, sh1, sh2 = self.get_input_shapes(obj)
        if None in [f1, f2, sh1, sh2]:
            print("Input Error\n", f1, f2, sh1, sh2)
            return
        blso = blendSolids.BlendSolid(f1, f2, sh1, sh2)
        # print(blso)
        # if obj.Algo == "ManualMatch" and len(obj.MatchingShapes) > 1:
        #     blso.match_shapes(*self.get_orientation_shapes(obj))
        #     obj.Offset = [FreeCAD.Vector(*tup) for tup in blso.offset]
        # else:
        #     blso.offset = obj.Offset
        blso.set_continuity([obj.Continuity1, obj.Continuity2])
        # print("continuity set")
        if obj.AutoScale == "Manual":
            blso.set_size(obj.Scale1, obj.Scale2)
            # print("set_size OK")
        elif obj.AutoScale == "RegularPoles":
            blso.auto_scale(obj.ScaleSamples)
            # print("auto_scale OK")
        elif obj.AutoScale == "MinimizeCurvature":
            blso.minimize_curvature(obj.ScaleSamples)
        # print("updating surfaces")
        blso.update_surfaces(obj.Samples)
        # print("surfaces updated")
        obj.Scale1 = blso.surfaces()[0].edge1.size.values
        obj.Scale2 = blso.surfaces()[0].edge2.size.values
        shape = blso.Shape
        if isinstance(shape, Part.Solid):  # and shape.isValid():
            obj.ShapeType = "Solid"
            if obj.Fuse:
                fuse = shape.fuse([sh1, sh2], 1e-7)
                # print(fuse)
                if len(fuse.Solids) == 1:
                    shape = fuse.Solids[0]
                    obj.ShapeType = "Fused"
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
        # if prop == "Algo":
        #     if obj.Algo == "ManualMatch":
        #         obj.setEditorMode("Offset", 1)
        #         obj.setEditorMode("MatchingShapes", 0)
        #     else:
        #         obj.setEditorMode("Offset", 0)
        #         obj.setEditorMode("MatchingShapes", 2)
        if prop in ["Continuity1", "Continuity2"]:
            self.execute(obj)


class BlendSolidViewProxy:
    """Proxy of a BlendSolid FeaturePython ViewObject"""
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

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

    def claimChildren(self):
        if self.Object.ShapeType == "Fused":
            o1 = self.Object.Sources[0][0]
            o2 = self.Object.Sources[1][0]
            o1.ViewObject.Visibility = False
            o2.ViewObject.Visibility = False
            return [o1, o2]
        return []

    def onDelete(self, feature, subelements):
        if feature.Object.ShapeType == "Fused":
            o1 = self.Object.Sources[0][0]
            o2 = self.Object.Sources[1][0]
            o1.ViewObject.Visibility = True
            o2.ViewObject.Visibility = True
        return True


class BlendSolidCommand:
    """Create a BlendSurface FeaturePython object"""
    def makeFeature(self, sel=[]):  # , untwist=[]):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Blend Solid")
        BlendSolidProxy(fp)
        BlendSolidViewProxy(fp.ViewObject)
        fp.Sources = sel
        FreeCAD.ActiveDocument.recompute()
        # if untwist:
        #     fp.Algo = "ManualMatch"
        #     fp.MatchingShapes = untwist
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        sources = []
        # untwist = []
        for selobj in sel:
            for sen in selobj.SubElementNames:
                # if ("Edge" in sen) or ("Vertex" in sen):
                #     untwist.append((selobj.Object, sen))
                if "Face" in sen:
                    sources.append((selobj.Object, sen))
        if not len(sources) == 2:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))
        else:
            f1 = sources[0][0].getSubObject(sources[0][1])
            f2 = sources[1][0].getSubObject(sources[1][1])
            if len(f1.Edges) == len(f2.Edges):
                self.makeFeature(sources)
            else:
                FreeCAD.Console.PrintError("BlendSolid : The two faces must have the same number of edges\n")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('Curves_BlendSolid', BlendSolidCommand())

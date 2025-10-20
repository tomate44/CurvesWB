# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "BlendSurface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Create a surface between two edges with some continuity with their support faces"
__usage__ = """You must select 4 subshapes in the 3D View :
- EDGE1 on FACE1
- EDGE2 on FACE2"""

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import blend_curve
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'blendSurf.svg')
# debug = _utils.debug
# debug = _utils.doNothing


class BlendSurfaceFP2:
    """Proxy of a BlendSurface FeaturePython object"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList", "Sources",
                        "Base", "Edges and support faces")
        obj.addProperty("App::PropertyInteger", "Samples",
                        "Base", "Number of samples to generate surface")
        obj.addProperty("App::PropertyInteger", "Continuity1",
                        "Continuity", "Continuity level with face of edge 1")
        obj.addProperty("App::PropertyInteger", "Continuity2",
                        "Continuity", "Continuity level with face of edge 2")
        obj.addProperty("App::PropertyEnumeration", "AutoScale",
                        "Scale", "Compute scales to get regular poles, or minimal curvature")
        obj.addProperty("App::PropertyInteger", "ScaleSamples",
                        "Scale", "Number of samples for auto scaling")
        obj.addProperty("App::PropertyFloatList", "Scale1",
                        "Scale", "Scale values along edge 1")
        obj.addProperty("App::PropertyFloatList", "Scale2",
                        "Scale", "Scale values along edge 2")
        obj.ScaleSamples = 3
        obj.Samples = 20
        obj.Continuity1 = 2
        obj.Continuity2 = 2
        obj.AutoScale = ["RegularPoles", "MinimizeCurvature", "Manual"]
        obj.AutoScale = "RegularPoles"
        obj.Proxy = self

    def get_input_shapes(self, obj):
        if hasattr(obj, "Sources"):
            edges = []
            faces = []
            for tups in obj.Sources:
                o = tups[0]
                for son in tups[1]:
                    ss = o.getSubObject(son)
                    if isinstance(ss, Part.Edge):
                        edges.append(ss)
                    elif isinstance(ss, Part.Face):
                        faces.append(ss)
            return edges, faces
        return None, None

    def execute(self, obj):
        edges, faces = self.get_input_shapes(obj)
        bs = blend_curve.BlendSurface(edges[0], faces[0], edges[-1], faces[-1])
        bs.edge1.continuity = obj.Continuity1
        bs.edge2.continuity = obj.Continuity2
        if obj.AutoScale == "Manual":
            bs.edge1.size = obj.Scale1
            bs.edge2.size = obj.Scale2
        else:
            if obj.AutoScale == "RegularPoles":
                bs.auto_scale(obj.ScaleSamples)
            elif obj.AutoScale == "MinimizeCurvature":
                bs.minimize_curvature(obj.ScaleSamples)
            obj.Scale1 = bs.edge1.size.values
            obj.Scale2 = bs.edge2.size.values
        bs.perform(obj.Samples)
        obj.Shape = bs.face

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


class BlendSurfaceVP2:
    """Proxy of a BlendSurface FeaturePython ViewObject"""
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


class BlendSurf2Command:
    """Create a BlendSurface FeaturePython object"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Blend Surface")
        BlendSurfaceFP2(fp)
        if FreeCAD.GuiUp:
            BlendSurfaceVP2(fp.ViewObject)
        else:
            fp.ViewObject.Proxy = 0
        fp.Sources = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx('', 0)
        sources = []
        for selobj in sel:
            for sen in selobj.SubElementNames:
                if "Edge" in sen:
                    sources.append((selobj.Object, sen))
                elif "Face" in sen:
                    sources.append((selobj.Object, sen))
        if sources:
            self.makeFeature(sources)
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
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Curves_BlendSurf2', BlendSurf2Command())

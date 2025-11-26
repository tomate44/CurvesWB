# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "MultiLoft"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Loft profile objects made of multiple faces in parallel"""

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'multiLoft.svg')
# debug = _utils.debug
# debug = _utils.doNothing


class MultiLoftFP:
    """Creates a MultiLoft"""
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
        src_shapes = []
        for o in obj.Sources:
            sh = o.Shape.copy()
            if hasattr(sh, "getGlobalPlacement"):
                sh.Placement = o.getGlobalPlacement()
            src_shapes.append(sh)
        solids = []
        for i in range(len(src_shapes[0].Faces)):
            faces = [src_shapes[0].Faces[i], src_shapes[-1].Faces[i]]
            loft = []
            num_wires = len(faces[0].Wires)
            for j in range(num_wires):
                wires = []
                for o in src_shapes:
                    wires.append(o.Faces[i].Wires[j])
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
        if prop in ["Ruled", "Closed", "MaxDegree"]:
            self.execute(obj)
        return


class MultiLoftVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

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
        return self.Object.Sources

    def onDelete(self, feature, subelements):  # subelements is a tuple of strings
        for c in self.Object.Sources:
            if hasattr(c, "ViewObject"):
                c.ViewObject.Visibility = True
        return True


class MultiLoftCommand:
    """Creates a MultiLoft feature"""
    def makeFeature(self, sel):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "MultiLoft")
        MultiLoftFP(fp)
        MultiLoftVP(fp.ViewObject)
        fp.Sources = sel
        for c in sel:
            if hasattr(c, "ViewObject"):
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
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('MultiLoft', MultiLoftCommand())

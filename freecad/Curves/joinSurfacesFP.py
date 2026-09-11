# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Join Surfaces'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Join surfaces into a single BSpline surface'

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves.BaseProxy import BaseFPOProxy
from freecad.Curves.lib import bspline_surface
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'join_surfaces.svg')


class JoinSurfaceFP(BaseFPOProxy):
    def __init__(self, obj):
        super().__init__(obj)
        obj.addProperty("App::PropertyLinkSubList", "Faces",
                        "Input", "The faces to join")
        obj.addProperty("App::PropertyFloat", "Tolerance",
                        "Settings", "Tolerance for knot insertion")
        obj.addProperty("App::PropertyInteger", "ContinuityU",
                        "Shape Info", "Continuity of surface in U direction")
        obj.addProperty("App::PropertyInteger", "ContinuityV",
                        "Shape Info", "Continuity of surface in V direction")
        obj.setExpression('Tolerance', u'1e-07')
        obj.setEditorMode("ContinuityU", 1)
        obj.setEditorMode("ContinuityV", 1)
        obj.Proxy = self

    def execute(self, obj):
        faces = []
        for o, subnames in obj.Faces:
            fl = []
            for subname in subnames:
                # print(subname)
                # print(o.getSubObject(subname))
                f = o.getSubObject(subname)
                if isinstance(f, Part.Face):
                    fl.append(f)
            if len(fl) > 0:
                faces.extend(fl)
            else:
                faces.extend(o.Shape.Faces)
        # print(faces)
        sl = []
        for f in faces:
            if isinstance(f.Surface, Part.BSplineSurface):
                sl.append(f.Surface)
            else:
                rts = Part.RectangularTrimmedSurface(
                    f.Surface, *f.ParameterRange)
                sl.append(rts.toBSpline())
        if len(sl) < 2:
            raise ValueError(f"{obj.Label}: Needs at least 2 faces")
        s1, s2 = sl[:2]
        s1, s2 = bspline_surface.match_orientation(s1, s2)
        result = bspline_surface.join_surfaces(s1, s2, obj.Tolerance)
        for i in range(2, len(sl)):
            s2 = sl[i]
            s1, s2 = bspline_surface.match_orientation(result, s2)
            result = bspline_surface.join_surfaces(s1, s2, obj.Tolerance)
        _ = bspline_surface.raise_continuity(result, 0, 1, 1e-7)
        uc, uv = bspline_surface.get_continuities(result)
        obj.ContinuityU = uc
        obj.ContinuityV = uv
        obj.Shape = result.toShape()

    def onChanged(self, obj, prop):
        return False

    def onDocumentRestored(self, obj):
        obj.setEditorMode("ContinuityU", 1)
        obj.setEditorMode("ContinuityV", 1)


class JoinSurfaceVP:
    def __init__(self, viewobj):
        viewobj.addProperty("App::PropertyBool", "ClaimChildren",
                            "Display Options",
                            "Claim input face objects as children ?")
        viewobj.ClaimChildren = True
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
        if self.Object.ViewObject.ClaimChildren:
            ol = [o[0] for o in self.Object.Faces]
            return ol
        return []

    def onChanged(self, obj, prop):
        if prop == "ClaimChildren":
            self.Object.recompute()
        return False


class JoinSurfaceCmd:
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "JoinSurface")
        JoinSurfaceFP(fp)
        JoinSurfaceVP(fp.ViewObject)
        fp.Faces = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select at least two faces.\n")
            return
        faces = []
        for so in sel:
            if so.SubElementNames:
                faces.append((so.Object, so.SubElementNames))
            else:
                faces.append(so.Object)
        # print(faces)
        self.makeFeature(faces)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Curves_JoinSurface', JoinSurfaceCmd())

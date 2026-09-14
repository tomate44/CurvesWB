# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Join Surfaces'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Join surfaces into a single BSpline surface'

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves.BaseProxy import BaseFPOProxy, BaseFPOViewProxy
from freecad.Curves.lib import bspline_surface
from freecad.Curves import ICONPATH
from freecad.Curves.lib.precision import tol3d, tol2d

TOOL_ICON = os.path.join(ICONPATH, 'join_surfaces.svg')


class JoinSurfaceFP(BaseFPOProxy):
    def __init__(self, obj):
        super().__init__(obj)
        obj.addProperty("App::PropertyLinkSubList", "Faces",
                        "Input", "The faces to join")
        obj.addProperty("App::PropertyFloat", "Tolerance2D",
                        "Settings", "Parametric tolerance for knot insertion")
        obj.addProperty("App::PropertyFloat", "Tolerance3D",
                        "Settings", "Tolerance for knot removal (smoothing)")
        obj.addProperty("App::PropertyInteger", "ContinuityU",
                        "Shape Info", "Continuity of surface in U direction")
        obj.addProperty("App::PropertyInteger", "ContinuityV",
                        "Shape Info", "Continuity of surface in V direction")
        obj.setExpression('Tolerance2D', str(tol2d))
        obj.setExpression('Tolerance3D', str(tol3d))
        obj.setEditorMode("ContinuityU", 1)
        obj.setEditorMode("ContinuityV", 1)
        obj.Proxy = self

    def execute(self, obj):
        # Populate the face list from Feature Property
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
        # Convert faces to BSpline surfaces
        sl = []
        for f in faces:
            if isinstance(f.Surface, Part.BSplineSurface):
                sl.append(f.Surface)
            else:
                rts = Part.RectangularTrimmedSurface(
                    f.Surface, *f.ParameterRange)
                sl.append(rts.toBSpline())
        # Join surfaces and try to raise continuity
        result = bspline_surface.join_multiple_surfaces(sl, obj.Tolerance2D)
        _ = bspline_surface.raise_continuity(result, 0, 1, obj.Tolerance3D)
        uc, uv = bspline_surface.get_continuities(result)
        obj.ContinuityU = uc
        obj.ContinuityV = uv
        obj.Shape = result.toShape()

    def onChanged(self, obj, prop):
        return False

    def onDocumentRestored(self, obj):
        obj.setEditorMode("ContinuityU", 1)
        obj.setEditorMode("ContinuityV", 1)


class JoinSurfaceVP(BaseFPOViewProxy):
    def __init__(self, viewobj):
        viewobj.addProperty("App::PropertyBool", "ClaimChildren",
                            "Display Options",
                            "Claim input face objects as children ?")
        viewobj.ClaimChildren = True
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

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

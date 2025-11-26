# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Parametric Gordon surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates a surface that skins a network of curves."

# from importlib import reload
import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH
from freecad.Curves.gordon import InterpolateCurveNetwork

TOOL_ICON = os.path.join(ICONPATH, 'gordon.svg')
DEBUG = False
# debug = _utils.debug
# debug = _utils.doNothing


def debug(o):
    if not DEBUG:
        return
    if isinstance(o, Part.BSplineCurve):
        FreeCAD.Console.PrintWarning("\nBSplineCurve\n")
        FreeCAD.Console.PrintWarning("Degree: %d\n" % (o.Degree))
        FreeCAD.Console.PrintWarning("NbPoles: %d\n" % (o.NbPoles))
        FreeCAD.Console.PrintWarning("Knots: %d (%0.2f - %0.2f)\n" % (o.NbKnots, o.FirstParameter, o.LastParameter))
        FreeCAD.Console.PrintWarning("Mults: %s\n" % (o.getMultiplicities()))
        FreeCAD.Console.PrintWarning("Periodic: %s\n" % (o.isPeriodic()))
    elif isinstance(o, Part.BSplineSurface):
        FreeCAD.Console.PrintWarning("\nBSplineSurface\n************\n")
        try:
            u = o.uIso(o.UKnotSequence[0])
            debug(u)
        except Part.OCCError:
            FreeCAD.Console.PrintError("Failed to compute uIso curve\n")
        try:
            v = o.vIso(o.VKnotSequence[0])
            debug(v)
        except Part.OCCError:
            FreeCAD.Console.PrintError("Failed to compute vIso curve\n")
        FreeCAD.Console.PrintWarning("************\n")
    else:
        FreeCAD.Console.PrintMessage("%s\n" % o)


class gordonFP:
    """Creates a surface that skins a network of curves"""

    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList", "Sources", "Gordon", "Curve network")
        obj.addProperty("App::PropertyFloat", "Tol3D", "Gordon", "3D tolerance").Tol3D = 1e-2
        obj.addProperty("App::PropertyFloat", "Tol2D", "Gordon", "Parametric tolerance").Tol2D = 1e-5
        obj.addProperty("App::PropertyInteger", "MaxCtrlPts", "Gordon", "Max Number of control points").MaxCtrlPts = 80
        obj.addProperty("App::PropertyEnumeration", "Output", "Base", "Output type").Output = ["Surface", "Wireframe"]
        obj.addProperty("App::PropertyInteger", "SamplesU", "Wireframe", "Number of samples in U direction").SamplesU = 16
        obj.addProperty("App::PropertyInteger", "SamplesV", "Wireframe", "Number of samples in V direction").SamplesV = 16
        obj.addProperty("App::PropertyBool", "FlipNormal", "Surface", "Flip surface normal").FlipNormal = False
        obj.Output = "Surface"
        obj.setEditorMode("Tol2D", 2)
        obj.setEditorMode("SamplesU", 2)
        obj.setEditorMode("SamplesV", 2)
        obj.Proxy = self

    def onDocumentRestored(self, fp):
        if not hasattr(fp, "Output"):
            fp.addProperty("App::PropertyEnumeration", "Output", "Base", "Output type").Output = ["Surface", "Wireframe"]

    def onChanged(self, fp, prop):
        if prop == "Output":
            if fp.Output == "Surface":
                fp.setEditorMode("SamplesU", 2)
                fp.setEditorMode("SamplesV", 2)
                fp.setEditorMode("FlipNormal", 0)
            else:
                fp.setEditorMode("SamplesU", 0)
                fp.setEditorMode("SamplesV", 0)
                fp.setEditorMode("FlipNormal", 2)

    def get_guides_and_profiles(self, obj):
        edges = list()
        for o in obj.Sources:
            if len(o.Shape.Wires) >= 1:
                for w in o.Shape.Wires:
                    if len(w.Edges) > 1:
                        bs = w.approximate(1e-10, 1e-7, 25, 999)
                        edges.append(bs.toShape())
                    else:
                        edges.append(w.Edges[0])
            else:
                edges += o.Shape.Edges
        comp = Part.Compound(edges)
        size = comp.BoundBox.DiagonalLength
        profiles = list()
        guides = [edges[0]]
        for e in edges[1:]:
            d, pts, info = edges[0].distToShape(e)
            if d < (obj.Tol3D * size):
                profiles.append(e)
            else:
                guides.append(e)
        return guides, profiles

    def execute(self, obj):
        if len(obj.Sources) == 0:
            return
        elif len(obj.Sources) == 2:
            guides = obj.Sources[0].Shape.Edges
            profiles = obj.Sources[1].Shape.Edges
        else:
            guides, profiles = self.get_guides_and_profiles(obj)

        guide_curves = [e.Curve.toBSpline(e.FirstParameter, e.LastParameter) for e in guides]
        profile_curves = [e.Curve.toBSpline(e.FirstParameter, e.LastParameter) for e in profiles]
        debug("%d guides / %d profiles" % (len(guide_curves), len(profile_curves)))
        guides_closed = all([c.isClosed() for c in guide_curves])
        profile_closed = all([c.isClosed() for c in profile_curves])
        if guides_closed:
            debug("All guides are closed")
            # profile_curves.append(profile_curves[0])
        if profile_closed:
            debug("All profiles are closed")
            # guide_curves.append(guide_curves[0])
        # create the gordon surface
        gordon_surf = InterpolateCurveNetwork(profile_curves, guide_curves, obj.Tol3D, obj.Tol2D)
        gordon_surf.max_ctrl_pts = obj.MaxCtrlPts
        # gordon.perform()
        # s = gordon.surface_intersections()
        # debug(s)
        # debug(s.getPoles())
        # obj.Shape = s.toShape()
        # poly = list()
        # for row in s.getPoles():
        #     poly.append(Part.makePolygon(row))
        # s = gordon.surface_guides()
        # for row in s.getPoles():
        #     poly.append(Part.makePolygon(row))
        # obj.Shape = gordon.curve_network()
        # display curves and resulting surface
        s = gordon_surf.surface()
        if obj.Output == "Wireframe":
            edges = list()
            u0, u1, v0, v1 = s.bounds()
            for i in range(obj.SamplesU + 1):
                pu = u0 + (u1 - u0) * float(i) / obj.SamplesU
                edges.append(s.uIso(pu).toShape())
            for i in range(obj.SamplesV + 1):
                pv = v0 + (v1 - v0) * float(i) / obj.SamplesV
                edges.append(s.vIso(pv).toShape())
            obj.Shape = Part.Compound(edges)
        else:
            f = s.toShape()
            if obj.FlipNormal:
                f.reverse()
            obj.Shape = f
        del gordon_surf


class gordonVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        if hasattr(self.Object, "Sources"):
            return self.Object.Sources
        else:
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


class gordonCommand:
    """Creates a surface that skins a network of curves"""

    def makeGordonFeature(self, source):
        gordonObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Gordon")
        gordonFP(gordonObj)
        gordonVP(gordonObj.ViewObject)
        gordonObj.Sources = source
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select a curve network !\n")
        else:
            self.makeGordonFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            f = FreeCADGui.Selection.Filter("SELECT Part::Feature COUNT 1..100")
            return f.match()
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Gordon surface',
                'ToolTip': 'Creates a surface that skins a network of curves'}


FreeCADGui.addCommand('gordon', gordonCommand())

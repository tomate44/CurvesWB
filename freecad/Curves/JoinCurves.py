# -*- coding: utf-8 -*-

__title__ = "joinCurves"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Joins the selected edges into a BSpline Curve"
__usage__ = """Select the edges to join in the 3D View, or select an object containing multiple edges in the Tree View.
Activate the tool.
The output is a single BSpline curve joining all selected edges."""

import os
import FreeCAD
import FreeCADGui
import Part
from . import _utils
from . import ICONPATH
from . import approximate_extension

TOOL_ICON = os.path.join(ICONPATH, 'joincurve.svg')
# debug = _utils.debug
debug = _utils.doNothing


def forceC1Continuity(c, tol):
    mults = [int(m) for m in c.getMultiplicities()]
    for i in range(len(mults))[1:-1]:
        if mults[i] >= c.Degree:
            try:
                c.removeKnot(i + 1, c.Degree - 1, tol)
            except Part.OCCError:
                debug('failed to increase continuity.')
    return c


def alignedTangents(c0, c1, tol):
    t0 = c0.tangent(c0.LastParameter)[0]
    t1 = c1.tangent(c1.FirstParameter)[0]
    # t0.normalize()
    t1.negative()
    # t1.normalize()
    v = t0.sub(t1)
    if v.Length < tol:
        return True
    else:
        return False


def forceJoin(c0, c):
    p1 = c0.getPole(1)
    p2 = c0.getPole(c0.NbPoles)
    q1 = c.getPole(1)
    q2 = c.getPole(c.NbPoles)
    d1 = p1.distanceToPoint(q1)
    d2 = p1.distanceToPoint(q2)
    d3 = p2.distanceToPoint(q1)
    d4 = p2.distanceToPoint(q2)
    distmin = min([d1, d2, d3, d4])
    if distmin == d1:
        c.setPole(1, p1)
    elif distmin == d2:
        c.setPole(c.NbPoles, p1)
    elif distmin == d3:
        c.setPole(1, p2)
    elif distmin == d4:
        c.setPole(c.NbPoles, p2)
    r = c0.join(c)
    if r:
        debug("Gap detected, successfully fixed")
    else:
        debug("ERROR : Failed to fix gap")
    return r


def forceClosed(curves, tol=1e-7):
    p1 = curves[0].getPole(1)
    p2 = curves[-1].getPole(curves[-1].NbPoles)
    if p1.distanceToPoint(p2) > tol:
        curves[-1].setPole(curves[-1].NbPoles, p1)


class join:
    "joins the selected edges into a single BSpline Curve"
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty(
            "App::PropertyLinkSubList",
            "Edges",
            "InputSources",
            QT_TRANSLATE_NOOP("App::Property", "List of edges to join"),
        )
        obj.addProperty(
            "App::PropertyLink",
            "Base",
            "InputSources",
            QT_TRANSLATE_NOOP("App::Property", "Join all the edges of this base object"),
        )
        obj.addProperty(
            "App::PropertyFloat",
            "Tolerance",
            "Join",
            QT_TRANSLATE_NOOP("App::Property", "Tolerance"),
        ).Tolerance = 0.01
        obj.addProperty(
            "App::PropertyBool",
            "CornerBreak",
            "Join",
            QT_TRANSLATE_NOOP("App::Property", "Break on sharp corners"),
        ).CornerBreak = False
        obj.addProperty(
            "App::PropertyBool",
            "ForceContact",
            "Join",
            QT_TRANSLATE_NOOP("App::Property", "Force connection of edges"),
        ).ForceContact = True
        obj.addProperty(
            "App::PropertyBool",
            "ForceClosed",
            "Join",
            QT_TRANSLATE_NOOP("App::Property", "Force closed curve"),
        ).ForceClosed = False
        obj.addProperty(
            "App::PropertyBool",
            "Reverse",
            "Join",
            QT_TRANSLATE_NOOP("App::Property", "Reverse the output curve"),
        ).Reverse = False
        obj.addProperty(
            "App::PropertyInteger",
            "StartOffset",
            "Join",
            QT_TRANSLATE_NOOP("App::Property", "Set the start point of closed curve"),
        ).StartOffset = 0
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if hasattr(fp, "ExtensionProxy"):
            fp.ExtensionProxy.onChanged(fp, prop)

    def getEdges(self, obj):
        res = []
        if hasattr(obj, "Base"):
            if obj.Base:
                res = obj.Base.Shape.Edges
        if hasattr(obj, "Edges"):
            for link in obj.Edges:
                for ss in link[1]:
                    res.append(link[0].getSubObject(ss))
        return res

    def execute(self, obj):
        edges = self.getEdges(obj)
        if not edges:
            return
        # tmp = list()
        # for e in edges:
        #     if not isinstance(e.Curve, Part.BSplineCurve):
        #         tmp += e.toNurbs().Edges
        #     else:
        #         tmp.append(e)
        curves = list()
        for e in edges:
            try:
                c = e.toNurbs().Edge1.Curve
            except Exception as exc:
                debug(f"JoinCurve : Nurbs conversion error\n{exc}\n")
                c = e.Curve.toBSpline()
            c.segment(e.FirstParameter, e.LastParameter)
            curves.append(c)
        debug("Edges : \n{}".format(str(curves)))

        c0 = curves[0].copy()
        outcurves = []
        for n, c in enumerate(curves[1:]):
            debug("joining edges {} and {}".format(n + 1, n + 2))
            # i = False
            tempCurve = c0.copy()
            tan = alignedTangents(c0, c, obj.Tolerance)
            if (tan is False) & obj.CornerBreak:
                outcurves.append(c0)
                c0 = c.copy()
                debug("No tangency, adding breakpoint")
            else:
                r = c0.join(c)
                if r is False:  # join operation failed
                    if obj.ForceContact:
                        r = forceJoin(c0, c)
                    else:
                        outcurves.append(c0)
                        c0 = c.copy()
                        debug("Joining failed, adding breakpoint")
                if r:
                    i = forceC1Continuity(c0, obj.Tolerance)
                    if (not (i.Continuity == 'C1')) & obj.CornerBreak:
                        outcurves.append(tempCurve)
                        c0 = c.copy()
                        debug("Failed to smooth edge #{}".format(curves[1:].index(c) + 2))
        outcurves.append(c0)
        if obj.ForceClosed:
            forceClosed(outcurves)
        if obj.Reverse:
            for c in outcurves:
                c.reverse()
        if len(outcurves) == 1 and outcurves[0].isClosed():
            outcurves[0].setPeriodic()
            outcurves[0].setOrigin(1 + obj.StartOffset % outcurves[0].NbKnots)
        outEdges = [Part.Edge(c) for c in outcurves]

        if hasattr(obj, "ExtensionProxy"):
            appsh = obj.ExtensionProxy.approximate(obj, outEdges)
            if isinstance(appsh, (list, tuple)):
                w = Part.Wire(appsh)
                if w.isValid():
                    obj.Shape = w
                else:
                    obj.Shape = Part.Compound(appsh)
            else:
                obj.Shape = appsh
        else:
            obj.Shape = Part.Wire(outEdges)


class joinVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def dumps(self):
        return {"name": self.Object.Name}

    def loads(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])

    if (FreeCAD.Version()[0] == '0') and ('.'.join(FreeCAD.Version()[1:3]) < '21.2'):
        def __getstate__(self):
            return self.dumps()

        def __setstate__(self, state):
            self.loads(state)

    # def claimChildren(self):
        # return None #[self.Object.Base, self.Object.Tool]


class joinCommand:
    "joins the selected edges into a single BSpline Curve"
    def makeJoinFeature(self, source):
        joinCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "JoinCurve")
        join(joinCurve)
        approximate_extension.ApproximateExtension(joinCurve)
        joinCurve.Active = False
        joinVP(joinCurve.ViewObject)
        if isinstance(source, list):
            joinCurve.Edges = source
        else:
            joinCurve.Base = source
        FreeCAD.ActiveDocument.recompute()
        # joinCurve.ViewObject.LineWidth = 1.0
        joinCurve.ViewObject.LineColor = (0.3, 0.0, 0.5)

    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        try:
            ordered = FreeCADGui.activeWorkbench().Selection
            if ordered:
                sel = ordered
        except AttributeError:
            pass
        if sel == []:
            FreeCAD.Console.PrintError(translate("Log", "{} :\n{}\n")).format(__title__, __usage__)
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        edges.append((selobj.Object, selobj.SubElementNames[i]))
            else:
                self.makeJoinFeature(selobj.Object)
                selobj.Object.ViewObject.Visibility = False
        if edges:
            self.makeJoinFeature(edges)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            # f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            # return f.match()
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand("Curves_JoinCurve", joinCommand())

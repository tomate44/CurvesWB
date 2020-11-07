# -*- coding: utf-8 -*-

__title__ = "Blend curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Blend curve between two edges."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

from pivy import coin
from freecad.Curves import nurbs_tools
from freecad.Curves import CoinNodes
from freecad.Curves import graphics
from freecad.Curves import manipulators

TOOL_ICON = os.path.join(ICONPATH, 'blend1.svg')
# debug = _utils.debug
debug = _utils.doNothing


class BlendCurveFP:
    def __init__(self, obj, edges):
        debug("BlendCurve class Init")
        obj.addProperty("App::PropertyLinkSub", "Edge1", "Edge1", "Edge 1").Edge1 = edges[0]
        obj.addProperty("App::PropertyLinkSub", "Edge2", "Edge2", "Edge 2").Edge2 = edges[1]
        obj.addProperty("App::PropertyInteger", "DegreeMax", "BlendCurve", "Max degree of the Blend curve").DegreeMax = 9
        obj.addProperty("App::PropertyFloatConstraint", "Parameter1", "Edge1", "Location of blend curve")
        obj.addProperty("App::PropertyFloatConstraint", "Scale1", "Edge1", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration", "Continuity1", "Edge1", "Continuity").Continuity1 = ["C0", "G1", "G2", "G3", "G4"]
        obj.addProperty("App::PropertyFloatConstraint", "Parameter2", "Edge2", "Location of blend curve")
        obj.addProperty("App::PropertyFloatConstraint", "Scale2", "Edge2", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration", "Continuity2", "Edge2", "Continuity").Continuity2 = ["C0", "G1", "G2", "G3", "G4"]
        obj.addProperty("App::PropertyVectorList", "CurvePts", "BlendCurve", "CurvePts")
        obj.addProperty("App::PropertyEnumeration", "Output", "BlendCurve", "Output type").Output = ["Wire", "Joined", "Single"]
        obj.Scale1 = (1., -5.0, 5.0, 0.05)
        obj.Scale2 = (1., -5.0, 5.0, 0.05)
        obj.Parameter1 = (1.0, 0.0, 1.0, 0.05)
        obj.Parameter2 = (1.0, 0.0, 1.0, 0.05)
        obj.Proxy = self

    def compute(self, fp):
        e1 = _utils.getShape(fp, "Edge1", "Edge")
        e2 = _utils.getShape(fp, "Edge2", "Edge")
        if e1 and e2:
            bc = nurbs_tools.blendCurve(e1, e2)
            bc.param1 = e1.FirstParameter + fp.Parameter1 * (e1.LastParameter - e1.FirstParameter)
            bc.param2 = e2.FirstParameter + fp.Parameter2 * (e2.LastParameter - e2.FirstParameter)
            bc.cont1 = self.getContinuity(fp.Continuity1)
            bc.cont2 = self.getContinuity(fp.Continuity2)
            bc.scale1 = fp.Scale1
            bc.scale2 = fp.Scale2
            bc.maxDegree = fp.DegreeMax
            bc.compute()
            return bc
        return None

    def execute(self, fp):
        bc = self.compute(fp)
        if (bc is None) or (bc.Curve is None):
            fp.CurvePts = []
            fp.Shape = Part.Shape()
        else:
            fp.CurvePts = bc.Curve.getPoles()
            if fp.Output == "Wire":
                fp.Shape = bc.getWire()
            elif fp.Output == "Joined":
                fp.Shape = bc.getJoinedCurve().toShape()
            else:
                fp.Shape = bc.Curve.toShape()

    def onChanged(self, fp, prop):
        if prop == "Scale1":
            if fp.Scale1 == 0:
                fp.Scale1 = 0.0001
            self.execute(fp)
        elif prop == "Scale2":
            if fp.Scale2 == 0:
                fp.Scale2 = 0.0001
            self.execute(fp)
        elif prop in ("Parameter1", "Parameter2"):
            self.execute(fp)
        elif prop == "DegreeMax":
            if fp.DegreeMax < 1:
                fp.DegreeMax = 1
            elif fp.DegreeMax > 9:
                fp.DegreeMax = 9

    def onDocumentRestored(self, fp):
        debug("{} restored !".format(fp.Label))
        fp.Scale1 = (fp.Scale1, -5.0, 5.0, 0.05)
        fp.Scale2 = (fp.Scale2, -5.0, 5.0, 0.05)
        fp.Parameter1 = (fp.Parameter1, 0.0, 1.0, 0.05)
        fp.Parameter2 = (fp.Parameter2, 0.0, 1.0, 0.05)

    def getContinuity(self, cont):
        if cont == "C0":
            return(0)
        elif cont == "G1":
            return(1)
        elif cont == "G2":
            return(2)
        elif cont == "G3":
            return(3)
        else:
            return(4)


class pointEditor(object):
    """Interpolation curve free-hand editor
    my_editor = pointEditor([points],obj)
    obj is the FreeCAD object that will receive
    the curve shape at the end of editing.
    points can be :
    - Vector (free point)
    - (Vector, shape) (point on shape)"""
    def __init__(self, points=[], fp=None):
        self.points = list()
        self.fp = fp
        self.curve = None
        self.root_inserted = False
        self.ctrl_keys = {"i": [self.insert],
                          "v": [self.text_change],
                          "q": [self.quit],
                          "\uffff": [self.remove_point]}
        for p in points:
            if isinstance(p, FreeCAD.Vector):
                self.points.append(manipulators.ShapeSnap(p))
            elif isinstance(p, (tuple, list)):
                self.points.append(manipulators.ShapeSnap(p[0], p[1]))
            elif isinstance(p, manipulators.ShapeSnap):
                self.points.append(p)
            elif isinstance(p, manipulators.CustomText):
                self.points.append(p)
            else:
                FreeCAD.Console.PrintError("pointEditor : bad input")
        for p in points:
            if hasattr(p, "ctrl_keys"):
                for key in p.ctrl_keys:
                    if key in self.ctrl_keys:
                        # print(key)
                        self.ctrl_keys[key].extend(p.ctrl_keys[key])
                    else:
                        self.ctrl_keys[key] = p.ctrl_keys[key]
        # Setup coin objects
        if self.fp:
            self.guidoc = self.fp.ViewObject.Document
        else:
            if not FreeCADGui.ActiveDocument:
                self.guidoc = FreeCAD.newDocument("New")
        self.guidoc = FreeCADGui.ActiveDocument
        self.view = self.guidoc.ActiveView
        self.rm = self.view.getViewer().getSoRenderManager()
        self.sg = self.view.getSceneGraph()
        self.setup_InteractionSeparator()

    def setup_InteractionSeparator(self):
        if self.root_inserted:
            self.sg.removeChild(self.root)
        self.root = graphics.InteractionSeparator(self.rm)
        self.root.setName("InteractionSeparator")
        # self.root.ovr_col = "yellow"
        # self.root.sel_col = "green"
        self.root.pick_radius = 40
        # self.root.on_drag.append(self.update_curve)
        # Keyboard callback
        # self.events = coin.SoEventCallback()
        self._controlCB = self.root.events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self.controlCB)
        # populate root node
        # self.root.addChild(self.events)
        self.root += self.points
        self.build_lines()
        self.root += self.lines
        # set FreeCAD color scheme
        for o in self.points:  # + self.lines:
            o.ovr_col = "yellow"
            o.sel_col = "green"
        self.root.register()
        self.sg.addChild(self.root)
        self.root_inserted = True
        self.root.selected_objects = list()

    def build_lines(self):
        self.lines = list()
        for m in self.points:
            if isinstance(m, manipulators.TangentSnap):
                line = manipulators.Line([m.parent, m])
                line.dynamic = False
                line.set_color("blue")
                self.lines.append(line)

    def controlCB(self, attr, event_callback):
        event = event_callback.getEvent()
        if event.getState() == event.UP:
            # FreeCAD.Console.PrintMessage("Key pressed : %s\n"%event.getKey())
            if chr(event.getKey()) in self.ctrl_keys:
                for foo in self.ctrl_keys[chr(event.getKey())]:
                    if foo.__self__ is self:
                        foo()
                    elif foo.__self__.parent in self.root.selected_objects:
                        foo()

    def remove_point(self):
        pts = list()
        for o in self.root.dynamic_objects:
            if isinstance(o, manipulators.Object3D):
                pts.append(o)
        self.points = pts
        self.setup_InteractionSeparator()

    def insert(self):
        # get selected lines and subdivide them
        # pts = []
        for o in self.root.selected_objects:
            # p1 = o.points[0]
            mark = manipulators.ShapeSnap(o.points, o.snap_shape)
            self.points.append(mark)
            # new_select.append(mark)
        # self.points.append(pts)
        self.setup_InteractionSeparator()
        # self.root.selected_objects = new_select
        return True

    def text_change(self):
        for o in self.root.selected_objects:
            if o._text_type == 2:
                o._text_type = 0
            else:
                o._text_type += 1

    def quit(self):
        self.root.events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self._controlCB)
        self.root.unregister()
        # self.root.removeAllChildren()
        self.sg.removeChild(self.root)
        self.root_inserted = False


class BlendCurveVP:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.select_state = True
        self.active = False
        self.ps = 0.0

    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False
        self.select_state = vobj.Selectable
        self.ip = None

    def update_shape(self):
        e1 = _utils.getShape(self.Object, "Edge1", "Edge")
        e2 = _utils.getShape(self.Object, "Edge2", "Edge")
        if e1 and e2:
            bc = nurbs_tools.blendCurve(e1, e2)
            v = Part.Vertex(self.m1.point)
            proj = v.distToShape(self.m1.snap_shape)[1][0][1]
            bc.param1 = e1.Curve.parameter(proj)
            # bc.param1 = (pa1 - self.m1.snap_shape.FirstParameter) / (self.m1.snap_shape.LastParameter - self.m1.snap_shape.FirstParameter)
            bc.scale1 = self.t1.parameter
            bc.cont1 = self.Object.Proxy.getContinuity(self.c1.text[0])

            v = Part.Vertex(self.m2.point)
            proj = v.distToShape(self.m2.snap_shape)[1][0][1]
            bc.param2 = e2.Curve.parameter(proj)
            # bc.param2 = (pa2 - self.m2.snap_shape.FirstParameter) / (self.m2.snap_shape.LastParameter - self.m2.snap_shape.FirstParameter)
            bc.scale2 = self.t2.parameter
            bc.cont2 = self.Object.Proxy.getContinuity(self.c2.text[0])
            bc.maxDegree = self.Object.DegreeMax
            bc.compute()
            self.Object.Shape = bc.Curve.toShape()
            return bc

    def setEdit(self, vobj, mode=0):
        debug("BlendCurve Edit mode = {}".format(mode))
        if mode == 0:
            if vobj.Selectable:
                self.select_state = True
                vobj.Selectable = False
                self.ps = vobj.PointSize
                vobj.PointSize = 0.0
            pts = list()
            e1 = _utils.getShape(self.Object, "Edge1", "Edge")
            e2 = _utils.getShape(self.Object, "Edge2", "Edge")

            pa1 = e1.FirstParameter + (e1.LastParameter - e1.FirstParameter) * self.Object.Parameter1
            pa2 = e2.FirstParameter + (e2.LastParameter - e2.FirstParameter) * self.Object.Parameter2

            d = e1.valueAt(pa1).distanceToPoint(e2.valueAt(pa2))

            self.m1 = manipulators.EdgeSnapAndTangent(e1.valueAt(pa1), e1)
            self.m1.set_color("cyan")
            self.m1.marker.markerIndex = coin.SoMarkerSet.CIRCLE_LINE_9_9
            pts.append(self.m1)
            self.c1 = manipulators.CycleText(self.m1)
            self.c1.text_list = ["C0", "G1", "G2", "G3", "G4"]
            self.c1.text = self.Object.Continuity1
            self.c1.show()
            pts.append(self.c1)

            self.t1 = manipulators.TangentSnap(self.m1)
            self.t1._scale = d / 3.0
            self.t1.parameter = self.Object.Scale1
            pts.append(self.t1)
            self.tt1 = manipulators.ParameterText(self.t1)
            self.tt1.show()
            pts.append(self.tt1)

            self.m2 = manipulators.EdgeSnapAndTangent(e2.valueAt(pa2), e2)
            self.m2.set_color("red")
            self.m2.marker.markerIndex = coin.SoMarkerSet.CIRCLE_LINE_9_9
            pts.append(self.m2)
            self.c2 = manipulators.CycleText(self.m2)
            self.c2.text_list = ["C0", "G1", "G2", "G3", "G4"]
            self.c2.text = self.Object.Continuity2
            self.c2.show()
            pts.append(self.c2)

            self.t2 = manipulators.TangentSnap(self.m2)
            self.t2._scale = d / 3.0
            self.t2.parameter = self.Object.Scale2
            pts.append(self.t2)
            self.tt2 = manipulators.ParameterText(self.t2)
            self.tt2.show()
            pts.append(self.tt2)

            self.ip = pointEditor(pts, self.Object)
            debug("pointEditor created\n")
            self.ip.root.on_drag.append(self.update_shape)
            self.active = True
            return True
        return False

    def unsetEdit(self, vobj, mode=0):
        e1 = _utils.getShape(self.Object, "Edge1", "Edge")
        e2 = _utils.getShape(self.Object, "Edge2", "Edge")
        if isinstance(self.ip, pointEditor):
            v = Part.Vertex(self.m1.point)
            proj = v.distToShape(self.m1.snap_shape)[1][0][1]
            pa1 = e1.Curve.parameter(proj)
            self.Object.Parameter1 = (pa1 - self.m1.snap_shape.FirstParameter) / (self.m1.snap_shape.LastParameter - self.m1.snap_shape.FirstParameter)
            self.Object.Scale1 = self.t1.parameter
            self.Object.Continuity1 = self.c1.text[0]

            v = Part.Vertex(self.m2.point)
            proj = v.distToShape(self.m2.snap_shape)[1][0][1]
            pa2 = e2.Curve.parameter(proj)
            self.Object.Parameter2 = (pa2 - self.m2.snap_shape.FirstParameter) / (self.m2.snap_shape.LastParameter - self.m2.snap_shape.FirstParameter)
            self.Object.Scale2 = self.t2.parameter
            self.Object.Continuity2 = self.c2.text[0]

            vobj.Selectable = self.select_state
            vobj.PointSize = self.ps
            self.ip.quit()
        self.ip = None
        self.active = False
        # vobj.Visibility = True
        return True

    def doubleClicked(self, vobj):
        if not hasattr(self, 'active'):
            self.active = False
        if not self.active:
            self.active = True
            # self.setEdit(vobj)
            vobj.Document.setEdit(vobj)
        else:
            vobj.Document.resetEdit()
            self.active = False
        return True

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def getChildren(self):
        return [self.Object.Edge1[0], self.Object.Edge2[0]]

    # def claimChildren(self):
        # return self.getChildren()


class oldBlendCurveVP:
    def __init__(self, obj):
        debug("VP init")
        obj.Proxy = self
        self.build()
        # self.children = []

    def claimChildren(self):
        if hasattr(self, "children"):
            return(self.children)
        else:
            return []

    def build(self):
        self.active = False
        if not hasattr(self, 'switch'):
            self.sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
            self.switch = coin.SoSwitch()
            if hasattr(self, 'Object'):
                self.switch.setName("{}_ControlPoints".format(self.Object.Name))
            self.empty = coin.SoSeparator()  # Empty node
            self.node = coin.SoSeparator()
            self.coord = CoinNodes.coordinate3Node()
            self.poly = CoinNodes.polygonNode((0.5, 0.5, 0.5), 1)
            self.marker = CoinNodes.markerSetNode((1, 0, 0), coin.SoMarkerSet.DIAMOND_FILLED_7_7)
            self.node.addChild(self.coord)
            self.node.addChild(self.poly)
            self.node.addChild(self.marker)
            self.switch.addChild(self.empty)
            self.switch.addChild(self.node)
            self.sg.addChild(self.switch)

    def setVisi(self, objs, vis):
        for o in objs:
            o.ViewObject.Visibility = vis

    def attach(self, vobj):
        debug("VP attach")
        self.Object = vobj.Object
        self.children = []
        # self.claimed = False

    def updateData(self, fp, prop):
        if prop == "CurvePts":
            if hasattr(self, 'coord') and hasattr(self, 'poly'):
                self.coord.points = fp.CurvePts
                self.poly.vertices = self.coord.points
                self.marker.color = [(1, 0, 0)] * (len(fp.CurvePts) - 1) + [(1, 1, 0)]
        elif prop == "Output":
            if fp.Output in ("Wire", "Joined"):
                if self.children == []:
                    if fp.Edge1[0] == fp.Edge2[0]:
                        self.children = [fp.Edge1[0]]
                    else:
                        self.children = [fp.Edge1[0], fp.Edge2[0]]
                    self.setVisi(self.children, False)
                    # self.claimed = True
            else:
                if not self.children == []:
                    self.setVisi(self.children, True)
                    # self.claimed = True
                    self.children = []

    def onChanged(self, vp, prop):
        if prop == "Visibility":
            if (vp.Visibility is True) and (self.active is True):
                self.switch.whichChild = 1
            elif (vp.Visibility is False) and (self.active is True):
                self.switch.whichChild = 0

    def doubleClicked(self, vobj):
        if not hasattr(self, 'active'):
            self.active = False
        if not self.active:
            self.active = True
            if (vobj.Visibility is True):
                self.switch.whichChild = 1
        else:
            self.active = False
            self.switch.whichChild = 0
        # self.Object.DegreeMax = self.Object.DegreeMax
        # FreeCAD.ActiveDocument.recompute()
        return True

    def setEdit(self, vobj, mode):
        debug("Start Edit")
        return True

    def unsetEdit(self, vobj, mode):
        debug("End Edit")
        return True

    def getIcon(self):
        # if self.active:
        # return(_utils.iconsPath() + '/blend2.svg')
        return TOOL_ICON

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self, state):
        debug("setstate")
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        self.build()
        return None

    def onDelete(self, feature, subelements):
        if hasattr(self, 'active'):
            if self.active:
                self.sg.removeChild(self.switch)
        return True


class ParametricBlendCurve:
    """Prepare selection and create blendCurve FeaturePython object."""
    def getEdge(self, edge):
        n = eval(edge[1].lstrip('Edge'))
        return edge[0].Shape.Edges[n - 1]

    def normalizedParam(self, edge, par, endClamp=False):
        e = self.getEdge(edge)
        goodpar = (par - e.FirstParameter) * 1.0 / (e.LastParameter - e.FirstParameter)
        if endClamp:
            if goodpar < 0.5:
                goodpar = 0.0
            else:
                goodpar = 1.0
        return(goodpar)

    def parseSel(self, selectionObject):
        res = []
        param = []
        for obj in selectionObject:
            for i in range(len(obj.SubObjects)):
                so = obj.SubObjects[i]
                if isinstance(so, Part.Edge):
                    res.append([obj.Object, obj.SubElementNames[i]])
                    p = obj.PickedPoints[i]
                    poe = so.distToShape(Part.Vertex(p))
                    par = poe[2][0][2]
                    param.append(par)
        return res, param

    def line(self, ed, p):
        e = self.getEdge(ed)
        pt = e.valueAt(p)
        t = e.tangentAt(p).multiply(100000)
        line = Part.LineSegment(pt, pt.add(t)).toShape()
        return line

    def getOrientation(self, e1, p1, e2, p2):
        r1 = -1.0
        r2 = -1.0
        l1 = self.line(e1, p1)
        l2 = self.line(e2, p2)
        dts = l1.distToShape(l2)
        par1 = dts[2][0][2]
        par2 = dts[2][0][5]
        if par1:
            r1 = 1.0
        if par2:
            r2 = 1.0
        return r1, r2

    def Activated(self):
        try:
            s = FreeCADGui.activeWorkbench().Selection
        except AttributeError:
            s = FreeCADGui.Selection.getSelectionEx()
        edges, param = self.parseSel(s)
        if len(edges) > 1:
            for j in range(int(len(edges) / 2)):
                i = j * 2
                obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Blend Curve")
                BlendCurveFP(obj, edges[i: i + 2])
                BlendCurveVP(obj.ViewObject)
                obj.Parameter1 = self.normalizedParam(edges[i], param[i], False)
                obj.Parameter2 = self.normalizedParam(edges[i + 1], param[i + 1], False)
                obj.Continuity1 = "G1"
                obj.Continuity2 = "G1"
                obj.Output = "Single"
                ori1, ori2 = self.getOrientation(edges[i], param[i], edges[i + 1], param[i + 1])
                obj.Scale1 = ori1
                obj.Scale2 = ori2
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}


FreeCADGui.addCommand('ParametricBlendCurve', ParametricBlendCurve())

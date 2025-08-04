# -*- coding: utf-8 -*-

__title__ = "Blend curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Blend curve between two edges.  Double-clic object to enable/disable freehand mouse editing."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

from pivy import coin
# from freecad.Curves import nurbs_tools
from freecad.Curves import blend_curve
from freecad.Curves import CoinNodes
from freecad.Curves import graphics
from freecad.Curves import manipulators

TOOL_ICON = os.path.join(ICONPATH, 'blend1.svg')
# debug = _utils.debug
debug = _utils.doNothing

if not blend_curve.CAN_MINIMIZE:
    __doc__ += "\nInstall 'scipy' python package for AutoScale feature"


class BlendCurveFP:
    def __init__(self, obj, edges):
        debug("BlendCurve class Init")
        obj.addProperty("App::PropertyLinkSub", "Edge1", "Edge1", "Edge 1").Edge1 = edges[0]
        obj.addProperty("App::PropertyLinkSub", "Edge2", "Edge2", "Edge 2").Edge2 = edges[1]
        # obj.addProperty("App::PropertyInteger", "DegreeMax", "BlendCurve", "Max degree of the Blend curve").DegreeMax = 9
        obj.addProperty("App::PropertyDistance", "Parameter1", "Edge1", "Location on first edge")
        obj.addProperty("App::PropertyBool", "Reverse1", "Edge1", "Reverse Edge").Reverse1 = False
        obj.addProperty("App::PropertyFloatConstraint", "Scale1", "Edge1", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration", "Continuity1", "Edge1", "Continuity").Continuity1 = ["C0", "G1", "G2", "G3", "G4"]
        obj.addProperty("App::PropertyDistance", "Parameter2", "Edge2", "Location on second edge")
        obj.addProperty("App::PropertyBool", "Reverse2", "Edge2", "Reverse Edge").Reverse2 = False
        obj.addProperty("App::PropertyFloatConstraint", "Scale2", "Edge2", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration", "Continuity2", "Edge2", "Continuity").Continuity2 = ["C0", "G1", "G2", "G3", "G4"]
        obj.addProperty("App::PropertyVectorList", "CurvePts", "BlendCurve", "Poles of the Bezier curve")
        obj.addProperty("App::PropertyEnumeration", "Output", "BlendCurve", "Output type").Output = ["Wire", "Joined", "Single"]
        obj.addProperty("App::PropertyBool", "AutoScale", "BlendCurve", "Compute scales to get minimal curvature along curve").AutoScale = False
        obj.Scale1 = (1., -5.0, 5.0, 0.05)
        obj.Scale2 = (1., -5.0, 5.0, 0.05)
        obj.setEditorMode("CurvePts", 2)
        obj.Proxy = self

    def check_minimize(self, fp):
        if blend_curve.CAN_MINIMIZE:
            fp.setEditorMode("AutoScale", 0)
        else:
            FreeCAD.Console.PrintWarning("BlendCurve: Install 'scipy' python package for AutoScale feature\n")
            fp.setEditorMode("AutoScale", 2)

    def getShape(self, fp, prop):
        sub = None
        if hasattr(fp, prop) and fp.getPropertyByName(prop):
            obj, senl = fp.getPropertyByName(prop)
            for sen in senl:
                if ("Edge" in sen) or ("Line" in sen):
                    sh = obj.Shape.copy()
                    sh.Placement = obj.getGlobalPlacement()
                    if hasattr(sh, "getElementName"):
                        sub = sh.getElement(sh.getElementName(sen))
                    else:
                        sub = sh.getElement(sen)
                    break
        return sub

    def migrate(self, fp):
        if hasattr(fp, "DegreeMax"):
            fp.removeProperty("DegreeMax")
        if not hasattr(fp, "AutoScale"):
            fp.addProperty("App::PropertyBool", "AutoScale", "BlendCurve",
                           "Compute scales to get minimal curvature along curve").AutoScale = False
        if not hasattr(fp, "Reverse1"):
            fp.addProperty("App::PropertyBool", "Reverse1", "Edge1", "Reverse Edge").Reverse1 = False
        if not hasattr(fp, "Reverse2"):
            fp.addProperty("App::PropertyBool", "Reverse2", "Edge2", "Reverse Edge").Reverse2 = False
        if fp.getTypeIdOfProperty("Parameter1") == "App::PropertyFloatConstraint":
            e1 = self.getShape(fp, "Edge1")
            val = fp.Parameter1 * e1.Length
            fp.removeProperty("Parameter1")
            fp.addProperty("App::PropertyDistance", "Parameter1", "Edge1", "Location on first edge")
            fp.Parameter1 = val
        if fp.getTypeIdOfProperty("Parameter2") == "App::PropertyFloatConstraint":
            e2 = self.getShape(fp, "Edge2")
            val = fp.Parameter2 * e2.Length
            fp.removeProperty("Parameter2")
            fp.addProperty("App::PropertyDistance", "Parameter2", "Edge1", "Location on second edge")
            fp.Parameter2 = val

    def compute(self, fp):
        e1 = self.getShape(fp, "Edge1")
        e2 = self.getShape(fp, "Edge2")
        r1 = fp.Parameter1
        if fp.Reverse1:
            r1 = -r1
            if r1 == 0:
                r1 = 1e50
        r2 = fp.Parameter2
        if fp.Reverse2:
            r2 = -r2
            if r2 == 0:
                r2 = 1e50
        if e1 and e2:
            # p1 = e1.getParameterByLength(fp.Parameter1)
            # p2 = e2.getParameterByLength(fp.Parameter2)
            c1 = blend_curve.PointOnEdge(e1)
            c1.distance = r1
            c1.continuity = self.getContinuity(fp.Continuity1)
            # c1.scale = fp.Scale1
            c2 = blend_curve.PointOnEdge(e2)
            c2.distance = r2
            c2.continuity = self.getContinuity(fp.Continuity2)
            # c2.scale = fp.Scale2
            bc = blend_curve.BlendCurve(c1, c2)
            bc.nb_samples = 200
            # bc.auto_scale()
            bc.scale1 = fp.Scale1
            bc.scale2 = fp.Scale2
            bc.perform()
            return bc

    def execute(self, fp):
        bc = self.compute(fp)
        if (bc is None) or (bc.curve is None):
            fp.CurvePts = []
            fp.Shape = Part.Shape()
            return None
        if fp.AutoScale:
            bc.scale1 = .01
            bc.scale2 = .01
            bc.auto_orient()
            bc.minimize_curvature()
            fp.Scale1 = bc.scale1
            fp.Scale2 = bc.scale2
        fp.CurvePts = bc.curve.getPoles()
        if fp.Output in ["Wire", "Joined"]:
            w = Part.Wire(bc.point1.rear_segment() + [bc.shape] + bc.point2.front_segment())
            if fp.Output == "Joined":
                w = w.approximate(1e-7, 1e-7, 99, 9).toShape()
        else:
            w = bc.shape
        if hasattr(fp, "getParent"):
            parent = fp.getParent()
            if parent and hasattr(parent, "getGlobalPlacement"):
                glopl = parent.getGlobalPlacement()
                w.transformShape(glopl.inverse().Matrix)
                fp.Placement = glopl.inverse()
        fp.Shape = w

    def onChanged(self, fp, prop):
        if 'Restore' in fp.State:
            return
        if prop == "AutoScale" and fp.AutoScale:
            fp.setEditorMode("Scale1", 2)
            fp.setEditorMode("Scale2", 2)
        if prop == "AutoScale" and not fp.AutoScale:
            fp.setEditorMode("Scale1", 0)
            fp.setEditorMode("Scale2", 0)
        elif prop == "Scale1":
            if fp.Scale1 == 0:
                fp.Scale1 = 0.0001
            if not fp.AutoScale:
                self.execute(fp)
        elif prop == "Scale2":
            if fp.Scale2 == 0:
                fp.Scale2 = 0.0001
            if not fp.AutoScale:
                self.execute(fp)
        elif prop == "Parameter1":
            e1 = self.getShape(fp, "Edge1")
            if fp.Parameter1 > e1.Length:
                fp.Parameter1 = e1.Length
            elif fp.Parameter1 < 0.0:
                fp.Parameter1 = 0.0
        elif prop == "Parameter2":
            e2 = self.getShape(fp, "Edge2")
            if fp.Parameter2 > e2.Length:
                fp.Parameter2 = e2.Length
            elif fp.Parameter2 < 0.0:
                fp.Parameter2 = 0.0
        if prop in ("Parameter1", "Parameter2",
                    "Continuity1", "Continuity2"
                    "Output"):
            self.execute(fp)

    def onDocumentRestored(self, fp):
        debug("{} restored !".format(fp.Label))
        fp.setEditorMode("CurvePts", 2)
        self.check_minimize(fp)
        self.migrate(fp)

    def getContinuity(self, cont):
        if cont == "C0":
            return 0
        elif cont == "G1":
            return 1
        elif cont == "G2":
            return 2
        elif cont == "G3":
            return 3
        else:
            return 4


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
        self.ps = 1.0

    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False
        self.select_state = vobj.Selectable
        self.ps = 1.0
        self.ip = None

    def get_length(self, edge, point):
        try:
            return edge.Curve.toShape(edge.FirstParameter, edge.Curve.parameter(point)).Length
        except Part.OCCError:
            return 0.0

    def get_param(self, edge, point):
        try:
            return edge.Curve.parameter(point)
        except Part.OCCError:
            return 0.0

    def update_shape(self):
        e1 = self.Object.Proxy.getShape(self.Object, "Edge1")
        e2 = self.Object.Proxy.getShape(self.Object, "Edge2")
        if self.bc:
            # self.bc.constraints = []
            # bc = nurbs_tools.blendCurve(e1, e2)
            v = Part.Vertex(self.m1.point)
            proj = v.distToShape(self.m1.snap_shape)[1][0][1]
            param1 = self.get_param(e1, proj)  # self.get_length(e1, proj)
            # bc.param1 = (pa1 - self.m1.snap_shape.FirstParameter) / (self.m1.snap_shape.LastParameter - self.m1.snap_shape.FirstParameter)
            cont1 = self.Object.Proxy.getContinuity(self.c1.text[0])
            self.bc.point1 = blend_curve.PointOnEdge(e1, param1, cont1)
            self.bc.scale1 = self.t1.parameter

            v = Part.Vertex(self.m2.point)
            proj = v.distToShape(self.m2.snap_shape)[1][0][1]
            param2 = self.get_param(e2, proj)  # self.get_length(e2, proj)
            # bc.param2 = (pa2 - self.m2.snap_shape.FirstParameter) / (self.m2.snap_shape.LastParameter - self.m2.snap_shape.FirstParameter)
            cont2 = self.Object.Proxy.getContinuity(self.c2.text[0])
            self.bc.point2 = blend_curve.PointOnEdge(e2, param2, cont2)
            self.bc.scale2 = -self.t2.parameter

            self.bc.perform()
            sh = self.bc.shape
            parent = self.Object.getParent()
            if parent and hasattr(parent, "getGlobalPlacement"):
                glopl = parent.getGlobalPlacement()
                sh.transformShape(glopl.inverse().Matrix)
                self.Object.Placement = glopl.inverse()
            self.Object.Shape = sh
            for obj in self.Object.InList:
                if hasattr(obj, "Proxy") and "Curves.ParametricComb.Comb" in str(obj.Proxy):
                    obj.Proxy.execute(obj)
            return self.bc

    def setEdit(self, vobj, mode=0):
        debug("BlendCurve Edit mode = {}".format(mode))
        self.Object.AutoScale = False
        if mode == 0:
            if vobj.Selectable:
                self.select_state = True
                vobj.Selectable = False
                self.ps = vobj.PointSize
                vobj.PointSize = 0.0
            pts = list()
            self.bc = self.Object.Proxy.compute(self.Object)

            # e1 = self.getShape(self.Object, "Edge1", "Edge")
            # e2 = self.getShape(self.Object, "Edge2", "Edge")
            # pa1 = e1.getParameterByLength(self.Object.Parameter1)
            # pa2 = e2.getParameterByLength(self.Object.Parameter2)

            d = self.bc.point1.point.distanceToPoint(self.bc.point2.point)

            self.m1 = manipulators.EdgeSnapAndTangent(self.bc.point1.point, self.bc.point1.edge)
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

            self.m2 = manipulators.EdgeSnapAndTangent(self.bc.point2.point, self.bc.point2.edge)
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
            self.t2.parameter = -self.Object.Scale2
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
        e1 = self.Object.Proxy.getShape(self.Object, "Edge1")
        e2 = self.Object.Proxy.getShape(self.Object, "Edge2")
        if isinstance(self.ip, pointEditor):
            v = Part.Vertex(self.m1.point)
            proj = v.distToShape(self.m1.snap_shape)[1][0][1]
            # pa1 = e1.Curve.parameter(proj)
            self.Object.Parameter1 = self.get_length(e1, proj)  # e1.Curve.toShape(e1.FirstParameter, pa1).Length
            self.Object.Scale1 = self.t1.parameter
            self.Object.Continuity1 = self.c1.text[0]

            v = Part.Vertex(self.m2.point)
            proj = v.distToShape(self.m2.snap_shape)[1][0][1]
            # pa2 = e2.Curve.parameter(proj)
            # self.Object.Parameter2 = (pa2 - self.m2.snap_shape.FirstParameter) / (self.m2.snap_shape.LastParameter - self.m2.snap_shape.FirstParameter)
            self.Object.Parameter2 = self.get_length(e2, proj)  # e2.Curve.toShape(e2.FirstParameter, pa2).Length
            self.Object.Scale2 = -self.t2.parameter
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
            FreeCAD.ActiveDocument.recompute()
        return True

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
            self.Object.Document.recompute()
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

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
          debug("setstate")
          self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
          self.build()
          return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

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
        if "Line" in edge[1]:
            return edge[0].Shape
        n = eval(edge[1].lstrip('Edge'))
        return edge[0].Shape.Edges[n - 1]

    def normalizedParam(self, edge, par, endClamp=False):
        e = self.getEdge(edge)
        goodpar = (par - e.FirstParameter) * 1.0 / (e.LastParameter - e.FirstParameter)
        if endClamp:
            if goodpar < 0.1:
                goodpar = 0.0
            elif goodpar > 0.9:
                goodpar = 1.0
        return goodpar

    def get_distance(self, edge, par, endClamp=False):
        e = self.getEdge(edge)
        ne = e.Curve.toShape(e.FirstParameter, par)
        dist = ne.Length
        if endClamp:
            if dist / e.Length < 0.05:
                dist = 0.0
            elif dist / e.Length > 0.95:
                dist = e.Length
        return dist

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

    #def getOrientation(self, e1, p1, e2, p2):
        #r1 = -1.0
        #r2 = 1.0
        #l1 = self.line(e1, p1)
        #l2 = self.line(e2, p2)
        #dts = l1.distToShape(l2)
        #par1 = dts[2][0][2]
        #par2 = dts[2][0][5]
        #if par1:
            #r1 = 1.0
        #if par2:
            #r2 = -1.0
        #return r1, r2

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges, param = self.parseSel(s)
        if len(edges) > 1:
            for j in range(int(len(edges) / 2)):
                i = j * 2
                obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Blend Curve")
                BlendCurveFP(obj, edges[i: i + 2])
                BlendCurveVP(obj.ViewObject)
                obj.Parameter1 = self.get_distance(edges[i], param[i], True)
                obj.Parameter2 = self.get_distance(edges[i + 1], param[i + 1], True)
                obj.Continuity1 = "G1"
                obj.Continuity2 = "G1"
                obj.Output = "Single"
                #ori1, ori2 = self.getOrientation(edges[i], param[i], edges[i + 1], param[i + 1])
                #obj.Scale1 = ori1
                #obj.Scale2 = ori2
                bc = obj.Proxy.compute(obj)
                bc.auto_scale()
                bc.minimize_curvature()
                obj.Scale1 = bc.point1.size
                obj.Scale2 = bc.point2.size
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('ParametricBlendCurve', ParametricBlendCurve())

# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part
from pivy import coin
from freecad.Curves import _utils
from freecad.Curves import graphics
# from graphics import COLORS
# FreeCAD.Console.PrintMessage("Using local Pivy.graphics library\n")


def parameterization(points, a, closed):
    """Computes a knot Sequence for a set of points
    fac (0-1) : parameterization factor
    fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length"""
    def distance(p1, p2):
        p = p2 - p1
        if isinstance(p, FreeCAD.Vector):
            return p.Length
        return p.length()

    pts = points.copy()
    # print(f"parameterization on type {pts[0]}")
    if closed:
        le = distance(pts[-1], pts[0])
        if le > 1e-7:  # we need to add the first point as the end point
            pts.append(pts[0])
    params = [0]
    for i in range(1, len(pts)):
        le = distance(pts[i - 1], pts[i])
        pl = pow(le, a)
        params.append(params[-1] + pl)
    return params


class ConnectionMarker(graphics.Marker):
    def __init__(self, points):
        super(ConnectionMarker, self).__init__(points, True)


class MarkerOnShape(graphics.Marker):
    def __init__(self, points, sh=None):
        super(MarkerOnShape, self).__init__(points, True)
        self._shape = None
        self._sublink = None
        self._tangent = None
        self._translate = coin.SoTranslation()
        self._text_font = coin.SoFont()
        self._text_font.name = "Arial:Bold"
        self._text_font.size = 13.0
        self._text = coin.SoText2()
        self._text_switch = coin.SoSwitch()
        self._text_switch.addChild(self._translate)
        self._text_switch.addChild(self._text_font)
        self._text_switch.addChild(self._text)
        self.on_drag_start.append(self.add_text)
        self.on_drag_release.append(self.remove_text)
        self.addChild(self._text_switch)
        if isinstance(sh, Part.Shape):
            self.snap_shape = sh
        elif isinstance(sh, (tuple, list)):
            self.sublink = sh

    def subshape_from_sublink(self, o):
        name = o[1][0]
        if 'Vertex' in name:
            n = eval(name.lstrip('Vertex'))
            return(o[0].Shape.Vertexes[n - 1])
        elif 'Edge' in name:
            n = eval(name.lstrip('Edge'))
            return(o[0].Shape.Edges[n - 1])
        elif 'Face' in name:
            n = eval(name.lstrip('Face'))
            return(o[0].Shape.Faces[n - 1])

    def add_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_ALL
        self.on_drag.append(self.update_text)

    def remove_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_NONE
        self.on_drag.remove(self.update_text)

    def update_text(self):
        p = self.points[0]
        coords = ['{: 9.3f}'.format(p[0]), '{: 9.3f}'.format(p[1]), '{: 9.3f}'.format(p[2])]
        self._translate.translation = p
        self._text.string.setValues(0, 3, coords)

    @property
    def tangent(self):
        return self._tangent

    @tangent.setter
    def tangent(self, t):
        if isinstance(t, FreeCAD.Vector):
            if t.Length > 1e-7:
                self._tangent = t
                self._tangent.normalize()
                self.marker.markerIndex = coin.SoMarkerSet.DIAMOND_FILLED_9_9
            else:
                self._tangent = None
                self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9
        else:
            self._tangent = None
            self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9

    @property
    def snap_shape(self):
        return self._shape

    @snap_shape.setter
    def snap_shape(self, sh):
        if isinstance(sh, Part.Shape):
            self._shape = sh
        else:
            self._shape = None
        self.alter_color()

    @property
    def sublink(self):
        return self._sublink

    @sublink.setter
    def sublink(self, sl):
        if isinstance(sl, (tuple, list)) and not (sl == self._sublink):
            self._shape = self.subshape_from_sublink(sl)
            self._sublink = sl
        else:
            self._shape = None
            self._sublink = None
        self.alter_color()

    def alter_color(self):
        if isinstance(self._shape, Part.Vertex):
            self.set_color("white")
        elif isinstance(self._shape, Part.Edge):
            self.set_color("cyan")
        elif isinstance(self._shape, Part.Face):
            self.set_color("magenta")
        else:
            self.set_color("black")

    def __repr__(self):
        return("MarkerOnShape({})".format(self._shape))

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, p in enumerate(pts):
                p[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                p[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                p[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
                if self._shape:
                    v = Part.Vertex(p[0], p[1], p[2])
                    proj = v.distToShape(self._shape)[1][0][1]
                    # FreeCAD.Console.PrintMessage("%s -> %s\n"%(p.getValue(), proj))
                    p[0] = proj.x
                    p[1] = proj.y
                    p[2] = proj.z
            self.points = pts
            for foo in self.on_drag:
                foo()


class ConnectionPolygon(graphics.Polygon):
    std_col = "green"

    def __init__(self, markers):
        super(ConnectionPolygon, self).__init__(
            sum([m.points for m in markers], []), True)
        self.markers = markers

        for m in self.markers:
            m.on_drag.append(self.updatePolygon)

    def updatePolygon(self):
        self.points = sum([m.points for m in self.markers], [])

    @property
    def drag_objects(self):
        return self.markers

    def check_dependency(self):
        if any([m._delete for m in self.markers]):
            self.delete()


class ConnectionLine(graphics.Line):
    def __init__(self, markers):
        super(ConnectionLine, self).__init__(
            sum([m.points for m in markers], []), True)
        self.markers = markers
        self._linear = False
        for m in self.markers:
            m.on_drag.append(self.updateLine)

    def updateLine(self):
        self.points = sum([m.points for m in self.markers], [])
        if self._linear:
            p1 = self.markers[0].points[0]
            p2 = self.markers[-1].points[0]
            t = p2 - p1
            tan = FreeCAD.Vector(t[0], t[1], t[2])
            for m in self.markers:
                m.tangent = tan

    @property
    def linear(self):
        return self._linear

    @linear.setter
    def linear(self, b):
        self._linear = bool(b)

    @property
    def drag_objects(self):
        return self.markers

    def check_dependency(self):
        if any([m._delete for m in self.markers]):
            self.delete()


class InterpoCurveEditor(object):
    """Interpolation curve free-hand editor
    my_editor = InterpoCurveEditor([points], obj)
    obj is the FreeCAD object that will receive
    the curve shape at the end of editing.
    points can be :
    - Vector (free point)
    - (Vector, shape) (point on shape)"""
    def __init__(self, points=[], fp=None):
        self.points = list()
        self.curve = Part.BSplineCurve()
        self.fp = fp
        self.root_inserted = False
        self.periodic = False
        self.param_factor = 1.0
        # self.support = None  #  Not yet implemented
        for p in points:
            if isinstance(p, FreeCAD.Vector):
                self.points.append(MarkerOnShape([p]))
            elif isinstance(p, (tuple, list)):
                self.points.append(MarkerOnShape([p[0]], p[1]))
            elif isinstance(p, (MarkerOnShape, ConnectionMarker)):
                self.points.append(p)
            else:
                FreeCAD.Console.PrintError("InterpoCurveEditor : bad input")
        #  Setup coin objects
        if self.fp:
            self.guidoc = self.fp.ViewObject.Document
        else:
            if not FreeCADGui.ActiveDocument:
                FreeCAD.newDocument("New")
        self.guidoc = FreeCADGui.ActiveDocument
        self.view = self.guidoc.ActiveView
        self.rm = self.view.getViewer().getSoRenderManager()
        self.sg = self.view.getSceneGraph()
        self.setup_InteractionSeparator()
        self.update_curve()

    def setup_InteractionSeparator(self):
        if self.root_inserted:
            self.sg.removeChild(self.root)
        self.root = graphics.InteractionSeparator(self.rm)
        self.root.setName("InteractionSeparator")
        # self.root.ovr_col = "yellow"
        # self.root.sel_col = "green"
        self.root.pick_radius = 40
        self.root.on_drag.append(self.update_curve)
        #  Keyboard callback
        # self.events = coin.SoEventCallback()
        self._controlCB = self.root.events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self.controlCB)
        #  populate root node
        # self.root.addChild(self.events)
        self.root += self.points
        self.build_lines()
        self.root += self.lines
        #  set FreeCAD color scheme
        for o in self.points + self.lines:
            o.ovr_col = "yellow"
            o.sel_col = "green"
        self.root.register()
        self.sg.addChild(self.root)
        self.root_inserted = True
        self.root.selected_objects = list()

    def compute_tangents(self):
        tans = list()
        flags = list()
        for i in range(len(self.points)):
            if isinstance(self.points[i].snap_shape, Part.Face):
                for vec in self.points[i].points:
                    u, v = self.points[i].snap_shape.Surface.parameter(FreeCAD.Vector(vec))
                    norm = self.points[i].snap_shape.normalAt(u, v)
                    cp = self.curve.parameter(FreeCAD.Vector(vec))
                    t = self.curve.tangent(cp)[0]
                    pl = Part.Plane(FreeCAD.Vector(), norm)
                    ci = Part.Geom2d.Circle2d()
                    ci.Radius = t.Length * 2
                    w = Part.Wire([ci.toShape(pl)])
                    f = Part.Face(w)
                    # proj = f.project([Part.Vertex(t)])
                    proj = Part.Vertex(t).distToShape(f)[1][0][1]
                    # pt = proj.Vertexes[0].Point
                    # FreeCAD.Console.PrintMessage("Projection %s -> %s\n"%(t, proj))
                    if proj.Length > 1e-7:
                        tans.append(proj)
                        flags.append(True)
                    else:
                        tans.append(FreeCAD.Vector(1, 0, 0))
                        flags.append(False)
            elif self.points[i].tangent:
                for j in range(len(self.points[i].points)):
                    tans.append(self.points[i].tangent)
                    flags.append(True)
            else:
                for j in range(len(self.points[i].points)):
                    tans.append(FreeCAD.Vector(0, 0, 0))
                    flags.append(False)
        return(tans, flags)

    def update_curve(self):
        pts = list()
        for p in self.points:
            pts += p.points
        # FreeCAD.Console.PrintMessage("pts :\n%s\n"%str(pts))
        if len(pts) > 1:
            fac = self.param_factor
            if self.fp:
                fac = self.fp.Parametrization
            params = parameterization(pts, fac, self.periodic)
            self.curve.interpolate(Points=pts, Parameters=params, PeriodicFlag=self.periodic)
            tans, flags = self.compute_tangents()
            if any(flags):
                if (len(tans) == len(pts)) and (len(flags) == len(pts)):
                    self.curve.interpolate(Points=pts, Parameters=params, PeriodicFlag=self.periodic, Tangents=tans, TangentFlags=flags)
            if self.fp:
                self.fp.Shape = self.curve.toShape()

    def build_lines(self):
        self.lines = list()
        for i in range(len(self.points) - 1):
            line = ConnectionLine([self.points[i], self.points[i + 1]])
            line.set_color("blue")
            self.lines.append(line)

    def controlCB(self, attr, event_callback):
        event = event_callback.getEvent()
        if event.getState() == event.UP:
            # FreeCAD.Console.PrintMessage("Key pressed : %s\n"%event.getKey())
            if event.getKey() == ord("i"):
                self.subdivide()
            elif event.getKey() == ord("p"):
                self.set_planar()
            elif event.getKey() == ord("t"):
                self.set_tangents()
            elif event.getKey() == ord("q"):
                if self.fp:
                    self.fp.ViewObject.Proxy.doubleClicked(self.fp.ViewObject)
                else:
                    self.quit()
            elif event.getKey() == ord("s"):
                sel = FreeCADGui.Selection.getSelectionEx()
                tup = None
                if len(sel) == 1:
                    tup = (sel[0].Object, sel[0].SubElementNames)
                for i in range(len(self.root.selected_objects)):
                    if isinstance(self.root.selected_objects[i], MarkerOnShape):
                        self.root.selected_objects[i].sublink = tup
                        FreeCAD.Console.PrintMessage("Snapped to {}\n".format(str(self.root.selected_objects[i].sublink)))
                        self.root.selected_objects[i].drag_start()
                        self.root.selected_objects[i].drag((0, 0, 0.))
                        self.root.selected_objects[i].drag_release()
                        self.update_curve()
            elif event.getKey() == ord("l"):
                self.toggle_linear()
            elif (event.getKey() == 65535) or (event.getKey() == 65288):  # Suppr or Backspace
                # FreeCAD.Console.PrintMessage("Some objects have been deleted\n")
                pts = list()
                for o in self.root.dynamic_objects:
                    if isinstance(o, MarkerOnShape):
                        pts.append(o)
                self.points = pts
                self.setup_InteractionSeparator()
                self.update_curve()

    def toggle_linear(self):
        for o in self.root.selected_objects:
            if isinstance(o, ConnectionLine):
                o.linear = not o.linear
                i = self.lines.index(o)
                if i > 0:
                    self.lines[i - 1].linear = False
                if i < len(self.lines) - 1:
                    self.lines[i + 1].linear = False
                o.updateLine()
                o.drag_start()
                o.drag((0, 0, 0.00001))
                o.drag_release()
                self.update_curve()

    def set_tangents(self):
        # view_dir = FreeCAD.Vector(0, 0, 1)
        view_dir = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        markers = list()
        for o in self.root.selected_objects:
            if isinstance(o, MarkerOnShape):
                markers.append(o)
            elif isinstance(o, ConnectionLine):
                markers.extend(o.markers)
        if len(markers) > 0:
            for m in markers:
                if m.tangent:
                    m.tangent = None
                else:
                    i = self.points.index(m)
                    if i == 0:
                        m.tangent = -view_dir
                    else:
                        m.tangent = view_dir
        self.update_curve()

    def set_planar(self):
        # view_dir = FreeCAD.Vector(0, 0, 1)
        view_dir = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        markers = list()
        for o in self.root.selected_objects:
            if isinstance(o, MarkerOnShape):
                markers.append(o)
            elif isinstance(o, ConnectionLine):
                markers.extend(o.markers)
        if len(markers) > 2:
            vec0 = markers[0].points[0]
            vec1 = markers[-1].points[0]
            p0 = FreeCAD.Vector(vec0[0], vec0[1], vec0[2])
            p1 = FreeCAD.Vector(vec1[0], vec1[1], vec1[2])
            pl = Part.Plane(p0, p1, p1 + view_dir)
            for o in markers:
                if isinstance(o.snap_shape, Part.Vertex):
                    FreeCAD.Console.PrintMessage("Snapped to Vertex\n")
                elif isinstance(o.snap_shape, Part.Edge):
                    FreeCAD.Console.PrintMessage("Snapped to Edge\n")
                    c = o.snap_shape.Curve
                    pts = pl.intersect(c)[0]
                    new_pts = list()
                    for ip in o.points:
                        iv = FreeCAD.Vector(ip[0], ip[1], ip[2])
                        dmin = 1e50
                        new = None
                        for op in pts:
                            ov = FreeCAD.Vector(op.X, op.Y, op.Z)
                            if iv.distanceToPoint(ov) < dmin:
                                dmin = iv.distanceToPoint(ov)
                                new = ov
                        new_pts.append(new)
                    o.points = new_pts
                elif isinstance(o.snap_shape, Part.Face):
                    FreeCAD.Console.PrintMessage("Snapped to Face\n")
                    s = o.snap_shape.Surface
                    cvs = pl.intersect(s)
                    new_pts = list()
                    for ip in o.points:
                        iv = Part.Vertex(FreeCAD.Vector(ip[0], ip[1], ip[2]))
                        dmin = 1e50
                        new = None
                        for c in cvs:
                            e = c.toShape()
                            d, pts, info = iv.distToShape(e)
                            if d < dmin:
                                dmin = d
                                new = pts[0][1]
                        new_pts.append(new)
                    o.points = new_pts
                else:
                    FreeCAD.Console.PrintMessage("Not snapped\n")
                    new_pts = list()
                    for ip in o.points:
                        iv = FreeCAD.Vector(ip[0], ip[1], ip[2])
                        u, v = pl.parameter(iv)
                        new_pts.append(pl.value(u, v))
                    o.points = new_pts
        for li in self.lines:
            li.updateLine()
        self.update_curve()

    def subdivide(self):
        #  get selected lines and subdivide them
        pts = list()
        new_select = list()
        for o in self.lines:
            # FreeCAD.Console.PrintMessage("object %s\n"%str(o))
            if isinstance(o, ConnectionLine):
                pts.append(o.markers[0])
                if o in self.root.selected_objects:
                    idx = self.lines.index(o)
                    FreeCAD.Console.PrintMessage("Subdividing line  #{}\n".format(idx))
                    p1 = o.markers[0].points[0]
                    p2 = o.markers[1].points[0]
                    par1 = self.curve.parameter(FreeCAD.Vector(p1))
                    par2 = self.curve.parameter(FreeCAD.Vector(p2))
                    midpar = (par1 + par2) / 2.0
                    mark = MarkerOnShape([self.curve.value(midpar)])
                    pts.append(mark)
                    new_select.append(mark)
        pts.append(self.points[-1])
        self.points = pts
        self.setup_InteractionSeparator()
        self.root.selected_objects = new_select
        self.update_curve()
        return(True)

    def quit(self):
        self.root.events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self._controlCB)
        self.root.unregister()
        # self.root.removeAllChildren()
        self.sg.removeChild(self.root)
        self.root_inserted = False


def get_guide_params():
    sel = FreeCADGui.Selection.getSelectionEx()
    pts = list()
    for s in sel:
        pts.extend(list(zip(s.PickedPoints, s.SubObjects)))
    return(pts)


def main():
    obj = FreeCAD.ActiveDocument.addObject("Part::Spline", "profile")
    tups = get_guide_params()
    InterpoCurveEditor(tups, obj)
    FreeCAD.ActiveDocument.recompute()


if __name__ == '__main__':
    main()

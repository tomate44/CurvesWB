import FreeCAD
import FreeCADGui
import Part
from pivy import coin
from freecad.Curves import graphics


class ConnectionMarker(graphics.Marker):
    def __init__(self, points):
        super(ConnectionMarker, self).__init__(points, True)
        self.output = coin.SoDecomposeVec3f()
        self.output.vector.connectFrom(self.data.point)
        self.input = coin.SoComposeVec3f()
        self.data.point.connectFrom(self.input.vector)

    def connect_x(self, other):
        self.input.x.connectFrom(other.output.x)
        other.input.x.connectFrom(self.output.x)

    def connect_y(self, other):
        self.input.y.connectFrom(other.output.y)
        other.input.y.connectFrom(self.output.y)

    def connect_z(self, other):
        self.input.z.connectFrom(other.output.z)
        other.input.z.connectFrom(self.output.z)


class ConnectionLine(graphics.Line):
    def __init__(self, markers):
        super(ConnectionLine, self).__init__(
            sum([m.points for m in markers], []), True)
        self.markers = markers
        for m in self.markers:
            m.on_drag.append(self.updateLine)

    def updateLine(self):
        self.points = sum([m.points for m in self.markers], [])

    @property
    def drag_objects(self):
        return self.markers

    def check_dependency(self):
        if any([m._delete for m in self.markers]):
            self.delete()

class RectangleEditor:
    """Rectangle free-hand editor
    my_editor = RectangleEditor(bounds, fp)"""
    def __init__(self, bounds=[0, 20, 0, 10], fp=None):
        self.points = []
        self.fp = fp
        self.root_inserted = False
        self.update_func = None

        u0, u1, v0, v1 = bounds
        self.points.append(ConnectionMarker([(u0, v0, 0)]))
        self.points.append(ConnectionMarker([(u0, v1, 0)]))
        self.points.append(ConnectionMarker([(u1, v1, 0)]))
        self.points.append(ConnectionMarker([(u1, v0, 0)]))

        self.points[1].connect_x(self.points[0])
        self.points[3].connect_y(self.points[0])
        self.points[3].connect_x(self.points[2])
        self.points[1].connect_y(self.points[2])

        # Setup coin objects
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
        self.update()

    def setup_InteractionSeparator(self):
        if self.root_inserted:
            self.sg.removeChild(self.root)
        self.root = graphics.InteractionSeparator(self.rm)
        self.root.setName("InteractionSeparator")
        self.root.pick_radius = 40
        self.root.on_drag.append(self.update)
        self._controlCB = self.root.events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self.controlCB)
        self.root += self.points
        self.build_lines()
        funcs = [line.updateLine for line in self.lines]
        for m in self.points:
            m.on_drag.extend(funcs)
        self.root += self.lines
        for o in self.points + self.lines:
            o.ovr_col = "yellow"
            o.sel_col = "blue"
        self.root.register()
        self.sg.addChild(self.root)
        self.root_inserted = True
        self.root.selected_objects = list()

    def build_lines(self):
        tmp_pts = self.points
        tmp_pts.append(self.points[0])
        self.lines = list()
        for i in range(len(tmp_pts) - 1):
            line = ConnectionLine([tmp_pts[i], tmp_pts[i + 1]])
            self.lines.append(line)
        self.lines[3].set_color("red")
        self.lines[0].set_color("green")

    def update(self):
        # b = "{:0.3f}, {:0.3f}, {:0.3f}, {:0.3f}\n".format( *self.bounds())
        # FreeCAD.Console.PrintMessage(b)
        if callable(self.update_func):
            self.update_func()
        return

    def bounds(self):
        return [self.points[0].points[0][0],
                self.points[3].points[0][0],
                self.points[0].points[0][1],
                self.points[1].points[0][1]]

    def controlCB(self, attr, event_callback):
        event = event_callback.getEvent()
        if event.getState() == event.UP:
            if event.getKey() == ord("q"):
                if self.fp:
                    self.fp.ViewObject.Proxy.doubleClicked(self.fp.ViewObject)
                else:
                    self.quit()

    def quit(self):
        self.root.events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self._controlCB)
        self.root.unregister()
        self.sg.removeChild(self.root)
        self.root_inserted = False


# RectangleEditor()

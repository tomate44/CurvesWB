import FreeCAD
import FreeCADGui
import Part
from pivy import coin
from freecad.Curves import graphics


# class ConnectionMarker(graphics.Marker):
    # def __init__(self, points):
        # super(ConnectionMarker, self).__init__(points, True)
        # self.output = coin.SoDecomposeVec3f()
        # self.output.vector.connectFrom(self.data.point)
        # self.input = coin.SoComposeVec3f()
        # self.data.point.connectFrom(self.input.vector)

    # def connect_x(self, other):
        # self.input.x.connectFrom(other.output.x)
        # other.input.x.connectFrom(self.output.x)

    # def connect_y(self, other):
        # self.input.y.connectFrom(other.output.y)
        # other.input.y.connectFrom(self.output.y)

    # def connect_z(self, other):
        # self.input.z.connectFrom(other.output.z)
        # other.input.z.connectFrom(self.output.z)


class ConstrainedMarker(graphics.Marker):
    def __init__(self, points):
        super(ConstrainedMarker, self).__init__(points, True)
        self.constraint = (1.0, 1.0, 1.0)
        self.x_drag_objects = []
        self.y_drag_objects = []
        self.z_drag_objects = []
        # self.on_drag_start.append(self.init_constraints)
        # self.on_drag_start.append(self.release)
        # self.on_drag_release.append(self.release_constraints)

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, pt in enumerate(pts):
                pt[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                pt[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                pt[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
            self.points = pts
            for o in self.x_drag_objects:
                o.drag([mouse_coords[0], 0, 0], fact)
            for o in self.y_drag_objects:
                o.drag([0, mouse_coords[1], 0], fact)
            for o in self.z_drag_objects:
                o.drag([0, 0, mouse_coords[0]], fact)
            for foo in self.on_drag:
                foo()

    def drag_start(self):
        self._tmp_points = self.points
        for o in self.x_drag_objects:
            o.drag_start()
        for o in self.y_drag_objects:
            o.drag_start()
        for o in self.z_drag_objects:
            o.drag_start()
        if self.enabled:
            for foo in self.on_drag_start:
                foo()

    #def init_constraints(self):
        #for o in self.x_drag_objects:
            #o.x_drag()
        #for o in self.y_drag_objects:
            #o.y_drag()
        #for o in self.z_drag_objects:
            #o.z_drag()

    #def release_constraints(self):
        #for o in self.x_drag_objects + self.y_drag_objects + self.z_drag_objects:
            #o.release()

    #def x_drag(self):
        #self.constraint = (1.0, 0.0, 0.0)

    #def y_drag(self):
        #self.constraint = (0.0, 1.0, 0.0)

    #def z_drag(self):
        #self.constraint = (0.0, 0.0, 1.0)

    #def release(self):
        #self.constraint = (1.0, 1.0, 1.0)


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

        self.points = [ConstrainedMarker([FreeCAD.Vector(0, 0, 0)]) for i in range(4)]
        u0, u1, v0, v1 = bounds
        self.points[0].points = [(u0, v0, 0)]
        self.points[1].points = [(u0, v1, 0)]
        self.points[2].points = [(u1, v1, 0)]
        self.points[3].points = [(u1, v0, 0)]

        self.points[0].x_drag_objects.append(self.points[1])
        self.points[0].y_drag_objects.append(self.points[3])

        self.points[1].x_drag_objects.append(self.points[0])
        self.points[1].y_drag_objects.append(self.points[2])

        self.points[2].x_drag_objects.append(self.points[3])
        self.points[2].y_drag_objects.append(self.points[1])

        self.points[3].x_drag_objects.append(self.points[2])
        self.points[3].y_drag_objects.append(self.points[0])

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

        print(f"init : {self.bounds()}")

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

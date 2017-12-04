from pivy import coin
import FreeCAD as App
import FreeCADGui
import numpy

def depth(l):
    return isinstance(l, list) and max(map(depth, l))+1


def vector3D(vec):
    if len(vec) == 0:
        return(vec)
    elif not isinstance(vec[0], (list, tuple, numpy.ndarray, App.Vector)):
        if len(vec) == 3:
            return vec
        elif len(vec) == 2:
            return numpy.array(vec).tolist() + [0.]
        else:
            print("something wrong with this list: ", vec)
    else:
        return [vector3D(i) for i in vec]


COLORS = {
    "black": (0, 0, 0),
    "white": (1., 1., 1.),
    "grey": (0.5, 0.5, 0.5),
    "red": (1., 0., 0.),
    "blue": (0., 0., 1.),
    "green": (0., 1., 1.),
    "yellow": (0., 1., 0.)
}


class Object3D(coin.SoSeparator):
    std_col = "black"
    ovr_col = "red"
    sel_col = "yellow"
    disabled_col = "grey"

    def __init__(self, dynamic=False):
        super(Object3D, self).__init__()
        self._sel_color = COLORS[self.sel_col]
        self._ovr_color = COLORS[self.ovr_col]
        self._std_color = COLORS[self.std_col]
        self.data = coin.SoCoordinate4()
        self.color = coin.SoMaterial()
        self.color.diffuseColor = self._std_color
        self.addChild(self.color)
        self.addChild(self.data)
        self.start_pos = None
        self.dynamic = dynamic
        self.on_drag = []
        self.on_drag_release = []
        self.on_drag_start = []
        self._delete = False
        self._tmp_points = None
        self.enabled = True

    def set_disabled(self):
        self.color.diffuseColor = COLORS[self.disabled_col]
        self.enabled = False

    def set_enabled(self):
        self.color.diffuseColor = COLORS[self.std_col]
        self.enabled = True

    def set_color(self, col):
        self.std_col = col
        self._std_color = COLORS[self.std_col]
        self.color.diffuseColor = self._std_color

    @property
    def points(self):
        return self.data.point.getValues()

    @points.setter
    def points(self, points):
        self.data.point.setValue(0, 0, 0, 1.)
        self.data.point.setValues(0, len(points), points)

    def set_mouse_over(self):
        if self.enabled:
            self.color.diffuseColor = self._ovr_color

    def unset_mouse_over(self):
        if self.enabled:
            self.color.diffuseColor = self._std_color

    def select(self):
        if self.enabled:
            self.color.diffuseColor = self._sel_color

    def unselect(self):
        if self.enabled:
            self.color.diffuseColor = self._std_color

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, pt in enumerate(pts):
                if not isinstance(mouse_coords, list):
                    if fact == 0:
                        pt[3] = self._tmp_points[i][3]
                        pt[0] = self._tmp_points[i][0]
                        pt[1] = self._tmp_points[i][1]
                        pt[2] = self._tmp_points[i][2]
                    elif (mouse_coords > 0.0):
                        pt[3] = self._tmp_points[i][3] * (mouse_coords + 1.) * fact
                        pt[0] = self._tmp_points[i][0] * (mouse_coords + 1.) * fact
                        pt[1] = self._tmp_points[i][1] * (mouse_coords + 1.) * fact
                        pt[2] = self._tmp_points[i][2] * (mouse_coords + 1.) * fact
                    elif (mouse_coords < 0.0):
                        pt[3] = self._tmp_points[i][3] / ( abs(mouse_coords - 1) * fact )
                        pt[0] = self._tmp_points[i][0] / ( abs(mouse_coords - 1) * fact )
                        pt[1] = self._tmp_points[i][1] / ( abs(mouse_coords - 1) * fact )
                        pt[2] = self._tmp_points[i][2] / ( abs(mouse_coords - 1) * fact )
                    else:
                        pt[3] = self._tmp_points[i][3]
                        pt[0] = self._tmp_points[i][0]
                        pt[1] = self._tmp_points[i][1]
                        pt[2] = self._tmp_points[i][2]
                    #App.Console.PrintMessage("Weight : " + str(pt[3]) + "\n")
                else:
                    pt[3] = self._tmp_points[i][3]
                    pt[0] = pt[3] * mouse_coords[0] * fact + self._tmp_points[i][0]
                    pt[1] = pt[3] * mouse_coords[1] * fact + self._tmp_points[i][1]
                    pt[2] = pt[3] * mouse_coords[2] * fact + self._tmp_points[i][2]
                    # print("X-move : ", mouse_coords[0])
            self.points = pts
            for i in self.on_drag:
                i()

    def drag_release(self):
        if self.enabled:
            for i in self.on_drag_release:
                i()

    def drag_start(self):
        self._tmp_points = self.points
        print(self._tmp_points)
        if self.enabled:
            for i in self.on_drag_start:
                i()

    @property
    def drag_objects(self):
        if self.enabled:
            return [self]

    def delete(self):
        if self.enabled:
            self.removeAllChildren()
            self._delete = True

    def check_dependency(self):
        pass


class Marker(Object3D):
    def __init__(self, points, dynamic=False):
        super(Marker, self).__init__(dynamic)
        self.marker = coin.SoMarkerSet()
        self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_7_7
        if depth(points) != 2:
            raise AttributeError("depth of list should be 2")
        self.points = points
        self.addChild(self.marker)


class Line(Object3D):
    def __init__(self, points, dynamic=False):
        super(Line, self).__init__(dynamic)
        self.drawstyle = coin.SoDrawStyle()
        self.line = coin.SoLineSet()
        self.points = points
        self.addChild(self.drawstyle)
        self.addChild(self.line)


class Axis(coin.SoSeparator):
    def __init__(self):
        super(Axis, self).__init__()
        self.xAxisSep = coin.SoSeparator()
        self.yAxisSep = coin.SoSeparator()
        self.zAxisSep = coin.SoSeparator()
        self.xaxisColor = coin.SoBaseColor()
        self.yaxisColor = coin.SoBaseColor()
        self.zaxisColor = coin.SoBaseColor()
        self.xaxisColor.rgb  = (0.8,0,0)
        self.xpts = [] #[[p[0]-1000,p[1],p[2]],[p[0]+1000,p[1],p[2]]]
        self.yaxisColor.rgb  = (0,0.8,0)
        self.ypts = [] #[[p[0],p[1]-1000,p[2]],[p[0],p[1]+1000,p[2]]]
        self.zaxisColor.rgb  = (0,0,0.8)
        self.zpts = [] #[[p[0],p[1],p[2]-1000],[p[0],p[1],p[2]+1000]]
        self.xaxis = coin.SoLineSet()
        self.xaxisPoints = coin.SoCoordinate3()
        self.xaxisPoints.point.setValue(0,0,0)
        self.xaxisPoints.point.setValues(0,len(self.xpts),self.xpts)
        self.xAxisSep.addChild(self.xaxisColor)
        self.xAxisSep.addChild(self.xaxisPoints)
        self.xAxisSep.addChild(self.xaxis)
        self.yaxis = coin.SoLineSet()
        self.yaxisPoints = coin.SoCoordinate3()
        self.yaxisPoints.point.setValue(0,0,0)
        self.yaxisPoints.point.setValues(0,len(self.ypts),self.ypts)
        self.yAxisSep.addChild(self.yaxisColor)
        self.yAxisSep.addChild(self.yaxisPoints)
        self.yAxisSep.addChild(self.yaxis)
        self.zaxis = coin.SoLineSet()
        self.zaxisPoints = coin.SoCoordinate3()
        self.zaxisPoints.point.setValue(0,0,0)
        self.zaxisPoints.point.setValues(0,len(self.zpts),self.zpts)
        self.zAxisSep.addChild(self.zaxisColor)
        self.zAxisSep.addChild(self.zaxisPoints)
        self.zAxisSep.addChild(self.zaxis)
        self.xState = False
        self.yState = False
        self.zState = False

    def setPoint(self,pt):
        p = [pt[0] / pt[3], pt[1] / pt[3], pt[2] / pt[3]]
        self.xpts = [[p[0]-1000,p[1],p[2]],[p[0]+1000,p[1],p[2]]]
        self.ypts = [[p[0],p[1]-1000,p[2]],[p[0],p[1]+1000,p[2]]]
        self.zpts = [[p[0],p[1],p[2]-1000],[p[0],p[1],p[2]+1000]]
        self.xaxisPoints.point.setValue(0,0,0)
        self.xaxisPoints.point.setValues(0,len(self.xpts),self.xpts)
        self.yaxisPoints.point.setValue(0,0,0)
        self.yaxisPoints.point.setValues(0,len(self.ypts),self.ypts)
        self.zaxisPoints.point.setValue(0,0,0)
        self.zaxisPoints.point.setValues(0,len(self.zpts),self.zpts)

    def show(self,x,y,z):

        if (self.xState and not x):
            self.removeChild(self.xAxisSep)
            self.xState = False
        if (self.yState and not y):
            self.removeChild(self.yAxisSep)
            self.yState = False
        if (self.zState and not z):
            self.removeChild(self.zAxisSep)
            self.zState = False
        if (not self.xState and x):
            self.addChild(self.xAxisSep)
            self.xState = True
        if (not self.yState and y):
            self.addChild(self.yAxisSep)
            self.yState = True
        if (not self.zState and z):
            self.addChild(self.zAxisSep)
            self.zState = True



class Container(coin.SoSeparator):
    def __init__(self):
        super(Container, self).__init__()
        self.objects = []
        self.select_object = []
        self.drag_objects = []
        self.over_object = None
        self.start_pos = None
        self.view = None
        self.on_drag = []
        self.on_drag_release = []
        self.on_drag_start = []
        self._direction = None
        self.Axis = None
        self.nbUPoles = 1
        self.nbVPoles = 1

    def addChild(self, child):
        super(Container, self).addChild(child)
        if hasattr(child, "dynamic"):
            if child.dynamic:
                self.objects.append(child)

    def addChildren(self, children):
        for i in children:
            self.addChild(i)

    def Highlight(self, obj):
        if self.over_object:
            self.over_object.unset_mouse_over()
        self.over_object = obj
        if self.over_object:
            self.over_object.set_mouse_over()
        self.ColorSelected()

    def Select(self, obj, multi=False):
        if not multi:
            for o in self.select_object:
                o.unselect()
            self.select_object = []
        if obj:
            if obj in self.select_object:
                self.select_object.remove(obj)
            else:
                self.select_object.append(obj)
                p = obj.points[0]
                if p[3]:
                    s = str(p[0]/p[3])[:5] + " / " + str(p[1]/p[3])[:5] + " / " + str(p[2]/p[3])[:5] + " / " + str(p[3])[:5]
                    App.Console.PrintMessage(s + "\n")
                
        self.ColorSelected()
        self.selection_changed()

    def selection_changed(self):
        pass

    def ColorSelected(self):
        for obj in self.select_object:
            obj.select()

    def cursor_pos(self, event):
        pos = event.getPosition()
        return self.view.getPoint(*pos)

    def mouse_over_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        obj = self.SendRay(pos)
        self.Highlight(obj)

    def SendRay(self, mouse_pos):
        """sends a ray trough the scene and return the nearest entity"""
        render_manager = self.view.getViewer().getSoRenderManager()
        ray_pick = coin.SoRayPickAction(render_manager.getViewportRegion())
        ray_pick.setPoint(coin.SbVec2s(*mouse_pos))
        ray_pick.setRadius(20)
        ray_pick.setPickAll(True)
        ray_pick.apply(render_manager.getSceneGraph())
        picked_point = ray_pick.getPickedPointList()
        return self.ObjById(picked_point)

    def ObjById(self, picked_point):
        for point in picked_point:
            path = point.getPath()
            length = path.getLength()
            point = path.getNode(length - 2)
            point = list(filter(
                lambda ctrl: ctrl.getNodeId() == point.getNodeId(),
                self.objects))
            if point != []:
                return point[0]
        return None

    def select_cb(self, event_callback):
        event = event_callback.getEvent()
        if (event.getState() == coin.SoMouseButtonEvent.DOWN and
                event.getButton() == event.BUTTON1):
            pos = event.getPosition()
            obj = self.SendRay(pos)
            self.Select(obj, event.wasCtrlDown())

    def select_all_cb(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord("a")):
            if event.getState() == event.DOWN:
                if self.select_object:
                    for o in self.select_object:
                        o.unselect()
                    self.select_object = []
                else:
                    for obj in self.objects:
                        if obj.dynamic:
                            self.select_object.append(obj)
                self.ColorSelected()
                self.selection_changed()
        elif (event.getKey() == ord("r")):
            if event.getState() == event.DOWN:
                if self.select_object:
                    active = self.select_object[-1]
                    for o in self.select_object:
                        o.unselect()
                    self.select_object = []
                    i = self.objects.index(active)
                    u = i / self.nbVPoles
                    v = i % self.nbVPoles
                    App.Console.PrintMessage("Point UV : " + str((u,v)) + "\n")
                    for j in range(len(self.objects)):
                        if self.objects[j].dynamic:
                            if ((j / self.nbVPoles) == u ):
                                self.select_object.append(self.objects[j])
                    self.ColorSelected()
                    self.selection_changed()
        elif (event.getKey() == ord("c")):
            if event.getState() == event.DOWN:
                if self.select_object:
                    active = self.select_object[-1]
                    for o in self.select_object:
                        o.unselect()
                    self.select_object = []
                    i = self.objects.index(active)
                    u = i / self.nbVPoles
                    v = i % self.nbVPoles
                    App.Console.PrintMessage("NbUPoles : " + str(self.nbVPoles) + "\n")
                    App.Console.PrintMessage("Point IUV : " + str((i,u,v)) + "\n")
                    for j in range(len(self.objects)):
                        if self.objects[j].dynamic:
                            if ((j % self.nbVPoles) == v ):
                                self.select_object.append(self.objects[j])
                    self.ColorSelected()
                    self.selection_changed()

    def drag_cb(self, event_callback):
        event = event_callback.getEvent()
        if (type(event) == coin.SoMouseButtonEvent and
                event.getState() == coin.SoMouseButtonEvent.DOWN
                and event.getButton() == coin.SoMouseButtonEvent.BUTTON1):
            self.register(self.view)
            if self.drag:
                self.view.removeEventCallbackPivy(
                    coin.SoEvent.getClassTypeId(), self.drag)
                self._direction = None
            self.drag = None
            self.start_pos = None
            self.removeChild(self.Axis)
            self.Axis = None
            for obj in self.drag_objects:
                obj.drag_release()
            for foo in self.on_drag_release:
                foo()
        if (type(event) == coin.SoKeyboardEvent and
                event.getState() == coin.SoMouseButtonEvent.DOWN):
            try:
                key = chr(event.getKey())
            except ValueError:
                # there is no character for this value
                key = "_"
            App.Console.PrintMessage(str(key))
            if key in "sxyz":   # and key != self._direction:
                if key == "s":
                    if self._direction == "s":
                        self.Axis.show(False,False,False)
                        self._direction = None
                    else:
                        self.Axis.show(True,False,False)
                        self._direction = "s"
                elif key == "x":
                    if self._direction == "x":
                        self.Axis.show(False,True,True)
                        self._direction = "yz"
                    elif self._direction == "yz":
                        self.Axis.show(False,False,False)
                        self._direction = None
                    else:
                        self.Axis.show(True,False,False)
                        self._direction = "x"
                elif key == "y":
                    if self._direction == "y":
                        self.Axis.show(True,False,True)
                        self._direction = "xz"
                    elif self._direction == "xz":
                        self.Axis.show(False,False,False)
                        self._direction = None
                    else:
                        self.Axis.show(False,True,False)
                        self._direction = "y"
                elif key == "z":
                    if self._direction == "z":
                        self.Axis.show(True,True,False)
                        self._direction = "xy"
                    elif self._direction == "xy":
                        self.Axis.show(False,False,False)
                        self._direction = None
                    else:
                        self.Axis.show(False,False,True)
                        self._direction = "z"


            diff = self.cursor_pos(event) - self.start_pos
            diff = self.constrained_vector(diff)
            # self.start_pos = self.cursor_pos(event)
            for obj in self.drag_objects:
                obj.drag(diff, 1)
            for foo in self.on_drag:
                foo()
            #self._direction = key

        elif type(event) == coin.SoLocation2Event:
            if   event.wasShiftDown():
                fact = 0.3
                prop = 0.0
            elif event.wasCtrlDown():
                fact = 0.0
                prop = 1.0
            else:
                fact = 1.0
                prop = 0.0
            #fact = 0.3 if event.wasShiftDown() else 1.
            l = 1. * len(self.drag_objects)
            diff = self.cursor_pos(event) - self.start_pos
            diff = self.constrained_vector(diff)
            # self.start_pos = self.cursor_pos(event)
            dol = []
            for obj in self.drag_objects:
                dol.append(self.objects.index(obj))
            dol.sort()
            i = 1.
            for j in dol: #self.objects:
                self.objects[j].drag(diff, fact + prop * i / l)
                #App.Console.PrintMessage("prop : " + str(fact + prop * i / l) + "\n")
                i += 1.
            App.Console.PrintMessage("Drag objects indexes : " + str(dol) + "\n")
            
            for foo in self.on_drag:
                foo()

    def grab_cb(self, event_callback):
        # press g to move an entity
        event = event_callback.getEvent()
        # get all drag objects, every selected object can add some drag objects
        # but the eventhandler is not allowed to call the drag twice on an object
        if event.getKey() == ord("g"):
            self.drag_objects = set()
            for i in self.select_object:
                for j in i.drag_objects:
                    self.drag_objects.add(j)
            if self.select_object:
                p = self.select_object[0].points[0]
                self.Axis = Axis()
                self.Axis.setPoint(p)
                self.addChild(self.Axis)
            # check if something is selected
            if self.drag_objects:
                # first delete the selection_cb, and higlight_cb
                self.unregister()
                # now add a callback that calls the dragfunction of the selected entities
                self.start_pos = self.cursor_pos(event)
                self.drag = self.view.addEventCallbackPivy(
                    coin.SoEvent.getClassTypeId(), self.drag_cb)
                for obj in self.drag_objects:
                    obj.drag_start()
                for foo in self.on_drag_start:
                    foo()

    def delete_cb(self, event_callback):
        event = event_callback.getEvent()
        # get all drag objects, every selected object can add some drag objects
        # but the eventhandler is not allowed to call the drag twice on an object
        if event.getKey() == ord("x"):
            #self.removeSelected()
            pass

    def quit_cb(self, event_callback):
        event = event_callback.getEvent()
        # get all drag objects, every selected object can add some drag objects
        # but the eventhandler is not allowed to call the drag twice on an object
        if event.getKey() == ord("q"):
            self.removeAllChildren()
            self.unregister()

    def register(self, view):
        self.view = view
        self.mouse_over = self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over_cb)
        self.select = self.view.addEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select_cb)
        self.grab = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.grab_cb)
        self.delete = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.delete_cb)
        self.select_all = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all_cb)
        self.quit = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.quit_cb)

    def unregister(self):
        self.view.removeEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over)
        self.view.removeEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.grab)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.delete)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.quit)

    def removeSelected(self):
        temp = []
        for i in self.select_object:
            i.delete()
        for i in self.objects:
            i.check_dependency()    #dependency length max = 1
        for i in self.objects:
            if i._delete:
                temp.append(i)
        self.select_object = []
        self.over_object = None
        for i in temp:
            self.objects.remove(i)
            self.removeChild(i)
        self.selection_changed()

    def removeAllChildren(self):
        for i in self.objects:
            i.delete()
        self.objects = []
        super(Container, self).removeAllChildren()

    def constrained_vector(self, vector):
        if self._direction is None:
            return [vector[0], vector[1], vector[2]]
        elif self._direction == "x":
            return [vector[0], 0, 0]
        elif self._direction == "y":
            return [0, vector[1], 0]
        elif self._direction == "z":
            return [0, 0, vector[2]]
        elif self._direction == "yz":
            return [0, vector[1], vector[2]]
        elif self._direction == "xz":
            return [vector[0], 0, vector[2]]
        elif self._direction == "xy":
            return [vector[0], vector[1], 0]
        elif self._direction == "xy":
            return [vector[0], vector[1], 0]
        elif self._direction == "s":
            return vector[0]

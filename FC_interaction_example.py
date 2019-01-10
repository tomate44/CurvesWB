import FreeCAD
import FreeCADGui
import Part

import _utils

import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QColor
from pivy import quarter, coin, graphics, utils

class ConnectionMarker(graphics.Marker):
    def __init__(self, points):
        super(ConnectionMarker, self).__init__(points, True)

class MarkerOnEdge(graphics.Marker):
    def __init__(self, tuples):
        points = list()
        for t in tuples:
            points.append(t[0].valueAt(t[1]))
        super(MarkerOnEdge, self).__init__(points, True)
        self.edge_params = tuples

    def __repr__(self):
        pts = list()
        for p in self.points:
            pts.append(p.getValue())
        return("MarkerOnEdge(%s)"%pts)

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, p in enumerate(pts):
                p[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                p[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                p[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
                v = Part.Vertex(p[0],p[1],p[2])
                proj = v.distToShape(self.edge_params[i][0])[1][0][1]
                # FreeCAD.Console.PrintMessage("%s -> %s\n"%(p.getValue(),proj))
                p[0] = proj.x
                p[1] = proj.y
                p[2] = proj.z
                self.edge_params[i][1] = self.edge_params[i][0].Curve.parameter(proj)
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

class InterpolationPolygon(object):
    def __init__(self, points=[]):
        if len(points) > 0:
            if isinstance(points[0],FreeCAD.Vector):
                self.points = points
            elif isinstance(points[0],tuple):




def get_guide_params():
    sel = Gui.Selection.getSelectionEx()
    pts = list()
    for so in sel:
        pts.extend(so.PickedPoints)
    edges = list()
    for so in sel:
        for sen in so.SubElementNames:
            n = eval(sen.lstrip("Edge"))
            e = so.Object.Shape.Edges[n-1]
            edges.append(e)
    inter = list()
    for pt in pts:
        sol = None
        min = 1e50
        for e in edges:
            d,points,info = e.distToShape(Part.Vertex(pt))
            if d < min:
                min = d
                sol = [e,e.Curve.parameter(points[0][0])]
        inter.append(sol)
    return(inter)

def controlCB(attr, event_callback):
    event = event_callback.getEvent()
    FreeCAD.Console.PrintMessage("Key pressed : %s\n"%chr(event.getKey()))
    if event.getKey() == ord("s"):
        pass
    elif event.getKey() == ord("q"):
        pass


def main():
#    app = QApplication(sys.argv)
#    utils.addMarkerFromSvg("test.svg", "CUSTOM_MARKER",  40)
#    viewer = quarter.QuarterWidget()
#    root = graphics.InteractionSeparator(viewer.sorendermanager)
    if not FreeCAD.ActiveDocument:
        appdoc = FreeCAD.newDocument("New")
    doc = FreeCADGui.ActiveDocument
    view = doc.ActiveView
    viewer = view.getViewer()
    rm = viewer.getSoRenderManager()
    sg = view.getSceneGraph()
    root = graphics.InteractionSeparator(rm)
    root.pick_radius = 40

    events = coin.SoEventCallback()
    _controlCB = events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), controlCB)
    root.addChild(events)
    # events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), _controlCB)


    points = list()
    for s in get_guide_params():
        moe = MarkerOnEdge([s])
        points.append(moe)
    print(points)

    my_range = list(range(1,len(points)))
    my_range.reverse()
    new = list()
    for i in my_range:
        p1 = points[i-1].points[0]
        p2 = points[i].points[0]
        mp = (p1+p2)/2.0
        FreeCAD.Console.PrintMessage("inserting %s at index %d\n"%(str(mp.getValue()),i))
        points.insert(i,ConnectionMarker([mp]))
        

    lines = [ConnectionLine([points[i], points[i+1]]) for i in range(len(points)-1)]
    print(lines)


    

    root += points + lines # + polygons
    root.register()

    sg.addChild(root)


if __name__ == '__main__':
    main()

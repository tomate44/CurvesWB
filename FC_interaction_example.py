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
    def __init__(self, points):
        super(ConnectionMarker, self).__init__(points, True)
    def __repr__(self):
        pts = list()
        for p in self.points:
            pts.append(p.getValue())
        return("MarkerOnEdge(%s)"%pts)
    def stickOnEdge(self,e):
        if isinstance(e,Part.Edge):
            self.edge = e
            self.parameters = [e.Curve.parameter(FreeCAD.Vector(p.getValue())) for p in self.points]
            # TODO implement edge constraint
            for m in self.markers:
                m.on_drag.append(self.updatePolygon)
        if len(self.parameters) == len(self.points):
            return(True)
        return(False)


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

    #print(get_guide_params())

#    m1 = ConnectionMarker([[-1, -1, -1]])
#    m2 = ConnectionMarker([[-1,  1, -1]])
#    m3 = ConnectionMarker([[ 1,  1, -1]])
#    m4 = ConnectionMarker([[ 1, -1, -1]])
#
#    m5 = ConnectionMarker([[-1, -1,  1]])
#    m6 = ConnectionMarker([[-1,  1,  1]])
#    m7 = ConnectionMarker([[ 1,  1,  1]])
#    m8 = ConnectionMarker([[ 1, -1,  1]])

    points = [ConnectionMarker([s[0].valueAt(s[1])]) for s in get_guide_params()]
    print(points)

    lines = [ConnectionLine([points[i], points[i+1]]) for i in range(len(points)-1)]
    print(lines)

#    l01 = ConnectionLine([m1, m2])
#    l02 = ConnectionLine([m2, m3])
#    l03 = ConnectionLine([m3, m4])
#    l04 = ConnectionLine([m4, m1])
#
#    l05 = ConnectionLine([m5, m6])
#    l06 = ConnectionLine([m6, m7])
#    l07 = ConnectionLine([m7, m8])
#    l08 = ConnectionLine([m8, m5])
#
#    l09 = ConnectionLine([m1, m5])
#    l10 = ConnectionLine([m2, m6])
#    l11 = ConnectionLine([m3, m7])
#    l12 = ConnectionLine([m4, m8])

#    lines = [l01, l02, l03, l04, l05, l06, l07, l08, l09, l10, l11, l12]
#
#    p1 = ConnectionPolygon([m1, m2, m3, m4])
#    p2 = ConnectionPolygon([m8, m7, m6, m5])
#    p3 = ConnectionPolygon([m5, m6, m2, m1])
#    p4 = ConnectionPolygon([m6, m7, m3, m2])
#    p5 = ConnectionPolygon([m7, m8, m4, m3])
#    p6 = ConnectionPolygon([m8, m5, m1, m4])
#
#    polygons = [p1, p2, p3, p4, p5, p6]
    root += points + lines # + polygons
    root.register()

    sg.addChild(root)
#    viewer.setBackgroundColor(QColor(255, 255, 255))
#    viewer.setWindowTitle("minimal")
#    viewer.show()
#    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

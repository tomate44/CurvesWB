# SPDX-License-Identifier: LGPL-2.1-or-later

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
# not yet implemented
#class MarkerOnShape(graphics.Marker):
    #def __init__(self, points, shape=None):
        #super(MarkerOnShape, self).__init__(points, True)
        #if isinstance(shape,Part.Shape):
            #self.support = shape
        #else:
            #ci = Part.Geom2d.Circle2d()
            #ci.Radius = 1e50
            #self.support = ci.toShape(shape)

    #def __repr__(self):
        ##pts = list()
        ##for p in self.points:
            ##pts.append(p.getValue())
        #return("MarkerOnShape(%s)"%self.support)

    #def drag(self, mouse_coords, fact=1.):
        #if self.enabled:
            #pts = self.points
            #for i, p in enumerate(pts):
                #p[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                #p[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                #p[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
                #v = Part.Vertex(p[0],p[1],p[2])
                #proj = v.distToShape(self.support)[1][0][1]
                ## FreeCAD.Console.PrintMessage("%s -> %s\n"%(p.getValue(),proj))
                #p[0] = proj.x
                #p[1] = proj.y
                #p[2] = proj.z
                ##self.edge_params[i][1] = self.edge_params[i][0].Curve.parameter(proj)
            #self.points = pts
            #for foo in self.on_drag:
                #foo()


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
    def __init__(self, points=[], fp = None):
        self.points = points
        self.curve = Part.BSplineCurve()
        self.fp = fp
        self.root_inserted = False
        #self.support = None # Not yet implemented
        if len(points) > 0:
            if isinstance(points[0],FreeCAD.Vector):
                self.points = [ConnectionMarker([p]) for p in points]
            elif isinstance(points[0],(tuple,list)):
                self.points = [MarkerOnEdge([p]) for p in points]
            else:
                FreeCAD.Console.PrintError("InterpolationPolygon : bad input")
        
        # Setup coin objects
        if not FreeCAD.ActiveDocument:
            appdoc = FreeCAD.newDocument("New")
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
        self.root.pick_radius = 40
        self.root.on_drag.append(self.update_curve)
        # Keyboard callback
        #self.events = coin.SoEventCallback()
        self._controlCB = self.root.events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self.controlCB)
        # populate root node
        #self.root.addChild(self.events)
        self.root += self.points
        self.build_lines()
        self.root += self.lines
        self.root.register()
        self.sg.addChild(self.root)
        self.root_inserted = True

    def update_curve(self):
        pts = list()
        for p in self.points:
            pts += p.points
        FreeCAD.Console.PrintMessage("pts :\n%s\n"%str(pts))
        if len(pts) > 1:
            self.curve.interpolate(pts)
            #FreeCAD.Console.PrintMessage("update_curve\n")
            if self.fp:
                self.fp.Shape = self.curve.toShape()

    def build_lines(self):
        self.lines = list()
        for i in range(len(self.points)-1):
            line = ConnectionLine([self.points[i], self.points[i+1]]) 
            line.set_color("blue")
            self.lines.append(line)
    
    def controlCB(self, attr, event_callback):
        event = event_callback.getEvent()
        if event.getState() == event.UP:
            FreeCAD.Console.PrintMessage("Key pressed : %s\n"%chr(event.getKey()))
            if event.getKey() == ord("s"):
                self.subdivide()
            elif event.getKey() == ord("q"):
                self.quit()
    
    def subdivide(self):
        # get selected lines and subdivide them
        pts = list()
        for o in self.lines:
            FreeCAD.Console.PrintMessage("object %s\n"%str(o))
            if isinstance(o,ConnectionLine):
                pts.append(o.markers[0])
                if o in self.root.selected_objects:
                    idx = self.lines.index(o)
                    FreeCAD.Console.PrintMessage("Subdividing line #%d\n"%idx)
    #                m1,m2 = o.markers
    #                i1 = self.points.index(m1)
    #                i2 = self.points.index(m2)
                    p1 = o.markers[0].points[0]
                    p2 = o.markers[1].points[0]
                    #mp = (p1+p2)/2.0
                    #pts.append(ConnectionMarker([mp]))
                    par1 = self.curve.parameter(FreeCAD.Vector(p1))
                    par2 = self.curve.parameter(FreeCAD.Vector(p2))
                    midpar = (par1+par2)/2.0
                    pts.append(ConnectionMarker([self.curve.value(midpar)]))                    
        pts.append(self.points[-1])
        self.points = pts
        self.setup_InteractionSeparator()
        self.update_curve()
        return(True)
    
    def quit(self):
        #self.sg.removeChild(self.root)
        #self.root_inserted = False
        self.root.events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self._controlCB)
        self.root.unregister()
        self.sg.removeChild(self.root)
        self.root_inserted = False
            



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
    obj = FreeCAD.ActiveDocument.addObject("Part::Spline","profile")
    tups = get_guide_params()
    ip = InterpolationPolygon(tups, obj)
    FreeCAD.ActiveDocument.recompute()

if __name__ == '__main__':
    main()

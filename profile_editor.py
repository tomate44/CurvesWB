import FreeCAD
import FreeCADGui
import Part

import _utils

import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QColor
from pivy import quarter, coin, graphics, utils


def subshape_from_sublink(o):
    name = o[1][0]
    if 'Vertex' in name:
        n = eval(name.lstrip('Vertex'))
        return(o[0].Shape.Vertexes[n-1])
    elif 'Edge' in name:
        n = eval(name.lstrip('Edge'))
        return(o[0].Shape.Edges[n-1])
    elif 'Face' in name:
        n = eval(name.lstrip('Face'))
        return(o[0].Shape.Faces[n-1])

class ConnectionMarker(graphics.Marker):
    def __init__(self, points):
        super(ConnectionMarker, self).__init__(points, True)

class MarkerOnShape(graphics.Marker):
    def __init__(self, points, sh=None):
        super(MarkerOnShape, self).__init__(points, True)
        self.shape = None
        self.sublink = None
        if isinstance(sh,Part.Shape):
            self.shape = sh
        elif isinstance(sh,(tuple,list)):
            if True: # I should put a try / except here
                self.shape = subshape_from_sublink(sh)
                self.sublink = sh

    def __repr__(self):
        return("MarkerOnShape(%s)"%self.shape)

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, p in enumerate(pts):
                p[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                p[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                p[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
                if self.shape:
                    v = Part.Vertex(p[0],p[1],p[2])
                    proj = v.distToShape(self.shape)[1][0][1]
                    # FreeCAD.Console.PrintMessage("%s -> %s\n"%(p.getValue(),proj))
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

class InterpoCurveEditor(object):
    """Interpolation curve free-hand editor
    my_editor = InterpoCurveEditor([points],obj)
    obj is the FreeCAD object that will recieve
    the curve shape at the end of editing.
    points can be :
    - Vector (free point)
    - (Vector, shape) (point on shape)"""
    def __init__(self, points=[], fp = None):
        self.points = list()
        self.curve = Part.BSplineCurve()
        self.fp = fp
        self.root_inserted = False
        #self.support = None # Not yet implemented
        for p in points:
            if isinstance(p,FreeCAD.Vector):
                self.points.append(MarkerOnShape([p]))
            elif isinstance(p,(tuple,list)):
                self.points.append(MarkerOnShape([p[0]],p[1]))
            elif isinstance(p,(MarkerOnShape, ConnectionMarker)):
                self.points.append(p)
            else:
                FreeCAD.Console.PrintError("InterpoCurveEditor : bad input")
        
        # Setup coin objects
        if self.fp:
            self.guidoc = self.fp.ViewObject.Document
        else:
            if not FreeCADGui.ActiveDocument:
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
        #FreeCAD.Console.PrintMessage("pts :\n%s\n"%str(pts))
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
            FreeCAD.Console.PrintMessage("Key pressed : %s\n"%event.getKey())
            if event.getKey() == ord("s"):
                self.subdivide()
            elif event.getKey() == ord("q"):
                if self.fp:
                    self.fp.ViewObject.Proxy.doubleClicked(self.fp.ViewObject)
                else:
                    self.quit()
            elif (event.getKey() == 65535) or (event.getKey() == 65288): # Suppr or Backspace
                FreeCAD.Console.PrintMessage("Some objects have been deleted\n")
                pts = list()
                for o in self.root.dynamic_objects:
                    if isinstance(o,MarkerOnShape):
                        pts.append(o)
                self.points = pts
                self.setup_InteractionSeparator()
                self.update_curve()
    
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
                    pts.append(MarkerOnShape([self.curve.value(midpar)]))                    
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
        #self.root.removeAllChildren()
        self.sg.removeChild(self.root)
        self.root_inserted = False
            



def get_guide_params():
    sel = FreeCADGui.Selection.getSelectionEx()
    pts = list()
    for s in sel:
        pts.extend(list(zip(s.PickedPoints,s.SubObjects)))
    return(pts)

def main():
    obj = FreeCAD.ActiveDocument.addObject("Part::Spline","profile")
    tups = get_guide_params()
    ip = InterpoCurveEditor(tups, obj)
    FreeCAD.ActiveDocument.recompute()

if __name__ == '__main__':
    main()

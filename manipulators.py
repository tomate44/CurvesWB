# -*- coding: utf-8 -*-

__title__ = "Manipulators"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "FreeCAD interactive editing library"

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
#import FreeCADGui
#import Part
#import _utils
#from pivy import coin
import graphics


class Point(graphics.Marker):
    def __init__(self, points):
        if isinstance(points, (list, tuple)):
            pts = [self.vector(p) for p in points]
        else:
            pts = [self.vector(points)]
        super(Point, self).__init__(pts, True)
            
    def vector(self, p):
        if isinstance(p, FreeCAD.Vector):
            return p
        elif isinstance(p, Part.Vertex):
            return p.Point
        elif isinstance(p, Part.Point):
            return FreeCAD.Vector(p[0],p[1],p[2])
        else:
            return None
            
    @property 
    def vectors(self):
        return [FreeCAD.Vector(p[0],p[1],p[2]) for p in self.points]
        
class ShapeSnap(object):
    def __init__(self, sh=None):
        self.snap_shape = sh
    @property
    def snap_shape(self):
        return self._shape
    @snap_shape.setter
    def snap_shape(self, sh):
        if isinstance(sh,Part.Shape):
            self._shape = sh
            self.on_drag.append(self.snap_drag)
        else:
            self._shape = None
            if self.snap_drag in self.on_drag:
                self.on_drag.remove(self.snap_drag)
    def snap_drag(self):
        if self.enabled:
            pts = self.points
            for p in pts:
                v = Part.Vertex(p[0],p[1],p[2])
                proj = v.distToShape(self._shape)[1][0][1]
                # FreeCAD.Console.PrintMessage("%s -> %s\n"%(p.getValue(),proj))
                p[0] = proj.x
                p[1] = proj.y
                p[2] = proj.z
            self.points = pts


class MarkerOnShape(graphics.Marker):
    def __init__(self, points, sh=None):
        super(MarkerOnShape, self).__init__(points, True)
        self._shape = None
        self._sublink = None
        self._tangent = None
        self._translate = coin.SoTranslation()
        self._text = coin.SoText2()
        self._text_switch = coin.SoSwitch()
        self._text_switch.addChild(self._translate)
        self._text_switch.addChild(self._text)
        self.on_drag_start.append(self.add_text)
        self.on_drag_release.append(self.remove_text)
        self.addChild(self._text_switch)
        
        if isinstance(sh,Part.Shape):
            self.snap_shape = sh
        elif isinstance(sh,(tuple,list)):
            self.sublink = sh

    def subshape_from_sublink(self, o):
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

    def add_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_ALL
        self.on_drag.append(self.update_text)
        
    def remove_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_NONE
        self.on_drag.remove(self.update_text)
        
    def update_text(self):
        p = self.points[0]
        coords = ['{: 9.3f}'.format(p[0]),'{: 9.3f}'.format(p[1]),'{: 9.3f}'.format(p[2])]
        self._translate.translation = p
        self._text.string.setValues(0,3,coords)

    @property
    def tangent(self):
        return self._tangent
    @tangent.setter
    def tangent(self, t):
        if isinstance(t,FreeCAD.Vector):
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
        if isinstance(sh,Part.Shape):
            self._shape = sh
        else:
            self._shape = None
        self.alter_color()

    @property
    def sublink(self):
        return self._sublink
    @sublink.setter
    def sublink(self, sl):
        if isinstance(sl,(tuple,list)) and not (sl == self._sublink):
            self._shape = self.subshape_from_sublink(sl)
            self._sublink = sl
        else:
            self._shape = None
            self._sublink = None
        self.alter_color()

    def alter_color(self):
        if   isinstance(self._shape, Part.Vertex):
            self.set_color("white")
        elif isinstance(self._shape, Part.Edge):
            self.set_color("cyan")
        elif isinstance(self._shape, Part.Face):
            self.set_color("magenta")
        else:
            self.set_color("black")

    def __repr__(self):
        return("MarkerOnShape(%s)"%self._shape)

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, p in enumerate(pts):
                p[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                p[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                p[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
                if self._shape:
                    v = Part.Vertex(p[0],p[1],p[2])
                    proj = v.distToShape(self._shape)[1][0][1]
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
        self._linear = False
        for m in self.markers:
            m.on_drag.append(self.updateLine)

    def updateLine(self):
        self.points = sum([m.points for m in self.markers], [])
        if self._linear:
            p1 = self.markers[0].points[0]
            p2 = self.markers[-1].points[0]
            t = p2-p1
            tan = FreeCAD.Vector(t[0],t[1],t[2])
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

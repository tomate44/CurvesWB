# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Manipulators"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "FreeCAD interactive editing library"

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
#import FreeCADGui
import Part
#import _utils
from pivy import coin
from freecad.Curves import graphics

class Object3D(graphics.Object3D):
    """freeCAD manipulator base class"""
    def __init__(self, points, dynamic=True):
        if isinstance(points, (list, tuple)):
            pts = [self.vector(p) for p in points]
        else:
            pts = [self.vector(points)]
        super(Object3D, self).__init__(pts, dynamic)
        self.ctrl_keys = dict()
    def vector(self, p):
        if isinstance(p, FreeCAD.Vector):
            return p
        elif isinstance(p, Part.Vertex):
            return p.Point
        else:
            return FreeCAD.Vector(p[0],p[1],p[2])
    @property 
    def vectors(self):
        return [FreeCAD.Vector(p[0],p[1],p[2]) for p in self.points]
    @property 
    def point(self):
        return self.vector(self.points[0])


class Point(Object3D):
    """Basic point manipulator"""
    def __init__(self, points, dynamic=True):
        super(Point, self).__init__(points, dynamic)
        self.marker = coin.SoMarkerSet()
        self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_5_5
        self.addChild(self.marker)
        
class ShapeSnap(Point):
    """Point manipulator that snaps to a shape"""
    def __init__(self, points, sh=None):
        super(ShapeSnap, self).__init__(points)
        self.snap_shape = sh
    @property
    def snap_shape(self):
        return self._shape
    @snap_shape.setter
    def snap_shape(self, sh):
        if isinstance(sh,Part.Shape):
            self._shape = sh
            if not self.snap_drag in self.on_drag:
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
                proj = v.distToShape(self.snap_shape)[1][0][1]
                # FreeCAD.Console.PrintMessage("%s -> %s\n"%(p.getValue(),proj))
                p[0] = proj.x
                p[1] = proj.y
                p[2] = proj.z
            self.points = pts

class EdgeSnapAndTangent(ShapeSnap):
    """Point manipulator that snaps to an edge, and generates
    a tangent edge that another manipulator can snap to"""
    def __init__(self, points, sh=None):
        super(EdgeSnapAndTangent, self).__init__(points, sh)
        #self.tangent = None
        self.tangent_update()
        #self.tangent_update_cb = []
        self.on_drag.append(self.tangent_update)
    def tangent_update(self):
        v = Part.Vertex(self.point)
        p = v.distToShape(self.snap_shape)[1][0][1]
        try:
            par = self.snap_shape.Curve.parameter(p)
        except:
            print("Failed to get curve parameter")
            par = self.snap_shape.FirstParameter
        #print(par)
        tan = self.snap_shape.tangentAt(par)
        e = Part.makeLine(p, p+tan)
        self.tangent =  e.Curve.toShape(-2e10, 2e10)


class SubLinkSnap(ShapeSnap):
    """Point manipulator that snaps to a shape provided by a PropertySubLink"""
    def __init__(self, points, sl=None):
        super(SubLinkSnap, self).__init__(points, True)
        sublink = sl
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
    @property
    def sublink(self):
        return self._sublink
    @sublink.setter
    def sublink(self, sl):
        sub = None
        if isinstance(sl,(tuple,list)) and not (sl == self._sublink):
            sub = self.subshape_from_sublink(sl)
        if sub:
            self._sublink = sl
            self.snap_shape = sub
        else:
            self._sublink = None
            self.snap_shape = None

class TangentSnap(ShapeSnap):
    """Point manipulator that snaps to the tangent of a ShapeSnap manipulator"""
    def __init__(self, manip):
        super(TangentSnap, self).__init__(FreeCAD.Vector())
        self.parent = manip
        self._par = 1.0
        self._scale = 1.0
        self.update_tangent()
        #p = self.snap_shape.valueAt(self.par)
        #self.points = [p]
        self.parent.on_drag.append(self.update_tangent)
        self.on_drag.append(self.update_parameter)
    def update_tangent(self):
        self.snap_shape = self.parent.tangent
        self.points = [self.snap_shape.valueAt(self._par * self._scale)]
    def update_parameter(self):
        p = self.vector(self.points[0])
        self._par = self.snap_shape.Curve.parameter(p) / self._scale
    @property
    def parameter(self):
        return self._par
    @parameter.setter
    def parameter(self, t):
        self._par = t
        self.points = [self.snap_shape.valueAt(self._par * self._scale)]
        

class WithCustomTangent(object):
    """Point Extension class that adds a custom tangent"""
    def __init__(self):
        self._tangent = None
    @property
    def tangent(self):
        return self._tangent
    @tangent.setter
    def tangent(self, t):
        if isinstance(t, FreeCAD.Vector) and t.Length > 1e-7:
            self._tangent = t
            #self._tangent.normalize()
            self.marker.markerIndex = coin.SoMarkerSet.DIAMOND_FILLED_9_9
        else:
            self._tangent = None
            self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9
    def set_tangent_toward_point(self, p):
        if self.vector(p):
            self.tangent = self.vector(p) - self.vector(self.points[0])

class CustomText(Object3D):
    """Text manipulator"""
    def __init__(self, parent, dynamic=False):
        super(CustomText, self).__init__(parent.points, dynamic)
        #self._text_offset = FreeCAD.Vector(0,0,0)
        self._text_translate = coin.SoTranslation()
        self._text_font = coin.SoFont()
        self._text_font.name = "Arial:Bold"
        self._text_font.size = 13.0
        self._text = coin.SoText2()
        self._text_switch = coin.SoSwitch()
        self._text_switch.addChild(self._text_translate)
        self._text_switch.addChild(self._text_font)
        self._text_switch.addChild(self._text)
        self.addChild(self._text_switch)
        self.parent = parent
        self.parent.on_drag.append(self.translate)
        self.translate()
    def show(self):
        self._text_switch.whichChild = coin.SO_SWITCH_ALL
    def hide(self):
        self._text_switch.whichChild = coin.SO_SWITCH_NONE
    def translate(self):
        self._text_translate.translation = self.parent.point
    @property
    def text(self):
        return self._text.string.getValues()
    @text.setter
    def text(self, txt):
        strlist = []
        if isinstance(txt, str):
            strlist = [txt]
        elif isinstance(txt, (list, tuple)):
            strlist = txt
        self._text.string.setValues(0, len(strlist), strlist)

class CycleText(CustomText):
    """Text manipulator that cycles through a list of strings"""
    def __init__(self, parent, dynamic=False):
        super(CycleText, self).__init__(parent, dynamic)
        self.text_list = ["",]
        self.ctrl_keys = {"c" : [self.cycle]}
    def cycle(self):
        if self.text[0] in self.text_list:
            n = self.text_list.index(self.text[0])
            if n < len(self.text_list)-1:
                self.text = self.text_list[n+1]
            else:
                self.text = self.text_list[0]
        else:
            self.text = self.text_list[0]

class ParameterText(CustomText):
    """Text manipulator that displays the parameter value of its parent"""
    def __init__(self, parent, dynamic=False):
        super(ParameterText, self).__init__(parent, dynamic)
        self.parent.on_drag.append(self.update_text)
        if hasattr(self.parent, "parent"):
            self.parent.parent.on_drag.append(self.translate)
    def update_text(self):
        self.text = '{: 9.3f}'.format(self.parent.parameter)

class MarkerOnShape(graphics.Marker):
    def __init__(self, points, sh=None):
        super(MarkerOnShape, self).__init__(points, True)
        self._shape = None
        self._sublink = None
        self._tangent = None
        self._text_translate = coin.SoTranslation()
        self._text = coin.SoText2()
        self._text_switch = coin.SoSwitch()
        self._text_switch.addChild(self._text_translate)
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
        self._text_translate.translation = p
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

class Line(graphics.Line):
    def __init__(self, markers):
        super(Line, self).__init__(
            sum([m.points for m in markers], []), True)
        self.markers = markers
        for m in self.markers: # If some markers are moved ...
            m.on_drag.append(self.updateLine)
        #self.markers[0].on_drag.append(self.updateLine)

    def updateLine(self): # ... consecutively copy their points (SoCoordinate3)
        self.points = sum([m.points for m in self.markers], [])

    @property
    def drag_objects(self):
        return self.markers

    def check_dependency(self):
        if any([m._delete for m in self.markers]):
            self.delete()

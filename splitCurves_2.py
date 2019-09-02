# -*- coding: utf-8 -*-

__title__ = "Split curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Splits the selected edge."

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
from pivy import coin
import graphics
import profile_editor

TOOL_ICON = _utils.iconsPath() + '/splitcurve.svg'
debug = _utils.debug
#debug = _utils.doNothing

class split:
    """Splits the selected edge."""
    def __init__(self, obj, e):
        obj.Proxy = self
        obj.addProperty("App::PropertyLinkSub",
                        "Source",
                        "Split",
                        "Edge to split").Source = e
        obj.addProperty("App::PropertyStringList",
                        "Values",
                        "Split",
                        "List of splitting locations\n% and units are allowed\nNegative values are computed from edge end")
        #obj.addProperty("App::PropertyFloatList",
                        #"Parameters",
                        #"Split",
                        #"Parameter list")
        #obj.setEditorMode("Parameters",2)

    def parse_values(self, edge, values):
        #edge = _utils.getShape(fp, "Source", "Edge")
        if not edge:
            return
        l = edge.Length
        parameters = []
        for v in values:
            num_val = None
            par = None
            if "%" in v:
                num_val = float(v.split("%")[0]) * l / 100
            else:
                num_val = FreeCAD.Units.parseQuantity(v).Value
            if num_val < 0:
                par = edge.Curve.parameterAtDistance(num_val, edge.LastParameter)
            else:
                par = edge.Curve.parameterAtDistance(num_val, edge.FirstParameter)
            if par > edge.FirstParameter and par < edge.LastParameter :
                parameters.append(par)
        parameters.sort()
        return parameters

    def onChanged(self, fp, prop):
        e = None
        if hasattr(fp, "Source"):
            e = _utils.getShape(fp, "Source", "Edge")
        if not e:
            return
        if prop == "Source":
            debug("Split : Source changed")
            self.execute(fp)
        if prop == "Values":
            debug("Split : Values changed")
            self.execute(fp)

    def execute(self, obj):
        e = _utils.getShape(obj, "Source", "Edge")
        params = []
        if hasattr(obj, "Values"):
            params = self.parse_values(e, obj.Values)
        if params == []:
            obj.Shape = e
            return
        if params[0] > e.FirstParameter:
            params.insert(0, e.FirstParameter)
        if params[-1] < e.LastParameter:
            params.append(e.LastParameter)
        edges = []
        for i in range(len(params)-1):
            c = e.Curve.trim(params[i], params[i+1])
            edges.append(c.toShape())
        w = Part.Wire(edges)
        if w.isValid():
            obj.Shape = w
        else:
            FreeCAD.Console.PrintError("Split curve : Invalid Wire !")
            obj.Shape = e

class MarkerOnEdge(graphics.Marker):
    def __init__(self, points, sh=None):
        super(MarkerOnEdge, self).__init__(points, True)
        self._shape = None
        self._sublink = None
        self._tangent = None
        self._text_type = 0
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

    def add_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_ALL
        self.on_drag.append(self.update_text)
        
    def remove_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_NONE
        self.on_drag.remove(self.update_text)
        
    def update_text(self):
        p = self.points[0]
        par = self._shape.Curve.parameter(FreeCAD.Vector(p[0],p[1],p[2]))
        if self._text_type == 0 :
            coords = ['{: 9.3f}'.format(par)]
        elif self._text_type == 1 :
            c = self._shape.Curve.trim(self._shape.FirstParameter, par)
            abscissa = c.length()
            coords = ['{: 9.3f} mm'.format(abscissa)]
        elif self._text_type == 2 :
            if par <= self._shape.FirstParameter:
                abscissa = 0
            else:
                c = self._shape.Curve.trim(self._shape.FirstParameter, par)
                abscissa = c.length()
            perc = 100 * abscissa / self._shape.Length
            coords = ['{: 9.3f} %'.format(perc)]
        self._text_translate.translation = p
        self._text.string.setValues(0,len(coords),coords)

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
        # self.alter_color()

    @property
    def sublink(self):
        return self._sublink
    @sublink.setter
    def sublink(self, sl):
        if isinstance(sl,(tuple,list)) and not (sl == self._sublink):
            self._shape = subshape_from_sublink(sl)
            self._sublink = sl
        else:
            self._shape = None
            self._sublink = None
        # self.alter_color()

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


class pointEditor(object):
    """Interpolation curve free-hand editor
    my_editor = pointEditor([points],obj)
    obj is the FreeCAD object that will receive
    the curve shape at the end of editing.
    points can be :
    - Vector (free point)
    - (Vector, shape) (point on shape)"""
    def __init__(self, points=[], fp = None):
        self.points = list()
        self.fp = fp
        self.curve = None
        self.root_inserted = False
        for p in points:
            if isinstance(p,FreeCAD.Vector):
                self.points.append(MarkerOnEdge([p]))
            elif isinstance(p,(tuple,list)):
                self.points.append(MarkerOnEdge([p[0]],p[1]))
            elif isinstance(p, MarkerOnEdge):
                self.points.append(p)
            else:
                FreeCAD.Console.PrintError("pointEditor : bad input")
        
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

    def setup_InteractionSeparator(self):
        if self.root_inserted:
            self.sg.removeChild(self.root)
        self.root = graphics.InteractionSeparator(self.rm)
        self.root.setName("InteractionSeparator")
        #self.root.ovr_col = "yellow"
        #self.root.sel_col = "green"
        self.root.pick_radius = 40
        #self.root.on_drag.append(self.update_curve)
        # Keyboard callback
        #self.events = coin.SoEventCallback()
        self._controlCB = self.root.events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self.controlCB)
        # populate root node
        #self.root.addChild(self.events)
        self.root += self.points
        #self.build_lines()
        #self.root += self.lines
        # set FreeCAD color scheme
        for o in self.points: # + self.lines:
            o.ovr_col = "yellow"
            o.sel_col = "green"
        self.root.register()
        self.sg.addChild(self.root)
        self.root_inserted = True
        self.root.selected_objects = list()

    def build_lines(self):
        self.lines = list()
        for i in range(len(self.points)-1):
            line = profile_editor.ConnectionLine([self.points[i], self.points[i+1]]) 
            line.set_color("blue")
            self.lines.append(line)

    def controlCB(self, attr, event_callback):
        event = event_callback.getEvent()
        if event.getState() == event.UP:
            #FreeCAD.Console.PrintMessage("Key pressed : %s\n"%event.getKey())
            if event.getKey() == ord("i"):
                self.insert()
            elif event.getKey() == ord("v"):
                self.text_change()
            elif event.getKey() == ord("q"):
                if self.fp:
                    self.fp.ViewObject.Proxy.doubleClicked(self.fp.ViewObject)
                else:
                    self.quit()
            elif (event.getKey() == 65535) or (event.getKey() == 65288): # Suppr or Backspace
                #FreeCAD.Console.PrintMessage("Some objects have been deleted\n")
                pts = list()
                for o in self.root.dynamic_objects:
                    if isinstance(o,MarkerOnEdge):
                        pts.append(o)
                self.points = pts
                self.setup_InteractionSeparator()

    def insert(self):
        # get selected lines and subdivide them
        # pts = []
        for o in self.root.selected_objects:
            #p1 = o.points[0]
            mark = MarkerOnEdge(o.points, o.snap_shape)
            self.points.append(mark)
            #new_select.append(mark)
        #self.points.append(pts)
        self.setup_InteractionSeparator()
        #self.root.selected_objects = new_select
        return True
    
    def text_change(self):
        for o in self.root.selected_objects:
            if o._text_type == 2:
                o._text_type = 0
            else:
                o._text_type += 1
    
    def quit(self):
        self.root.events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self._controlCB)
        self.root.unregister()
        #self.root.removeAllChildren()
        self.sg.removeChild(self.root)
        self.root_inserted = False
            
   

class splitVP:
    def __init__(self,vobj):
        vobj.Proxy = self
        self.select_state = True
        self.active = False
        self.ps = 0.0
        
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False
        self.select_state = vobj.Selectable
        self.ip = None

    def setEdit(self,vobj,mode=0):
        if mode == 0:
            if vobj.Selectable:
                self.select_state = True
                vobj.Selectable = False
                self.ps = vobj.PointSize
                vobj.PointSize = 0.0
            pts = list()
            sl = self.Object.Source
            e = _utils.getShape(self.Object, "Source", "Edge")
            params = []
            if hasattr(self.Object, "Values"):
                params = self.Object.Proxy.parse_values(e, self.Object.Values)
            if params == []:
                return False
            pts = list()
            for p in params:
                print("{} -> {}".format(p, e.valueAt(p)))
                pts.append(MarkerOnEdge([e.valueAt(p)], e))
            self.ip = pointEditor(pts, self.Object)
            self.ip.curve = e.Curve
            #vobj.Visibility = False
            self.active = True
            return True
        return False

    def unsetEdit(self,vobj,mode=0):
        e = _utils.getShape(self.Object, "Source", "Edge")
        if isinstance(self.ip, pointEditor):
            params = list()
            for p in self.ip.points:
                if isinstance(p, MarkerOnEdge):
                    pt = p.points[0]
                    par = e.Curve.parameter(FreeCAD.Vector(pt[0],pt[1],pt[2]))
                    temp = e.Curve.copy()
                    temp.segment(temp.FirstParameter, par)
                    params.append("{:.3f}mm".format(temp.length()))
            self.Object.Values = params
            vobj.Selectable = self.select_state
            vobj.PointSize = self.ps
            self.ip.quit()
        self.ip = None
        self.active = False
        #vobj.Visibility = True
        return True

    def doubleClicked(self,vobj):
        if not hasattr(self,'active'):
            self.active = False
        if not self.active:
            self.active = True
            #self.setEdit(vobj)
            vobj.Document.setEdit(vobj)
        else:
            vobj.Document.resetEdit()
            self.active = False
        return True

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

    def claimChildren(self):
        return [self.Object.Source[0]]

class splitCommand:
    """Splits the selected edges."""
    def makeSplitFeature(self,e):
        splitCurve = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","SplitCurve")
        split(splitCurve, e)
        splitVP(splitCurve.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        splitCurve.Values = ["50%"]
        splitCurve.ViewObject.PointSize = 5.0

    def Activated(self):
        edges = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select the edges to split first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        self.makeSplitFeature((selobj.Object, selobj.SubElementNames[i]))
                        if selobj.Object.Shape:
                            if len(selobj.Object.Shape.Edges) == 1:
                                selobj.Object.ViewObject.Visibility = False
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Edge COUNT 1..1000")
            return f.match()
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Split Curve', 'ToolTip': 'Splits the selected edge'}

FreeCADGui.addCommand('split', splitCommand())

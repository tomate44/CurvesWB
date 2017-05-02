import os
import FreeCAD, FreeCADGui, Part
from pivy import coin
import CoinNodes
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class bezierCurve:
    "this class will create a bezier curve after the user clicked 4 points on the screen"
    def Activated(self):
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.obj = FreeCAD.ActiveDocument.addObject("Part::Feature","BezierCurve")
        self.stack = [FreeCAD.Vector(0,0,0)]
        self.markerPos = None
        self.snap = False
        self.snapShape = None
        self.point = FreeCAD.Vector(0,0,0)
        self.curve = Part.BezierCurve()
        self.clicCB     = self.view.addEventCallbackPivy( coin.SoMouseButtonEvent.getClassTypeId(), self.clic_cb)
        self.keyboardCB = self.view.addEventCallbackPivy( coin.SoKeyboardEvent.getClassTypeId(), self.kb_cb)
        self.cursorCB   = self.view.addEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), self.cursor_cb)
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addObserver(self)
        self.nodeInit()

    def nodeInit(self):
        self.sg = self.view.getSceneGraph()
        self.coord = CoinNodes.coordinate3Node([(0,0,0)])
        self.markers = CoinNodes.markerSetNode((1,0.35,0.8),70)
        self.polygon = CoinNodes.sensorPolyNode((0.5,0.9,0.1),2)
        self.polygon.linkTo(self.coord)
        self.sg.addChild(self.coord)
        self.sg.addChild(self.markers)
        #self.sg.addChild(self.polygon)

    def addPole(self):
        self.stack.append(self.point)
        self.coord.add((self.point.x, self.point.y, self.point.z))
        if len(self.stack) == 2:
            self.sg.addChild(self.polygon)
        elif len(self.stack) >= 9:
            self.finish()

    def finish(self):
        self.curve.setPoles(self.stack[0:-1])
        self.obj.Shape = self.curve.toShape()
        self.sg.removeChild(self.polygon)
        self.sg.removeChild(self.markers)
        self.sg.removeChild(self.coord)
        self.view.removeEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), self.cursorCB)
        self.view.removeEventCallbackPivy( coin.SoKeyboardEvent.getClassTypeId(), self.keyboardCB)
        self.view.removeEventCallbackPivy( coin.SoMouseButtonEvent.getClassTypeId(), self.clicCB)

    def getSnapPoint(self, pt):
        return(pt)

    def addPreSelection(self,doc,obj,sub):
        self.snapShape = self.getShape(doc,obj,sub)

    def removePreSelection(self,doc,obj,sub):
        self.snapShape = None

    def kb_cb(self, event_callback):
        event = event_callback.getEvent()
        if (type(event) == coin.SoKeyboardEvent):
            key = ""
            try:
                key = event.getKey()
            except ValueError:
                # there is no character for this value
                key = ""
            if key == coin.SoKeyboardEvent.LEFT_CONTROL:
                if event.getState() == coin.SoButtonEvent.DOWN:
                    self.snap = True
                elif event.getState() == coin.SoButtonEvent.UP:
                    self.snap = False
            elif key == coin.SoKeyboardEvent.RETURN:
                self.finish()
            
    def clic_cb(self, event_callback):
        event = event_callback.getEvent()
        if (type(event) == coin.SoMouseButtonEvent and
                event.getState() == coin.SoMouseButtonEvent.DOWN
                and event.getButton() == coin.SoMouseButtonEvent.BUTTON1):
            self.addPole()
            FreeCADGui.Selection.clearSelection()

    def cursor_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        self.point = self.view.getPoint(pos[0],pos[1])
        if self.snap and not (self.snapShape == None):
            self.point = self.getSnapPoint(point)
        l = len(self.coord.point.getValues())
        self.coord.point.set1Value(l-1,self.point)
        self.stack[-1] = self.point
        if len(self.stack) >1:
            self.curve.setPoles(self.stack)
            self.obj.Shape = self.curve.toShape()
        

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/bezier.svg', 'MenuText': 'Bezier Curve', 'ToolTip': 'Creates a Bezier curve by clicking 4 points on the screen'}
FreeCADGui.addCommand('bezierCurve', bezierCurve())

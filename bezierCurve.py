import os
import FreeCAD, FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class bezierCurve:
    "this class will create a bezier curve after the user clicked 4 points on the screen"
    def Activated(self):
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.stack = []
        self.callback = self.view.addEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.getpoint)
    def makeBCurve(self,poles):
        c = Part.BezierCurve()
        c.increase(len(poles)-1)
        for i in range(len(poles)):
            c.setPole(i+1,FreeCAD.Vector(poles[i]))
        Part.show(c.toShape())
    def getpoint(self,event_cb):
        event = event_cb.getEvent()
        if event.getState() == SoMouseButtonEvent.DOWN:
            #print "MouseButton DOWN"
            pos = event.getPosition()
            point = self.view.getPoint(pos[0],pos[1])
            self.stack.append(point)
            if len(self.stack) == 4:
                self.makeBCurve(self.stack)
                self.view.removeEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.callback)
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/bezier.svg', 'MenuText': 'Bezier Curve', 'ToolTip': 'Creates a Bezier curve by clicking 4 points on the screen'}
FreeCADGui.addCommand('bezierCurve', bezierCurve())
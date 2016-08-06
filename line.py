import os
import FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class line:
 "this class will create a line after the user clicked 2 points on the screen"
 def Activated(self):
   self.view = FreeCADGui.ActiveDocument.ActiveView
   self.stack = []
   self.callback = self.view.addEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.getpoint)
 def getpoint(self,event_cb):
   event = event_cb.getEvent()
   if event.getState() == SoMouseButtonEvent.DOWN:
     pos = event.getPosition()
     point = self.view.getPoint(pos[0],pos[1])
     self.stack.append(point)
     if len(self.stack) == 2:
       l = Part.Line(self.stack[0],self.stack[1])
       shape = l.toShape()
       Part.show(shape)
       self.view.removeEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.callback)
 def GetResources(self):
     return {'Pixmap' : path_curvesWB_icons+'/line.svg', 'MenuText': 'Line', 'ToolTip': 'Creates a line by clicking 2 points on the screen'}
FreeCADGui.addCommand('line', line())
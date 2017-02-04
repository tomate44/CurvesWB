import os
import FreeCAD, FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class lineSet:
    "a coin lineSet Object"
    def __init__(self):
        self.rootNode = SoSeparator()
        self.color = SoBaseColor()
        self.color.rgb  = (0.8,0,0)
        self.coords = SoCoordinate3()
        print(str(self.coords.point.getValues()))
        self.lineSet = SoLineSet()
        self.rootNode.addChild(self.color)
        self.rootNode.addChild(self.coords)
        self.rootNode.addChild(self.lineSet)
        self.pts = []
    def addPoint(self, point):
        #pts = self.coords.point.getValues()
        print(str(point))
        self.pts.append(SbVec3f(point.x,point.y,point.z))
        self.coords.point.setValue(0,0,0)
        self.coords.point.setValues(0,len(self.pts),self.pts)

class bezierCurve:
    "this class will create a bezier curve after the user clicked 4 points on the screen"
    def Activated(self):
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.stack = []
        self.callback = self.view.addEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.getpoint)
        self.nodeInit()
    def nodeInit(self):
        self.sg = self.view.getSceneGraph()
        self.lineSet = lineSet()
        self.sg.addChild(self.lineSet.rootNode)
    def makeBCurve(self,poles):
        c = Part.BezierCurve()
        c.increase(len(poles)-1)
        for i in range(len(poles)):
            c.setPole(i+1,FreeCAD.Vector(poles[i]))
        Part.show(c.toShape())
    def getpoint(self,event_cb):
        event = event_cb.getEvent()
        if ( event.getState() == SoMouseButtonEvent.DOWN and event.getButton() == event.BUTTON1 ):
            #print "MouseButton DOWN"
            pos = event.getPosition()
            point = self.view.getPoint(pos[0],pos[1])
            self.stack.append(point)
            self.lineSet.addPoint(point)
            if len(self.stack) == 2:
                #self.sg.addChild(self.lineSet.rootNode)
                self.index = self.sg.findChild(self.lineSet.rootNode)
                print(str(self.index))
            if len(self.stack) == 4:
                #self.sg.removeChild(self.index)
                self.lineSet.coords.point.setValue(0,0,0)
                self.makeBCurve(self.stack)
                self.view.removeEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.callback)
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/bezier.svg', 'MenuText': 'Bezier Curve', 'ToolTip': 'Creates a Bezier curve by clicking 4 points on the screen'}
FreeCADGui.addCommand('bezierCurve', bezierCurve())

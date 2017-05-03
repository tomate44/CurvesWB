import FreeCAD
import FreeCADGui
from pivy import coin
import dummy


path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage("%s\n"%string)

class HUD:
    "Creates a static Head-Up-Display in the 3D view"
    def __init__(self):
        debug("HUD init")

        self.HUDNode = coin.SoSeparator()
        
        self.cam = coin.SoOrthographicCamera()
        self.cam.aspectRatio = 1
        self.cam.viewportMapping = coin.SoCamera.LEAVE_ALONE

        self.trans = coin.SoTranslation()
        self.trans.translation = (-0.98,0.90,0)

        self.myFont = coin.SoFont()
        self.myFont.name = "osiFont,FreeSans,sans"
        self.myFont.size.setValue(16.0)
        
        self.SoText2  = coin.SoText2()
        self.SoText2.string = ""

        self.color = coin.SoBaseColor()
        self.color.rgb = (0,0,0)

        self.HUDNode.addChild(self.cam)
        self.HUDNode.addChild(self.trans)
        self.HUDNode.addChild(self.color)
        self.HUDNode.addChild(self.myFont)
        self.HUDNode.addChild(self.SoText2)

    def add(self):
        self.activeDoc = FreeCADGui.ActiveDocument
        self.view = self.activeDoc.ActiveView
        self.sg = self.view.getSceneGraph()
        self.viewer=self.view.getViewer()
        self.render=self.viewer.getSoRenderManager()
        self.sup = self.render.addSuperimposition(self.HUDNode)
        self.sg.touch()

    def remove(self):
        self.render.removeSuperimposition(self.sup)
        self.sg.touch()


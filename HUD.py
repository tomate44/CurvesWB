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

class textArea(coin.SoSeparator):
    """Creates a text area node for HUD"""
    def __init__(self):
        super(textArea, self).__init__()
        
        self.trans = coin.SoTranslation()
        self.trans.translation = (-0.98,0.90,0)

        self.font = coin.SoFont()
        self.font.name = "osiFont,FreeSans,sans"
        self.font.size.setValue(16.0)
        
        self.text  = coin.SoText2()
        self.text.string = ""

        self.color = coin.SoBaseColor()
        self.color.rgb = (0,0,0)
        
        self.addChild(self.trans)
        self.addChild(self.color)
        self.addChild(self.font)
        self.addChild(self.text)
        
    @property
    def fontColor(self):
        return self.color.rgb.getValue()

    @fontColor.setter
    def fontColor(self, color):
        self.color.rgb = (color[0], color[1], color[2])
        
    @property
    def fontName(self):
        self.font.name.getValue()

    @fontName.setter
    def fontName(self, name):
        self.font.name = name


class HUD:
    """Creates a static Head-Up-Display in the 3D view"""
    def __init__(self):
        debug("HUD init")

        self.HUDNode = coin.SoSeparator()
        
        self.cam = coin.SoOrthographicCamera()
        self.cam.aspectRatio = 1
        self.cam.viewportMapping = coin.SoCamera.LEAVE_ALONE



        self.HUDNode.addChild(self.cam)


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


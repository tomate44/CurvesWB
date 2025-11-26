# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
from pivy import coin
import dummy


#path_curvesWB = os.path.dirname(dummy.__file__)
#path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage("%s\n"%string)

class textArea(coin.SoSeparator):
    """Creates a text area node for HUD"""
    def __init__(self):
        super(textArea, self).__init__()
        
        self.trans = coin.SoTranslation()
        self.trans.translation = (-0.98,0.95,0)

        self.font = coin.SoFont()
        self.font.name = "osiFont,FreeSans,sans"
        self.font.size.setValue(16.0)
        
        self.str  = coin.SoText2()
        self.str.string = ""

        self.color = coin.SoBaseColor()
        self.color.rgb = (0,0,0)
        
        self.addChild(self.trans)
        self.addChild(self.color)
        self.addChild(self.font)
        self.addChild(self.str)
        
    @property
    def fontColor(self):
        return( self.color.rgb.getValue())

    @fontColor.setter
    def fontColor(self, color):
        self.color.rgb = (color[0], color[1], color[2])
        
    @property
    def fontName(self):
        return( self.font.name.getValue())

    @fontName.setter
    def fontName(self, name):
        self.font.name = name

    @property
    def fontSize(self):
        return( self.font.size.getValue())

    @fontSize.setter
    def fontSize(self, val):
        self.font.size.setValue(val)

    @property
    def position(self):
        p = self.trans.translation.getValue()
        return( (p[0],p[1]))

    @position.setter
    def position(self, val):
        p = ( val[0], val[1], 0.0)
        self.trans.translation = p

    def setFont(self, name, size, color):
        self.fontName  = name
        self.fontSize  = size
        self.fontColor = color

    @property
    def text(self):
        return( self.str.string.getValues())

    @text.setter
    def text(self, s):
        if isinstance(s,str):
            self.str.string = s
        elif isinstance(s,list):
            self.str.string.setValues(0,len(s),s)

    def addText(self, s):
        t = self.text
        if isinstance(s,str):
            t.append(s)
        elif isinstance(s,list):
            t += s        
        self.text = t



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

    def addBlock(self, block):
        self.HUDNode.addChild(block)

    def removeBlock(self, block):
        self.HUDNode.removeChild(block)



def main():

    Block1 = textArea()
    Block1.setFont("Sans", 9.0, (1.,0.,0.))
    Block1.text = "Some text ..."
    Block1.addText("Here is a new line")

    Block2 = textArea()
    Block2.position = (0.5,0.9)
    Block2.setFont("FreeMono", 15.0, (0.,1.,1.))
    Block2.text = "Here is another"
    Block2.addText("text block")

    myHud = HUD()
    myHud.addBlock(Block1)
    myHud.addBlock(Block2)
    myHud.add()

if __name__ == '__main__':
    main()

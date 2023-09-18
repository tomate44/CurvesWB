import sys
if sys.version_info.major >= 3:
    from importlib import reload

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

from PySide import QtGui, QtCore
from pivy import coin
from freecad.Curves.Gui import Zebra_Gui

TOOL_ICON =  os.path.join( ICONPATH, 'zebra.svg')



class zebra(QtGui.QWidget):
    def __init__(self):

        super(zebra, self).__init__()
        #self.zebraWidget = QtGui.QWidget()
        self.ui = Zebra_Gui.Ui_Zebra()
        self.ui.setupUi(self) #.zebraWidget)
        self.tabIndex = 0
        self.comboview = None

        self.StripeWidth = 25
        self.Scale = 20
        self.Rotation = 157

        self.coinSetUp()

        self.ui.horizontalSlider.setMaximum(50)
        self.ui.horizontalSlider.valueChanged[int].connect(self.changeSlide_1)
        self.ui.horizontalSlider.setValue(self.StripeWidth)

        self.ui.horizontalSlider_2.setMaximum(40)
        self.ui.horizontalSlider_2.valueChanged[int].connect(self.changeSlide_2)
        self.ui.horizontalSlider_2.setValue(self.Scale)

        self.ui.horizontalSlider_3.setMaximum(314)
        self.ui.horizontalSlider_3.valueChanged[int].connect(self.changeSlide_3)
        self.ui.horizontalSlider_3.setValue(self.Rotation)

        self.ui.pushButton.clicked.connect(self.quit)

        #self.zebraWidget.show()

    def coinSetUp(self):
        #print "coinSetUp"
        self.TexW = 10
        self.TexH = 100

        self.sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
        #print str( FreeCADGui.ActiveDocument.Document.Label )
        #print str( self.sg )
        

        self.stripes = coin.SoTexture2()
        self.sg.insertChild(self.stripes,0)
        self.stripes.filename = ""

        self.string = '\xff' * 50 + '\x00' * self.StripeWidth
        self.chars = self.string * self.TexW * self.TexH

        self.img = coin.SoSFImage()
        self.img.setValue(coin.SbVec2s(len(self.string) * self.TexW ,self.TexH), 1, self.chars);

        self.stripes.image = self.img

        # **** here we can transform the texture
        self.transTexture = coin.SoTexture2Transform()
        self.sg.insertChild(self.transTexture,1)
        #transTexture.translation.setValue(1, 1)
        self.transTexture.scaleFactor.setValue(self.Scale, self.Scale)
        self.transTexture.rotation.setValue(1. * self.Rotation / 100)
        #transTexture.center.setValue(0, .5)

        self.tc = coin.SoTextureCoordinateEnvironment()
        self.sg.insertChild(self.tc,2)

    def coinQuit(self):
        #print "coinQuit"
        self.sg.removeChild(self.tc)
        self.sg.removeChild(self.transTexture)
        self.sg.removeChild(self.stripes)

    def changeSlide_1(self, value):
        #print "Stripes width : "+str(value)
        self.StripeWidth = value
        self.string = '\xff' * 50 + '\x00' * self.StripeWidth
        self.chars = self.string * self.TexW * self.TexH
        self.img.setValue(coin.SbVec2s(0 ,0), 1, '');
        self.img.setValue(coin.SbVec2s(len(self.string) * self.TexW ,self.TexH), 1, self.chars);
        self.stripes.image = self.img

    def changeSlide_2(self, value):
        #print "scale : "+str(value)
        self.Scale = value
        if self.Scale < 20 :
            scale = 1. * self.Scale / 20
        else:
            scale = self.Scale -19
        self.transTexture.scaleFactor.setValue(scale, scale)

    def changeSlide_3(self, value):
        #print "Rotation : "+str(value)
        self.Rotation = value
        self.transTexture.rotation.setValue(1. * self.Rotation / 100)

    def quit(self):
        #print "Quit ..."
        self.coinQuit()
        self.close() #zebraWidget.close()
        self.comboview.removeTab(self.tabIndex)
        ZebraTool.active = False


def getMainWindow():
   "returns the main window"
   # using QtGui.qApp.activeWindow() isn't very reliable because if another
   # widget than the mainwindow is active (e.g. a dialog) the wrong widget is
   # returned
   return(FreeCADGui.getMainWindow())
   toplevel = QtGui.qApp.topLevelWidgets()
   for i in toplevel:
       if i.metaObject().className() == "Gui::MainWindow":
           return i
   raise Exception("No main window found")

def getComboView(mw):
   dw=mw.findChildren(QtGui.QDockWidget)
   for i in dw:
       if str(i.objectName()) == "Combo View":
           return i.findChild(QtGui.QTabWidget)
       elif str(i.objectName()) == "Python Console":
           return i.findChild(QtGui.QTabWidget)
   raise Exception ("No tab widget found")

class ZebraTool:
    def __init__(self):
        ZebraTool.active = False
    def Activated(self):
        if not ZebraTool.active:
            self.mw = getMainWindow()
            self.tab = getComboView(self.mw)
            self.tab2=zebra()
            i = self.tab.addTab(self.tab2,"Zebra Tool")
            self.tab.setCurrentIndex(i)
            self.tab2.comboview = self.tab
            self.tab2.tabIndex = i
            self.tab2.show()
            ZebraTool.active = True
        else:
            FreeCAD.Console.PrintMessage("Zebra already active\n")
        


    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'ZebraTool',
                'ToolTip': 'Zebra texture for surface inspection.<br>Just activate the tool.'}

FreeCADGui.addCommand('ZebraTool', ZebraTool())

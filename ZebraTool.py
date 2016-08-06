import FreeCAD
import os, dummy, FreeCADGui, sys
import Part
from PySide import QtGui, QtCore
from pivy import coin
import Zebra_Gui
reload(Zebra_Gui)

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')



class zebra(QtGui.QWidget):
    def __init__(self):

        super(zebra, self).__init__()
        #self.zebraWidget = QtGui.QWidget()
        self.ui = Zebra_Gui.Ui_Zebra()
        self.ui.setupUi(self) #.zebraWidget)

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
        print "coinSetUp"
        self.TexW = 10
        self.TexH = 100

        self.sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
        print str( FreeCADGui.ActiveDocument.Document.Label )
        print str( self.sg )
        

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
        print "coinQuit"
        self.sg.removeChild(self.tc)
        self.sg.removeChild(self.transTexture)
        self.sg.removeChild(self.stripes)

    def changeSlide_1(self, value):
        print "Stripes width : "+str(value)
        self.StripeWidth = value
        self.string = '\xff' * 50 + '\x00' * self.StripeWidth
        self.chars = self.string * self.TexW * self.TexH
        self.img.setValue(coin.SbVec2s(0 ,0), 1, '');
        self.img.setValue(coin.SbVec2s(len(self.string) * self.TexW ,self.TexH), 1, self.chars);
        self.stripes.image = self.img

    def changeSlide_2(self, value):
        print "scale : "+str(value)
        self.Scale = value
        if self.Scale < 20 :
            scale = 1. * self.Scale / 20
        else:
            scale = self.Scale -19
        self.transTexture.scaleFactor.setValue(scale, scale)

    def changeSlide_3(self, value):
        print "Rotation : "+str(value)
        self.Rotation = value
        self.transTexture.rotation.setValue(1. * self.Rotation / 100)

    def quit(self):
        print "Quit ..."
        self.coinQuit()
        self.close() #zebraWidget.close()
        mw = getMainWindow()
        tab = getComboView(getMainWindow())
        tab.removeTab(2)


def getMainWindow():
   "returns the main window"
   # using QtGui.qApp.activeWindow() isn't very reliable because if another
   # widget than the mainwindow is active (e.g. a dialog) the wrong widget is
   # returned
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
    def Activated(self):
        mw = getMainWindow()
        tab = getComboView(getMainWindow())

        tab2=zebra()
        tab.addTab(tab2,"Zebra Tool")   #.zebraWidget,"Zebra Tool")
        tab2.show()   #zebraWidget.show()   

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/zebra.svg', 'MenuText': 'ZebraTool', 'ToolTip': 'Zebra texture for surface inspection'}

FreeCADGui.addCommand('ZebraTool', ZebraTool())

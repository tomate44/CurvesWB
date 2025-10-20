# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import FreeCAD
import FreeCADGui
from freecad.Curves import ICONPATH

from PySide import QtGui, QtCore
from pivy import coin
from freecad.Curves.Gui import Zebra_Gui

TOOL_ICON = os.path.join(ICONPATH, 'zebra.svg')


def execute_later(callback, delay=0):
    QtCore.QTimer.singleShot(delay, callback)


def show_task_panel(widget):
    FreeCADGui.Control.closeDialog()
    execute_later(lambda: FreeCADGui.Control.showDialog(widget), 10)


def close_task_panel():
    FreeCADGui.Control.closeDialog()


class zebra(QtGui.QDialog):

    def __init__(self):
        super().__init__()
        self.ui = Zebra_Gui.Ui_Zebra()
        self.setLayout(QtGui.QVBoxLayout())
        self.ui.setupUi(self)
        self.layout().addWidget(self.ui.verticalLayoutWidget)

        self.StripeWidth = 25
        self.Scale = 20
        self.Rotation = 157

        self.coinSetUp()

        self.ui.horizontalSlider.setMaximum(50)
        self.ui.horizontalSlider.valueChanged[int].connect(self.changeSlide_1)
        self.ui.horizontalSlider.setValue(self.StripeWidth)

        self.ui.horizontalSlider_2.setMaximum(40)
        self.ui.horizontalSlider_2.valueChanged[int].connect(
            self.changeSlide_2)
        self.ui.horizontalSlider_2.setValue(self.Scale)

        self.ui.horizontalSlider_3.setMaximum(314)
        self.ui.horizontalSlider_3.valueChanged[int].connect(
            self.changeSlide_3)
        self.ui.horizontalSlider_3.setValue(self.Rotation)

        self.ui.pushButton.clicked.connect(self.quit)

    def coinSetUp(self):
        self.TexW = 10
        self.TexH = 100

        self.sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()

        self.stripes = coin.SoTexture2()
        self.sg.insertChild(self.stripes, 0)
        self.stripes.filename = ""

        self.string = '\xff' * 50 + '\x00' * self.StripeWidth
        self.chars = self.string * self.TexW * self.TexH

        self.img = coin.SoSFImage()
        self.img.setValue(coin.SbVec2s(len(self.string) *
                          self.TexW, self.TexH), 1, self.chars)

        self.stripes.image = self.img

        # **** here we can transform the texture
        self.transTexture = coin.SoTexture2Transform()
        self.sg.insertChild(self.transTexture, 1)
        # transTexture.translation.setValue(1, 1)
        self.transTexture.scaleFactor.setValue(self.Scale, self.Scale)
        self.transTexture.rotation.setValue(1. * self.Rotation / 100)
        # transTexture.center.setValue(0, .5)

        self.tc = coin.SoTextureCoordinateEnvironment()
        self.sg.insertChild(self.tc, 2)

    def coinQuit(self):
        self.sg.removeChild(self.tc)
        self.sg.removeChild(self.transTexture)
        self.sg.removeChild(self.stripes)

    def changeSlide_1(self, value):
        self.StripeWidth = value
        self.string = '\xff' * 50 + '\x00' * self.StripeWidth
        self.chars = self.string * self.TexW * self.TexH
        self.img.setValue(coin.SbVec2s(0, 0), 1, '')
        self.img.setValue(coin.SbVec2s(len(self.string) *
                          self.TexW, self.TexH), 1, self.chars)
        self.stripes.image = self.img

    def changeSlide_2(self, value):
        self.Scale = value
        if self.Scale < 20:
            scale = 1. * self.Scale / 20
        else:
            scale = self.Scale - 19
        self.transTexture.scaleFactor.setValue(scale, scale)

    def changeSlide_3(self, value):
        self.Rotation = value
        self.transTexture.rotation.setValue(1. * self.Rotation / 100)

    def quit(self):
        self.coinQuit()
        self.close()
        close_task_panel()
        ZebraTool.active = False


class ZebraForm:
    def __init__(self, zebra):
        self.form = zebra
        zebra.show()
        zebra.adjustSize()

    def accept(self):
        self.form.quit()

    def reject(self):
        self.form.quit()


class ZebraTool:
    def __init__(self):
        ZebraTool.active = False

    def Activated(self):
        if not ZebraTool.active:
            self.gui = zebra()
            ZebraTool.active = True
            show_task_panel(ZebraForm(self.gui))
        else:
            FreeCAD.Console.PrintMessage("Zebra already active\n")

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'ZebraTool',
                'ToolTip': 'Zebra texture for surface inspection'}


FreeCADGui.addCommand('ZebraTool', ZebraTool())

# SPDX-License-Identifier: LGPL-2.1-or-later

# Form implementation generated from reading ui file './Zebra_Gui.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Zebra(object):
    def setupUi(self, Zebra):
        Zebra.setObjectName(_fromUtf8("Zebra"))
        Zebra.resize(241, 302)
        self.verticalLayoutWidget = QtGui.QWidget(Zebra)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 221, 251))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label, QtCore.Qt.AlignHCenter)
        self.horizontalSlider = QtGui.QSlider(self.verticalLayoutWidget)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName(_fromUtf8("horizontalSlider"))
        self.verticalLayout.addWidget(self.horizontalSlider)
        self.label_2 = QtGui.QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2, QtCore.Qt.AlignHCenter)
        self.horizontalSlider_2 = QtGui.QSlider(self.verticalLayoutWidget)
        self.horizontalSlider_2.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_2.setObjectName(_fromUtf8("horizontalSlider_2"))
        self.verticalLayout.addWidget(self.horizontalSlider_2)
        self.label_3 = QtGui.QLabel(self.verticalLayoutWidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout.addWidget(self.label_3, QtCore.Qt.AlignHCenter)
        self.horizontalSlider_3 = QtGui.QSlider(self.verticalLayoutWidget)
        self.horizontalSlider_3.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_3.setObjectName(_fromUtf8("horizontalSlider_3"))
        self.verticalLayout.addWidget(self.horizontalSlider_3)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.pushButton = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton, QtCore.Qt.AlignHCenter)

        self.retranslateUi(Zebra)
#        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("released()")), Zebra.close)
#        QtCore.QMetaObject.connectSlotsByName(Zebra)

    def retranslateUi(self, Zebra):
        Zebra.setWindowTitle(_translate("Zebra", "Zebra Stripes Tool", None))
        self.label.setText(_translate("Zebra", "Black Stripes Width", None))
        self.label_2.setText(_translate("Zebra", "Scale", None))
        self.label_3.setText(_translate("Zebra", "Rotation", None))
        self.pushButton.setText(_translate("Zebra", "Quit", None))


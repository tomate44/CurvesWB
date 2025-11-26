# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Sublink Editor"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Editor widget for sublink properties of objects"

import os
import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'sublink_edit.svg')
debug = _utils.debug

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
    dw = mw.findChildren(QtGui.QDockWidget)
    for i in dw:
        if str(i.objectName()) == "Combo View":
            return i.findChild(QtGui.QTabWidget)
        elif str(i.objectName()) == "Python Console":
            return i.findChild(QtGui.QTabWidget)
    raise Exception("No tab widget found")


class SubLinkEditorWidget(object):
    def __init__(self, obj):
        self.obj = obj
        self.main_win = FreeCADGui.getMainWindow()
        self.widget = QtGui.QDockWidget()
        self.widget.ui = myWidget_Ui(obj)
        self.widget.ui.setupUi(self.widget)

        self.widget.ui.pushButton_7.clicked.connect(self.accept)

        self.main_win.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget)
        self.widget.setFloating(True)

        self.initial_visibility = self.obj.ViewObject.Visibility
        self.obj.ViewObject.Visibility = False

    def quit(self):
        print("SubLinkEditorWidget quits")

    def accept(self):
        print('accept and resetEdit')
        FreeCADGui.ActiveDocument.resetEdit()
        self.widget.close()
        self.obj.ViewObject.Visibility = self.initial_visibility
        FreeCAD.ActiveDocument.recompute()
        return(True)

    def reject(self):
        print('reject and resetEdit')
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCADGui.Control.closeDialog()
        return(True)


class myGrpBox(QtGui.QGroupBox):
    def __init__(self, parent, link, obj):
        super(myGrpBox, self).__init__(parent)
        # self.rootNode = node
        self.obj = obj
        self.link = link
        self.parent = parent
        self.setupUi()

    def setupUi(self):
        # self.groupBox = QtGui.QGroupBox(self.dockWidgetContents)
        self.setObjectName(_fromUtf8(self.link))
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton = QtGui.QPushButton(self)
        self.pushButton.setObjectName(_fromUtf8("View"))
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self)
        self.pushButton_2.setObjectName(_fromUtf8("Set"))
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.pushButton.clicked.connect(self.view_link)
        self.pushButton.pressed.connect(self.set_selection)
        self.pushButton.released.connect(self.reset_selection)
        self.pushButton_2.clicked.connect(self.set_link)
        self.setTitle(self.link)
        self.pushButton.setText("View")
        self.pushButton_2.setText("Set")

    def getSelection(self):
        s = FreeCADGui.Selection.getSelectionEx()
        sel = list()
        if not s == []:
            for o in s:
                sel.append((o, o.Object.ViewObject.Visibility))
        return(sel)

    def set_selection(self):
        # self.obj.ViewObject.Visibility = False
        self.selection_buffer = self.getSelection()
        FreeCADGui.Selection.clearSelection()
        lnk = self.obj.getPropertyByName(self.link)
        self.sublink_viz = list()
        if lnk:
            if not isinstance(lnk[0], (list, tuple)):
                self.sublink_viz.append((lnk[0], lnk[0].ViewObject.Visibility))
                lnk[0].ViewObject.Visibility = True
                FreeCADGui.Selection.addSelection(lnk[0], lnk[1])
            else:
                for o in lnk:
                    self.sublink_viz.append((o[0], o[0].ViewObject.Visibility))
                    o[0].ViewObject.Visibility = True
                    for n in o[1]:
                        FreeCADGui.Selection.addSelection(o[0], n)

    def reset_selection(self):
        # self.obj.ViewObject.Visibility = True
        FreeCADGui.Selection.clearSelection()
        for o in self.selection_buffer:
            if o[0].HasSubObjects:
                for n in o[0].SubElementNames:
                    FreeCADGui.Selection.addSelection(o[0].Object, n)
                    o[0].Object.ViewObject.Visibility = o[1]
        for t in self.sublink_viz:
            t[0].ViewObject.Visibility = t[1]

    def view_link(self):
        debug("%s.%s = %s" % (self.obj.Label, self.link, self.obj.getPropertyByName(self.link)))
        # FreeCADGui.doCommand("print(FreeCAD.ActiveDocument.getObject('%s').%s)"%(self.obj.Name, self.link))

    def set_link(self):
        # debug("%s.%s -> Set button pressed"%(self.obj.Label, self.link))
        subs = list()
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Nothing selected !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                subs.append(("(FreeCAD.ActiveDocument.getObject('%s'),%s)" % (selobj.Object.Name, selobj.SubElementNames)))
        if self.obj.getTypeIdOfProperty(self.link) == 'App::PropertyLinkSub':
            if not len(subs) == 1:
                FreeCAD.Console.PrintError("This property accept only 1 subobject !\n")
            else:
                # FreeCADGui.doCommand("subobj = FreeCAD.ActiveDocument.getObject('%s')"%(subs[0][0].Name))
                FreeCADGui.doCommand("FreeCAD.ActiveDocument.getObject('%s').%s = %s" % (self.obj.Name, self.link, subs[0]))
        elif self.obj.getTypeIdOfProperty(self.link) == 'App::PropertyLinkSubList':
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.getObject('%s').%s = %s" % (self.obj.Name, self.link, self.concat(subs)))
        self.view_link()

    def concat(self, subs):
        st = "("
        for o in subs:
            st += o + ","
        st += ")"
        return(st)


class myWidget_Ui(object):
    def __init__(self, obj):
        self.link_sub = list()
        self.obj = obj
        for pro in obj.PropertiesList:
            if obj.getTypeIdOfProperty(pro) in ('App::PropertyLinkSub', 'App::PropertyLinkSubList'):
                print("%s (%s)" % (pro, obj.getTypeIdOfProperty(pro)))
                self.link_sub.append(pro)

    def setupUi(self, DockWidget):
        DockWidget.setObjectName(_fromUtf8("DockWidget"))
        DockWidget.resize(400, 200)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        # self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        for link in self.link_sub:
            groupBox = myGrpBox(self.dockWidgetContents, link, self.obj)
            self.verticalLayout.addWidget(groupBox)

        self.pushButton_7 = QtGui.QPushButton(self.dockWidgetContents)
        self.pushButton_7.setObjectName(_fromUtf8("pushButton_7"))
        self.verticalLayout.addWidget(self.pushButton_7, 0, QtCore.Qt.AlignHCenter)
        spacerItem = QtGui.QSpacerItem(20, 237, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)
        QtCore.QMetaObject.connectSlotsByName(DockWidget)

    def retranslateUi(self, DockWidget):
        DockWidget.setWindowTitle(self.obj.Label + " sublink editor")
        self.pushButton_7.setText(_translate("DockWidget", "Quit", None))


class sle:
    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if not len(s) == 1:
            FreeCAD.Console.PrintError("Select 1 object !\n")
        else:
            hasSubLink = False
            for p in s[0].PropertiesList:
                if s[0].getTypeIdOfProperty(p) in ('App::PropertyLinkSub', 'App::PropertyLinkSubList'):
                    hasSubLink = True
        if hasSubLink:
            self.sle = SubLinkEditorWidget(s[0])

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            selection = FreeCADGui.Selection.getSelection()
            if len(selection) == 1:
                return True
        return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('SublinkEditor', sle())


####################
#     testing      #
####################
class proxy(object):
    """Feature python proxy"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList", "Profile", "Profile", "SubShapes of the profile")
        obj.addProperty("App::PropertyLinkSub", "Location1", "Profile", "Vertex location on spine")
        obj.addProperty("App::PropertyLinkSub", "Location2", "Profile", "Vertex location on spine")
        obj.addProperty("App::PropertyLinkSub", "Location3", "Profile", "Vertex location on spine")
        obj.Proxy = self


class proxyVP(object):
    """View provider proxy"""
    def __init__(self, obj):
        debug("VP init")
        obj.Proxy = self

    def attach(self, vobj):
        self.Object = vobj.Object

    def setEdit(self, vobj, mode):
        debug("Start Edit / mode: %d" % mode)
        # https://www.freecadweb.org/wiki/PySide_Advanced_Examples/fr
        self.edit_widget = SubLinkEditorWidget(self.Object)
        return(True)

    def unsetEdit(self, vobj, mode):
        debug("End Edit")
        if self.edit_widget:
            del(self.edit_widget)
        # self.combo.removeTab(self.tab.idx)
        return(True)


def main():
    doc = FreeCAD.ActiveDocument
    obj = doc.addObject("Part::FeaturePython", "test")
    proxy(obj)
    proxyVP(obj.ViewObject)


if __name__ == '__main__':
    main()

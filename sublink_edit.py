import FreeCAD
import FreeCADGui
from PySide import QtGui,QtCore
import _utils

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
   raise Exception ("No tab widget found")

class proxy(object):
    """Feature python proxy"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList",  "Profile",    "Profile", "SubShapes of the profile")
        obj.addProperty("App::PropertyLinkSub",      "Location1",   "Profile", "Vertex location on spine")
        obj.addProperty("App::PropertyLinkSub",      "Location2",   "Profile", "Vertex location on spine")
        obj.addProperty("App::PropertyLinkSub",      "Location3",   "Profile", "Vertex location on spine")
        obj.Proxy = self

class proxyVP(object):
    """View provider proxy"""
    def __init__(self, obj ):
        debug("VP init")
        obj.Proxy = self

    def attach(self, vobj):
        self.Object = vobj.Object

    def setEdit(self,vobj,mode):
        debug("Start Edit / mode: %d"%mode)
        # https://www.freecadweb.org/wiki/PySide_Advanced_Examples/fr
        self.edit_widget = SubLinkEditorWidget(self.Object)
        return(True)

    def unsetEdit(self,vobj,mode):
        debug("End Edit")
        #self.combo.removeTab(self.tab.idx) 
        return(True)

class SubLinkEditorWidget(object):
    def __init__(self, obj):
        self.main_win = FreeCADGui.getMainWindow()
        self.widget = QtGui.QDockWidget()
        self.widget.ui = myWidget_Ui(obj)
        self.widget.ui.setupUi(self.widget)
        
        self.widget.ui.pushButton.clicked.connect(self.accept)
        
        self.main_win.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.widget)
        
    def quit(self):
        print("SubLinkEditorWidget quits")

    def accept(self):
        print 'accept and resetEdit'
        FreeCADGui.ActiveDocument.resetEdit()
        self.widget.close()
        return(True)

    def reject(self):
        print 'reject and resetEdit'
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCADGui.Control.closeDialog()
        return(True)

class subGroup(QtGui.QGroupBox):
    def __init__(self, widget, node, obj, prop):
        super(subGroup, self).__init__(widget)
        self.rootNode = node
        self.obj = obj
        self.prop = prop
        self.widget = widget
    def setupUi(self):
        self.setObjectName(_fromUtf8(self.prop))
        #self.resize(500, 400)
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(self.widget)
        self.groupBox.setObjectName(_fromUtf8(self.prop))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setObjectName(_fromUtf8("View"))
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self.groupBox)
        self.pushButton_2.setObjectName(_fromUtf8("Set"))
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.verticalLayout.addWidget(self.groupBox)

        self.retranslateUi(self.widget)
        self.pushButton.clicked.connect(self.view)
        self.pushButton_2.clicked.connect(self.setprop)

    def view(self):
        pass
    
    def setprop(self):
        pass

    def retranslateUi(self, Form):
        #Form.setWindowTitle(_translate("Form", "Form", None))
        self.groupBox.setTitle(_translate("Form", self.prop, None))
        self.pushButton.setText(_translate("Form", "View", None))
        self.pushButton_2.setText(_translate("Form", "Set", None))



class myWidget_Ui(object):
    def __init__(self, obj):
        self.link_sub = list()
        self.link_sub_list = list()
        self.obj = obj
        #sel = FreeCADGui.Selection.getSelection()
        #if sel == []:
            #self.cancel()
            #return(False)
        #else:
            #sel = sel[-1]
        for pro in obj.PropertiesList:
            if obj.getTypeIdOfProperty(pro) == 'App::PropertyLinkSub':
                print("PropertyLinkSub -> %s"%pro)
                self.link_sub.append(pro)
            elif obj.getTypeIdOfProperty(pro) == 'App::PropertyLinkSubList':
                print("PropertyLinkSubList -> %s"%pro)
                self.link_sub_list.append(pro)

    def setupUi(self, widget):
        widget.setObjectName(_fromUtf8("Sublink Editor"))
        widget.resize(240, 300)
        self.verticalLayoutWidget = QtGui.QWidget(widget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 320, 420))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        for link in self.link_sub:
            self.verticalLayout.addWidget(subGroup(widget,0,self.obj,link), QtCore.Qt.AlignHCenter)
        self.label_2 = QtGui.QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(_fromUtf8("label"))
        for link in self.link_sub_list:
            self.verticalLayout.addWidget(subGroup(widget,0,self.obj,link), QtCore.Qt.AlignHCenter)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.pushButton = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton, QtCore.Qt.AlignHCenter)

        self.pushButton.clicked.connect(self.quit)

        self.retranslateUi(widget)

    def retranslateUi(self, widget):
        widget.setWindowTitle(_translate("widget", "Sublink Editor", None))
        self.label.setText(_translate("widget", "LinkSub", None))
        self.label_2.setText(_translate("widget", "LinkSubList", None))
        self.pushButton.setText(_translate("widget", "Quit", None))

    def select(self):
        return()

    def endselect(self):
        return()

    def ok(self):
        self.quit()

    def cancel(self):
        self.quit()
    
    def quit(self):
        pass



doc = FreeCAD.ActiveDocument
obj = doc.addObject("Part::FeaturePython","test")
proxy(obj)
proxyVP(obj.ViewObject)



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
        obj.addProperty("App::PropertyLinkSub",      "Location",   "Profile", "Vertex location on spine")
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

class myWidget_Ui(object):
    def __init__(self, obj):
        self.link_sub = list()
        self.link_sub_list = list()
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

    def setupGroup(self, Form, link):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(555, 450)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(Form)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.tableWidget = QtGui.QTableWidget(self.groupBox)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(4)
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self.groupBox)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)

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
            self.setupGroup(widget, link)
        for link in self.link_sub_list:
            self.setupGroup(widget, link)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.pushButton = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton, QtCore.Qt.AlignHCenter)

        self.retranslateUi(widget)

    def retranslateUi(self, widget):
        widget.setWindowTitle(_translate("widget", "Sublink Editor", None))
        self.label.setText(_translate("widget", "Sublink Editor", None))
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



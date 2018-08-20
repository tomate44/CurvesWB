import FreeCAD
import FreeCADGui
from PySide import QtGui,QtCore
import _utils

debug = _utils.debug

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
        self.main_win.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.widget) 

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
    def setupUi(self, myWidget):
        myWidget.setObjectName("Sublinks Editor")
        #myWidget.resize(QtCore.QSize(300,100).expandedTo(myWidget.minimumSizeHint())) # sets size of the widget

#        self.label = QtGui.QLabel(myWidget) # creates a label
#        self.label.setGeometry(QtCore.QRect(50,50,200,24)) # sets its size
#        self.label.setObjectName("Editor") # sets its name, so it can be found by name

        self.vbox_1 = QtGui.QVBoxLayout()
        self.label_1 = QtGui.QLabel(myWidget)
        self.label_1.setText('LinkSub')
        self.vbox_1.addWidget(self.label_1, 1, QtCore.Qt.AlignCenter)

        for link in self.link_sub:
            label_link = QtGui.QLabel(myWidget)
            label_link.setText(link)
            set_button = QtGui.QPushButton('Select')
            set_button.clicked.connect(self.select)
            done_button = QtGui.QPushButton('Done')
            done_button.clicked.connect(self.endselect)
            hbox = QtGui.QHBoxLayout()
            self.vbox_1.addWidget(label_link, 1, QtCore.Qt.AlignCenter)
            hbox.addWidget(set_button, 1, QtCore.Qt.AlignCenter)
            hbox.addWidget(done_button, 1, QtCore.Qt.AlignCenter)
            self.vbox_1.addLayout(hbox)

        ok_button = QtGui.QPushButton('OK')
        ok_button.clicked.connect(self.ok)

        cancel_button = QtGui.QPushButton('Cancel')
        cancel_button.clicked.connect(self.cancel)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(ok_button, 1, QtCore.Qt.AlignCenter)
        hbox.addWidget(cancel_button, 1, QtCore.Qt.AlignCenter)
        self.vbox_1.addStretch(1)
        self.vbox_1.addLayout(hbox)

        myWidget.setLayout(self.vbox_1)

        desktop_widget = QtGui.QDesktopWidget()
        right = desktop_widget.availableGeometry().width()

        myWidget.setGeometry(right - 300, 0, 300, 150)
        myWidget.setWindowTitle('Edit linkSub property')
        #myWidget.show()

    def retranslateUi(self, draftToolbar): # built-in QT function that manages translations of widgets
        myWidget.setWindowTitle(QtGui.QApplication.translate("myWidget", "Sublinks Editor", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("myWidget", "Sublinks Editor", None, QtGui.QApplication.UnicodeUTF8)) 

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



# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part

from PySide.QtGui import * 
from PySide.QtCore import * 

def getComboView(mw):
   dw=mw.findChildren(QDockWidget)
   for i in dw:
       if str(i.objectName()) == "Combo View":
           return i.findChild(QTabWidget)
       elif str(i.objectName()) == "Python Console":
           return i.findChild(QTabWidget)
   raise Exception ("No tab widget found")

class Test:
    def setEdit(self):
        """ViewProvider setEdit example"""
        self.ed = VPEditor()
        self.group1 = self.ed.add_layout("Face 1")
        proped_11 = VectorListWidget() # PropEditor() #self.Object,"ScaleList1")
        proped_12 = VectorListWidget() #self.Object,"Continuity1")
        #proped_11.fillTable(((0.0,1.0),(0.4,1.5),(1.0,0.8)))
        proped_12.fillTable()
        self.ed.add_propeditor(proped_11, self.group1)
        #ed.add_propeditor(proped_12, self.group1)
        self.group2 = self.ed.add_layout("Face 2")
        proped_21 = VectorListWidget() #self.Object,"ScaleList2")
        #proped_22 = VectorListWidget() #self.Object,"Continuity2")
        self.ed.add_propeditor(proped_21, self.group2)
        #ed.add_propeditor(proped_22, self.group2)
        self.ed.add_close_button()

        self.mw = FreeCADGui.getMainWindow()
        self.ed.comboview = getComboView(self.mw)
        self.ed.tabIndex = self.ed.comboview.addTab(self.ed.widget,"Table")
        self.ed.comboview.setCurrentIndex(self.ed.tabIndex)
        self.ed.widget.show()

class VPEditor(QObject):
    """ViewProvider editor for FeaturePython objects"""
    def __init__(self, parent=None):
        super(VPEditor,self).__init__(parent)
        #self.proxy = proxy
        #self.vobj = vobj
        self.create_widget()

    def create_widget(self):
        """create an empty QWidget"""
        self.widget = QWidget()
        self.title = 'Table'
        self.left = 0
        self.top = 0
        self.width = 100
        self.height = 100
        self.widget.setWindowTitle(self.title)
        self.widget.setGeometry(self.left, self.top, self.width, self.height)
        self.widget.layout = QVBoxLayout()
        self.widget.setLayout(self.widget.layout)

    def add_layout(self,name):
        """add a grouping vertical layout to widget"""
        if self.widget:
            g = QVBoxLayout()
            label = QLabel()
            label.setText(name)
            g.addWidget(label)
            self.widget.layout.addLayout(g)
            return(g)
        else:
            FreeCAD.Console.PrintError("VPEditor has no widget !\n")
    def add_propeditor(self,editor,group):
        """add a property editor widget"""
        group.addWidget(editor)
        group.addLayout(editor.table_buttons)
    def add_ok_cancel_buttons(self):
        self.buttonLO = QHBoxLayout()
        self.ok = QPushButton()
        self.ok.setObjectName("OK")
        self.ok.setText("OK")
        self.cancel = QPushButton()
        self.cancel.setObjectName("Cancel")
        self.cancel.setText("Cancel")
        self.buttonLO.addWidget(self.ok) 
        self.buttonLO.addWidget(self.cancel)
        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)
        self.widget.layout.addStretch()
        self.widget.layout.addLayout(self.buttonLO)
    def add_close_button(self):
        self.close = QPushButton() #self.widget.layout)
        self.close.setObjectName("Close")
        self.close.setText("Close")
        self.close.clicked.connect(self.quit) # or reject ?
        self.widget.layout.addStretch()
        self.widget.layout.addWidget(self.close)
    @Slot()
    def accept(self):
        # do something
        self.quit()
    @Slot()
    def reject(self):
        # do something
        self.quit()
    @Slot()
    def quit(self):
        FreeCAD.Console.PrintMessage("VPEditor.Quit() \n")
        self.widget.close()
        try:
            self.comboview.removeTab(self.tabIndex)
            self.comboview.setCurrentIndex(0)
            FreeCADGui.ActiveDocument.resetEdit()
        except:
            FreeCAD.Console.PrintError("Failed to remove from ComboView\n")

class VectorListWidget(QTableWidget):
    def __init__(self, fp=None, prop=None, parent=None):
    #def __init__(self, parent=None):
        super(VectorListWidget, self).__init__(parent)
        self.fp = fp
        self.prop = prop
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Parameter","Scale"])
        self.move(10,10)
        self.createTableButtons()
        # connect signals
        self.doubleClicked.connect(self.on_double_click)
        self.itemClicked.connect(self.on_click)
        self.cellChanged.connect(self.cell_changed)
        vl = self.fp.getPropertyByName(self.prop)
        self.fillTable(vl)

    def fillTable(self,vectors):
        for v in vectors:
            n = self.rowCount()
            self.insertRow(n)
            self.setItem(n,0, QTableWidgetItem(str(v.x)))
            self.setItem(n,1, QTableWidgetItem(str(v.y)))

    def createTableButtons(self):
        self.table_buttons = QHBoxLayout()
        self.insertButton = QPushButton()
        self.insertButton.setObjectName("Insert")
        self.insertButton.setText("Insert")
        self.removeButton = QPushButton()
        self.removeButton.setObjectName("Remove")
        self.removeButton.setText("Remove")
        self.table_buttons.addWidget(self.insertButton) 
        self.table_buttons.addWidget(self.removeButton)
        self.insertButton.clicked.connect(self.insert)
        self.removeButton.clicked.connect(self.remove)

    def insert(self):
        idx = self.rowCount()
        self.insertRow(idx)
        self.setItem(idx,0, QTableWidgetItem("0."))
        self.setItem(idx,1, QTableWidgetItem("1.0"))

    def remove(self):
        idxs = list()
        for currentQTableWidgetItem in self.selectedItems():
            idxs.append(currentQTableWidgetItem.row())
        idxs = list(set(idxs))
        idxs.sort(reverse=True)
        for i in idxs:
            self.removeRow(i)
            print("removing row %d"%i)
        self.apply_changes()

    def cell_changed(self, row, col):
        sel = self.item(row, col)
        if col == 0:
            print("row %d: param changed : %s"%(row, sel.text()))
        elif col == 1:
            print("row %d: scale changed : %s"%(row, sel.text()))
        self.apply_changes()

    def apply_changes(self):
        vl = list()
        for i in range(self.rowCount()):
            p = self.item(i, 0)
            v = self.item(i, 1)
            if p and v:
                vl.append((float(p.text()),float(v.text()),0))
        self.set_prop(vl)
        self.fp.recompute()

    def on_double_click(self):
        for currentQTableWidgetItem in self.selectedItems():
            print("(%d,%d) double clicked : %s"%(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text()))

    def on_click(self):
        for currentQTableWidgetItem in self.selectedItems():
            print("(%d,%d) clicked : %s"%(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text()))

    def set_prop(self,data):
        docname = self.fp.Document.Name
        objname = self.fp.Name
        st = "FreeCAD.getDocument('"+docname+"').getObject('"+objname+"')."+self.prop+"="+str(data)
        FreeCADGui.doCommand(st)
 
if __name__ == '__main__':
    z=Test()
    z.setEdit()


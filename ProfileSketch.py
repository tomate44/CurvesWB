# -*- coding: utf8 -*-

import os
import FreeCAD, FreeCADGui
import Part, Sketcher
from pivy.coin import *
import dummy

try:
    from PySide import QtCore, QtGui, QtSvg
except ImportError:
    FreeCAD.Console.PrintMessage("Error: Python-pyside package must be installed on your system to use this tool.")


path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

class ProfileTaskPanel:
    '''A TaskPanel for the facebinder'''
    def __init__(self):
        
        self.obj = None
        self.form = QtGui.QWidget()
        self.form.setObjectName("FacebinderTaskPanel")
        self.grid = QtGui.QGridLayout(self.form)
        self.grid.setObjectName("grid")
        self.title = QtGui.QLabel(self.form)
        self.grid.addWidget(self.title, 0, 0, 1, 2)

        # tree
        self.tree = QtGui.QTreeWidget(self.form)
        self.grid.addWidget(self.tree, 1, 0, 1, 2)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Name","Subelement"])

        # buttons
        self.addButton = QtGui.QPushButton(self.form)
        self.addButton.setObjectName("addButton")
        self.addButton.setIcon(QtGui.QIcon(":/icons/Arch_Add.svg"))
        self.grid.addWidget(self.addButton, 3, 0, 1, 1)

        self.delButton = QtGui.QPushButton(self.form)
        self.delButton.setObjectName("delButton")
        self.delButton.setIcon(QtGui.QIcon(":/icons/Arch_Remove.svg"))
        self.grid.addWidget(self.delButton, 3, 1, 1, 1)

        QtCore.QObject.connect(self.addButton, QtCore.SIGNAL("clicked()"), self.addElement)
        QtCore.QObject.connect(self.delButton, QtCore.SIGNAL("clicked()"), self.removeElement)
        self.update()

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok)

    def update(self):
        'fills the treewidget'
        self.tree.clear()
        if self.obj:
            for f in [self.obj.Edge1,self.obj.Edge2]:
                if isinstance(f[1],tuple):
                    for subf in f[1]:
                        item = QtGui.QTreeWidgetItem(self.tree)
                        item.setText(0,f[0].Name)
                        item.setIcon(0,QtGui.QIcon(":/icons/Tree_Part.svg"))
                        item.setText(1,subf)  
                else:
                    item = QtGui.QTreeWidgetItem(self.tree)
                    item.setText(0,f[0].Name)
                    item.setIcon(0,QtGui.QIcon(":/icons/Tree_Part.svg"))
                    item.setText(1,str(f[1][0]))
        self.retranslateUi(self.form)

    def addElement(self):
        if self.obj:
            for sel in FreeCADGui.Selection.getSelectionEx():
                if sel.HasSubObjects:
                    obj = sel.Object
                    for elt in sel.SubElementNames:
                        if "Edge" in elt:
                            flist = [self.obj.Edge1,self.obj.Edge2]
                            found = False
                            for edge in flist:
                                if (edge[0] == obj.Name):
                                    if isinstance(edge[1],tuple):
                                        for subf in edge[1]:
                                            if subf == elt:
                                                found = True
                                    else:
                                        if (edge[1] == elt):
                                            found = True
                            if not found:
                                flist.append((obj,elt))
                                self.obj.Edge1 = flist[0]
                                self.obj.Edge2 = flist[1]
                                FreeCAD.ActiveDocument.recompute()
            self.update()

    def removeElement(self):
        if self.obj:
            it = self.tree.currentItem()
            if it:
                obj = FreeCAD.ActiveDocument.getObject(str(it.text(0)))
                elt = str(it.text(1))
                flist = []
                for edge in [self.obj.Edge1,self.obj.Edge2]:
                    if (edge[0].Name != obj.Name):
                        flist.append(edge)
                    else:
                        if isinstance(edge[1],tuple):
                            for subf in edge[1]:
                                if subf != elt:
                                    flist.append((obj,subf))
                        else:
                            if (edge[1] != elt):
                                flist.append(edge)
                self.obj.Edge1 = flist[0]
                self.obj.Edge2 = flist[1]
                FreeCAD.ActiveDocument.recompute()
            self.update()

    def accept(self):
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def retranslateUi(self, TaskPanel):
        TaskPanel.setWindowTitle(QtGui.QApplication.translate("draft", "Faces", None))
        self.delButton.setText(QtGui.QApplication.translate("draft", "Remove", None))
        self.addButton.setText(QtGui.QApplication.translate("draft", "Add", None))
        self.title.setText(QtGui.QApplication.translate("draft", "Facebinder elements", None))




class profile:
    "creates a profile sketch"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub",  "Edge1",        "Profile",   "First support edge")
        obj.addProperty("App::PropertyLinkSub",  "Edge2",        "Profile",   "Second support edge")
        obj.addProperty("App::PropertyFloat",    "Parameter1",   "Profile",   "Parameter on first edge")
        obj.addProperty("App::PropertyFloat",    "Parameter2",   "Profile",   "Parameter on second edge")
        obj.addProperty("App::PropertyVector",   "MainAxis",     "Profile",   "Main axis of the sketch")
        obj.addProperty("Part::PropertyPartShape","Shape",       "Profile",   "Shape of the object")
        obj.Proxy = self

    def getEdges(self, obj):
        res = []
        try:
            if hasattr(obj, "Edge1"):
                n = eval(obj.Edge1[1][0].lstrip('Edge'))
                res.append(obj.Edge1[0].Shape.Edges[n-1])
            if hasattr(obj, "Edge2"):
                n = eval(obj.Edge2[1][0].lstrip('Edge'))
                res.append(obj.Edge2[0].Shape.Edges[n-1])
            return(res)
        except TypeError:
            return(None)

    def execute(self, obj):
        e1,e2 = self.getEdges(obj)
        if hasattr(obj, "Parameter1") and hasattr(obj, "Parameter2") and hasattr(obj, "MainAxis"):
            l1 = Part.LineSegment(e1.valueAt(obj.Parameter1), e2.valueAt(obj.Parameter2))
            obj.Shape = l1.toShape().extrude(obj.MainAxis)
        return()
    
    def onChanged(self, fp, prop):
        e1,e2 = self.getEdges(fp)
        if prop == "Parameter1":
            if fp.Parameter1 < e1.FirstParameter:
                fp.Parameter1 = e1.FirstParameter
            elif fp.Parameter1 > e1.LastParameter:
                fp.Parameter1 = e1.LastParameter
        elif prop == "Parameter2":
            if fp.Parameter2 < e2.FirstParameter:
                fp.Parameter2 = e2.FirstParameter
            elif fp.Parameter2 > e2.LastParameter:
                fp.Parameter2 = e2.LastParameter
        elif prop in ["Edge1","Edge2","MainAxis"]:
            self.execute(fp)

class profileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/joincurve.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        debug("setEdit - %s - %s"%(str(vobj),str(mode)))
        #import DraftGui
        taskd = ProfileTaskPanel()
        taskd.obj = vobj.Object
        taskd.update()
        FreeCADGui.Control.showDialog(taskd)
        return(True)
    
    def unsetEdit(self,vobj,mode):
        debug("unsetEdit - %s - %s"%(str(vobj),str(mode)))
        FreeCADGui.Control.closeDialog()
        return False

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    #def claimChildren(self):
        #return None #[self.Object.Base, self.Object.Tool]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        return True


class profileCommand:
    "creates a profile sketch"
    def makeProfileFeature(self, shapes, params):
        prof = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','Profile')
        profile(prof)
        profileVP(prof.ViewObject)
        if isinstance(shapes,list):
            prof.Edge1 = shapes[0]
            prof.Edge2 = shapes[1]
            prof.Parameter1 = params[0]
            prof.Parameter2 = params[1]
            prof.MainAxis = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        else:
            prof.Base = source
        FreeCAD.ActiveDocument.recompute()
        prof.ViewObject.LineWidth = 2.0
        prof.ViewObject.LineColor = (0.5,0.0,0.5)

    def Activated(self):
        shapes = []
        params = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select 2 edges or vertexes first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        shapes.append((selobj.Object, selobj.SubElementNames[i]))
                        p = selobj.PickedPoints[i]
                        poe = selobj.SubObjects[i].distToShape(Part.Vertex(p))
                        par = poe[2][0][2]
                        params.append(par)
                    elif isinstance(selobj.SubObjects[i], Part.Vertex):
                        shapes.append((selobj.Object, selobj.SubElementNames[i]))
                        #p = selobj.PickedPoints[i]
                        #poe = so.distToShape(Part.Vertex(p))
                        #par = poe[2][0][2]
                        params.append(0)
            else:
                FreeCAD.Console.PrintError("Select 2 edges or vertexes first !\n")
        if shapes:
            self.makeProfileFeature(shapes, params)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/joincurve.svg', 'MenuText': 'Create profile sketch', 'ToolTip': 'creates a profile sketch'}

FreeCADGui.addCommand('profile', profileCommand())

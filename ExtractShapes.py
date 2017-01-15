import os
import FreeCAD,FreeCADGui, Part
from pivy.coin import *
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class extract:
    "this class will extract the selected shapes from objects"
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        for o in s:
            objName = o.ObjectName
            for so,name in zip(o.SubObjects,o.SubElementNames):
                fullname = objName+"_"+name
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature",fullname)
                newobj.Shape = so
            o.Object.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/extract.svg', 'MenuText': 'Extract', 'ToolTip': 'Extract selected shapes from objects'}

FreeCADGui.addCommand('extract', extract()) 

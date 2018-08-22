# -*- coding: utf-8 -*-

__title__ = "to console"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Objects to python console."

import FreeCAD
import FreeCADGui
import _utils

TOOL_ICON = _utils.iconsPath() + '/toconsole.svg'
#debug = _utils.debug
debug = _utils.doNothing

class ToConsole:
    "Brings the selected objects to the python console"
    def GetResources(self):
        return {'Pixmap'  : TOOL_ICON,
                'MenuText': "to Console",
                'Accel': "",
                'ToolTip': "Objects to console"}

    def Activated(self):
        doc = ''
        obj = ''
        sob = ''
        sublinks = '('

        doc_num = 0
        obj_num = 0
        face_num = 0
        edge_num = 0
        vert_num = 0

        selection = FreeCADGui.Selection.getSelectionEx()
        if selection == []:
            FreeCAD.Console.PrintError('Selection is empty.\n')

        for selobj in selection:
            if not selobj.DocumentName == doc:
                doc = selobj.DocumentName
                doc_num += 1
                FreeCADGui.doCommand("doc%d = FreeCAD.getDocument('%s')"%(doc_num,doc))
            if not selobj.ObjectName == obj:
                obj = selobj.ObjectName
                obj_num += 1
                FreeCADGui.doCommand("obj%d = doc%d.getObject('%s')"%(obj_num,doc_num,obj))
            if selobj.HasSubObjects:
                for sub in selobj.SubElementNames:
                    sublinks += "(obj%d,('%s')),"%(obj_num,sub)
                    if 'Vertex' in sub:
                        vert_num += 1
                        FreeCADGui.doCommand("v%d = obj%d.Shape.%s"%(vert_num,obj_num,sub))
                    if 'Edge' in sub:
                        edge_num += 1
                        FreeCADGui.doCommand("e%d = obj%d.Shape.%s"%(edge_num,obj_num,sub))
                    if 'Face' in sub:
                        face_num += 1
                        FreeCADGui.doCommand("f%d = obj%d.Shape.%s"%(face_num,obj_num,sub))
        sublinks += ")"
        if len(sublinks) > 2:
            FreeCADGui.doCommand("_sub_link_buffer = %s"%sublinks)
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            selection = FreeCADGui.Selection.getSelectionEx()
            if selection:
                return True
        else:
            return False

FreeCADGui.addCommand('to_console',ToConsole())

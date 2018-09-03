# -*- coding: utf-8 -*-

__title__ = "Select Adjacent faces"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Select the Adjacent faces of the selected subshape"

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = 'WhatsThis.svg'
debug = _utils.debug
debug = _utils.doNothing



class adjacentfacesCommand:
    """Select the Adjacent faces of the selected subshape"""

    def find_subobject(self, shape, subname):
        sub = None
        if 'Face' in subname:
            n = eval(subname.lstrip('Face'))
            sub = shape.Faces[n-1]
        elif 'Edge' in subname:
            n = eval(subname.lstrip('Edge'))
            sub = shape.Edges[n-1]
        elif 'Vertex' in subname:
            n = eval(subname.lstrip('Vertex'))
            sub = shape.Vertexes[n-1]
        return(sub)

    def get_subname(self, shape, sub):
        if isinstance(sub, Part.Face):
            for i in range(len(shape.Faces)):
                if sub.isEqual(shape.Faces[i]):
                    return("Face%d"%(i+1))
        elif isinstance(sub, Part.Edge):
            for i in range(len(shape.Edges)):
                if sub.isEqual(shape.Edges[i]):
                    return("Edge%d"%(i+1))
        if isinstance(sub, Part.Vertex):
            for i in range(len(shape.Vertexes)):
                if sub.isEqual(shape.Vertexes[i]):
                    return("Vertex%d"%(i+1))

    def Activated(self):
        search_type = Part.Face
        result = list()
        obj = None
        s = FreeCADGui.Selection.getSelectionEx()
        FreeCADGui.Selection.clearSelection()
        subs = list()
        for selo in s:
            if selo.HasSubObjects:
                obj = selo.Object
                shape = obj.Shape.copy()
                for subname in selo.SubElementNames:
                    #print(subname)
                    sub = self.find_subobject(shape, subname)
                    if isinstance(sub, Part.Face):
                        subs += sub.Edges
                    else:
                        subs.append(sub)
                for sub in subs:
                    anc = shape.ancestorsOfType(sub, search_type)
                    #print(anc)
                    result += anc
                    for a in anc:
                        FreeCADGui.Selection.addSelection(obj, self.get_subname(shape, a))

    def IsActive(self):
        s = FreeCADGui.Selection.getSelectionEx()
        for selo in s:
            if selo.HasSubObjects:
                return(True)
        return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Adjacent faces', 'ToolTip': 'Select the Adjacent faces of the selected subshape'}

FreeCADGui.addCommand('adjacent_faces', adjacentfacesCommand())



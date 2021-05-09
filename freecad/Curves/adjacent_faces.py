# -*- coding: utf-8 -*-

__title__ = "Select Adjacent faces"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Select the Adjacent faces of the selected subshape"
__usage__ = """Select a face or an edge in the 3D View, activate tool
and all the faces that touch it will be added to the selection."""

import os
import FreeCAD
from FreeCADGui import Selection as sel
from FreeCADGui import addCommand
import Part
from . import ICONPATH


TOOL_ICON = os.path.join(ICONPATH, 'adjacent_faces.svg')


class adjacentfacesCommand:
    """Select the Adjacent faces of the selected subshape"""

    def get_subname(self, shape, sub):
        if isinstance(sub, Part.Face):
            for i in range(len(shape.Faces)):
                if sub.isEqual(shape.Faces[i]):
                    return "Face{}".format(i + 1)
        elif isinstance(sub, Part.Edge):
            for i in range(len(shape.Edges)):
                if sub.isEqual(shape.Edges[i]):
                    return "Edge{}".format(i + 1)
        if isinstance(sub, Part.Vertex):
            for i in range(len(shape.Vertexes)):
                if sub.isEqual(shape.Vertexes[i]):
                    return "Vertex{}".format(i + 1)

    def Activated(self):
        search_type = Part.Face
        result = list()
        obj = None
        s = sel.getSelectionEx()
        sel.clearSelection()
        subs = list()
        for selo in s:
            if selo.HasSubObjects:
                obj = selo.Object
                shape = obj.Shape.copy()
                for subname in selo.SubElementNames:
                    sub = shape.getElement(subname)
                    if isinstance(sub, Part.Face):
                        subs += sub.Edges
                    else:
                        subs.append(sub)
                for sub in subs:
                    anc = shape.ancestorsOfType(sub, search_type)
                    result += anc
                    for a in anc:
                        sel.addSelection(obj, self.get_subname(shape, a))
        if len(result) == 0:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Adjacent faces',
                'ToolTip': "{}\n\n{}\n\n{}".format(__title__, __doc__, __usage__)}


addCommand('Curves_adjacent_faces', adjacentfacesCommand())

# -*- coding: utf-8 -*-

__title__ = "Curves workbench utilities"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Curves workbench utilities common to all tools."

import FreeCAD

def setIconsPath(path):
    global icons_path
    icons_path = path
    return(True)

def iconsPath():
    global icons_path
    return(icons_path)

def debug(string):
    FreeCAD.Console.PrintMessage("%s\n"%string)

def doNothing(string):
    return(None)

def getSubShape(shape, shape_type, n):
    if shape_type == "Vertex" and len(shape.Vertexes) >= n:
        return(shape.Vertexes[n-1])
    elif shape_type == "Edge" and len(shape.Edges) >= n:
        return(shape.Edges[n-1])
    elif shape_type == "Face" and len(shape.Faces) >= n:
        return(shape.Faces[n-1])
    else:
        return(None)

def getShape(obj, prop, shape_type):
    if hasattr(obj, prop):
        if obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSub":
            n = eval(obj.getPropertyByName(prop)[1][0].lstrip(shape_type))
            return(getSubShape(obj.getPropertyByName(prop)[0].Shape, shape_type, n))
        elif obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSubList":
            res = []
            for tup in obj.getPropertyByName(prop):
                n = eval(tup[1][0].lstrip(shape_type))
                res.append(getSubShape(tup[0].Shape, shape_type, n))
            return(res)
        else:
            FreeCAD.Console.PrintError("CurvesWB._utils.getShape: wrong property type.\n")
            return(None)
    else:
        FreeCAD.Console.PrintError("CurvesWB._utils.getShape: %r has no property %r\n"%(obj, prop))
        return(None)

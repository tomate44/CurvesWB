# -*- coding: utf-8 -*-

__title__ = "Oriented sketch"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Sketch normal to an edge, with up vector normal to a face"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import os
import FreeCAD
import FreeCADGui
import Part
import Sketcher
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join( ICONPATH, 'oriented_sketch.svg')
#debug = _utils.debug
#debug = _utils.doNothing

props = """
App::PropertyBool
App::PropertyBoolList
App::PropertyFloat
App::PropertyFloatList
App::PropertyFloatConstraint
App::PropertyQuantity
App::PropertyQuantityConstraint
App::PropertyAngle
App::PropertyDistance
App::PropertyLength
App::PropertySpeed
App::PropertyAcceleration
App::PropertyForce
App::PropertyPressure
App::PropertyInteger
App::PropertyIntegerConstraint
App::PropertyPercent
App::PropertyEnumeration
App::PropertyIntegerList
App::PropertyIntegerSet
App::PropertyMap
App::PropertyString
App::PropertyUUID
App::PropertyFont
App::PropertyStringList
App::PropertyLink
App::PropertyLinkSub
App::PropertyLinkList
App::PropertyLinkSubList
App::PropertyMatrix
App::PropertyVector
App::PropertyVectorList
App::PropertyPlacement
App::PropertyPlacementLink
App::PropertyColor
App::PropertyColorList
App::PropertyMaterial
App::PropertyPath
App::PropertyFile
App::PropertyFileIncluded
App::PropertyPythonObject
Part::PropertyPartShape
Part::PropertyGeometryList
Part::PropertyShapeHistory
Part::PropertyFilletEdges
Sketcher::PropertyConstraintList
"""

class orientedSketchFP:
    """Creates a Oriented sketch"""
    def __init__(self, obj, edge, face):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Edge", "OrientedSketch", "Edge support")
        obj.addProperty("App::PropertyLinkSub", "Face", "OrientedSketch", "Face support")
        obj.addProperty("App::PropertyFloatConstraint", "Parameter", "OrientedSketch", "Parameter on edge")
        obj.Proxy = self

        obj.Edge = edge
        obj.Face = face
        obj.Parameter = (0.0, 0.0, 1.0, 0.05)

    def execute(self, obj):
        edges = []
        for g in obj.Geometry:
            if hasattr(g, 'Construction') and not g.Construction:
                #try:
                edges.append(g.toShape())
                #except AttributeError:
                    #debug("Failed to convert %s to BSpline"%str(g))
        if edges:
            c = Part.Compound([])
            se = Part.sortEdges(edges)
            for l in se:
                c.add(Part.Wire(l))
            obj.Shape = c

    def onChanged(self, obj, prop):
        if prop == "Parameter":
            e = _utils.getShape(obj, "Edge", "Edge")
            f = _utils.getShape(obj, "Face", "Face")
            p = e.FirstParameter + (e.LastParameter - e.FirstParameter) * obj.Parameter
            loc = e.valueAt(p)
            u, v = f.Surface.parameter(loc)
            norm = f.normalAt(u, v)
            #print("{0!s} - {1!s}".format(p, loc))
            x = norm.cross(e.tangentAt(p))
            rot = FreeCAD.Rotation(x, norm, e.tangentAt(p))
            obj.Placement.Base = loc
            obj.Placement.Rotation = rot


class orientedSketchVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

class oriented_sketch_cmd:
    """Creates a Oriented sketch"""
    def makeFeature(self, e, f):
        fp = FreeCAD.ActiveDocument.addObject("Sketcher::SketchObjectPython", "Oriented sketch")
        orientedSketchFP(fp, e, f)
        orientedSketchVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        e = None
        f = None
        for s in sel:
            for sen in s.SubElementNames:
                if "Edge" in sen:
                    e = (s.Object, sen)
                elif "Face" in sen:
                    f = (s.Object, sen)
        if e and f:
            self.makeFeature(e, f)
        else:
            FreeCAD.Console.PrintError("Select 1 edge and 1 face first !\n")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('oriented_sketch', oriented_sketch_cmd())

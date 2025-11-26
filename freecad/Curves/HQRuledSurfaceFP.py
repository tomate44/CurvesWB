# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "HQ Ruled surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """High Quality ruled surface.
The 2 edges (or wires) are reparametrized before surface creation."""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import reparametrize as rp

from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join( ICONPATH, 'ruled_surface.svg')
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

class HQ_Ruled_SurfaceFP:
    """Creates a ..."""
    def __init__(self, obj, sources):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList",    "SourceObjects", "HQ_Ruled_Surface", "SourceObjects")
        obj.addProperty("App::PropertyLinkSubList", "SourceShapes",  "HQ_Ruled_Surface", "SourceShapes")
        obj.addProperty("App::PropertyInteger",     "Samples",       "HQ_Ruled_Surface", "Number of orthogonal samples").Samples = 20
        obj.addProperty("App::PropertyFloatConstraint","SmoothingFactorStart", "HQ_Ruled_Surface", "Smoothing factor on curve start")
        obj.addProperty("App::PropertyFloatConstraint","SmoothingFactorEnd", "HQ_Ruled_Surface", "Smoothing factor on curve end")
        obj.addProperty("App::PropertyInteger",     "Method", "HQ_Ruled_Surface", "Projection method (1,2,3,4)").Method = 3
        obj.addProperty("App::PropertyFloat", "Tol3D", "HQ_Ruled_Surface", "3D tolerance").Tol3D = 1e-5
        obj.addProperty("App::PropertyFloat", "Tol2D", "HQ_Ruled_Surface", "Parametric tolerance").Tol2D = 1e-8
        obj.SmoothingFactorStart = (0.2, 0.0, 0.5, 0.05)
        obj.SmoothingFactorEnd = (0.2, 0.0, 0.5, 0.05)
        objs = []
        shapes = []
        for s in sources:
            if isinstance(s, (list, tuple)):
                shapes.append(s)
            else:
                objs.append(s)
        obj.SourceObjects = objs
        obj.SourceShapes = shapes
        obj.setEditorMode("Tol3D",2)
        obj.setEditorMode("Tol2D",2)
        obj.setEditorMode("Method",0)
        obj.Proxy = self

    def get_curves(self, obj):
        curves = []
        edges = []
        for o in obj.SourceObjects:
            curves.extend(o.Shape.Wires)
            edges.extend(o.Shape.Edges)
        if len(curves) == 2:
            return curves[0], curves[1]
        if len(edges) == 2:
            return edges[0], edges[1]
        edges = _utils.getShape(obj, "SourceShapes", "Edge")
        if len(edges) == 2:
            return edges[0], edges[1]

    def execute(self, obj):
        c1, c2 = self.get_curves(obj)
        nc1, nc2 = rp.reparametrize(c1, c2, num=obj.Samples, smooth_start=obj.SmoothingFactorStart, smooth_end=obj.SmoothingFactorEnd, method=obj.Method )
        #com = Part.Compound([nc1.toShape(), nc2.toShape()])
        rs = Part.makeRuledSurface(nc1.toShape(), nc2.toShape())
        if isinstance(rs, Part.Face) and rs.isValid():
            obj.Shape = rs

    def onChanged(self, obj, prop):
        return(False)

class HQ_Ruled_SurfaceVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

class HQ_Ruled_Surface_Command:
    """Creates a ..."""
    def makeFeature(self, edges):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","HQ Ruled Surface")
        HQ_Ruled_SurfaceFP(fp, edges)
        HQ_Ruled_SurfaceVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        edges = []
        for so in s:
            for i in range(len(so.SubObjects)):
                #subshapes(su)
                if isinstance(so.SubObjects[i], Part.Edge):
                    edges.append((so.Object,(so.SubElementNames[i], )))
            if not so.HasSubObjects:
                if so.Object.Shape.Wires:
                    edges.append(so.Object)
                elif so.Object.Shape.Edges:
                    edges.append(so.Object)

        if len(edges) < 1:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(edges)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}

FreeCADGui.addCommand('hq_ruled_surface', HQ_Ruled_Surface_Command())

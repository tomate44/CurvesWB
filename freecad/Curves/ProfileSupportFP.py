# -*- coding: utf-8 -*-

__title__ = 'Profile Support'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Creates a support shape between two rails'

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH
from freecad.Curves import SweepObject

TOOL_ICON = os.path.join(ICONPATH, 'profile_support.svg')
# debug = _utils.debug
# debug = _utils.doNothing

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


class ProfileSupportFP:
    """Creates a ..."""
    def __init__(self, obj, sel):
        """Add the properties"""
        obj.addProperty("App::PropertyLink", "Rail1",
                        "Sources", "Tooltip")
        obj.addProperty("App::PropertyLink", "Rail2",
                        "Sources", "Tooltip")
        obj.addProperty("App::PropertyLink", "ProfileShape",
                        "Sources", "Tooltip")
        obj.addProperty("App::PropertyFloatConstraint", "Position1",
                        "Settings", "Tooltip")
        obj.addProperty("App::PropertyFloatConstraint", "Position2",
                        "Settings", "Tooltip")
        obj.addProperty("App::PropertyFloatConstraint", "NormalPosition",
                        "Settings", "Tooltip")
        obj.addProperty("App::PropertyBool", "NormalReverse",
                        "Settings", "Tooltip")
        obj.addProperty("App::PropertyDistance", "ChordLength",
                        "Info", "Tooltip")
        obj.addProperty("App::PropertyDistance", "Rail1Length",
                        "Info", "Tooltip")
        obj.addProperty("App::PropertyDistance", "Rail2Length",
                        "Info", "Tooltip")
        # obj.setPropertyStatus("ChordLength", "Output")
        # obj.setPropertyStatus("Rail1Length", "Output")
        # obj.setPropertyStatus("Rail2Length", "Output")
        obj.NormalPosition = (0.0, 0.0, 1.0, 0.05)
        obj.Position1 = (0.0, 0.0, 1.0, 0.05)
        obj.Position2 = (-0.05, -0.05, 1.0, 0.05)
        obj.setEditorMode("Position2", 2)
        obj.Rail1 = sel[0]
        if len(sel) == 3:
            obj.Rail2 = sel[1]
        obj.ProfileShape = sel[-1]
        obj.Proxy = self

    def execute(self, obj):
        e1 = obj.Rail1.Shape.Edge1
        if obj.Rail2:
            e2 = obj.Rail2.Shape.Edge1
        elif len(obj.Rail1.Shape.Edges) == 4:
            e2 = obj.Rail1.Shape.Edge3
        else:
            e2 = obj.Rail1.Shape.Edge2
        obj.Rail1Length = e1.Length
        obj.Rail2Length = e2.Length
        path2R = SweepObject.Path2Rails(e1, e2)
        path2R.ReversedNormal = obj.NormalReverse
        sh = obj.ProfileShape.Shape.copy()
        prof = SweepObject.ProfileShape(obj.ProfileShape.Shape)
        sp, ep = prof.end_points()
        size = (ep - sp).Length
        m, width = path2R.get_transform_matrix(obj.Position1, obj.Position2, obj.NormalPosition)
        sh = obj.ProfileShape.Shape.copy()
        sh.scale(width / size, sp)
        prof = SweepObject.ProfileShape(sh)
        obj.Shape = prof.BaseShape
        obj.Placement = FreeCAD.Placement(m)
        # p1 = e1.getParameterByLength(obj.Position1 * e1.Length)
        # origin = e1.valueAt(p1)
        # rs = Part.makeRuledSurface(e1, e2)
        # u0, v0 = rs.Surface.parameter(origin)
        # normal = rs.Surface.normal(u0, obj.NormalPosition)
        # if obj.NormalReverse:
        #     normal = -normal
        # uiso = rs.Surface.uIso(u0)
        # width = uiso.length()
        # obj.ChordLength = width
        # tangent = uiso.tangent(obj.NormalPosition)[0]
        # bino = -normal.cross(tangent)
        # # if obj.NormalReverse:
        # #     bino = -bino
        # m = FreeCAD.Matrix(tangent.x, normal.x, bino.x, origin.x,
        #                    tangent.y, normal.y, bino.y, origin.y,
        #                    tangent.z, normal.z, bino.z, origin.z,
        #                    0, 0, 0, 1)
        # # print(m.analyze())
        # line1 = Part.makeLine(FreeCAD.Vector(), FreeCAD.Vector(width, 0.0, 0.0))
        # pt = FreeCAD.Vector(obj.NormalPosition * width, 0.0, 0.0)
        # line2 = Part.makeLine(pt, pt + FreeCAD.Vector(0.0, width, 0.00))
        # obj.Shape = Part.Compound([line1, line2])
        # obj.Placement = FreeCAD.Placement(m)

    def onChanged(self, obj, prop):
        if prop == "Position1":
            # e1 = obj.Rail1.Shape.Edge1
            # if obj.Position1 > e1.Length:
            #     obj.Position1 = e1.Length
            # elif obj.Position1 < -e1.Length:
            #     obj.Position1 = -e1.Length
            self.execute(obj)
        if prop == "NormalPosition":
            self.execute(obj)


class ProfileSupportVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def claimChildren(self):
        return [self.Object.ProfileShape, ]

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None


class ProfileSupportCommand:
    """Create a ... feature"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Profile Support")
        ProfileSupportFP(fp, sel)
        ProfileSupportVP(fp.ViewObject)
        fp.ViewObject.PointSize = 5
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) < 1:
            FreeCAD.Console.PrintError("Select 2 edges\n")
        else:
            self.makeFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curves_ProfileSupport', ProfileSupportCommand())

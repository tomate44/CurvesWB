# -*- coding: utf-8 -*-

__title__ = "Constrained Profile"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates an constrained interpolation curve"

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
import profile_editor
reload(profile_editor)

TOOL_ICON = _utils.iconsPath() + '/icon.svg'
#debug = _utils.debug
#debug = _utils.doNothing

#App::PropertyBool
#App::PropertyBoolList
#App::PropertyFloat
#App::PropertyFloatList
#App::PropertyFloatConstraint
#App::PropertyQuantity
#App::PropertyQuantityConstraint
#App::PropertyAngle
#App::PropertyDistance
#App::PropertyLength
#App::PropertySpeed
#App::PropertyAcceleration
#App::PropertyForce
#App::PropertyPressure
#App::PropertyInteger
#App::PropertyIntegerConstraint
#App::PropertyPercent
#App::PropertyEnumeration
#App::PropertyIntegerList
#App::PropertyIntegerSet
#App::PropertyMap
#App::PropertyString
#App::PropertyUUID
#App::PropertyFont
#App::PropertyStringList
#App::PropertyLink
#App::PropertyLinkSub
#App::PropertyLinkList
#App::PropertyLinkSubList
#App::PropertyMatrix
#App::PropertyVector
#App::PropertyVectorList
#App::PropertyPlacement
#App::PropertyPlacementLink
#App::PropertyColor
#App::PropertyColorList
#App::PropertyMaterial
#App::PropertyPath
#App::PropertyFile
#App::PropertyFileIncluded
#App::PropertyPythonObject
#Part::PropertyPartShape
#Part::PropertyGeometryList
#Part::PropertyShapeHistory
#Part::PropertyFilletEdges
#Sketcher::PropertyConstraintList

def midpoint(e):
    p = e.FirstParameter + 0.5 * (e.LastParameter - e.FirstParameter)
    return(e.valueAt(p))

class GordonProfileFP:
    """Creates a ..."""
    def __init__(self, obj, s):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList",    "Support",         "Profile", "Support curves that are intersected").Support = s
        #obj.addProperty("App::PropertyEnumeration", "Parametrization", "Profile", "Parametrization type").Parametrization=["ChordLength","Centripetal","Uniform"]
        obj.addProperty("App::PropertyFloat",       "Tolerance",       "Profile", "Tolerance").Tolerance = 1e-5
        obj.addProperty("App::PropertyBool",        "Periodic",        "Profile", "Periodic curve").Periodic = False
        obj.addProperty("App::PropertyVectorList",  "Points",          "Profile", "Interpolated points")
        obj.addProperty("App::PropertyIntegerList", "Type",            "Profile", "Types of interpolated points")
        #obj.addProperty("App::PropertyVector",      "InitialTangent",  "Profile", "Initial Tangent")
        #obj.addProperty("App::PropertyVector",      "FinalTangent",    "Profile", "Final Tangent")
        #obj.addProperty("App::PropertyFloatList",   "Parameters",      "Profile", "Parameters of intersection points")
        #obj.setEditorMode("Parameters", 0)
        #obj.Parametrization = "ChordLength"
        obj.Proxy = self 

    def get_edges(self, fp):
        e = list()
        for o in fp.Support:
            e.extend(o.Shape.Edges)
        return(e)

    def get_points(self, fp):
        pts = list()
        for e in self.get_edges(fp):
            pts.append(midpoint(e))
        if len(pts) > 0:
            fp.Points = pts
            fp.Type = [1] * len(pts)

    def execute(self, obj):
        if len(obj.Points) == 0:
            self.get_points(obj)
        elif len(obj.Points) == 1:
            FreeCAD.Console.PrintError("Gordon Profile : Not enough points\n")
        else:
            curve = Part.BSplineCurve()
            curve.interpolate(Points=obj.Points, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance)
            obj.Shape = curve.toShape()

    def onChanged(self, fp, prop):
        return(False)

class GordonProfileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def doubleClicked(self,vobj):
        if not hasattr(self,'active'):
            self.active = False
        if not self.active:
            self.active = True
            pts = list()
            for i in range(len(self.Object.Points)):
                p = self.Object.Points[i]
                t = self.Object.Type[i]
                if t == 0:
                    pts.append(profile_editor.ConnectionMarker([p]))
                elif t == 1:
                    sol = None
                    mini = 1e50
                    for e in self.Object.Proxy.get_edges(self.Object):
                        d,points,info = e.distToShape(Part.Vertex(p))
                        if d < mini:
                            mini = d
                            sol = [e,e.Curve.parameter(points[0][0])]
                    pts.append(profile_editor.MarkerOnEdge([sol]))
            self.ip = profile_editor.InterpolationPolygon(pts, self.Object)
        else:
            self.active = False
            pts = list()
            typ = list()
            for p in self.ip.points:
                pts.append(p.points[0])
                if isinstance(p,profile_editor.ConnectionMarker):
                    typ.append(0)
                elif isinstance(p,profile_editor.MarkerOnEdge):
                    typ.append(1)
            self.Object.Points = pts
            self.Object.Type = typ
            self.ip.quit()
        return(True)

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class GordonProfileCommand:
    """Creates a ..."""
    def makeFeature(self, s):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Gordon Profile")
        GordonProfileFP(fp, s)
        GordonProfileVP(fp.ViewObject)
        #tups = profile_editor.get_guide_params()
        #ip = profile_editor.InterpolationPolygon(tups, fp)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('gordon_profile', GordonProfileCommand())

# -*- coding: utf-8 -*-

__title__ = "Helical Sweep"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Sweep an open wire along an helical path"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
import nurbs_tools
from math import pi
vec2 = FreeCAD.Base.Vector2d

TOOL_ICON = _utils.iconsPath() + '/helical_sweep.svg'
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

def vadd(v1,v2):
    return vec2(v1.x + v2.x, v1.y + v2.y)

def vmul(v1,f):
    return vec2(v1.x*f, v1.y*f)

class HelicalSweep:
    """Sweep a profile along an helical path"""
    def __init__(self):
        self._plane = Part.Plane()
        self.nb_of_turns = 2.5
        self.lead = 20.0
        self.flatends = False
        self.cylinder = Part.Cylinder()
        self.cylinder.transform(FreeCAD.Placement(FreeCAD.Vector(),FreeCAD.Vector(1,0,0),-90).toMatrix())
        self.rational_approx = True
        self.check_splines = False
    def set_placement(self,pl):
        self._plane.transform(pl.toMatrix())
        self.cylinder.transform(pl.toMatrix())
    def sweep_Point2D(self, v, y=0):
        if isinstance(v, FreeCAD.Base.Vector2d):
            sp = vec2(0,v.y)
            self.cylinder.Radius = v.x
        else:
            sp = vec2(0,y)
            self.cylinder.Radius = v
        vector_one_turn = vec2(2*pi,self.lead)
        vector_full_turns = vmul(vector_one_turn, self.nb_of_turns)
        lineseg = Part.Geom2d.Line2dSegment(sp, vadd(sp,vector_full_turns))
        if self.flatends:
            line = Part.Geom2d.Line2d(sp, vadd(sp,vector_full_turns))
            horiz = Part.Geom2d.Line2d(vec2(0,0), vec2(1,0))
            inter = line.intersectCC(horiz)[0]
            lineseg = Part.Geom2d.Line2dSegment(inter, vadd(inter,vector_full_turns))
        return lineseg.toShape(self.cylinder)
    def sweep_edge(self, e):
        #if isinstance(e.Curve,Part.Line):
            #fp = e.valueAt(e.FirstParameter)
            #lp = e.valueAt(e.LastParameter)
            #fp2d = vec2(*self._plane.projectPoint(fp,"LowerDistanceParameters"))
            #lp2d = vec2(*self._plane.projectPoint(lp,"LowerDistanceParameters"))
            #e1 = self.sweep_Point2D(fp2d)
            #e2 = self.sweep_Point2D(lp2d)
            #r = Part.makeRuledSurface(e1,e2)
            #return r
        if True:
            if self.rational_approx:
                approx = e.toNurbs().Edges[0]
            else:
                approx = e.Curve.toBSpline(e.FirstParameter,e.LastParameter).toShape()
            bs = approx.Curve
            #self.cylinder.transform(self.placement.toMatrix())
            poles = []
            weights = []
            oc = False
            for w,p in zip(bs.getWeights(), bs.getPoles()):
                p2d = vec2(*self._plane.projectPoint(p,"LowerDistanceParameters"))
                c = self.sweep_Point2D(p2d).Curve
                if oc and self.check_splines:
                    nurbs_tools.is_same(oc, c, 1e-3, True)
                oc = c
                poles.append(oc.getPoles())
                weights.append([w]*oc.NbPoles)
            bss = Part.BSplineSurface()
            bss.buildFromPolesMultsKnots(poles,
                                         bs.getMultiplicities(),oc.getMultiplicities(),  
                                         bs.getKnots(), oc.getKnots(),
                                         bs.isPeriodic(), oc.isPeriodic(),
                                         bs.Degree, oc.Degree,
                                         weights)
            return bss.toShape()
                
    def sweep_wire(self, w):
        faces = []
        for e in w.Edges:
            faces.append(self.sweep_edge(e))
        try:
            return Part.Shell(faces)
        except Part.OCCError:
            return Part.Compound(faces)


class HelicalSweepFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLink", "Profile", "Profile object")
        obj.addProperty("App::PropertyFloat", "Turns", "Settings", "Number of turns").Turns = 1.0
        obj.addProperty("App::PropertyFloat", "Lead", "Settings", "Thread lead (-1 for auto)").Lead = -1
        obj.addProperty("App::PropertyBool", "Rational", "Settings", "Allow rational bsplines").Rational = False
        obj.Proxy = self

    def execute(self, obj):
        edges =  obj.Profile.Shape.Edges
        hs = HelicalSweep()
        hs.rational_approx = obj.Rational
        gpl = obj.Profile.getGlobalPlacement()
        #o = gpl.multVec(FreeCAD.Vector(0,0,0))
        #x = gpl.multVec(FreeCAD.Vector(1,0,0))
        #y = gpl.multVec(FreeCAD.Vector(0,1,0))
        #hs._plane.transform(gpl.toMatrix())
        hs.set_placement(gpl)
        if hasattr(obj,"Lead") and obj.Lead >= 0:
            hs.lead = obj.Lead
        else:
            hs.lead = obj.Profile.getDatum("Lead").Value
        hs.nb_of_turns = obj.Turns
        faces = [hs.sweep_edge(e) for e in edges]
        obj.Shape = Part.Compound(faces)

    def onChanged(self, obj, prop):
        if prop == "Lead":
            if obj.Lead < 0:
                obj.Lead = -1

class HelicalSweepVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

class HelicalSweepCommand:
    """Creates a HelicalSweep Object"""
    def makeFeature(self, sel):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Helical Sweep")
        HelicalSweepFP(fp)
        HelicalSweepVP(fp.ViewObject)
        fp.Profile = sel
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel[0])

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('HelicalSweep', HelicalSweepCommand())

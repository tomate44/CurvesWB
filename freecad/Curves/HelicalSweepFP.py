# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Helical Sweep"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Sweep an open wire along an helical path"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import os
import FreeCAD
import FreeCADGui
import Part
from math import pi
from freecad.Curves import  _utils
from freecad.Curves import  nurbs_tools
vec2 = FreeCAD.Base.Vector2d

from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join( ICONPATH, 'helical_sweep.svg')
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
        self.lead = 10.0
        self.cylinder = Part.Cylinder()
        self.cylinder.transform(FreeCAD.Placement(FreeCAD.Vector(),FreeCAD.Vector(1,0,0),-90).toMatrix())
        self.rational_approx = True
        self.check_splines = False
        self.max_radius = 0
        self._placement = FreeCAD.Placement()
    def set_placement(self, pl):
        self._placement = pl
        self._plane.transform(pl.toMatrix())
        self.cylinder.transform(pl.toMatrix())
    def sweep_Point2D(self, v, extend=False):
        offset = 0
        nb_turns = self.nb_of_turns
        if extend:
            offset = -self.lead*2
            nb_turns = self.nb_of_turns + 4
        sp = vec2(0, v.y + offset)
        self.cylinder.Radius = v.x
        if v.x > self.max_radius:
            self.max_radius = v.x
        vector_one_turn = vec2(2*pi,self.lead)
        vector_full_turns = vmul(vector_one_turn, nb_turns)
        lineseg = Part.Geom2d.Line2dSegment(sp, vadd(sp,vector_full_turns))
        return lineseg.toShape(self.cylinder)
    def sweep_edge(self, e, extend=False):
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
            c = self.sweep_Point2D(p2d, extend).Curve
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
    def sweep_wire(self, w, solid=False):
        faces = []
        for e in w.Edges:
            faces.append(self.sweep_edge(e,solid))
        shell = Part.Shell(faces)
        shell.sewShape()
        if solid:
            cyl = Part.makeCylinder(self.max_radius*2, self.nb_of_turns*self.lead)
            cyl.Placement = self._placement.multiply(FreeCAD.Placement(FreeCAD.Vector(),FreeCAD.Vector(1,0,0),-90))
            common = cyl.common(shell)
            cut_faces = common.Faces
            new_edges = []
            for e1 in common.Edges:
                found = False
                for e2 in shell.Edges:
                    if nurbs_tools.is_same(e1.Curve, e2.Curve, tol=1e-7, full=False):
                        found = True
                        #print("found similar edges")
                        continue
                if not found:
                    new_edges.append(e1)
            #print(len(Part.sortEdges(new_edges)))
            el1, el2 = Part.sortEdges(new_edges)[0:2]
            f1 = Part.makeFace(Part.Wire(el1),'Part::FaceMakerSimple')
            f2 = Part.makeFace(Part.Wire(el2),'Part::FaceMakerSimple')
            cut_faces.extend([f1,f2])
            try:
                shell = Part.Shell(cut_faces)
                shell.sewShape()
                return Part.Solid(shell)
            except Part.OCCError:
                print("Failed to create solid")
                return Part.Compound(cut_faces)
        return shell



class HelicalSweepFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLink", "Profile", "Profile object")
        obj.addProperty("App::PropertyFloat", "Turns", "Settings", "Number of turns").Turns = 1.0
        obj.addProperty("App::PropertyFloat", "Lead", "Settings", "Thread lead (-1 for auto)").Lead = -1
        obj.addProperty("App::PropertyBool", "Rational", "Settings", "Allow rational bsplines").Rational = False
        obj.addProperty("App::PropertyBool", "Solid", "Settings", "Create a solid shape").Solid = False
        obj.Proxy = self

    def execute(self, obj):
        edges =  obj.Profile.Shape.Edges
        hs = HelicalSweep()
        hs.rational_approx = obj.Rational
        gpl = obj.Profile.getGlobalPlacement()
        hs.set_placement(gpl)
        # 3 priorities to get Lead value
        # 1 : obj.Lead property is >= 0
        # 2 : Sketch has a constraint called "Lead"
        # 3 : the longest of the DistanceY constraints
        if hasattr(obj,"Lead") and obj.Lead >= 0:
            hs.lead = obj.Lead
        else:
            dmin = 0
            for c in obj.Profile.Constraints:
                if c.Name == "Lead":
                    dmin = c.Value
                    continue
                else:
                    if c.Type == "DistanceY":
                        if c.Value > dmin:
                            dmin = c.Value
            hs.lead = dmin
        hs.nb_of_turns = obj.Turns
        obj.Shape = hs.sweep_wire(Part.Wire(edges), obj.Solid)
        
        #faces = [hs.sweep_edge(e, obj.Solid) for e in edges]
        #shell = Part.Shell(faces)
        #shell.sewShape()
        #obj.Shape = shell

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

    def claimChildren(self):
        return [self.Object.Profile]

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

class HelicalSweepCommand:
    """Creates a HelicalSweep Object"""
    def make_profile_sketch(self):
        import Sketcher
        sk = FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','Profile')
        sk.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(0,0,0,1))
        sk.MapMode = "Deactivated"
        sk.addGeometry(Part.LineSegment(FreeCAD.Vector(100.0,0.0,0),FreeCAD.Vector(127.0,12.0,0)),False)
        sk.addConstraint(Sketcher.Constraint('PointOnObject',0,1,-1)) 
        sk.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(125.0,17.0,0),FreeCAD.Vector(0,0,1),5.8),-1.156090,1.050925),False)
        sk.addConstraint(Sketcher.Constraint('Tangent',0,2,1,1)) 
        sk.addGeometry(Part.LineSegment(FreeCAD.Vector(128.0,22.0,0),FreeCAD.Vector(100.0,37.0,0)),False)
        sk.addConstraint(Sketcher.Constraint('Tangent',1,2,2,1)) 
        sk.addConstraint(Sketcher.Constraint('Vertical',0,1,2,2)) 
        sk.addConstraint(Sketcher.Constraint('DistanceY',0,1,2,2,37.5)) 
        sk.setDatum(4,FreeCAD.Units.Quantity('35.000000 mm'))
        sk.renameConstraint(4, u'Lead')
        sk.setDriving(4,False)
        sk.addConstraint(Sketcher.Constraint('Equal',2,0)) 
        FreeCAD.ActiveDocument.recompute()
        return sk

    def makeFeature(self, sel):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Helical Sweep")
        HelicalSweepFP(fp)
        fp.Profile = sel
        HelicalSweepVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            sel.append(self.make_profile_sketch())
        self.makeFeature(sel[0])

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}

FreeCADGui.addCommand('HelicalSweep', HelicalSweepCommand())

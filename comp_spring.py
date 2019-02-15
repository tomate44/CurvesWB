# -*- coding: utf-8 -*-

__title__ = "Compression Spring"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Parametric Compression Spring"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
from FreeCAD import Vector

TOOL_ICON = _utils.iconsPath() + '/icon.svg'
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

class CompSpring(object):
    def __init__(self, length=10, turns=5, wireDiam=0.25, diameter=4.0, samples=16):
        self.epsilon = 1e-2
        self.length = length
        self.turns = turns
        self.wire_diam = wireDiam
        self.diameter = diameter
        self.samples = samples

    def min_length(self):
        return((self.turns+1)*(self.wire_diam + self.epsilon))

    def offset_points(self,pts,start,step,power=1):
        npts = list()
        for i in range(len(pts)):
            v = float(i)/(len(pts)-1)
            if power < 0:
                fac = pow(v,1./abs(power))
            else:
                fac = pow(v,power)
            npts.append(pts[i] + Vector(0,0,start + fac*step))
        return(npts)

    def point_lists(self):
        helix_radius = (self.diameter - self.wire_diam) / 2.0
        if self.length < self.min_length():
            print("Spring too short")
            return()
        free_space = self.length - self.min_length()
        if self.turns <= 2:
            print("Spring must have more than 2 turns")
            return()
        step = free_space / (self.turns - 2)
        circle = Part.Circle(Vector(),Vector(0,0,1),helix_radius)
        pts = circle.discretize(self.samples)
        points = list()
        start = self.wire_diam / 2.0
        pts1 = self.offset_points(pts,start,self.wire_diam+self.epsilon,2)
        points.append(pts1)
        start += self.wire_diam+self.epsilon
        for i in range(self.turns-2):
            pts1 = self.offset_points(pts,start,self.wire_diam+step)
            points.append(pts1)
            start += self.wire_diam+step
        pts1 = self.offset_points(pts,start,self.wire_diam+self.epsilon,-2)
        points.append(pts1)
        return(points)

    def curves(self):
        curves = list()
        pl = self.point_lists()
        for pts in pl:
            bs = Part.BSplineCurve()
            bs.interpolate(pts)
            curves.append(bs)
        return(curves)

    def edges(self):
        edges = list()
        for c in self.curves():
            edges.append(c.toShape())
        return(edges)

    def wire(self, single=True):
        if single:
            return(Part.Wire(self.single_edge()))
        else:
            return(Part.Wire(self.edges()))

    def single_curve(self):
        pl = self.point_lists()
        pts = pl[0][:-1]
        for arr in pl[1:-1]:
            pts += arr[1:-1]
        pts += pl[-1][1:]
        bs = Part.BSplineCurve()
        bs.interpolate(pts)
        return(bs)

    def single_edge(self):
        return(self.single_curve().toShape())

    def shape(self, single=False):
        path = self.wire(single)
        c = Part.Circle(path.Edges[0].valueAt(path.Edges[0].FirstParameter), path.Edges[0].tangentAt(path.Edges[0].FirstParameter), self.wire_diam/2.0)
        pro = Part.Wire([c.toShape()])
        ps = Part.BRepOffsetAPI.MakePipeShell(path)
        ps.setFrenetMode(True)
        #ps.setForceApproxC1(True)
        ps.setTolerance(1e-1, 1e-1, 0.5)
        ps.setMaxDegree(3)
        ps.setMaxSegments(999)
        ps.add(pro)
        if ps.isReady():
            ps.build()
            ps.makeSolid()
            return(ps.shape())
        return(None)
        

class CompSpringFP:
    """Creates a Parametric Compression Spring"""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyFloat", "Length", "CompSpring", "Spring Length").Length = 10.0
        obj.addProperty("App::PropertyInteger", "Turns", "CompSpring", "Number of turns").Turns = 5
        obj.addProperty("App::PropertyFloat", "WireDiameter", "CompSpring", "Diameter of the spring wire").WireDiameter = 0.5
        obj.addProperty("App::PropertyFloat", "Diameter", "CompSpring", "Diameter of the spring").Diameter = 4.0
        obj.addProperty("App::PropertyInteger", "Samples", "Setting", "Number of point samples by turn").Samples = 16
        obj.addProperty("App::PropertyBool", "Smooth", "Setting", "make spring with a single tube surface").Smooth = False
        obj.addProperty("App::PropertyBool", "WireOutput", "Setting", "Output a wire shape").WireOutput=True
        obj.Proxy = self

    def spring(self, obj):
        try:
            return(CompSpring(obj.Length, obj.Turns, obj.WireDiameter, obj.Diameter, obj.Samples))
        except AttributeError:
            return(None)

    def execute(self, obj):
        cs = self.spring(obj)
        if not cs: return()
        if obj.WireOutput:
            obj.Shape = cs.wire(obj.Smooth)
        else:
            obj.Shape = cs.shape(obj.Smooth)

    def onChanged(self, obj, prop):
        if prop in ("Length","Turns","WireDiameter"):
            cs = self.spring(obj)
            if cs:
                if obj.Length < cs.min_length():
                    obj.Length = cs.min_length()

class CompSpringVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class CompSpringCommand:
    """Creates a Parametric Compression Spring"""
    def makeFeature(self):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CompSpring")
        CompSpringFP(fp)
        CompSpringVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        self.makeFeature()

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('comp_spring', CompSpringCommand())

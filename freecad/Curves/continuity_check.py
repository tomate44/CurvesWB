# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH
from freecad.Curves.Blending.smooth_objects import SmoothPoint
from math import pi

TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')
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


from math import pi
vec2 = FreeCAD.Base.Vector2d


def derivativesAt(edge, point):
    par = edge.Curve.parameter(point)
    res = [edge.Curve.getD0(par), ]
    res.extend([edge.Curve.getDN(par, i + 1) for i in range(4)])
    return SmoothPoint(res)



def edge_to_edge_continuity(e1, e2, tol=1e-7):
    dist, pts, info = e1.distToShape(e2)
    sp1 = derivativesAt(e1, pts[0][0])
    sp2 = derivativesAt(e2, pts[0][1])
    return sp1.continuity_with(sp2)


class SeamSampler:
    def __init__(self, edge, faces):
        self.faces = faces
        self.seam = edge
        self.line_size = 1.0

    def lines2d(self, nb):
        lines = []
        line = Part.Geom2d.Line2dSegment(vec2(-self.line_size, 0), vec2(self.line_size, 0))
        for i in range(nb):
            li = line.copy()
            li.rotate(vec2(), (i + 1) * pi / (nb + 1))
            lines.append(li)
        return lines

    def edges2d(self, lines, plane):
        return [li.toShape(plane) for li in lines]

    def projected_lines(self, samples=10, lines=1, tol=1e-7):
        checker = self.lines2d(lines)
        comp = Part.Compound(self.faces)
        proj = []
        for pt in self.seam.discretize(samples):
            n1 = self.faces[0].normalAt(*self.faces[0].Surface.parameter(pt))
            n2 = self.faces[1].normalAt(*self.faces[1].Surface.parameter(pt))
            avn = 0.5 * (n1 + n2)
            t = self.seam.tangentAt(self.seam.Curve.parameter(pt))
            y = avn.cross(t)
            print(y)
            plane = Part.Plane(pt, pt + t, pt + y)
            star = self.edges2d(checker, plane)
            for e in star:
                parproj = comp.makeParallelProjection(e, -avn)
                if len(parproj.Edges) == 2:
                    proj.append(Part.Wire(parproj.Edges))
        return proj



"""
doc1 = FreeCAD.getDocument('blendsurface')
o1 = doc1.getObject('Blend_Surface002')
e1 = o1.Shape.Edge1
f1 = o1.Shape.Face1
o2 = doc1.getObject('MultiLoft_Face102')
f2 = o2.Shape.Face1
ol = (o1,o2,)
fl = (f1,f2,)

ss = SeamSampler(e1, fl)
for edges in ss.continuity(20, 3):
	w = Part.Wire(edges)
	Part.show(w)

"""

class ContinuityCheckerFP:
    """Creates a ..."""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Sources",
                        "Base", "The list of seam edges to check")
        obj.addProperty("App::PropertyInteger", "Samples",
                        "Settings", "Number of test samples on edge")
        obj.addProperty("App::PropertyInteger", "Lines",
                        "Settings", "Number of test lines on each sample")
        obj.addProperty("App::PropertyFloat", "Tolerance",
                        "Settings", "Continuity tolerance")
        obj.Proxy = self

    def execute(self, obj):
        s = obj.Sources[0]
        e = s.getSubObject(obj.Sources[1][0])
        faces = s.Shape.ancestorsOfType(e, Part.Face)
        if len(faces) >= 1:
            ss = SeamSampler(e, faces)
            wires = ss.projected_lines(obj.Samples, obj.Lines, obj.Tolerance)
            obj.Shape = Part.Compound(wires)
        else:
            obj.Shape = Part.Shape()

    def onChanged(self, obj, prop):
        return False


class ContinuityCheckerVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def updateData(self, fp, prop):
        colors = []
        for w in fp.Shape.Wires:
            cont = edge_to_edge_continuity(w.Edge1, w.Edge2, fp.Tolerance)
            colors.extend([self.cont_colors[cont], self.cont_colors[cont]])
        fp.ViewObject.LineColorArray = colors

    def attach(self, viewobj):
        self.Object = viewobj.Object
        self.cont_colors = dict()
        self.cont_colors[-1] = (0.0, 0.0, 0.0, 0.0)
        self.cont_colors[0] = (1.0, 0.0, 0.0, 0.0)
        self.cont_colors[1] = (0.1, 1.0, 0.0, 0.0)
        self.cont_colors[2] = (0.0, 1.0, 0.0, 0.0)
        self.cont_colors[3] = (0.0, 1.0, 1.0, 0.0)
        self.cont_colors[4] = (0.0, 0.0, 1.0, 0.0)

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None


class ContinuityCheckerCommand:
    """Create a ... feature"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Continuity Checker")
        ContinuityCheckerFP(fp)
        ContinuityCheckerVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
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


FreeCADGui.addCommand('Curves_ContinuityCheckerCmd', ContinuityCheckerCommand())

"""
from importlib import reload
from freecad.Curves import continuity_check
reload(continuity_check)
FreeCADGui.runCommand('Curves_ContinuityCheckerCmd')
"""

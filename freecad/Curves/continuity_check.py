# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
import FreeCAD
import FreeCADGui
# import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH
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


class SeamSampler:
    def __init__(self, edge, faces):
        self.faces = faces
        self.seam = edge

    def lines2d(self, nb):
        lines = []
        line = Part.Geom2d.Line2dSegment(vec2(-0.1, 0), vec2(0.1, 0))
        for i in range(nb):
            li = line.copy()
            li.rotate(vec2(), (i + 1) * pi / (nb + 1))
            lines.append(li)
        return lines

    def edges2d(self, lines, plane):
        return [li.toShape(plane) for li in lines]

    def continuity(self, samples=10, lines=1, tol=1e-7):
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
                    proj.append(parproj.Edges)
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
        obj.addProperty("App::PropertyLinkList", "Sources",
                        "Base", "The list of seam edges to check")
        obj.addProperty("App::PropertyInteger", "Samples",
                        "Settings", "Number of test samples on edge")
        obj.addProperty("App::PropertyInteger", "Lines",
                        "Settings", "Number of test lines on each sample")
        obj.addProperty("App::PropertyFloat", "Tolerance",
                        "Settings", "Continuity tolerance")
        obj.Proxy = self

    def execute(self, obj):
        obj.Shape = None

    def onChanged(self, obj, prop):
        return False


class ContinuityCheckerVP:
    def __init__(self, viewobj):
        viewobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, viewobj):
        self.Object = viewobj.Object

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

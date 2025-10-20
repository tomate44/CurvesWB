# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'WaterLine'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Generates waterline curves on selected surfaces'

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'WaterLine.svg')


# Reminder : Available properties
"""
obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "FeaturePython")
for prop in obj.supportedProperties():
    print(prop)

"""


class WaterLineFP:
    """Creates WaterLine sections"""
    def __init__(self, obj, links):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Source", "Source", "The source face or object").Source = links
        obj.addProperty("App::PropertyInteger", "Number", "Settings", "The number of waterlines").Number = 4
        obj.addProperty("App::PropertyVector", "Direction", "Settings", "Axis of the cutting planes").Direction = FreeCAD.Vector(0, 0, 1)
        obj.Proxy = self

    def get_source_shapes(self, obj):
        faces = []
        for link in obj.Source:
            fl = []
            for name in link[1]:
                if "Face" in name:
                    # print("Face found")
                    fl.append(link[0].getSubObject(name))
            if len(fl) == 0:
                # print("adding obj faces")
                fl = link[0].Shape.Faces
            faces.extend(fl)
        return faces

    def params(self, line, comp):
        bb = comp.BoundBox
        pars = []
        for i in range(8):
            pt = bb.getPoint(i)
            pars.append(line.parameter(pt))
        # vl = [Part.Vertex(bb.getPoint(i)) for i in range(8)]
        # vertexes = Part.Compound(vl)
        # plane = Part.Plane(line.value(par), line.Direction)
        # plsh = plane.toShape()
        # dist, pts, info = vertexes.distToShape(plsh)
        # pars = []
        # for pl in pts:
        #     pars.append(line.parameter(pl[0]))
        # pars.sort()
        return pars

    def execute(self, obj):
        faces = self.get_source_shapes(obj)
        print(faces)
        comp = Part.Compound(faces)
        axis = obj.Direction
        line = Part.Line()
        line.Direction = axis
        pars = self.params(line, comp)
        minpar = min(pars)
        maxpar = max(pars)
        # print(minpar, maxpar)
        shapes = []
        for i in range(1, obj.Number + 1):
            par = minpar + i * (maxpar - minpar) / (obj.Number + 1)
            # print(par)
            plane = Part.Plane(line.value(par), axis)
            edges = []
            for f in faces:
                inter = plane.intersectSS(f.Surface)
                for itr in inter:
                    edges.append(itr.toShape())
            shapes.append(Part.Compound(edges))
        compound = Part.Compound(shapes)
        obj.Shape = compound

    def onChanged(self, obj, prop):
        return False


class WaterLineVP:
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


class WaterLineCommand:
    "Create a WaterLine feature"

    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Waterline")
        WaterLineFP(fp, sel)
        WaterLineVP(fp.ViewObject)
        fp.ViewObject.PointSize = 1
        fp.ViewObject.LineWidth = 1
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select a face or an object first !\n")
            return
        links = []
        for so in sel:
            if so.HasSubObjects:
                links.append((so.Object, so.SubElementNames))
            else:
                links.append((so.Object, ["", ]))
        print(links)
        self.makeFeature(links)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Curves_WaterlineCurves', WaterLineCommand())

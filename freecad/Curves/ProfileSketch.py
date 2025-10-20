# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Profile support plane'
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = 'Creates a support plane for sketches'

import os
import FreeCAD
import FreeCADGui
import Part
from . import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'profileSupport.svg')
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class profileSupportFP:
    "creates a profile sketch"
    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSub", "Edge1", "Profile", "First support edge")
        obj.addProperty("App::PropertyLinkSub", "Edge2", "Profile", "Second support edge")
        obj.addProperty("App::PropertyFloat", "Parameter1", "Profile", "Parameter on first edge")
        obj.addProperty("App::PropertyFloat", "Parameter2", "Profile", "Parameter on second edge")
        obj.addProperty("App::PropertyVector", "MainAxis", "Profile", "Main axis of the sketch")
        obj.Proxy = self

    def getEdges(self, obj):
        res = []
        try:
            if hasattr(obj, "Edge1"):
                n = eval(obj.Edge1[1][0].lstrip('Edge'))
                res.append(obj.Edge1[0].Shape.Edges[n - 1])
            if hasattr(obj, "Edge2"):
                n = eval(obj.Edge2[1][0].lstrip('Edge'))
                res.append(obj.Edge2[0].Shape.Edges[n - 1])
            return(res)
        except TypeError:
            return [None, None]

    def execute(self, obj):
        e1, e2 = self.getEdges(obj)
        if (not e1) or (not e2):
            return()
        if hasattr(obj, "Parameter1") and hasattr(obj, "Parameter2") and hasattr(obj, "MainAxis"):
            l1 = Part.LineSegment(e1.valueAt(obj.Parameter1), e2.valueAt(obj.Parameter2))
            v = FreeCAD.Vector(obj.MainAxis)
            if v.Length < 1e-6:
                v = FreeCAD.Vector(0, 0, 1)
            direction = v.normalize().multiply(l1.length())
            obj.Shape = l1.toShape().extrude(direction)
        return()

    def onChanged(self, fp, prop):
        e1, e2 = self.getEdges(fp)
        if prop == "Parameter1":
            if fp.Parameter1 < e1.FirstParameter:
                fp.Parameter1 = e1.FirstParameter
            elif fp.Parameter1 > e1.LastParameter:
                fp.Parameter1 = e1.LastParameter
        elif prop == "Parameter2":
            if fp.Parameter2 < e2.FirstParameter:
                fp.Parameter2 = e2.FirstParameter
            elif fp.Parameter2 > e2.LastParameter:
                fp.Parameter2 = e2.LastParameter
        elif prop in ["Edge1", "Edge2", "MainAxis"]:
            self.execute(fp)


class profileSupportVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return None

        def loads(self, state):
            return None

    else:
        def __getstate__(self):
            return None

        def __setstate__(self, state):
            return None

    # def claimChildren(self):
        # return None #[self.Object.Base, self.Object.Tool]

    def onDelete(self, feature, subelements):  # subelements is a tuple of strings
        return True


class profSupCommand:
    "creates a profile sketch support"
    def makeProfileFeature(self, shapes, params):
        prof = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', 'Profile')
        profileSupportFP(prof)
        profileSupportVP(prof.ViewObject)
        if isinstance(shapes, list):
            prof.Edge1 = shapes[0]
            prof.Edge2 = shapes[1]
            prof.Parameter1 = params[0]
            prof.Parameter2 = params[1]
            prof.MainAxis = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        FreeCAD.ActiveDocument.recompute()
        prof.ViewObject.LineWidth = 2.0
        prof.ViewObject.LineColor = (0.5, 0.0, 0.5)

    def Activated(self):
        shapes = []
        params = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select 2 edges or vertexes first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        shapes.append((selobj.Object, selobj.SubElementNames[i]))
                        p = selobj.PickedPoints[i]
                        poe = selobj.SubObjects[i].distToShape(Part.Vertex(p))
                        par = poe[2][0][2]
                        params.append(par)
                    elif isinstance(selobj.SubObjects[i], Part.Vertex):
                        shapes.append((selobj.Object, selobj.SubElementNames[i]))
                        # p = selobj.PickedPoints[i]
                        # poe = so.distToShape(Part.Vertex(p))
                        # par = poe[2][0][2]
                        params.append(0)
            else:
                FreeCAD.Console.PrintError("Select 2 edges or vertexes first !\n")
        if shapes:
            self.makeProfileFeature(shapes, params)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('profileSupportCmd', profSupCommand())

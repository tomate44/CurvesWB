# -*- coding: utf-8 -*-

__title__ = 'Title'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Doc'

import os
from importlib import reload
import FreeCAD
import FreeCADGui
# import Part
from freecad.Curves import ProfileMatcher
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'icon.svg')


# Reminder : Available properties
"""
obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "FeaturePython")
for prop in obj.supportedProperties():
    print(prop)

"""


class ProfileMatcherAppProxy:
    """Creates a ..."""
    def __init__(self, obj, links=[]):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Profiles", "Profiles",
                        "Input shapes").Profiles = links
        obj.addProperty("App::PropertyFloat", "VertexTolerance", "Settings",
                        "Tolerance to find vertex match. as percent of the profiles length")
        obj.addProperty("App::PropertyBool", "RemoveC1Vertexes", "Settings",
                        "Allow to remove C1 continuous vertexes that have no match with other vertexes")
        obj.addProperty("App::PropertyFloat", "AngularTolerance", "Settings",
                        "Angular tolerance to find C1 continuous vertexes, in degrees")
        obj.VertexTolerance = 0.1
        obj.RemoveC1Vertexes = True
        obj.AngularTolerance = 0.1
        obj.Proxy = self

    def execute(self, obj):
        shapes = []
        for source, subnames in obj.Profiles:
            if subnames:
                for name in subnames:
                    shapes.append(source.getSubObject(name))
            else:
                shapes.append(source.Shape)
        reload(ProfileMatcher)
        pm = ProfileMatcher.ProfileMatcher(shapes, obj.VertexTolerance, obj.RemoveC1Vertexes, obj.AngularTolerance)
        obj.Shape = pm.Shape

    def onChanged(self, obj, prop):
        return False


class ProfileMatcherGuiProxy:
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


class ProfileMatcherCommand:
    """Create a ... feature"""
    def makeFeature(self, sel=None):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "ProfileMatcher")
        ProfileMatcherAppProxy(fp, sel)
        ProfileMatcherGuiProxy(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        selobj = FreeCADGui.Selection.getSelectionEx()
        if selobj == []:
            FreeCAD.Console.PrintError("Select at least 2 profiles !\n")
        else:
            links = []
            for sel in selobj:
                if sel.SubElementNames:
                    links.append([sel.Object, sel.SubElementNames])
                else:
                    links.append(sel.Object)
            # print(links)
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


FreeCADGui.addCommand('Curves_ProfileMatcher', ProfileMatcherCommand())

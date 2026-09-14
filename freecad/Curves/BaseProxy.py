# SPDX-License-Identifier: LGPL-2.1-or-later


import FreeCAD
from freecad.Curves import WB_NAME, WB_URL, WB_WIKI_URL


class BaseFPOProxy:
    def __init__(self, obj):
        obj.addProperty("App::PropertyString", "Name", "Workbench", "Name of the workbench that provides this feature")
        obj.addProperty("App::PropertyString", "Website", "Workbench", "URL of the workbench that provides this feature")
        obj.addProperty("App::PropertyString", "Wiki", "Workbench", "URL of the documentation of this workbench")
        obj.Name = WB_NAME
        obj.Website = WB_URL
        obj.Wiki = WB_WIKI_URL
        obj.setEditorMode("Name", 1)
        obj.setEditorMode("Website", 1)
        obj.setEditorMode("Wiki", 1)


class BaseFPOViewProxy:
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

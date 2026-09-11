# SPDX-License-Identifier: LGPL-2.1-or-later


from freecad.Curves import WB_NAME, WB_WIKI_URL


class BaseFPOProxy:
    def __init__(self, obj):
        obj.addProperty("App::PropertyString", "WorkbenchName", "Workbench", "Origin workbench of this tool")
        obj.addProperty("App::PropertyString", "WikiURL", "Workbench", "Tool documentation URL")
        obj.WorkbenchName = WB_NAME
        obj.WikiURL = WB_WIKI_URL
        obj.setEditorMode("WorkbenchName", 1)
        obj.setEditorMode("WikiURL", 1)


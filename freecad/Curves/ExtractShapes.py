# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Extract subshape"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Make a non-parametric copy of selected subshapes.
Same as Part_ElementCopy"""

import os
import FreeCAD
import FreeCADGui
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'extract.svg')


class extract:
    """Make a non-parametric copy of selected subshapes."""
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        for o in s:
            sh = o.Object.Shape.copy()
            if hasattr(o.Object, "getGlobalPlacement"):
                gpl = o.Object.getGlobalPlacement()
                sh.Placement = gpl
            for name in o.SubElementNames:
                fullname = "{}_{}".format(o.ObjectName, name)
                newobj = o.Document.addObject("Part::Feature", fullname)
                newobj.Shape = sh.getElement(name)
            o.Object.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}\n\n{}".format(__title__, __doc__)}


FreeCADGui.addCommand('extract', extract())

# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Paste SVG"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Paste the SVG content of the clipboard"
__usage__ = """When working in parallel with FreeCAD and a SVG editor (Inkscape),
copy (CTRL-C) an object in the SVG editor, switch to FreeCAD and activate tool.
This will import the SVG content of the clipboard into the active FreeCAD document."""

import xml.sax
import importSVG
import os
import FreeCAD
import FreeCADGui
from PySide import QtGui
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'svg_rv3.svg')


class pasteSVG:
    def Activated(self):
        cb = QtGui.QApplication.clipboard()
        t = cb.text()

        if t[0:5] == '<?xml':
            h = importSVG.svgHandler()
            doc = FreeCAD.ActiveDocument
            if not doc:
                doc = FreeCAD.newDocument("SvgImport")
            h.doc = doc
            xml.sax.parseString(t, h)
            doc.recompute()
            FreeCADGui.SendMsgToActiveView("ViewFit")
        else:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))

    def IsActive(self):
        cb = QtGui.QApplication.clipboard()
        cb_content = cb.text()
        if cb_content[0:5] == '<?xml':
            return True

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('pasteSVG', pasteSVG())

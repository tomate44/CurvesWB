# -*- coding: utf-8 -*-

import FreeCAD

translate = FreeCAD.Qt.translate
QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP

__title__ = QT_TRANSLATE_NOOP("Curves_PasteSVG", "Paste SVG")
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = translate("Curves_PasteSVG", "Paste the SVG content of the clipboard")
__usage__ = translate(
    "Curves_PasteSVG",
    """When working in parallel with FreeCAD and a SVG editor (Inkscape),
copy (CTRL-C) an object in the SVG editor, switch to FreeCAD and activate tool.
This will import the SVG content of the clipboard into the active FreeCAD document.""",
)

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
            FreeCAD.Console.PrintError(translate("Log", "{} :\n{}\n")).format(__title__, __usage__)

    def IsActive(self):
        cb = QtGui.QApplication.clipboard()
        cb_content = cb.text()
        if cb_content[0:5] == '<?xml':
            return True

    def GetResources(self):
        return {
            "Pixmap": TOOL_ICON,
            "MenuText": __title__,
            "ToolTip": "{}<br><br><b>{} :</b><br>{}".format(
                __doc__, translate("Curves_PasteSVG", "Usage"), "<br>".join(__usage__.splitlines())
            ),
        }


FreeCADGui.addCommand("Curves_PasteSVG", pasteSVG())

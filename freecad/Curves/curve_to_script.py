# -*- coding: utf-8 -*-

__title__ = "BSpline to script"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates a python script to build the selected BSpline curves."
__usage__ = """Select some Bezier or BSpline curves in the 3D View and activate the tool.
The selected curves will be re-created with commands in the python console."""

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'curve_to_console.svg')


def curve_to_script(i, c):
    com = ["import FreeCAD",
           "from FreeCAD import Vector",
           "import Part", ""]
    if isinstance(c, Part.BSplineCurve):
        com.append("poles{} = {}".format(i, c.getPoles()))
        com.append("weights{} = {}".format(i, c.getWeights()))
        com.append("knots{} = {}".format(i, c.getKnots()))
        com.append("mults{} = {}".format(i, c.getMultiplicities()))
        com.append("periodic{} = {}".format(i, c.isPeriodic()))
        com.append("degree{} = {}".format(i, c.Degree))
        com.append("rational{} = {}".format(i, c.isRational()))
        com.append("bs{} = Part.BSplineCurve()".format(i))
        com.append("bs{}.buildFromPolesMultsKnots(poles{}, mults{}, knots{}, periodic{}, degree{}, weights{}, rational{})".format(i, i, i, i, i, i, i, i))
        com.append('obj{} = FreeCAD.ActiveDocument.addObject("Part::Spline","BSplineCurve{}")'.format(i, i))
        com.append("obj{}.Shape = bs{}.toShape()".format(i, i))
    elif isinstance(c, Part.BezierCurve):
        com.append("poles{} = {}".format(i, c.getPoles()))
        com.append("be{} = Part.BezierCurve()".formati)
        com.append("be{}.increase({})".format(i, c.Degree))
        com.append("be{}.setPoles(poles{})".format(i, i))
        if c.isRational():
            w = c.getWeights()
            for j in range(len(w)):
                com.append("be{}.setWeight({},{})".format(i, j + 1, w[j]))
        com.append('obj{} = FreeCAD.ActiveDocument.addObject("Part::Spline","BezierCurve{}")'.format(i, i))
        com.append("obj{}.Shape = be{}.toShape()".format(i, i))
    com.append("")

    for s in com:
        FreeCADGui.doCommand(s)


class NurbsToConsole:
    "Brings the selected BSpline curves to the python console"
    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': "BSpline to Console",
                'Accel': "",
                'ToolTip': "{}\n{}".format(__doc__, __usage__)}

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        i = 0
        for so in s:
            for sso in so.SubObjects:
                if hasattr(sso, "Curve"):
                    c = sso.Curve
                    curve_to_script(i, c)
                    i += 1
        if i == 0:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False


FreeCADGui.addCommand('Curves_bspline_to_console', NurbsToConsole())

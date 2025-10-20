# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Macro IsoCurves"
__author__ = "Chris_G"
__doc__ = '''
Macro IsoCurves.
Creates a parametric isoCurve from a face

Instructions:
Select a face in the 3D View.
Then, in Py console:

import IsoCurves
IsoCurves.run()

'''

import os
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
# import Part
from freecad.Curves import isocurves
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'isocurve.svg')

# debug = _utils.debug
debug = _utils.doNothing


def makeIsoCurveFeature():
    '''makeIsoCurveFeature(): makes a IsoCurve parametric feature object. Returns the new object.'''
    selfobj = App.ActiveDocument.addObject("Part::FeaturePython", "IsoCurve")
    IsoCurve(selfobj)
    ViewProviderIsoCurve(selfobj.ViewObject)
    return selfobj


class IsoCurve:
    "The IsoCurve feature object"

    def __init__(self, selfobj):
        selfobj.addProperty("App::PropertyLinkSub", "Face", "IsoCurve", "Input face")
        selfobj.addProperty("App::PropertyFloat", "Parameter", "IsoCurve", "IsoCurve parameter").Parameter = 0.
        selfobj.addProperty("App::PropertyInteger", "NumberU", "IsoCurve", "Number of IsoCurve in U direction").NumberU = 5
        selfobj.addProperty("App::PropertyInteger", "NumberV", "IsoCurve", "Number of IsoCurve in V direction").NumberV = 5
        selfobj.addProperty("App::PropertyEnumeration", "Mode", "IsoCurve", "Number of IsoCurve").Mode = ["Single", "Multi"]
        selfobj.addProperty("App::PropertyEnumeration", "Orientation", "IsoCurve", "Curve Orientation").Orientation = ["U", "V"]
        selfobj.Mode = "Multi"
        selfobj.setEditorMode("Parameter", 2)
        selfobj.setEditorMode("Orientation", 2)
        selfobj.setEditorMode("NumberU", 0)
        selfobj.setEditorMode("NumberV", 0)
        selfobj.Proxy = self

    def split(self, e, t0, t1):
        p0, p1 = e.ParameterRange
        if (t0 > p0) & (t1 < p1):
            w = e.split([t0, t1])
            return w.Edges[1]
        elif (t0 > p0):
            w = e.split(t0)
            return w.Edges[1]
        elif (t1 < p1):
            w = e.split(t1)
            return w.Edges[0]
        else:
            return e

    def getBounds(self, obj):
        face = self.getFace(obj)
        self.u0, self.u1, self.v0, self.v1 = face.ParameterRange

    def getFace(self, obj):
        if hasattr(obj, "Face"):
            return _utils.getShape(obj, "Face", "Face")

    def tangentAt(self, selfobj, p):
        if selfobj.Orientation == 'U':
            if (p >= self.v0) & (p <= self.v1):
                return selfobj.Shape.tangentAt(p)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n" % (self.v0, self.v1))
        if selfobj.Orientation == 'V':
            if (p >= self.u0) & (p <= self.u1):
                return selfobj.Shape.tangentAt(p)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n" % (self.u0, self.u1))

    def normalAt(self, selfobj, p):
        face = self.getFace(selfobj)
        if selfobj.Orientation == 'U':
            if (p >= self.v0) & (p <= self.v1):
                return face.normalAt(selfobj.Parameter, p)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n" % (self.v0, self.v1))
        if selfobj.Orientation == 'V':
            if (p >= self.u0) & (p <= self.u1):
                return face.normalAt(p, selfobj.Parameter)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n" % (self.u0, self.u1))

    def execute(self, selfobj):
        face = self.getFace(selfobj)
        # u0,u1,v0,v1 = face.ParameterRange
        if face:
            if selfobj.Mode == 'Multi':
                w = isocurves.multiIso(face, selfobj.NumberU, selfobj.NumberV).toShape()
            else:
                if selfobj.Orientation == 'U':
                    ci = isocurves.multiIso(face, 1, 0)
                    ci.paramu = [selfobj.Parameter]
                    ci.computeU()
                else:
                    ci = isocurves.multiIso(face, 0, 1)
                    ci.paramv = [selfobj.Parameter]
                    ci.computeV()
                w = ci.toShape()
            selfobj.Shape = w
            selfobj.Placement = face.Placement

    def onChanged(self, selfobj, prop):
        if prop == 'Face':
            face = self.getFace(selfobj)
            if not face:
                return
            self.getBounds(selfobj)
            if selfobj.Orientation == "U":
                self.p0 = self.u0
                self.p1 = self.u1
            else:
                self.p0 = self.v0
                self.p1 = self.v1
        if prop == 'Mode':
            if selfobj.Mode == "Single":
                selfobj.setEditorMode("Parameter", 0)
                selfobj.setEditorMode("Orientation", 0)
                selfobj.setEditorMode("NumberU", 2)
                selfobj.setEditorMode("NumberV", 2)
            elif selfobj.Mode == "Multi":
                selfobj.setEditorMode("Parameter", 2)
                selfobj.setEditorMode("Orientation", 2)
                selfobj.setEditorMode("NumberU", 0)
                selfobj.setEditorMode("NumberV", 0)
            self.execute(selfobj)
        if prop == 'Parameter':
            if selfobj.Parameter < self.p0:
                selfobj.Parameter = self.p0
            elif selfobj.Parameter > self.p1:
                selfobj.Parameter = self.p1
            self.execute(selfobj)
        if prop == 'NumberU':
            if selfobj.NumberU < 0:
                selfobj.NumberU = 0
            elif selfobj.NumberU > 1000:
                selfobj.NumberU = 1000
            self.execute(selfobj)
        if prop == 'NumberV':
            if selfobj.NumberV < 0:
                selfobj.NumberV = 0
            elif selfobj.NumberV > 1000:
                selfobj.NumberV = 1000
            self.execute(selfobj)
        if prop == 'Orientation':
            self.getBounds(selfobj)
            if selfobj.Orientation == "U":
                self.p0 = self.u0
                self.p1 = self.u1
            else:
                self.p0 = self.v0
                self.p1 = self.v1
            self.execute(selfobj)


class ViewProviderIsoCurve:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    if App.Version()[0] == '0' and '.'.join(App.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = App.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = App.ActiveDocument.getObject(state["name"])
            return None


class CommandMacroIsoCurve:
    "Command to create IsoCurve feature"

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': "IsoCurve",
                'Accel': "",
                'ToolTip': "IsoCurve: Create an IsoCurve from a face"}

    def Activated(self):
        run()

    def IsActive(self):
        if App.ActiveDocument:
            # sel = Gui.Selection.getSelectionEx()
            f = Gui.Selection.Filter("SELECT Part::Feature SUBELEMENT Face COUNT 1..1000")
            return f.match()
        else:
            return False


if App.GuiUp:
    Gui.addCommand("IsoCurve", CommandMacroIsoCurve())


def run():
    f = Gui.Selection.Filter("SELECT Part::Feature SUBELEMENT Face COUNT 1..1000")
    try:
        if not f.match():
            raise Exception("Select at least one face.")
        try:
            App.ActiveDocument.openTransaction("Macro IsoCurve")
            r = f.result()
            for e in r:
                for s in e:
                    for f in s.SubElementNames:
                        # App.ActiveDocument.openTransaction("Macro IsoCurve")
                        selfobj = makeIsoCurveFeature()
                        # so = sel[0].SubObjects[0]
                        # p = sel[0].PickedPoints[0]
                        # poe = so.distToShape(Part.Vertex(p))
                        # par = poe[2][0][2]
                        # selfobj.Face = [sel[0].Object,sel[0].SubElementNames]
                        selfobj.Face = [s.Object, f]
                        # selfobj.Parameter = par[0]
                        selfobj.Proxy.execute(selfobj)
        finally:
            App.ActiveDocument.commitTransaction()
    except Exception as err:
        from PySide import QtGui
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText("{0}".format(err))
        mb.setWindowTitle("Macro IsoCurve")
        mb.exec_()

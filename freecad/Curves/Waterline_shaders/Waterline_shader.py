# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
from os import path


class WaterlineAnalysisShader:

    def __init__(self):
        shaderpath = path.dirname(path.abspath(__file__))
        self.vertexShader = coin.SoVertexShader()
        self.vertexShader.sourceProgram.setValue(path.join(shaderpath, 'Waterline_Vertex_Shader.glsl'))

        self.fragmentShader = coin.SoFragmentShader()
        self.fragmentShader.sourceProgram.setValue(path.join(shaderpath, 'Waterline_Fragment_Shader.glsl'))

        self.axis_direction = coin.SoShaderParameter3f()
        self.axis_direction.name = "axis_direction"

        self.origin = coin.SoShaderParameter3f()
        self.origin.name = "origin"

        self.main_unit = coin.SoShaderParameter1f()
        self.main_unit.name = "main_unit"

        self.nb_subunits = coin.SoShaderParameter1i()
        self.nb_subunits.name = "nb_subunits"

        self.tolerance = coin.SoShaderParameter1f()
        self.tolerance.name = "tolerance"

        self.unit_color = coin.SoShaderParameter3f()
        self.unit_color.name = "unit_color"

        self.subunit_color = coin.SoShaderParameter3f()
        self.subunit_color.name = "subunit_color"

        self.AxisDirection = (0, 0, 1)
        self.Origin = (0, 0, 0)
        self.MainUnit = 10.0
        self.NbSubUnits = 10
        self.Tolerance = 1e-2
        self.UnitColor = (1, 0, 0)
        self.SubUnitColor = (0.5, 0.5, 0.5)

        params = [self.axis_direction,
                  self.origin,
                  self.main_unit,
                  self.nb_subunits,
                  self.tolerance,
                  self.unit_color,
                  self.subunit_color]
        self.fragmentShader.parameter.setValues(0, len(params), params)

        self.shaderProgram = coin.SoShaderProgram()
        self.shaderProgram.shaderObject.set1Value(0, self.vertexShader)
        self.shaderProgram.shaderObject.set1Value(1, self.fragmentShader)

    @property
    def AxisDirection(self):
        return self.axis_direction.value.getValue().getValue()

    @AxisDirection.setter
    def AxisDirection(self, v):
        self.axis_direction.value = v

    @property
    def Origin(self):
        return self.origin.value.getValue().getValue()

    @Origin.setter
    def Origin(self, v):
        self.origin.value = v

    @property
    def MainUnit(self):
        return self.main_unit.value.getValue()

    @MainUnit.setter
    def MainUnit(self, v):
        self.main_unit.value = v

    @property
    def NbSubUnits(self):
        return self.nb_subunits.value.getValue()

    @NbSubUnits.setter
    def NbSubUnits(self, v):
        self.nb_subunits.value = v

    @property
    def Tolerance(self):
        return self.tolerance.value.getValue()

    @Tolerance.setter
    def Tolerance(self, v):
        self.tolerance.value = v

    @property
    def UnitColor(self):
        return self.unit_color.value.getValue().getValue()

    @UnitColor.setter
    def UnitColor(self, v):
        self.unit_color.value = v

    @property
    def SubUnitColor(self):
        return self.subunit_color.value.getValue().getValue()

    @SubUnitColor.setter
    def SubUnitColor(self, v):
        self.subunit_color.value = v

    @property
    def Shader(self):
        return self.shaderProgram


#
#doc = App.newDocument()
#doc.addObject("Part::Ellipsoid", "Ellipsoid")
#doc.addObject("Part::Torus", "Torus")
#doc.recompute()
"""
from importlib import reload
from freecad.Curves.Waterline_shaders import Waterline_shader
reload(Waterline_shader)

view = Gui.ActiveDocument.ActiveView
view.viewIsometric()
Gui.SendMsgToActiveView("ViewFit")

root = view.getViewer().getSceneGraph()
shader = Waterline_shader.WaterlineAnalysisShader()
#shader.UnitColor = (1, 0, 0)
#shader.MainUnit = 20.0
root.insertChild(shader.Shader, 0)


"""

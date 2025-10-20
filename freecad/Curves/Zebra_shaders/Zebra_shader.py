# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
from os import path


class SurfaceAnalysisShader:

    def __init__(self, mode=0, fixed_light=0):
        shaderpath = path.dirname(path.abspath(__file__))
        self.vertexShader = coin.SoVertexShader()
        self.vertexShader.sourceProgram.setValue(path.join(shaderpath,'Zebra_Vertex_Shader.glsl'))  # phong_vshader

        self.fragmentShader = coin.SoFragmentShader()
        self.fragmentShader.sourceProgram.setValue(path.join(shaderpath,'Zebra_Fragment_Shader.glsl'))  # phong_fshader

        self.analysis_direction = coin.SoShaderParameter3f()
        self.analysis_direction.name = "analysis_direction"

        self.fixed_light = coin.SoShaderParameter1i()
        self.fixed_light.name = "fixed_light"

        self.mode = coin.SoShaderParameter1i()
        self.mode.name = "mode"

        self.stripes_color_1 = coin.SoShaderParameter3f()
        self.stripes_color_1.name = "stripes_color_1"

        self.stripes_color_2 = coin.SoShaderParameter3f()
        self.stripes_color_2.name = "stripes_color_2"

        self.stripes_number = coin.SoShaderParameter1i()
        self.stripes_number.name = "stripes_number"

        self.stripes_ratio = coin.SoShaderParameter1f()
        self.stripes_ratio.name = "stripes_ratio"

        self.rainbow_angle_1 = coin.SoShaderParameter1f()
        self.rainbow_angle_1.name = "rainbow_angle_1"

        self.rainbow_angle_2 = coin.SoShaderParameter1f()
        self.rainbow_angle_2.name = "rainbow_angle_2"

        self.curves_angles = coin.SoShaderParameterArray1f()
        self.curves_angles.name = "curves_angles"

        self.curves_tolerance = coin.SoShaderParameter1f()
        self.curves_tolerance.name = "curves_tolerance"

        self.shading = coin.SoShaderParameter1f()
        self.shading.name = "shading"

        self.AnalysisDirection = (1, 0, 0)
        self.Fixed = fixed_light
        self.Mode = mode
        self.Color1 = (1, 1, 1)
        self.Color2 = (0, 0, 0)
        self.StripesNumber = 12
        self.StripesRatio = 0.5
        self.RainbowAngle1 = 0.0
        self.RainbowAngle2 = 180.0
        self.CurvesAngles = [45.0, 90.0, 135.0]
        self.CurvesTolerance = 0.5
        self.Shading = 0.2

        params = [self.analysis_direction,
                  self.fixed_light,
                  self.mode,
                  self.stripes_color_1,
                  self.stripes_color_2,
                  self.stripes_number,
                  self.stripes_ratio,
                  self.rainbow_angle_1,
                  self.rainbow_angle_2,
                  self.curves_angles,
                  self.curves_tolerance,
                  self.shading]
        self.fragmentShader.parameter.setValues(0, len(params), params)

        self.shaderProgram = coin.SoShaderProgram()
        self.shaderProgram.shaderObject.set1Value(0, self.vertexShader)
        self.shaderProgram.shaderObject.set1Value(1, self.fragmentShader)

    @property
    def AnalysisDirection(self):
        return self.analysis_direction.value.getValue().getValue()

    @AnalysisDirection.setter
    def AnalysisDirection(self, v):
        self.analysis_direction.value = v

    @property
    def Fixed(self):
        return self.fixed_light.value.getValue()

    @Fixed.setter
    def Fixed(self, v):
        self.fixed_light.value = v

    @property
    def Mode(self):
        return self.mode.value.getValue()

    @Mode.setter
    def Mode(self, v):
        self.mode.value = v

    @property
    def Color1(self):
        return self.stripes_color_1.value.getValue().getValue()

    @Color1.setter
    def Color1(self, v):
        self.stripes_color_1.value = v

    @property
    def Color2(self):
        return self.stripes_color_2.value.getValue().getValue()

    @Color2.setter
    def Color2(self, v):
        self.stripes_color_2.value = v

    @property
    def StripesNumber(self):
        return self.stripes_number.value.getValue()

    @StripesNumber.setter
    def StripesNumber(self, v):
        self.stripes_number.value = v

    @property
    def StripesRatio(self):
        return self.stripes_ratio.value.getValue()

    @StripesRatio.setter
    def StripesRatio(self, v):
        self.stripes_ratio.value = v

    @property
    def RainbowAngle1(self):
        return self.rainbow_angle_1.value.getValue()

    @RainbowAngle1.setter
    def RainbowAngle1(self, v):
        self.rainbow_angle_1.value = v

    @property
    def RainbowAngle2(self):
        return self.rainbow_angle_2.value.getValue()

    @RainbowAngle2.setter
    def RainbowAngle2(self, v):
        self.rainbow_angle_2.value = v

    @property
    def CurvesAngles(self):
        val = []
        for v in self.curves_angles.value.getValues():
            if v >= 0:
                val.append(v)
        return val

    @CurvesAngles.setter
    def CurvesAngles(self, v):
        if len(v) < 20:
            comp = [-1] * (20 - len(v))
            v += comp
        self.curves_angles.value.setValues(0, 20, v[:20])

    @property
    def CurvesTolerance(self):
        return self.curves_tolerance.value.getValue()

    @CurvesTolerance.setter
    def CurvesTolerance(self, v):
        self.curves_tolerance.value = v

    @property
    def Shading(self):
        return self.shading.value.getValue()

    @Shading.setter
    def Shading(self, v):
        self.shading.value = v

    @property
    def Shader(self):
        return self.shaderProgram


"""
doc = App.newDocument()
doc.addObject("Part::Ellipsoid", "Ellipsoid")
doc.addObject("Part::Torus", "Torus")
doc.recompute()

view = Gui.ActiveDocument.ActiveView
view.viewIsometric()
Gui.SendMsgToActiveView("ViewFit")

root = view.getViewer().getSceneGraph()
shader = SurfaceAnalysisShader(0, 1)
root.insertChild(shader.Shader, 0)
"""



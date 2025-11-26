# SPDX-License-Identifier: LGPL-2.1-or-later

from pivy import coin
from os import path


class DraftAnalysisShader:
    """
    Draft analysis shader interface.
    Example:
    root = FreeCAD.ActiveDocument.ActiveObject.ViewObject.RootNode
    shader = SurfaceAnalysisShader()
    root.insertChild(shader.Shader, 0)
    """

    def __init__(self):
        self._angles = [1.0, 1.0, 0.05, 0.05]
        self._colors = [(0, 0, 1), (0, 1, 1), (1, 0, 0),
                        (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        shaderpath = path.dirname(path.abspath(__file__))
        self.vertexShader = coin.SoVertexShader()
        self.vertexShader.sourceProgram.setValue(path.join(shaderpath, 'DA_Vert_Shader.glsl'))

        self.fragmentShader = coin.SoFragmentShader()
        self.fragmentShader.sourceProgram.setValue(path.join(shaderpath, 'DA_Frag_Shader.glsl'))

        self.shaderProgram = coin.SoShaderProgram()
        self.shaderProgram.shaderObject.set1Value(0, self.vertexShader)
        self.shaderProgram.shaderObject.set1Value(1, self.fragmentShader)

        self.analysis_direction = coin.SoShaderParameter3f()
        self.analysis_direction.name = "analysis_direction"

        self.angles = coin.SoShaderParameterArray1f()
        self.angles.name = "angles"

        self.colors = coin.SoShaderParameterArray3f()
        self.colors.name = "colors"

        self.shading = coin.SoShaderParameter1f()
        self.shading.name = "shading"

        self.Direction = (0, 0, 1)
        self.Shading = 0.2
        self.set_angles()
        self.set_colors()

        params = [self.analysis_direction,
                  self.angles,
                  self.colors,
                  self.shading]
        self.fragmentShader.parameter.setValues(0, len(params), params)

        self.shaderProgram = coin.SoShaderProgram()
        self.shaderProgram.shaderObject.set1Value(0, self.vertexShader)
        self.shaderProgram.shaderObject.set1Value(1, self.fragmentShader)

    @property
    def Direction(self):
        "Draft analysis direction"
        return self.analysis_direction.value.getValue().getValue()

    @Direction.setter
    def Direction(self, v):
        self.analysis_direction.value = v

    def set_angles(self):
        angle_list = [0.0,
                      90.0 - self._angles[0] - self._angles[2],
                      90.0 - self._angles[0],
                      90.0,
                      90.0 + self._angles[1],
                      90.0 + self._angles[1] + self._angles[3],
                      180.0]
        self.angles.value.setValues(0, len(angle_list), angle_list)

    @property
    def DraftAnglePos(self):
        "Positive draft angle (0->90 degrees)"
        return self._angles[0]

    @DraftAnglePos.setter
    def DraftAnglePos(self, v):
        self._angles[0] = v
        self.set_angles()

    @property
    def DraftAngleNeg(self):
        "Negative draft angle (0->90 degrees)"
        return self._angles[1]

    @DraftAngleNeg.setter
    def DraftAngleNeg(self, v):
        self._angles[1] = v
        self.set_angles()

    @property
    def DraftTolPos(self):
        "Positive draft angle tolerance (0->90 degrees)"
        return self._angles[2]

    @DraftTolPos.setter
    def DraftTolPos(self, v):
        self._angles[2] = v
        self.set_angles()

    @property
    def DraftTolNeg(self):
        "Negative draft angle tolerance (0->90 degrees)"
        return self._angles[3]

    @DraftTolNeg.setter
    def DraftTolNeg(self, v):
        self._angles[3] = v
        self.set_angles()

    def set_colors(self):
        color_list = [self._colors[0]] + self._colors + [self._colors[-1]]
        self.colors.value.setValues(0, len(color_list), color_list)

    @property
    def ColorInDraftPos(self):
        "Color of the positive In-Draft area (normalized (r, g, b))"
        return self._colors[0]

    @ColorInDraftPos.setter
    def ColorInDraftPos(self, v):
        self._colors[0] = v
        self.set_colors()

    @property
    def ColorInDraftNeg(self):
        "Color of the negative In-Draft area (normalized (r, g, b))"
        return self._colors[5]

    @ColorInDraftNeg.setter
    def ColorInDraftNeg(self, v):
        self._colors[5] = v
        self.set_colors()

    @property
    def ColorOutOfDraftPos(self):
        "Color of the positive Out-of-Draft area (normalized (r, g, b))"
        return self._colors[2]

    @ColorOutOfDraftPos.setter
    def ColorOutOfDraftPos(self, v):
        self._colors[2] = v
        self.set_colors()

    @property
    def ColorOutOfDraftNeg(self):
        "Color of the negative Out-of-Draft area (normalized (r, g, b))"
        return self._colors[3]

    @ColorOutOfDraftNeg.setter
    def ColorOutOfDraftNeg(self, v):
        self._colors[3] = v
        self.set_colors()

    @property
    def ColorInTolerancePos(self):
        "Color of the positive tolerance area (normalized (r, g, b))"
        return self._colors[1]

    @ColorInTolerancePos.setter
    def ColorInTolerancePos(self, v):
        self._colors[1] = v
        self.set_colors()

    @property
    def ColorInToleranceNeg(self):
        "Color of the negative tolerance area (normalized (r, g, b))"
        return self._colors[4]

    @ColorInToleranceNeg.setter
    def ColorInToleranceNeg(self, v):
        self._colors[4] = v
        self.set_colors()

    @property
    def Shading(self):
        "Amount of original shape shading (0.0->1.0)"
        return self.shading.value.getValue()

    @Shading.setter
    def Shading(self, v):
        self.shading.value = v

    @property
    def Shader(self):
        return self.shaderProgram

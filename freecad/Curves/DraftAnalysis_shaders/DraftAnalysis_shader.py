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

        self.draft_angle_1 = coin.SoShaderParameter1f()
        self.draft_angle_1.name = "draft_angle_1"

        self.draft_angle_2 = coin.SoShaderParameter1f()
        self.draft_angle_2.name = "draft_angle_2"

        self.tol_angle_1 = coin.SoShaderParameter1f()
        self.tol_angle_1.name = "tol_angle_1"

        self.tol_angle_2 = coin.SoShaderParameter1f()
        self.tol_angle_2.name = "tol_angle_2"

        self.color_indraft_pos = coin.SoShaderParameter3f()
        self.color_indraft_pos.name = "color_indraft_pos"

        self.color_indraft_neg = coin.SoShaderParameter3f()
        self.color_indraft_neg.name = "color_indraft_neg"

        self.color_outdraft_pos = coin.SoShaderParameter3f()
        self.color_outdraft_pos.name = "color_outdraft_pos"

        self.color_outdraft_neg = coin.SoShaderParameter3f()
        self.color_outdraft_neg.name = "color_outdraft_neg"

        self.color_tol_pos = coin.SoShaderParameter3f()
        self.color_tol_pos.name = "color_tol_pos"

        self.color_tol_neg = coin.SoShaderParameter3f()
        self.color_tol_neg.name = "color_tol_neg"

        self.shading = coin.SoShaderParameter1f()
        self.shading.name = "shading"

        self.Direction = (0, 0, 1)
        self.DraftAngle1 = 1.0
        self.DraftAngle2 = 1.0
        self.DraftTol1 = 0.05
        self.DraftTol2 = 0.05
        self.ColorInDraft1 = (0, 0, 1)
        self.ColorInDraft2 = (0, 1, 0)
        self.ColorOutOfDraft1 = (1, 0, 0)
        self.ColorOutOfDraft2 = (1, 0, 0)
        self.ColorTolDraft1 = (0, 1, 1)
        self.ColorTolDraft2 = (1, 1, 0)
        self.Shading = 0.2

        params = [self.analysis_direction,
                  self.draft_angle_1,
                  self.draft_angle_2,
                  self.tol_angle_1,
                  self.tol_angle_2,
                  self.color_indraft_pos,
                  self.color_indraft_neg,
                  self.color_outdraft_pos,
                  self.color_outdraft_neg,
                  self.color_tol_pos,
                  self.color_tol_neg,
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

    @property
    def DraftAngle1(self):
        "Positive draft angle (0->90 degrees)"
        return self.draft_angle_1.value.getValue()

    @DraftAngle1.setter
    def DraftAngle1(self, v):
        self.draft_angle_1.value = v

    @property
    def DraftAngle2(self):
        "Negative draft angle (0->90 degrees)"
        return self.draft_angle_2.value.getValue()

    @DraftAngle2.setter
    def DraftAngle2(self, v):
        self.draft_angle_2.value = v

    @property
    def DraftTol1(self):
        "Positive draft angle tolerance (0->90 degrees)"
        return self.tol_angle_1.value.getValue()

    @DraftTol1.setter
    def DraftTol1(self, v):
        self.tol_angle_1.value = v

    @property
    def DraftTol2(self):
        "Negative draft angle tolerance (0->90 degrees)"
        return self.tol_angle_2.value.getValue()

    @DraftTol2.setter
    def DraftTol2(self, v):
        self.tol_angle_2.value = v

    @property
    def ColorInDraft1(self):
        "Color of the positive In-Draft area (normalized (r, g, b))"
        return self.color_indraft_pos.value.getValue().getValue()

    @ColorInDraft1.setter
    def ColorInDraft1(self, v):
        self.color_indraft_pos.value = v

    @property
    def ColorInDraft2(self):
        "Color of the negative In-Draft area (normalized (r, g, b))"
        return self.color_indraft_neg.value.getValue().getValue()

    @ColorInDraft2.setter
    def ColorInDraft2(self, v):
        self.color_indraft_neg.value = v

    @property
    def ColorOutOfDraft1(self):
        "Color of the positive Out-of-Draft area (normalized (r, g, b))"
        return self.color_outdraft_pos.value.getValue().getValue()

    @ColorOutOfDraft1.setter
    def ColorOutOfDraft1(self, v):
        self.color_outdraft_pos.value = v

    @property
    def ColorOutOfDraft2(self):
        "Color of the negative Out-of-Draft area (normalized (r, g, b))"
        return self.color_outdraft_neg.value.getValue().getValue()

    @ColorOutOfDraft2.setter
    def ColorOutOfDraft2(self, v):
        self.color_outdraft_neg.value = v

    @property
    def ColorTolDraft1(self):
        "Color of the positive tolerance area (normalized (r, g, b))"
        return self.color_tol_pos.value.getValue().getValue()

    @ColorTolDraft1.setter
    def ColorTolDraft1(self, v):
        self.color_tol_pos.value = v

    @property
    def ColorTolDraft2(self):
        "Color of the negative tolerance area (normalized (r, g, b))"
        return self.color_tol_neg.value.getValue().getValue()

    @ColorTolDraft2.setter
    def ColorTolDraft2(self, v):
        self.color_tol_neg.value = v

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

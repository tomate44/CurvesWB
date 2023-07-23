import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
from os import path


class DraftAnalysisShader:

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

        self.color_1 = coin.SoShaderParameter3f()
        self.color_1.name = "color_1"

        self.color_2 = coin.SoShaderParameter3f()
        self.color_2.name = "color_2"

        self.color_3 = coin.SoShaderParameter3f()
        self.color_3.name = "color_3"

        self.color_4 = coin.SoShaderParameter3f()
        self.color_4.name = "color_4"

        self.color_5 = coin.SoShaderParameter3f()
        self.color_5.name = "color_5"

        self.opacity = coin.SoShaderParameter1f()
        self.opacity.name = "opacity"

        self.Direction = (0, 0, 1)
        self.DraftAngle1 = 1.0
        self.DraftAngle2 = 1.0
        self.DraftTol1 = 0.05
        self.DraftTol2 = 0.05
        self.ColorInDraft1 = (0, 0, 1)
        self.ColorInDraft2 = (0, 1, 0)
        self.ColorOutOfDraft = (1, 0, 0)
        self.ColorTolDraft1 = (0, 1, 1)
        self.ColorTolDraft2 = (1, 1, 0)
        self.Opacity = 0.8

        params = [self.analysis_direction,
                  self.draft_angle_1,
                  self.draft_angle_2,
                  self.tol_angle_1,
                  self.tol_angle_2,
                  self.color_1,
                  self.color_2,
                  self.color_3,
                  self.color_4,
                  self.color_5,
                  self.opacity]
        self.fragmentShader.parameter.setValues(0, len(params), params)

        self.shaderProgram = coin.SoShaderProgram()
        self.shaderProgram.shaderObject.set1Value(0, self.vertexShader)
        self.shaderProgram.shaderObject.set1Value(1, self.fragmentShader)

    @property
    def Direction(self):
        return self.analysis_direction.value.getValue().getValue()

    @Direction.setter
    def Direction(self, v):
        self.analysis_direction.value = v

    @property
    def DraftAngle1(self):
        return self.draft_angle_1.value.getValue()

    @DraftAngle1.setter
    def DraftAngle1(self, v):
        self.draft_angle_1.value = v

    @property
    def DraftAngle2(self):
        return self.draft_angle_2.value.getValue()

    @DraftAngle2.setter
    def DraftAngle2(self, v):
        self.draft_angle_2.value = v

    @property
    def DraftTol1(self):
        return self.tol_angle_1.value.getValue()

    @DraftTol1.setter
    def DraftTol1(self, v):
        self.tol_angle_1.value = v

    @property
    def DraftTol2(self):
        return self.tol_angle_2.value.getValue()

    @DraftTol2.setter
    def DraftTol2(self, v):
        self.tol_angle_2.value = v

    @property
    def ColorInDraft1(self):
        return self.color_1.value.getValue().getValue()

    @ColorInDraft1.setter
    def ColorInDraft1(self, v):
        self.color_1.value = v

    @property
    def ColorInDraft2(self):
        return self.color_2.value.getValue().getValue()

    @ColorInDraft2.setter
    def ColorInDraft2(self, v):
        self.color_2.value = v

    @property
    def ColorOutOfDraft(self):
        return self.color_3.value.getValue().getValue()

    @ColorOutOfDraft.setter
    def ColorOutOfDraft(self, v):
        self.color_3.value = v

    @property
    def ColorTolDraft1(self):
        return self.color_4.value.getValue().getValue()

    @ColorTolDraft1.setter
    def ColorTolDraft1(self, v):
        self.color_4.value = v

    @property
    def ColorTolDraft2(self):
        return self.color_5.value.getValue().getValue()

    @ColorTolDraft2.setter
    def ColorTolDraft2(self, v):
        self.color_5.value = v

    @property
    def Opacity(self):
        return self.opacity.value.getValue()

    @Opacity.setter
    def Opacity(self, v):
        self.opacity.value = v

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
# shader = SurfaceAnalysisShader(0, 1)
shader = PhongShader()
root.insertChild(shader.Shader, 0)
"""



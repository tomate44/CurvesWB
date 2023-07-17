from pivy.coin import *

shaderSearchDir = "/home/tomate/Documents/FC-Files/Zebra_shaders/"


def createShader():
    vertexShader = SoVertexShader()
    vertexShader.sourceProgram.setValue(shaderSearchDir + 'Zebra_Vertex_Shader.glsl')  # phong_vshader

    fragmentShader = SoFragmentShader()
    fragmentShader.sourceProgram.setValue(shaderSearchDir + 'Zebra_Fragment_Shader.glsl')  # phong_fshader

    # Shader parameters 
    """
    uniform vec3 analysis_direction;
    uniform int  mode; // 0=Stripes 1=Rainbow 2=Curves
    uniform vec3 stripes_color_1;
    uniform vec3 stripes_color_2;
    uniform int  stripes_number;
    uniform float rainbow_angle_1;
    uniform float rainbow_angle_2;
    uniform float curves_angles[20];
    uniform float curves_tolerance;
    """

    analysis_direction = SoShaderParameter3f()
    analysis_direction.name = "analysis_direction"
    analysis_direction.value = (1, 0, 0)

    fixed_light = SoShaderParameter1i()
    fixed_light.name = "fixed_light"
    fixed_light.value = 0

    mode = SoShaderParameter1i()
    mode.name = "mode"
    mode.value = 1  # 0=Stripes 1=Rainbow 2=Curves

    stripes_color_1 = SoShaderParameter3f()
    stripes_color_1.name = "stripes_color_1"
    stripes_color_1.value = (1, 1, 1)

    stripes_color_2 = SoShaderParameter3f()
    stripes_color_2.name = "stripes_color_2"
    stripes_color_2.value = (0, 0, 0)

    stripes_number = SoShaderParameter1i()
    stripes_number.name = "stripes_number"
    stripes_number.value = 12

    stripes_ratio = SoShaderParameter1f()
    stripes_ratio.name = "stripes_ratio"
    stripes_ratio.value = 0.5

    rainbow_angle_1 = SoShaderParameter1f()
    rainbow_angle_1.name = "rainbow_angle_1"
    rainbow_angle_1.value = 30.0

    rainbow_angle_2 = SoShaderParameter1f()
    rainbow_angle_2.name = "rainbow_angle_2"
    rainbow_angle_2.value = 150.0

    curves_angles = SoShaderParameterArray1f()
    curves_angles.name = "curves_angles"
    angles = [30.0, 60.0, 90.0, 120.0, 150.0]
    comp = [-1] * (20 - len(angles))
    angles += comp
    curves_angles.value.setValues(0, len(angles), angles)
    # print(len(angles))

    curves_tolerance = SoShaderParameter1f()
    curves_tolerance.name = "curves_tolerance"
    curves_tolerance.value = 0.4

    # vertexShader.parameter.set1Value(0, lightdir)
    params = [analysis_direction, fixed_light, mode, stripes_color_1, stripes_color_2, stripes_number, stripes_ratio, rainbow_angle_1, rainbow_angle_2, curves_angles, curves_tolerance]
    fragmentShader.parameter.setValues(0, len(params), params)

    shaderProgram = SoShaderProgram()
    shaderProgram.shaderObject.set1Value(0, vertexShader)
    shaderProgram.shaderObject.set1Value(1, fragmentShader)

    return shaderProgram


doc = App.newDocument()
doc.addObject("Part::Ellipsoid","Ellipsoid")
doc.addObject("Part::Torus","Torus")
doc.recompute()

view = Gui.ActiveDocument.ActiveView
view.viewIsometric()
Gui.SendMsgToActiveView("ViewFit")

root = view.getViewer().getSceneGraph()
shader = createShader()
root.insertChild(shader, 0)




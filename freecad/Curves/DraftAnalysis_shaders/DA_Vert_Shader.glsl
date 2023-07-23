varying vec4 eposition;
varying vec3 normal;
varying vec3 diffuseColor;

void main()
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    eposition = gl_ModelViewMatrix * gl_Vertex;
    normal = gl_NormalMatrix * gl_Normal;
}

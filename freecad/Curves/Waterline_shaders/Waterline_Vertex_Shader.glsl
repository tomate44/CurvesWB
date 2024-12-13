// uniform vec3 lightdir;
varying vec4 eposition;
varying vec3 normal;
varying vec3 diffuseColor;
varying vec4 vertex;
// varying mat4 normmat;

void main()
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    vertex = gl_Vertex;
    eposition = gl_ModelViewMatrix * gl_Vertex;
    normal = gl_NormalMatrix * gl_Normal;
    // normmat = gl_ModelViewMatrix;
}

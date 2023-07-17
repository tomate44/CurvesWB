// uniform vec3 lightdir;
varying vec4 eposition;
varying vec3 normal;
varying vec3 diffuseColor;
// varying vec4 direction;

void main()
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    eposition = gl_ModelViewMatrix * gl_Vertex;
    normal = gl_NormalMatrix * gl_Normal;
//     direction = gl_ModelViewMatrix * vec4(lightdir, 0.0);
}

#define PI 3.1415926538

varying vec4 eposition;
varying vec3 normal;
varying vec4 vertex;
// varying mat4 normmat;
uniform vec3 axis_direction;
uniform vec3 origin;
uniform float main_unit;
uniform int nb_subunits;
uniform float tolerance;
uniform vec3 unit_color;
uniform vec3 subunit_color;

void main(void)
{
//     gl_FragColor = vec4(unit_color, 1.0);
    vec3 dir;
    float color = 0.0;
    dir = vec3(gl_ModelViewMatrix * vec4(axis_direction, 0.0));
    dir = axis_direction;
    float subunit = (main_unit / float(nb_subunits));
    float depth = gl_FragCoord.z / gl_FragCoord.w;
    if (mod(vertex.z, main_unit) < (main_unit / 10.0))
    {
        color = 1.0;
    }
    else if (mod(vertex.z, subunit) < (subunit / 10.0))
    {
        color = 0.5;
    }
    // ambient
    vec3 ambient = gl_FrontMaterial.ambient.rgb;
    // diffuse
    vec3 diffuse = gl_FrontMaterial.diffuse.rgb;
    // specular
    vec3 specular = gl_FrontMaterial.specular.rgb;
    vec4 result = vec4((ambient + diffuse + specular), 1.0);

    if (color > 0.0)
    {
        gl_FragColor = vec4(unit_color, color);
    }
    else
    {
        // gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0); // result;
        gl_FragColor = gl_Color;
    }
}

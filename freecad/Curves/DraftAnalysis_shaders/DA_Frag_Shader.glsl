#define PI 3.1415926538

varying vec4 eposition;
varying vec3 normal;
uniform vec3 analysis_direction;
uniform float draft_angle_1;
uniform float draft_angle_2;
uniform float tol_angle_1;
uniform float tol_angle_2;
uniform vec3 color_indraft_pos;
uniform vec3 color_indraft_neg;
uniform vec3 color_outdraft_pos;
uniform vec3 color_outdraft_neg;
uniform vec3 color_tol_pos;
uniform vec3 color_tol_neg;
uniform float shading;

void main(void)
{
    vec3 color;
    vec3 dir = vec3(gl_ModelViewMatrix * vec4(analysis_direction, 0.0));
    float nDotDir = dot(normalize(normal), normalize(dir));
    float angle = (acos(nDotDir) * 180.0 / PI) - 90.0;
    if (angle < -draft_angle_1 - tol_angle_1)
        color = color_indraft_pos;
    else if (angle < (-draft_angle_1))
        color = color_tol_pos;
    else if (angle < 0.0)
        color = color_outdraft_pos;
    else if (angle < draft_angle_2)
        color = color_outdraft_neg;
    else if (angle < (draft_angle_2 + tol_angle_2))
        color = color_tol_neg;
    else
        color = color_indraft_neg;

    // ambient
    vec3 ambient = gl_FrontMaterial.ambient.rgb;
    // diffuse
    vec3 norm = normalize(normal);
    float diff = dot(norm, dir);
    vec3 diffuse = diff * color; //gl_FrontMaterial.diffuse.rgb;
    // specular
    vec3 view = vec3(0,0,-1);
    vec3 reflectDir = reflect(dir, norm);
    float spec = pow(max(dot(view, reflectDir), 0.0), 8.0); //gl_FrontMaterial.shininess);
    vec3 specular = 0.5 * spec * vec3(1,1,1); //gl_FrontMaterial.specular.rgb;

    vec4 result = vec4(ambient, 1.0) + vec4(diffuse, 1.0) + vec4(specular,1.0);
    // FragColor = vec4(result, 1.0);

    gl_FragColor = (shading * result) + (1.0 - shading) * vec4(color, 1.0);
}

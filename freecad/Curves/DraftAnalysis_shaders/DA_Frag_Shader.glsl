#define PI 3.1415926538

varying vec4 eposition;
varying vec3 normal;
// varying mat4 normmat;
uniform vec3 analysis_direction;
uniform float draft_angle_1;
uniform float draft_angle_2;
uniform float tol_angle_1;
uniform float tol_angle_2;
uniform vec3 color_1;
uniform vec3 color_2;
uniform vec3 color_3;
uniform vec3 color_4;
uniform vec3 color_5;
uniform float opacity;

// void RainbowColor(in float t,
//                   in float t0,
//                   in float t1,
//                   in int num,
//                   inout vec3 color)
// {
//     if (t < t0)
//         color = stripes_color_1;
//     else if (t > t1)
//         color = stripes_color_2;
//     else
//     {
//         float range = abs(t1 - t0);
//         vec3 colors[5];
//         colors[0] = vec3(1,0,0);
//         colors[1] = vec3(1,1,0);
//         colors[2] = vec3(0,1,0);
//         colors[3] = vec3(0,1,1);
//         colors[4] = vec3(0,0,1);
//         float rel = (t - t0) / range;
//         float sv = 4.0 * float(num) * rel;
//         int idx = int(floor(mod(sv, 4.0)));
//         float ratio = mod(sv, 1.0);
//         color = colors[idx + 1] * ratio + colors[idx] * (1.0 - ratio);
//     }
// }

void main(void)
{
    vec3 color;
    vec3 dir = vec3(gl_ModelViewMatrix * vec4(analysis_direction, 0.0));
    float nDotDir = dot(normalize(normal), normalize(dir));
    float angle = (acos(nDotDir) * 180.0 / PI) - 90.0;
    if (angle < (-draft_angle_1 - tol_angle_1))
        color = color_1;
    else if (angle < (-draft_angle_1 + tol_angle_1))
        color = color_4;
    else if (angle < (draft_angle_2 - tol_angle_2))
        color = color_3;
    else if (angle < (draft_angle_2 + tol_angle_2))
        color = color_5;
    else
        color = color_2;

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

    gl_FragColor = ((1.0 - opacity) * result) + opacity * vec4(color, 1.0);
}

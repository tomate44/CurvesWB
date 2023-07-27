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

void PickColor(in float t,
               in float tol,
               inout vec3 color)
{
    float knots[7];
    knots[0] = 0.0;
    knots[1] = 90.0 - draft_angle_1 - tol_angle_1;
    knots[2] = 90.0 - draft_angle_1;
    knots[3] = 90.0;
    knots[4] = 90.0 + draft_angle_2;
    knots[5] = 90.0 + draft_angle_2 + tol_angle_2;
    knots[6] = 180.0;
    vec3 colors[8];
    colors[0] = color_indraft_pos;
    colors[1] = color_indraft_pos;
    colors[2] = color_tol_pos;
    colors[3] = color_outdraft_pos;
    colors[4] = color_outdraft_neg;
    colors[5] = color_tol_neg;
    colors[6] = color_indraft_neg;
    colors[7] = color_indraft_neg;
    for (int i=0; i<6; i++)
    {
        // float diff = knots[i] - t;
        if ((t >= (knots[i] + tol)) && (t <= (knots[i+1] - tol)))
        {
            color = colors[i + 1];
            return;
        }
    }
    for (int i=0; i<6; i++)
    {
        float diff = t - knots[i];
        if (abs(diff) >= tol)
            continue;
        float rel = 0.5 * (1.0 + (diff / tol));
        color = rel * colors[i + 1] + (1.0 - rel) * colors[i];
        return;
    }
    color = colors[6];
}

void main(void)
{
    vec3 color = color_indraft_pos;
    vec3 dir = vec3(gl_ModelViewMatrix * vec4(analysis_direction, 0.0));
    float nDotDir = dot(normalize(normal), normalize(dir));
    float angle = (acos(nDotDir) * 180.0 / PI);

    PickColor(angle, 1e-3, color);
    // ambient
    vec3 ambient = gl_FrontMaterial.ambient.rgb;
    // diffuse
    vec3 norm = normalize(normal);
    float diff = dot(norm, dir);
    vec3 diffuse = diff * color; //gl_FrontMaterial.diffuse.rgb;
    // specular
    vec3 view = vec3(0,0,-1);
    vec3 reflectDir = reflect(dir, norm);
    float spec = pow(max(dot(view, reflectDir), 0.0), gl_FrontMaterial.shininess); //);
    vec3 specular = 0.5 * spec * gl_FrontMaterial.specular.rgb; //gl_FrontMaterial.specular.rgb;

    vec4 result = vec4(ambient, 1.0) + vec4(diffuse, 1.0) + vec4(specular,1.0);
    // FragColor = vec4(result, 1.0);

    gl_FragColor = (shading * result) + (1.0 - shading) * vec4(color, 1.0);
}

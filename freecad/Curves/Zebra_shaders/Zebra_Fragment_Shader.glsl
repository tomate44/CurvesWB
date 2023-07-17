#define PI 3.1415926538

varying vec4 eposition;
varying vec3 normal;
// varying vec4 direction;
uniform vec3 analysis_direction;
uniform int fixed_light;
uniform int  mode; // 0=Stripes 1=Rainbow 2=Curves
uniform vec3 stripes_color_1;
uniform vec3 stripes_color_2;
uniform int  stripes_number;
uniform float stripes_ratio;
uniform float rainbow_angle_1;
uniform float rainbow_angle_2;
uniform float curves_angles[20];
uniform float curves_tolerance;

void main(void)
{
    vec3 dir;
    vec3 color;
    if (fixed_light == 1)
        dir = vec3(gl_ModelViewMatrix * vec4(analysis_direction, 0.0));
    else
        dir = analysis_direction;
    float nDotDir = dot(normalize(normal), normalize(dir));
    if (mode == 0) // Stripes
    {
        float multDot = 0.5 * float(stripes_number) * nDotDir;
        float modulo = mod(multDot, 1.0);
        if (modulo > stripes_ratio)
            color = stripes_color_1;
        else
            color = stripes_color_2;
    }
    if (mode == 1) // Rainbow
    {
        float angle = acos(nDotDir) * 180.0 / PI;
        if (angle < rainbow_angle_1)
            color = vec3(1,1,1);
        else if (angle > rainbow_angle_2)
            color = vec3(0,0,0);
        else
        {
            float range = abs(rainbow_angle_1 - rainbow_angle_2);
            vec3 colors[5];
            colors[0] = vec3(1,0,0);
            colors[1] = vec3(1,1,0);
            colors[2] = vec3(0,1,0);
            colors[3] = vec3(0,1,1);
            colors[4] = vec3(0,0,1);
            float rel_angle = (4.0 * (angle - rainbow_angle_1)) / range;
            int floor_angle = int(floor(rel_angle));
            float mod_angle = abs(mod(rel_angle, 1.0));
            color = colors[floor_angle + 1] * mod_angle + colors[floor_angle] * (1.0 - mod_angle);
        }
    }
    if (mode == 2) // Curves
    {
        float angle = acos(nDotDir) * 180.0 / PI;
        vec3 color = stripes_color_1;
        for(int i=0; i<20; i++)
        {
            float a = curves_angles[i];
            if (a > 0.0)
            {
                float diff = abs(angle - a);
                if (diff < curves_tolerance)
                    color = stripes_color_2;
            }
        }
    }
    gl_FragColor = vec4(color, gl_Color.a);
}

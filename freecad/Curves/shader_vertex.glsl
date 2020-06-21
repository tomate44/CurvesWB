varying vec3 ecPosition3;
varying vec3 fragmentNormal;
varying vec4 color;

void main(void)
{
    vec4 ecPosition = gl_ModelViewMatrix * gl_Vertex;
    ecPosition3 = ecPosition.xyz / ecPosition.w;
    fragmentNormal = normalize(gl_Normal);
    //fragmentNormal = normalize(gl_NormalMatrix * gl_Normal);
    vec4 front = vec4(1.0,0.2,0.2,1.0);

    gl_Position = ftransform();
    color = gl_Color;
}

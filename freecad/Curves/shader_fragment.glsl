varying vec3 ecPosition3;
varying vec3 fragmentNormal;
varying vec4 color;

void main(void)
{
    vec3 eye = -normalize(ecPosition3);
    vec4 ambient =  vec4(1.0, 0.0, 0.0, 1.0);
    vec4 diffuse =  vec4(0.0, 0.0, 1.0, 1.0);
    vec4 specular = vec4(1.0, 1.0, 0.0, 1.0);
//     vec3 color;

//     color =
//         gl_FrontLightModelProduct.sceneColor.rgb +
//         ambient.rgb * gl_FrontMaterial.ambient.rgb +
//         diffuse.rgb * gl_Color.rgb +
//         specular.rgb * gl_FrontMaterial.specular.rgb;
    float threshold = 0.7;
    vec3 ax = vec3(1.,0.,0.);
    vec3 ay = vec3(0.,1.,0.);
    vec3 az = vec3(0.,0.,1.);
    if (abs(dot(fragmentNormal,ax)) >= threshold) {
        gl_FragColor = vec4(ax,threshold);
    }
    else if (abs(dot(fragmentNormal,ay)) >= threshold) {
        gl_FragColor = vec4(ay,threshold);
    }
    else if (abs(dot(fragmentNormal,az)) >= threshold) {
        gl_FragColor = vec4(az,threshold);
    }
    else {
        gl_FragColor = vec4(gl_FrontLightModelProduct.sceneColor.rgb +
        ambient.rgb * gl_FrontMaterial.ambient.rgb +
        diffuse.rgb * color.rgb +
        specular.rgb * gl_FrontMaterial.specular.rgb, 1.0);
    }
}

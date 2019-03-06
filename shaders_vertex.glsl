#version 330

// in vec3 aPos; // the position variable has attribute position 0
//   
// out vec4 vertexColor; // specify a color output to the fragment shader
// 
// void main()
// {
//     gl_Position = vec4(aPos, 1.0); // see how we directly give a vec3 to vec4's constructor
//     vertexColor = vec4(0.5, aPos.y, aPos.z, 1.0); // set the output variable to a dark-red color
// }


in vec4 position;
in vec4 normal;
in vec4 color;
out vec4 vertexColor; // specify a color output to the fragment shader

// these come from the programmable pipeline
uniform mat4 modelViewMatrix;
uniform mat4 normalMatrix;


void main(void)
{
    vec4 ecPosition = modelViewMatrix * position;
    // vec3 ecPosition3 = ecPosition.xyz / ecPosition.w;
    vec4 fragmentNormal = normalize(normalMatrix * normal);
    //vec4 front = vec4(1.0,1.0,0.5,1.0);

    gl_Position = ecPosition;
    vertexColor = color;
}

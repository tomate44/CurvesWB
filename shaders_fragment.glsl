#version 330

in vec4 vertexColor;
out vec4 FragColor;
  
void main()
{             
    if(gl_FragCoord.x < 800)
        FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    else
        FragColor = vertexColor;        
}  

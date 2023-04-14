#version 330 core

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 vertexPosition_modelspace;
layout(location = 1) in vec3 vertexColor;

// Output data ; will be interpolated for each fragment.
out vec3 vColor;
out vec3 EyeDirection;

// Values that stay constant for the whole mesh.
uniform mat4 MVP;
uniform vec3 EyePos;

void main(){
	// Output position of the vertex, in clip space : MVP * position
	gl_Position =  MVP * vec4(vertexPosition_modelspace,1);
	EyeDirection = EyePos - vertexPosition_modelspace;
	vColor = vertexColor;
}
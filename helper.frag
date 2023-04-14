#version 330 core

in vec3 vColor;
in vec3 EyeDirection;

out vec3 color;

uniform float LightPower;
uniform float LightMinimal;

void main(){
  float distance = length( EyeDirection );

  color =
    vColor * 0.2 +
    vColor * LightMinimal +
    vColor * LightPower / ( distance * distance )
  ;
}
#version 330 core

in vec3 Normal;
in vec3 EyeDirection;
in float Normal_sign;

out vec3 color;

uniform vec3 LightRay_reverse;
uniform float LightPower;
uniform float LightMinimal;

void main(){
  vec3 baseColor = vec3(0.8, 0.4*Normal_sign, 0.1);
  vec3 specularColor = vec3(0.2, 0.2, 0.2);

  vec3 n = normalize( Normal );
  vec3 l = normalize( LightRay_reverse );
  //float cosTheta = clamp( dot( l,n ), 0,1 );
  float cosTheta = abs( dot( l,n ) );

  vec3 E = normalize(EyeDirection);
  vec3 R = reflect(-l,n);
  float cosAlpha = clamp( dot( E,R ), 0,1 );

  float distance = length( EyeDirection );

  color =
    baseColor * 0.2 +
    baseColor * LightMinimal * cosTheta +
    baseColor * LightPower * cosTheta / ( distance * distance ) +
    specularColor * LightPower * pow(cosAlpha,3) / (distance*distance)
  ;
}
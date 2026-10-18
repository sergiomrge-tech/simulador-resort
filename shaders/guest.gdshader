shader_type spatial;
render_mode diffuse_toon, specular_toon;
// Pinta o manequim Quaternius com zonas gravadas em COLOR.r (ver tools/color_zones.py).
instance uniform vec4 skin : source_color = vec4(0.78, 0.55, 0.40, 1.0);
instance uniform vec4 shirt : source_color = vec4(0.9, 0.3, 0.3, 1.0);
instance uniform vec4 shorts : source_color = vec4(0.2, 0.3, 0.6, 1.0);
instance uniform vec4 hair : source_color = vec4(0.1, 0.07, 0.05, 1.0);
uniform vec4 sandals : source_color = vec4(0.25, 0.15, 0.08, 1.0);
varying float zone;
void vertex(){ zone = COLOR.r * 255.0 / 32.0; }
void fragment(){
	vec3 c = skin.rgb;
	float r = 0.6;
	if (zone > 0.5 && zone < 1.5) { c = shirt.rgb; r = 0.85; }
	else if (zone > 1.5 && zone < 2.5) { c = shorts.rgb; r = 0.9; }
	else if (zone > 2.5 && zone < 3.5) { c = hair.rgb; r = 0.5; }
	else if (zone > 3.5) { c = sandals.rgb; r = 0.7; }
	// v0.7 cartoon: cores um pouco mais saturadas
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	ALBEDO = mix(vec3(l), c, 1.2);
	ROUGHNESS = r;
	RIM = 0.3;
	RIM_TINT = 0.5;
	SPECULAR = 0.3;
}

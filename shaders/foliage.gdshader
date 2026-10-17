shader_type spatial;
render_mode cull_disabled;
// Capim e arbustos (MultiMesh) com balanço de vento.
uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float sway = 0.12;
uniform vec3 tint : source_color = vec3(1.0);
void vertex(){
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float h = clamp(VERTEX.y, 0.0, 2.0);
	float s = sin(TIME * 1.6 + w.x * 0.35 + w.z * 0.25) + 0.4 * sin(TIME * 3.1 + w.x);
	VERTEX.x += s * sway * h * h;
	VERTEX.z += s * sway * 0.5 * h * h;
	NORMAL = vec3(0.0, 1.0, 0.0);
}
void fragment(){
	vec4 c = texture(tex, UV);
	if (c.a < 0.45) discard;
	ALBEDO = c.rgb * tint * mix(1.05, 0.6, UV.y);
	ROUGHNESS = 0.8;
	BACKLIGHT = vec3(0.25, 0.3, 0.1);
}

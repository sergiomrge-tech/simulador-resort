shader_type spatial;
render_mode cull_disabled;
// Folhas de coqueiro: balanço leve no alto da copa.
uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float sway = 0.09;
uniform vec3 tint : source_color = vec3(1.0, 0.98, 0.92);

void vertex() {
	float h = clamp(VERTEX.y / 7.5, 0.0, 1.4);
	float s = sin(TIME * 1.25 + VERTEX.x * 0.45 + VERTEX.z * 0.35);
	s += 0.35 * sin(TIME * 2.4 + VERTEX.z);
	VERTEX.x += s * sway * h * h;
	VERTEX.z += s * sway * 0.55 * h * h;
}

void fragment() {
	vec4 c = texture(tex, UV);
	if (c.a < 0.4) {
		discard;
	}
	ALBEDO = c.rgb * tint;
	ROUGHNESS = 0.75;
	BACKLIGHT = vec3(0.25, 0.35, 0.1);
}

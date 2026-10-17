shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha, diffuse_burley;
// Folíolos recortados por alpha, dos dois lados, com luz atravessando a lâmina.
uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float sway = 0.07;
instance uniform vec3 tint : source_color = vec3(1.0, 0.98, 0.9);

void vertex() {
	float h = clamp(VERTEX.y / 7.5, 0.0, 1.4);
	float s = sin(TIME * 1.25 + VERTEX.x * 0.45 + VERTEX.z * 0.35);
	s += 0.35 * sin(TIME * 2.4 + VERTEX.z);
	VERTEX.x += s * sway * h * h;
	VERTEX.z += s * sway * 0.55 * h * h;
}

void fragment() {
	vec4 c = texture(tex, UV);
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.42;
	ALBEDO = c.rgb * tint;
	ROUGHNESS = 0.62;
	SPECULAR = 0.15;
	BACKLIGHT = vec3(0.48, 0.62, 0.16);
}

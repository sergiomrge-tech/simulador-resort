shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha, diffuse_toon, specular_toon;
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
	float lum = dot(c.rgb, vec3(0.3, 0.55, 0.15));
	vec3 cartoon = mix(vec3(0.06, 0.26, 0.10), vec3(0.18, 0.44, 0.14), smoothstep(0.18, 0.3, lum));
	ALBEDO = cartoon * mix(vec3(1.0), tint, 0.3);
	ROUGHNESS = 0.62;
	SPECULAR = 0.15;
	BACKLIGHT = vec3(0.10, 0.18, 0.06);
}

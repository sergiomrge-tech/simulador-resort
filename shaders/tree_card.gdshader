shader_type spatial;
// Impostor de árvore tropical: cartão que gira em Y para a câmera.
render_mode cull_disabled, depth_prepass_alpha, diffuse_burley;

uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float aerial = 0.35;
uniform float dawn = 0.0;
uniform vec3 mist_color : source_color = vec3(0.80, 0.86, 0.90);
uniform vec3 fog_color : source_color = vec3(0.64, 0.76, 0.86);
varying vec3 tint;
varying float crown;

void vertex() {
	tint = INSTANCE_CUSTOM.rgb;
	crown = INSTANCE_CUSTOM.a;
	if (dot(tint, tint) < 0.01) {
		tint = vec3(0.75, 0.95, 0.62);
	}
	vec3 pos = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	vec3 to = cam - pos;
	to.y = 0.0;
	if (dot(to, to) < 0.0001) {
		to = vec3(0.0, 0.0, 1.0);
	} else {
		to = normalize(to);
	}
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), to));
	VERTEX.x += sin(TIME * 0.9 + pos.x * 0.17 + pos.z * 0.13) * 0.035 * UV.y;
	float sx = length(MODEL_MATRIX[0].xyz);
	float sy = length(MODEL_MATRIX[1].xyz);
	mat4 m = mat4(
		vec4(right * sx, 0.0),
		vec4(0.0, sy, 0.0, 0.0),
		vec4(to * sx, 0.0),
		vec4(pos, 1.0)
	);
	MODELVIEW_MATRIX = VIEW_MATRIX * m;
}

void fragment() {
	vec4 c = texture(tex, UV);
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.4;
	float dist = length(VERTEX);
	float air = clamp(smoothstep(60.0, 700.0, dist) * aerial, 0.0, 0.88);
	vec3 col = c.rgb * tint;
	float mist = clamp(crown, 0.0, 1.0) * dawn;
	col = mix(col, mist_color, mist * 0.72);
	col = mix(col, fog_color, air);
	EMISSION = mist_color * mist * 0.35;
	ALBEDO = col;
	ROUGHNESS = 0.84;
	SPECULAR = 0.08;
	BACKLIGHT = vec3(0.28, 0.40, 0.14);
}

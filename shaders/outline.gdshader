// Contorno cartoon em tela cheia (v0.7). Fica num quad preso à câmera e desenha linhas onde a
// profundidade ou a normal mudam de repente: silhuetas, quinas de caixas, borda das folhas.
shader_type spatial;
render_mode unshaded, fog_disabled, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform sampler2D normal_tex : hint_normal_roughness_texture, filter_nearest, repeat_disable;
uniform vec4 line_color : source_color = vec4(0.20, 0.18, 0.15, 0.46);
uniform float thickness = 0.8;
uniform float depth_sensitivity = 0.085;
uniform float normal_sensitivity = 0.85;
uniform float fade_start = 18.0;
uniform float fade_end = 65.0;

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

float lin_depth(vec2 uv, mat4 inv_proj) {
	float d = texture(depth_tex, uv).r;
	vec4 v = inv_proj * vec4(uv * 2.0 - 1.0, d, 1.0);
	return -v.z / v.w;
}

vec3 view_normal(vec2 uv) {
	return normalize(texture(normal_tex, uv).xyz * 2.0 - 1.0);
}

void fragment() {
	vec2 px = thickness / VIEWPORT_SIZE;
	vec2 uv = SCREEN_UV;
	float c = lin_depth(uv, INV_PROJECTION_MATRIX);
	float l = lin_depth(uv - vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float r = lin_depth(uv + vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float u = lin_depth(uv - vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	float d = lin_depth(uv + vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	float near_d = min(c, min(min(l, r), min(u, d)));
	// v0.7.3: segunda derivada do INVERSO da profundidade. Em perspectiva, 1/z varia de forma linear
	// na tela sobre qualquer plano, então pisos e paredes vistos de lado não geram mais linhas tracejadas
	// (antes o chão "tremia" ao andar); só quinas e silhuetas de verdade passam.
	float ic = 1.0 / max(c, 0.05);
	float dd = abs(1.0 / max(l, 0.05) + 1.0 / max(r, 0.05) - 2.0 * ic) + abs(1.0 / max(u, 0.05) + 1.0 / max(d, 0.05) - 2.0 * ic);
	float e_depth = smoothstep(depth_sensitivity, depth_sensitivity * 2.0, dd / ic);

	vec3 n = view_normal(uv);
	float nd = 0.0;
	nd += 1.0 - dot(n, view_normal(uv + vec2(px.x, 0.0)));
	nd += 1.0 - dot(n, view_normal(uv + vec2(0.0, px.y)));
	float e_norm = smoothstep(normal_sensitivity, normal_sensitivity * 1.6, nd);
	// o céu não tem normal útil
	if (c > 2000.0) {
		e_norm = 0.0;
	}
	float edge = max(e_depth, e_norm);
	edge *= 1.0 - smoothstep(fade_start, fade_end, near_d);
	ALBEDO = line_color.rgb;
	ALPHA = edge * line_color.a;
}

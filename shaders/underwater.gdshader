shader_type spatial;
// v0.9.5: visão embaixo d'água (snorkel). Quad de tela inteira preso à câmera: tinge, ondula e enevoa pela profundidade.
render_mode unshaded, cull_disabled, depth_draw_never, depth_test_disabled, fog_disabled, shadows_disabled;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture;
uniform vec3 water_col : source_color = vec3(0.04, 0.33, 0.42);
uniform float density = 0.11;
void vertex() { POSITION = vec4(VERTEX.xy * 2.0, 1.0, 1.0); }
void fragment() {
	vec2 uv = SCREEN_UV + vec2(sin(SCREEN_UV.y * 30.0 + TIME * 2.0), cos(SCREEN_UV.x * 25.0 + TIME * 1.7)) * 0.003;
	float d = texture(depth_tex, uv).r;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec4 ndc = vec4(uv * 2.0 - 1.0, d * 2.0 - 1.0, 1.0);
#else
	vec4 ndc = vec4(uv * 2.0 - 1.0, d, 1.0);
#endif
	vec4 view = INV_PROJECTION_MATRIX * ndc;
	float dist = -view.z / view.w;
	vec3 c = texture(screen_tex, uv).rgb;
	float f = clamp(1.0 - exp(-max(dist, 0.0) * density), 0.0, 0.93);
	// cáusticas orgânicas (linhas onduladas que se cruzam), não uma grade de pontos
	vec2 q = uv * vec2(9.0, 6.0);
	float w1 = sin(q.x * 3.1 + sin(q.y * 2.3 + TIME * 0.9) * 1.7 + TIME * 0.6);
	float w2 = sin(q.y * 3.7 + sin(q.x * 1.9 - TIME * 0.7) * 1.9 - TIME * 0.5);
	float caus = pow(clamp(1.0 - abs(w1 + w2) * 0.5, 0.0, 1.0), 8.0) * 0.08 * (1.0 - f);
	float vign = smoothstep(1.25, 0.35, length(SCREEN_UV - 0.5) * 1.6);
	ALBEDO = mix(c * vec3(0.55, 0.85, 0.95), water_col, f) * mix(0.7, 1.0, vign) + caus;
}

shader_type spatial;
// Serra: triplanar de floresta, grama e rocha, com névoa de alvorada nos cumes
// e perspectiva aérea mais forte na camada distante.
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D forest_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D forest_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D grass_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D grass_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D forest_rough : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_rough : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float tile = 0.05;
uniform float dawn = 0.0;
uniform float night = 0.0;
uniform float aerial = 0.2;
uniform float far_fade = 0.0;
uniform float has_rough = 0.0;
uniform vec3 mist_color : source_color = vec3(0.80, 0.86, 0.90);
uniform vec3 fog_color : source_color = vec3(0.64, 0.76, 0.86);

varying vec3 wpos;
varying vec3 wnor;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
vec3 tri(sampler2D tex, float sc) {
	vec3 bn = abs(normalize(wnor));
	bn /= (bn.x + bn.y + bn.z + 0.0001);
	return texture(tex, wpos.yz * sc).rgb * bn.x
		+ texture(tex, wpos.xz * sc).rgb * bn.y
		+ texture(tex, wpos.xy * sc).rgb * bn.z;
}
float tri_r(sampler2D tex, float sc) {
	vec3 bn = abs(normalize(wnor));
	bn /= (bn.x + bn.y + bn.z + 0.0001);
	return texture(tex, wpos.yz * sc).r * bn.x
		+ texture(tex, wpos.xz * sc).r * bn.y
		+ texture(tex, wpos.xy * sc).r * bn.z;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnor = normalize(mat3(MODEL_MATRIX) * NORMAL);
}

void fragment() {
	vec3 n = normalize(wnor);
	float slope = clamp(n.y, 0.0, 1.0);
	float steep = smoothstep(0.84, 0.46, slope);
	float peak = smoothstep(48.0, 96.0, wpos.y);
	float rock_w = clamp(max(steep, peak * 0.82), 0.0, 1.0);
	float patch = noise(wpos.xz * 0.018);
	rock_w = clamp(rock_w + smoothstep(0.68, 0.9, patch) * steep * 0.35, 0.0, 1.0);
	float forest_w = (1.0 - rock_w) * smoothstep(0.42, 0.78, patch);
	float grass_w = clamp(1.0 - rock_w - forest_w, 0.0, 1.0);
	vec3 forest_c = tri(forest_tex, tile) * vec3(0.62, 0.82, 0.48);
	vec3 grass_c = tri(grass_tex, tile * 1.2) * vec3(0.70, 1.05, 0.52);
	vec3 rock_c = tri(rock_tex, tile * 0.82) * vec3(0.82, 0.78, 0.72);
	vec3 col = forest_c * forest_w + grass_c * grass_w + rock_c * rock_w;
	float macro = noise(wpos.xz * 0.008) * 0.6 + noise(wpos.xz * 0.031) * 0.4;
	col *= mix(0.84, 1.08, macro);
	// Mata Atlântica: encostas verdes, rocha só onde o declive pede
	col = mix(col, col * vec3(0.72, 1.18, 0.66) + vec3(0.015, 0.04, 0.01), (1.0 - rock_w) * 0.42);
	float dist = length(VERTEX);
	float air = smoothstep(80.0, 820.0, dist) * (0.22 + aerial);
	air = clamp(air + far_fade * smoothstep(30.0, 520.0, dist), 0.0, 0.93);
	col = mix(col, fog_color, air);
	float mist = smoothstep(14.0, 58.0, wpos.y) * dawn;
	mist *= mix(0.45, 1.0, smoothstep(0.15, 0.7, slope));
	mist = clamp(mist, 0.0, 0.88);
	col = mix(col, mist_color, mist);
	if (far_fade > 0.2) {
		float g = dot(col, vec3(0.30, 0.55, 0.15));
		col = mix(col, vec3(g), far_fade * 0.45);
	}
	ALBEDO = col;
	EMISSION = mist_color * mist * (0.35 + dawn * 0.25) * (1.0 - night * 0.25);
	vec3 dn = tri(forest_nor, tile) * forest_w + tri(grass_nor, tile * 1.2) * grass_w + tri(rock_nor, tile * 0.82) * rock_w;
	dn = dn * 2.0 - 1.0;
	vec3 world_n = normalize(n + vec3(dn.x, dn.z * 0.2, dn.y) * mix(1.0, 0.28, far_fade));
	NORMAL = normalize((VIEW_MATRIX * vec4(world_n, 0.0)).xyz);
	float tex_r = mix(tri_r(forest_rough, tile), tri_r(rock_rough, tile * 0.82), rock_w);
	float lit_r = mix(0.92, 0.58, rock_w);
	ROUGHNESS = mix(lit_r, tex_r, has_rough);
	ROUGHNESS = mix(ROUGHNESS, 1.0, air * 0.45);
	SPECULAR = mix(0.12, 0.26, rock_w) * (1.0 - air);
}

shader_type spatial;
// Copa de Mata Atlântica. Rocha só em penhasco; a névoa azul é a do shader
// (a névoa da cena deixava a encosta cinza no llvmpipe).
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx, fog_disabled;

uniform sampler2D forest_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D forest_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D grass_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D grass_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D forest_rough : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_rough : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float tile = 0.055;
uniform float dawn = 0.0;
uniform float night = 0.0;
uniform float aerial = 0.35;
uniform float far_fade = 0.0;
uniform float has_rough = 0.0;
uniform float forest_bias = 0.0;
uniform vec3 mist_color : source_color = vec3(0.78, 0.86, 0.90);
uniform vec3 haze_color : source_color = vec3(0.50, 0.64, 0.78);

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
float fbm(vec2 p) {
	float a = noise(p) * 0.55;
	a += noise(p * 2.1 + vec2(3.2, 1.7)) * 0.30;
	a += noise(p * 4.3 + vec2(8.1, 2.4)) * 0.15;
	return a;
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
	// Rocha a partir de ~50°. A rampa da vila fica abaixo disso.
	float rock_w = smoothstep(0.64, 0.38, slope) * (1.0 - forest_bias);
	float grass_w = smoothstep(16.0, 3.0, wpos.y) * smoothstep(0.62, 0.9, slope) * (1.0 - rock_w);
	grass_w = clamp(grass_w, 0.0, 0.85);
	float forest_w = clamp(1.0 - rock_w - grass_w, 0.0, 1.0);

	float clump = fbm(wpos.xz * 0.02);
	float macro = fbm(wpos.xz * 0.0065 + vec2(4.0, 1.2));
	float fine = noise(wpos.xz * 0.11);
	vec3 shade = vec3(0.07, 0.30, 0.06);
	vec3 midc = vec3(0.13, 0.46, 0.09);
	vec3 lit = vec3(0.40, 0.66, 0.16);
	vec3 canopy = mix(shade, midc, clump);
	canopy = mix(canopy, lit, smoothstep(0.46, 0.82, macro) * smoothstep(18.0, 90.0, wpos.y));
	float valley = smoothstep(0.55, 0.18, macro);
	canopy *= mix(1.0, 0.72, valley);
	canopy *= mix(0.9, 1.12, fine);
	float detail = dot(tri(forest_tex, tile), vec3(0.25, 0.55, 0.20));
	canopy *= mix(0.86, 1.14, clamp(detail, 0.0, 1.0));

	float spot = smoothstep(0.68, 0.86, fbm(wpos.xz * 0.018 + vec2(12.0, 3.0)));
	float kind = noise(floor(wpos.xz * 0.012));
	vec3 bloom = vec3(0.78, 0.28, 0.48);
	bloom = mix(bloom, vec3(0.90, 0.74, 0.16), step(0.38, kind));
	bloom = mix(bloom, vec3(0.50, 0.22, 0.66), step(0.70, kind));
	canopy = mix(canopy, bloom, spot * forest_w * 0.82);

	vec3 grass = tri(grass_tex, tile * 1.2) * vec3(0.62, 0.92, 0.34);
	grass = mix(vec3(0.34, 0.55, 0.16), grass, 0.45);
	vec3 rock = tri(rock_tex, tile * 0.55) * vec3(0.78, 0.74, 0.68);
	vec3 col = canopy * forest_w + grass * grass_w + rock * rock_w;

	float dist = length(VERTEX);
	float air = smoothstep(180.0, 820.0, dist) * (0.42 + aerial);
	air = clamp(air + far_fade * 0.28, 0.0, 0.78);
	vec3 haze = mix(haze_color, vec3(0.62, 0.74, 0.86), clamp(far_fade, 0.0, 1.0));
	col = mix(col, haze, air);

	float mist = smoothstep(48.0, 140.0, wpos.y) * dawn;
	mist = clamp(mist, 0.0, 0.62);
	col = mix(col, mist_color, mist);

	ALBEDO = col;
	EMISSION = col * (0.42 * forest_w + 0.16 * grass_w) + mist_color * mist * 0.18 * (1.0 - night * 0.35);

	float e = 3.2;
	float b0 = fbm(wpos.xz * 0.05);
	float bx = fbm((wpos.xz + vec2(e, 0.0)) * 0.05) - b0;
	float bz = fbm((wpos.xz + vec2(0.0, e)) * 0.05) - b0;
	vec3 dn = tri(forest_nor, tile * 1.6) * forest_w + tri(rock_nor, tile * 0.55) * rock_w;
	dn = dn * 2.0 - 1.0;
	vec3 bumpy = n + vec3(-bx, 0.45, -bz) * (0.55 * forest_w) + vec3(dn.x, abs(dn.z) * 0.15, dn.y) * mix(0.22, 0.55, rock_w);
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(bumpy), 0.0)).xyz);
	float tex_r = mix(tri_r(forest_rough, tile), tri_r(rock_rough, tile * 0.55), rock_w);
	ROUGHNESS = mix(mix(0.96, 0.78, rock_w), tex_r, has_rough);
	ROUGHNESS = mix(ROUGHNESS, 1.0, air * 0.45);
	SPECULAR = mix(0.04, 0.16, rock_w) * (1.0 - air);
	BACKLIGHT = vec3(0.12, 0.22, 0.06) * forest_w;
}

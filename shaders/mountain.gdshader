shader_type spatial;
// Encosta de Mata Atlântica. O albedo é a copa vista de cima (verde dessaturado).
// Sem emissão: a luz do sol e o ambiente é que clareiam a crista. A névoa
// empurra a serra distante para a cor do céu.
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx, fog_disabled, ambient_light_disabled;

uniform sampler2D canopy_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D canopy_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D rock_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float tile = 0.0104167;
uniform float dawn = 0.0;
uniform float night = 0.0;
uniform float aerial = 0.2;
uniform float far_fade = 0.0;
uniform vec3 mist_color : source_color = vec3(0.75, 0.82, 0.88);
uniform vec3 haze_color : source_color = vec3(0.55, 0.70, 0.84);

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
	a += noise(p * 2.05 + vec2(3.1, 1.4)) * 0.30;
	a += noise(p * 4.1 + vec2(8.0, 2.2)) * 0.15;
	return a;
}
vec3 tri(sampler2D tex, float sc) {
	vec3 bn = abs(normalize(wnor));
	bn /= (bn.x + bn.y + bn.z + 0.0001);
	return texture(tex, wpos.yz * sc).rgb * bn.x
		+ texture(tex, wpos.xz * sc).rgb * bn.y
		+ texture(tex, wpos.xy * sc).rgb * bn.z;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnor = normalize(mat3(MODEL_MATRIX) * NORMAL);
}

void fragment() {
	vec3 n = normalize(wnor);
	float slope = clamp(n.y, 0.0, 1.0);
	// Rocha a partir de ~47° (n.y = cos). A encosta da vila fica abaixo disso.
	float rock_w = smoothstep(0.68, 0.42, slope);
	float grass_w = smoothstep(8.0, 1.5, wpos.y) * smoothstep(0.78, 0.96, slope) * (1.0 - rock_w);

	vec2 uv = wpos.xz * tile;
	vec3 canopy = texture(canopy_tex, uv).rgb;
	canopy *= vec3(0.95, 1.02, 0.62);
	float macro = fbm(wpos.xz * 0.0032 + vec2(2.0, 0.4));
	canopy *= mix(vec3(0.78, 0.88, 0.70), vec3(1.0, 1.08, 0.78), macro);
	canopy *= mix(0.86, 1.0, fbm(wpos.xz * 0.011));

	vec3 rock = tri(rock_tex, 0.045) * vec3(0.70, 0.68, 0.64);
	vec3 col = mix(canopy, canopy * vec3(0.92, 1.0, 0.78), grass_w * 0.28);
	col = mix(col, rock, rock_w);

	// A névoa de verdade é a do ambiente (depois da luz). Aqui só dessatura,
	// esfria e escurece com a distância, para a crista não acender acima do céu.
	float dist = length(VERTEX);
	float air = smoothstep(160.0, 920.0, dist);
	float far = clamp(air * (0.25 + aerial) + far_fade * air, 0.0, 1.0);
	float luma = dot(col, vec3(0.28, 0.58, 0.14));
	col = mix(col, vec3(luma * 0.92, luma, luma * 0.85), far * 0.5);
	col = mix(col, col * vec3(0.88, 0.94, 1.06), far * 0.35);
	col *= mix(1.0, 0.82, far);
	float mist = clamp(smoothstep(110.0, 260.0, wpos.y) * dawn, 0.0, 0.42);
	col = mix(col, mist_color, mist * (1.0 - night * 0.5));
	ALBEDO = col;

	vec3 tn = texture(canopy_nor, uv).rgb * 2.0 - 1.0;
	vec3 t = normalize(cross(n, vec3(0.0, 0.0, 1.0)));
	vec3 b = cross(n, t);
	tn.y = -tn.y;
	vec3 rn = tri(rock_nor, 0.045) * 2.0 - 1.0;
	vec3 wn = normalize(t * tn.x + b * tn.y + n * tn.z);
	wn = normalize(mix(wn, n + vec3(rn.x, 0.0, rn.y) * 0.35, rock_w));
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
	ROUGHNESS = mix(0.94, 0.8, rock_w);
	SPECULAR = mix(0.02, 0.12, rock_w) * (1.0 - air * 0.8);
}

void light() {
	// A encosta da vila fica à sombra do sol do meio-dia. O wrap mantém
	// um verde oliva, em vez do ambiente azul do céu.
	float nd = dot(NORMAL, LIGHT);
	float wrap = clamp(nd * 0.5 + 0.5, 0.0, 1.0);
	DIFFUSE_LIGHT += LIGHT_COLOR * wrap * wrap * ATTENUATION;
	SPECULAR_LIGHT = vec3(0.0);
}

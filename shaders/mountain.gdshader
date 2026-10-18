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
vec2 rot2(vec2 p, float a) {
	float c = cos(a);
	float s = sin(a);
	return vec2(c * p.x - s * p.y, s * p.x + c * p.y);
}
// Duas escalas giradas. O peso muda devagar, então a repetição da cúpula não alinha.
float tile_w(vec2 xz) {
	return smoothstep(0.30, 0.70, fbm(xz * 0.0065 + vec2(4.2, 1.1)));
}
vec3 canopy_alb(vec2 xz) {
	vec2 uv_a = xz * tile;
	vec2 uv_b = rot2(xz, 0.9) * (tile * 1.67) + vec2(0.37, 0.19);
	vec3 a = texture(canopy_tex, uv_a).rgb;
	vec3 b = texture(canopy_tex, uv_b).rgb;
	return mix(a, b, tile_w(xz));
}
vec3 canopy_nrm(vec2 xz) {
	vec2 uv_a = xz * tile;
	vec2 uv_b = rot2(xz, 0.9) * (tile * 1.67) + vec2(0.37, 0.19);
	vec3 a = texture(canopy_nor, uv_a).rgb * 2.0 - 1.0;
	vec3 b = texture(canopy_nor, uv_b).rgb * 2.0 - 1.0;
	return normalize(mix(a, b, tile_w(xz)));
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
	// Rocha só em paredão quase vertical. A crista larga continua floresta.
	float rock_w = smoothstep(0.38, 0.16, slope);
	float grass_w = smoothstep(8.0, 1.5, wpos.y) * smoothstep(0.78, 0.96, slope) * (1.0 - rock_w);

	// v0.7 cartoon: mata em dois verdes chapados com manchas arredondadas, pedra lilás-acinzentada
	float blob = fbm(wpos.xz * 0.018);
	vec3 canopy = mix(vec3(0.2, 0.62, 0.3), vec3(0.36, 0.78, 0.32), smoothstep(0.48, 0.53, blob));
	canopy = mix(canopy, vec3(0.13, 0.5, 0.3), smoothstep(0.66, 0.7, fbm(wpos.xz * 0.05 + 3.0)));
	vec3 rock = mix(vec3(0.62, 0.58, 0.68), vec3(0.74, 0.7, 0.78), step(0.5, fract(wpos.y * 0.15)));
	vec3 col = mix(canopy, canopy * vec3(0.96, 1.0, 0.90), grass_w * 0.22);

	// Longe: silhueta verde-azulada. Sem o cinza quente, que lia como pedra.
	float dist = length(VERTEX);
	float air = smoothstep(220.0, 980.0, dist);
	float far = clamp(air * (0.2 + aerial) + far_fade * air, 0.0, 1.0);
	rock_w *= 1.0 - smoothstep(0.2, 0.65, far);
	col = mix(col, rock, rock_w);
	vec3 far_green = vec3(0.3, 0.58, 0.62);
	col = mix(col, far_green, smoothstep(0.2, 1.0, far) * 0.45);
	float mist = clamp(smoothstep(110.0, 260.0, wpos.y) * dawn, 0.0, 0.25);
	col = mix(col, mist_color, mist * (1.0 - night * 0.5));
	// a serra não recebe luz ambiente: escurece o albedo para não estourar com o sol forte do cartoon
	ALBEDO = col * 0.62;

	vec3 tn = canopy_nrm(wpos.xz);
	vec3 t = normalize(cross(n, vec3(0.0, 0.0, 1.0)));
	vec3 b = cross(n, t);
	tn.y = -tn.y;
	vec3 rn = tri(rock_nor, 0.045) * 2.0 - 1.0;
	vec3 wn = normalize(t * tn.x + b * tn.y + n * tn.z);
	// O relevo da copa só sugere volume. Sozinho, a meia-lua vira sombra preta.
	wn = normalize(mix(n, wn, 0.12));
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
	float shade = mix(0.55, 1.0, smoothstep(0.42, 0.5, wrap));
	DIFFUSE_LIGHT += LIGHT_COLOR * shade * ATTENUATION;
	SPECULAR_LIGHT = vec3(0.0);
}

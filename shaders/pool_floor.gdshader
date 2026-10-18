shader_type spatial;
// Azulejos da piscina com cáusticas animadas (luz refratada pela água).
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float tile = 0.5;
uniform float caustic_strength = 1.4;
uniform float day = 1.0;
varying vec3 wpos;
varying vec3 wnrm;
vec2 h2(vec2 p){ p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float voronoi(vec2 x, float t){
	vec2 n = floor(x); vec2 f = fract(x); float md = 8.0;
	for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++){
		vec2 g = vec2(float(i), float(j));
		vec2 o = h2(n + g); o = 0.5 + 0.5 * sin(t + 6.2831 * o);
		vec2 r = g + o - f; md = min(md, dot(r, r));
	}
	return sqrt(md);
}
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz); }
void fragment(){
	vec3 an = abs(wnrm);
	vec2 uv = an.y > 0.5 ? wpos.xz : (an.x > 0.5 ? wpos.zy : wpos.xy);
	ALBEDO = texture(albedo_tex, uv * tile).rgb;
	NORMAL_MAP = texture(normal_tex, uv * tile).rgb;
	ROUGHNESS = 0.25;
	vec2 cuv = wpos.xz * 1.6 + vec2(wpos.y * 0.3);
	float c = pow(1.0 - voronoi(cuv, TIME * 1.1), 6.0) + pow(1.0 - voronoi(cuv * 1.3 + 3.1, TIME * 0.8), 6.0) * 0.7;
	float depth_fade = clamp(-wpos.y / 1.4, 0.2, 1.0);
	EMISSION = vec3(0.85, 1.0, 1.0) * c * caustic_strength * day * depth_fade * 0.35;
}

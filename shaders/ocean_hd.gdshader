shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_always, diffuse_toon, specular_toon;
// Mar cartoon (v0.7): faixas de cor por profundidade (turquesa → azul → azul-marinho), espuma branca
// recortada na arrebentação, linhas de onda subindo a praia e brilhos que piscam ao sol.
uniform sampler2D depth_tex : hint_depth_texture, filter_linear_mipmap;
uniform vec3 shallow : source_color = vec3(0.3, 0.95, 0.88);
uniform vec3 mid : source_color = vec3(0.08, 0.72, 0.9);
uniform vec3 deep : source_color = vec3(0.04, 0.4, 0.78);
uniform vec3 foam_col : source_color = vec3(1.0, 1.0, 1.0);
uniform float shore_z = -32.5;
uniform float night = 0.0;
varying vec3 wpos;
varying float crest;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), u.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
vec3 wave(vec2 p, vec2 dir, float amp, float len, float spd, float t){
	float k = 6.2831 / len;
	float f = k * (dot(dir, p) - spd * t);
	return vec3(dir.x * amp * 0.6 * cos(f), amp * sin(f), dir.y * amp * 0.6 * cos(f));
}
vec3 waves(vec2 p, float t){
	return wave(p, normalize(vec2(0.15, 1.0)), 0.22, 10.0, 1.6, t)
		+ wave(p, normalize(vec2(-0.4, 1.0)), 0.1, 4.8, 1.2, t)
		+ wave(p, normalize(vec2(0.7, 0.8)), 0.05, 2.4, 0.9, t);
}
void vertex(){
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float dist = clamp((shore_z - w.z) / 12.0, 0.15, 1.0);
	vec3 d = waves(w.xz, TIME) * dist;
	VERTEX += d;
	crest = d.y;
	float e = 0.25;
	vec3 dx = waves(w.xz + vec2(e, 0), TIME) * dist;
	vec3 dz = waves(w.xz + vec2(0, e), TIME) * dist;
	NORMAL = normalize(cross(vec3(0, dz.y - d.y, e), vec3(e, dx.y - d.y, 0)));
	wpos = w;
}
void fragment(){
	float t = TIME;
	float dr = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, dr, 1.0);
	v.xyz /= v.w;
	float thick = max(0.0, -v.z - (-VERTEX.z));
	float shore_d = shore_z - wpos.z;
	float n = noise(wpos.xz * 0.12 + vec2(t * 0.05, t * 0.08));
	// profundidade "desenhada": mistura espessura real com a distância da praia, em 3 faixas
	float depth_t = clamp(thick / 3.5 + shore_d / 55.0 + (n - 0.5) * 0.12, 0.0, 1.0);
	vec3 col = shallow;
	col = mix(col, mid, smoothstep(0.22, 0.26, depth_t));
	col = mix(col, deep, smoothstep(0.6, 0.64, depth_t));
	// manchas claras ondulando (reflexo do céu estilizado)
	float ripple = noise(wpos.xz * vec2(0.35, 0.9) + vec2(t * 0.3, t * 0.5));
	col = mix(col, col * 1.18 + vec3(0.04), smoothstep(0.62, 0.66, ripple) * 0.6);
	// espuma: borda colada na areia + 3 linhas de onda chegando + cristas
	float foam = 1.0 - smoothstep(0.08, 0.14, thick + (n - 0.5) * 0.12);
	float scallop = noise(vec2(wpos.x * 0.18, t * 0.25));
	for (int i = 0; i < 3; i++) {
		float spd = 0.15 + float(i) * 0.05;
		float phase = fract(shore_d * 0.18 - t * spd + float(i) * 0.33 + scallop * 0.2);
		float line = step(0.02, phase) * (1.0 - step(0.075 - float(i) * 0.012, phase));
		float reach = 1.0 - smoothstep(4.0, 10.0, shore_d);
		foam = max(foam, line * reach);
	}
	foam = max(foam, step(0.2, crest) * step(0.55, noise(wpos.xz * 1.2 + t)));
	col = mix(col, foam_col, foam);
	// brilhos do sol: pontinhos brancos que piscam
	float sp = hash(floor(wpos.xz * 2.0) + floor(t * 2.0));
	float sparkle = step(0.997, sp) * (1.0 - night) * smoothstep(3.0, 12.0, shore_d);
	col = mix(col, vec3(1.0), sparkle);
	col *= mix(1.0, 0.45, night);
	ALBEDO = col;
	ROUGHNESS = mix(0.25, 0.9, foam);
	SPECULAR = 0.5;
	METALLIC = 0.0;
	ALPHA = mix(0.82, 1.0, smoothstep(0.0, 0.6, thick) * (1.0 - foam) + foam);
}

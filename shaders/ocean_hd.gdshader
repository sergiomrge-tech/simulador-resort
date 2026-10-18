shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_always, specular_schlick_ggx;
// Mar (PC / Forward+): cor por profundidade real, refração da areia, espuma nas bordas e reflexo do céu.
uniform sampler2D depth_tex : hint_depth_texture, filter_linear_mipmap;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform vec3 shallow : source_color = vec3(0.22, 0.85, 0.78);
uniform vec3 deep : source_color = vec3(0.02, 0.24, 0.40);
uniform vec3 foam_col : source_color = vec3(0.97, 0.99, 1.0);
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
	return wave(p, normalize(vec2(0.15, 1.0)), 0.18, 9.0, 1.6, t)
		+ wave(p, normalize(vec2(-0.4, 1.0)), 0.09, 4.3, 1.2, t)
		+ wave(p, normalize(vec2(0.7, 0.8)), 0.05, 2.1, 0.9, t)
		+ wave(p, normalize(vec2(-0.8, 0.5)), 0.025, 1.1, 0.7, t);
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
	vec2 uv = wpos.xz * 0.35;
	float n1 = noise(uv + vec2(t * 0.15, t * 0.31));
	float n2 = noise(uv * 2.3 - vec2(t * 0.22, t * 0.12));
	float n3 = noise(uv * 6.0 + vec2(t * 0.4, -t * 0.3));
	vec3 nrm = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 0.3 + (n3 - 0.5) * 0.12, 0.0, (n2 - 0.5) * 0.3, 0.0)).xyz);
	// espessura da água até o fundo
	float dr = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, dr, 1.0);
	v.xyz /= v.w;
	float thick = max(0.0, -v.z - (-VERTEX.z));
	vec2 ruv = SCREEN_UV + (nrm.xy) * 0.025 * clamp(thick, 0.0, 1.0);
	float dr2 = texture(depth_tex, ruv).r;
	vec4 v2 = INV_PROJECTION_MATRIX * vec4(ruv * 2.0 - 1.0, dr2, 1.0);
	v2.xyz /= v2.w;
	if (-v2.z < -VERTEX.z) { ruv = SCREEN_UV; }
	vec3 behind = texture(screen_tex, ruv).rgb;
	float far_t = clamp((shore_z - wpos.z) / 70.0, 0.0, 1.0);
	vec3 water = mix(shallow, deep, clamp(thick / 5.0 + far_t * 0.6, 0.0, 1.0));
	float absorb = 1.0 - exp(-thick * 1.5);
	vec3 col = mix(behind * mix(vec3(1.0), shallow, 0.8) * 0.85, water, absorb);
	// espuma: borda rasa, duas linhas de arrebentação subindo a praia, cristas
	float edge = 1.0 - smoothstep(0.0, 0.16 + n2 * 0.14, thick);
	float shore_d = shore_z - wpos.z;
	float scallop = noise(vec2(wpos.x * 0.16, t * 0.22));
	float foam = edge * smoothstep(0.25, 0.7, n3 + 0.25);
	for (int i = 0; i < 3; i++) {
		float spd = 0.16 + float(i) * 0.05;
		float phase = fract(shore_d * 0.2 - t * spd + float(i) * 0.33 + scallop * 0.18);
		float line = smoothstep(0.0, 0.05, phase) * (1.0 - smoothstep(0.07, 0.28, phase));
		float reach = smoothstep(9.0, 0.15, shore_d);
		foam += line * reach * (0.85 - float(i) * 0.18);
	}
	foam += smoothstep(0.14, 0.26, crest) * 0.28 * n2;
	foam = clamp(foam, 0.0, 1.0);
	col = mix(col, foam_col, foam);
	col *= mix(1.0, 0.3, night);
	ALBEDO = col;
	NORMAL = nrm;
	ROUGHNESS = mix(0.03, 0.7, foam);
	SPECULAR = 0.65;
	METALLIC = 0.0;
	ALPHA = 1.0;
}

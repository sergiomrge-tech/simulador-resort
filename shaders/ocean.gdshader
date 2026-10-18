shader_type spatial;
render_mode cull_back, specular_schlick_ggx;
// Mar do Nordeste: ondas somadas, cor rasa->funda pela distância da praia, espuma na arrebentação.
uniform vec3 shallow : source_color = vec3(0.16, 0.78, 0.74);
uniform vec3 deep : source_color = vec3(0.02, 0.27, 0.42);
uniform vec3 foam_col : source_color = vec3(0.96, 0.98, 1.0);
uniform float shore_z = -36.0;      // linha da água (z do mundo)
uniform float deep_dist = 70.0;
uniform float time_scale = 1.0;
uniform float night = 0.0;          // 0 dia, 1 noite
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
void vertex(){
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME * time_scale;
	float dist = clamp((shore_z - w.z) / 12.0, 0.15, 1.0);
	vec3 d = vec3(0.0);
	d += wave(w.xz, normalize(vec2(0.15, 1.0)), 0.16, 9.0, 1.6, t);
	d += wave(w.xz, normalize(vec2(-0.4, 1.0)), 0.08, 4.3, 1.2, t);
	d += wave(w.xz, normalize(vec2(0.7, 0.8)), 0.04, 2.1, 0.9, t);
	d *= dist;
	VERTEX.y += d.y;
	VERTEX.x += d.x;
	VERTEX.z += d.z;
	crest = d.y;
	// normal aproximada
	float e = 0.4;
	vec3 dx = wave(w.xz + vec2(e,0), normalize(vec2(0.15,1.0)), 0.16, 9.0, 1.6, t) + wave(w.xz + vec2(e,0), normalize(vec2(-0.4,1.0)), 0.08, 4.3, 1.2, t);
	vec3 dz = wave(w.xz + vec2(0,e), normalize(vec2(0.15,1.0)), 0.16, 9.0, 1.6, t) + wave(w.xz + vec2(0,e), normalize(vec2(-0.4,1.0)), 0.08, 4.3, 1.2, t);
	vec3 d0 = wave(w.xz, normalize(vec2(0.15,1.0)), 0.16, 9.0, 1.6, t) + wave(w.xz, normalize(vec2(-0.4,1.0)), 0.08, 4.3, 1.2, t);
	vec3 n = normalize(cross(vec3(0, (dz.y - d0.y) * dist, e), vec3(e, (dx.y - d0.y) * dist, 0)));
	NORMAL = n;
	wpos = w;
}
void fragment(){
	float t = TIME * time_scale;
	float dist = clamp((shore_z - wpos.z) / deep_dist, 0.0, 1.0);
	vec3 col = mix(shallow, deep, pow(dist, 0.6));
	// ondulação fina
	vec2 uv = wpos.xz * 0.35;
	float n1 = noise(uv + vec2(t * 0.15, t * 0.31));
	float n2 = noise(uv * 2.3 - vec2(t * 0.22, t * 0.12));
	NORMAL = normalize(NORMAL + vec3((n1 - 0.5) * 0.25, 0.0, (n2 - 0.5) * 0.25));
	// duas linhas de arrebentação e cristas
	float shore_d = shore_z - wpos.z;
	float scallop = noise(vec2(wpos.x * 0.16, t * 0.22));
	float foam = 0.0;
	for (int i = 0; i < 3; i++) {
		float phase = fract(shore_d * 0.2 - t * (0.16 + float(i) * 0.05) + float(i) * 0.33 + scallop * 0.18);
		float line = smoothstep(0.0, 0.05, phase) * (1.0 - smoothstep(0.07, 0.28, phase));
		foam += line * smoothstep(9.0, 0.15, shore_d) * (0.9 - float(i) * 0.2);
	}
	foam += smoothstep(0.12, 0.22, crest) * 0.35 * n2;
	foam = clamp(foam, 0.0, 1.0);
	col = mix(col, foam_col, foam);
	col *= mix(1.0, 0.35, night);
	ALBEDO = col;
	ROUGHNESS = mix(0.06, 0.6, foam);
	METALLIC = 0.0;
	SPECULAR = 0.6;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	EMISSION = vec3(0.35, 0.55, 0.7) * fres * 0.25 * (1.0 - night);
}

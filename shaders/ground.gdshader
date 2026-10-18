shader_type spatial;
// Areia seca -> areia molhada perto da água, com variação para quebrar repetição.
uniform sampler2D dry_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D dry_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D wet_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D wet_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float tile = 0.22;
uniform float wet_start = -27.0;
uniform float wet_end = -34.0;
uniform float rain_wet = 0.0;
varying vec3 wpos;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), u.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment(){
	vec2 uv = wpos.xz * tile;
	vec2 uv2 = wpos.xz * tile * 0.37 + vec2(0.31, 0.77);
	float var = noise(wpos.xz * 0.08) * 0.6 + noise(wpos.xz * 0.31) * 0.4;
	vec3 dry = mix(texture(dry_tex, uv).rgb, texture(dry_tex, uv2).rgb, 0.4);
	dry *= mix(0.94, 1.05, var);
	// areia bege clara; o pôr do sol esquenta a luz, não o albedo
	dry = mix(dry * vec3(1.02, 0.99, 0.94), vec3(0.84, 0.78, 0.68), 0.34);
	vec3 wet = texture(wet_tex, uv * 0.8).rgb * vec3(0.78, 0.8, 0.78);
	float shore_n = (noise(wpos.xz * 0.11) - 0.5) * 3.4 + (noise(wpos.xz * 0.33) - 0.5) * 1.6;
	float w = smoothstep(wet_start, wet_end, wpos.z + shore_n);
	w = max(w, rain_wet * (0.42 + 0.2 * noise(wpos.xz * 0.15)));
	vec3 col = mix(dry, wet * vec3(0.72, 0.78, 0.8), w);
	// linha de espuma que a onda deixa na areia molhada
	float wash = smoothstep(0.28, 0.48, w) * (1.0 - smoothstep(0.55, 0.82, w));
	wash *= smoothstep(0.35, 0.75, noise(vec2(wpos.x * 0.42, wpos.z * 0.9)));
	col = mix(col, vec3(0.94, 0.95, 0.93), wash * 0.7);
	// conchinhas miúdas na areia seca
	float speckle = step(0.985, noise(wpos.xz * 3.7));
	col = mix(col, vec3(0.85, 0.8, 0.7), speckle * (1.0 - w));
	ALBEDO = col;
	vec3 nd = texture(dry_nor, uv).rgb;
	vec3 nw = texture(wet_nor, uv * 0.8).rgb;
	vec3 nmap = mix(nd, nw, w);
	float rip = noise(wpos.xz * 2.8) - 0.5;
	float rip2 = noise(wpos.xz * 1.1 + vec2(3.0, 1.7)) - 0.5;
	nmap.x += rip * 0.22 * (1.0 - w * 0.45);
	nmap.y += rip2 * 0.22 * (1.0 - w * 0.45);
	NORMAL_MAP = nmap;
	NORMAL_MAP_DEPTH = mix(0.85, 1.05, w);
	ROUGHNESS = mix(0.97, 0.18, w);
	SPECULAR = mix(0.12, 0.62, w);
}

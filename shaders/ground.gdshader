shader_type spatial;
// Areia seca -> areia molhada perto da água, com variação para quebrar repetição.
uniform sampler2D dry_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D dry_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D wet_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D wet_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float tile = 0.22;
uniform float wet_start = -27.0;
uniform float wet_end = -34.0;
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
	dry *= mix(0.92, 1.07, var);
	dry = dry * vec3(1.22, 1.12, 0.95);  // areia clara e quente do Nordeste
	vec3 wet = texture(wet_tex, uv * 0.8).rgb * 0.85;
	float w = smoothstep(wet_start, wet_end, wpos.z + (noise(wpos.xz * 0.2) - 0.5) * 2.5);
	ALBEDO = mix(dry, wet, w);
	vec3 nd = texture(dry_nor, uv).rgb;
	vec3 nw = texture(wet_nor, uv * 0.8).rgb;
	NORMAL_MAP = mix(nd, nw, w);
	NORMAL_MAP_DEPTH = 0.8;
	ROUGHNESS = mix(0.95, 0.35, w);
}

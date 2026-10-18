shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_always;
// Água da piscina (PC): refração dos azulejos, absorção por profundidade e reflexo.
uniform sampler2D depth_tex : hint_depth_texture, filter_linear_mipmap;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform vec3 tint : source_color = vec3(0.45, 0.88, 0.92);
uniform vec3 deep_tint : source_color = vec3(0.05, 0.45, 0.6);
varying vec3 wpos;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), u.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
void vertex(){
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += sin(wpos.x * 1.7 + TIME * 1.3) * 0.012 + cos(wpos.z * 2.1 + TIME) * 0.01;
}
void fragment(){
	vec2 uv = wpos.xz * 1.3;
	float n1 = noise(uv + TIME * vec2(0.3, 0.2));
	float n2 = noise(uv * 1.9 - TIME * vec2(0.25, 0.35));
	vec3 nrm = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 0.25, 0.0, (n2 - 0.5) * 0.25, 0.0)).xyz);
	float dr = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, dr, 1.0);
	v.xyz /= v.w;
	float thick = max(0.0, -v.z + VERTEX.z);
	vec2 ruv = SCREEN_UV + nrm.xy * 0.02;
	vec3 behind = texture(screen_tex, ruv).rgb;
	float absorb = 1.0 - exp(-thick * 0.6);
	ALBEDO = mix(behind * tint, deep_tint, absorb * 0.7);
	NORMAL = nrm;
	ROUGHNESS = 0.02;
	SPECULAR = 0.7;
	ALPHA = 1.0;
}

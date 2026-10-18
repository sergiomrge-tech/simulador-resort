shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_opaque;
// Água da piscina: turquesa clara, ondulação suave e reflexo (fresnel).
uniform vec3 tint : source_color = vec3(0.35, 0.85, 0.9);
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
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 0.35, 0.0, (n2 - 0.5) * 0.35, 0.0)).xyz);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	float caust = smoothstep(0.55, 0.95, n1 * n2 * 2.0);
	ALBEDO = tint + caust * 0.15;
	ALPHA = mix(0.55, 0.92, fres);
	ROUGHNESS = 0.04;
	SPECULAR = 0.7;
}

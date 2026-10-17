shader_type spatial;
// Cúpula opaca. A cor chega em sRGB pelo INSTANCE_CUSTOM; sem emissão e sem alpha.
render_mode cull_back, diffuse_burley, specular_schlick_ggx, depth_draw_opaque, fog_disabled, ambient_light_disabled;

uniform float aerial = 0.25;
uniform float dawn = 0.0;
uniform vec3 mist_color : source_color = vec3(0.75, 0.82, 0.88);
uniform vec3 haze_color : source_color = vec3(0.55, 0.70, 0.84);
varying vec3 albedo;
varying vec3 wpos;
varying vec3 wnor;

vec3 to_lin(vec3 c) {
	vec3 lo = c / 12.92;
	vec3 hi = pow((c + vec3(0.055)) / 1.055, vec3(2.4));
	return mix(lo, hi, step(vec3(0.04045), c));
}

void vertex() {
	vec3 tint = INSTANCE_CUSTOM.rgb;
	if (dot(tint, tint) < 0.002) {
		tint = vec3(0.239, 0.353, 0.204);
	}
	albedo = to_lin(tint);
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float up = clamp(wnor.y * 0.7 + 0.28, 0.0, 1.0);
	vec3 col = albedo * mix(0.62, 1.0, up);
	float dist = length(VERTEX);
	float air = clamp(smoothstep(200.0, 860.0, dist) * aerial, 0.0, 0.8);
	float luma = dot(col, vec3(0.30, 0.52, 0.18));
	col = mix(col, vec3(luma), air * 0.65);
	col *= mix(1.0, 0.75, air);
	float mist = smoothstep(110.0, 240.0, wpos.y) * dawn * 0.35;
	col = mix(col, mist_color, mist);
	ALBEDO = col;
	ROUGHNESS = 0.94;
	SPECULAR = 0.03;
}

void light() {
	float wrap = clamp(dot(NORMAL, LIGHT) * 0.5 + 0.5, 0.0, 1.0);
	DIFFUSE_LIGHT += LIGHT_COLOR * wrap * wrap * ATTENUATION;
	SPECULAR_LIGHT = vec3(0.0);
}

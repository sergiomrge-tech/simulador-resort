shader_type spatial;
// Copas baixas, sem tronco. A cor vem do vértice; INSTANCE_CUSTOM pinta a flor no topo.
render_mode cull_disabled, diffuse_burley, fog_disabled;

uniform float aerial = 0.3;
uniform float dawn = 0.0;
uniform vec3 mist_color : source_color = vec3(0.78, 0.86, 0.90);
uniform vec3 haze_color : source_color = vec3(0.45, 0.62, 0.82);
varying vec3 albedo;
varying vec3 wpos;

void vertex() {
	vec3 tint = INSTANCE_CUSTOM.rgb;
	if (dot(tint, tint) < 0.04) {
		tint = vec3(0.75, 1.0, 0.65);
	}
	float flower = INSTANCE_CUSTOM.a;
	vec3 leaf = COLOR.rgb;
	if (dot(leaf, leaf) < 0.02) {
		leaf = vec3(0.09, 0.34, 0.07);
	}
	leaf *= mix(tint, vec3(0.7, 1.0, 0.55), flower);
	albedo = mix(leaf, tint, flower * step(0.5, COLOR.a + flower));
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float dist = length(VERTEX);
	float air = clamp(smoothstep(120.0, 700.0, dist) * aerial, 0.0, 0.82);
	float mist = smoothstep(34.0, 90.0, wpos.y) * dawn * 0.7;
	vec3 col = mix(albedo, mist_color, mist);
	col = mix(col, haze_color, air);
	ALBEDO = col;
	EMISSION = col * 0.42;
	ROUGHNESS = 0.92;
	SPECULAR = 0.04;
	BACKLIGHT = vec3(0.16, 0.28, 0.07);
}

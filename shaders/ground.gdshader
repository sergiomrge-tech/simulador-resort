shader_type spatial;
render_mode diffuse_toon, specular_toon;
// Areia cartoon (v0.7): cor chapada quente com manchas suaves em dois tons, faixa de areia molhada
// recortada, linha de espuma que a onda deixa e conchinhas coloridas.
// (as texturas antigas continuam como uniforms só para o código que as define não reclamar)
uniform sampler2D dry_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D dry_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D wet_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D wet_nor : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float tile = 0.22;
uniform float wet_start = -27.0;
uniform float wet_end = -34.0;
uniform float rain_wet = 0.0;
uniform vec3 sand_light : source_color = vec3(1.0, 0.9, 0.64);
uniform vec3 sand_dark : source_color = vec3(0.98, 0.8, 0.54);
uniform vec3 sand_wet : source_color = vec3(0.86, 0.66, 0.46);
uniform vec3 foam : source_color = vec3(1.0, 1.0, 0.98);
varying vec3 wpos;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), u.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
void vertex(){ wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment(){
	float big = noise(wpos.xz * 0.06) * 0.65 + noise(wpos.xz * 0.21) * 0.35;
	// duas cores com borda macia: dá o ar de "pintado" sem virar textura realista
	vec3 dry = mix(sand_light, sand_dark, smoothstep(0.52, 0.58, big));
	// ondinhas de vento desenhadas como traços claros
	float streak = smoothstep(0.92, 0.97, sin(wpos.x * 1.3 + noise(wpos.xz * 0.4) * 6.0 + wpos.z * 0.4) * 0.5 + 0.5);
	dry = mix(dry, sand_light * 1.04, streak * 0.35);
	float shore_n = (noise(wpos.xz * 0.11) - 0.5) * 3.0 + (noise(wpos.xz * 0.33) - 0.5) * 1.2;
	float w = smoothstep(wet_start, wet_end, wpos.z + shore_n);
	w = max(w, rain_wet * 0.6);
	float wet_band = smoothstep(0.35, 0.42, w);
	vec3 col = mix(dry, sand_wet, wet_band);
	// linha de espuma branca recortada na beira da areia molhada
	float wash = smoothstep(0.3, 0.34, w) * (1.0 - smoothstep(0.4, 0.44, w));
	wash *= step(0.4, noise(vec2(wpos.x * 0.5, TIME * 0.2)));
	col = mix(col, foam, wash);
	// conchinhas coloridas
	float sp = noise(wpos.xz * 4.1);
	float shell = step(0.988, sp) * (1.0 - wet_band);
	vec3 shell_c = mix(vec3(1.0, 0.62, 0.55), vec3(1.0, 0.95, 0.85), step(0.5, hash(floor(wpos.xz * 4.1))));
	col = mix(col, shell_c, shell);
	ALBEDO = col;
	ROUGHNESS = mix(0.95, 0.35, wet_band);
	SPECULAR = mix(0.05, 0.4, wet_band);
}

shader_type spatial;
render_mode diffuse_toon, specular_toon;
// Pinta o manequim Quaternius com zonas gravadas em COLOR.r (ver tools/color_zones.py).
instance uniform vec4 skin : source_color = vec4(0.78, 0.55, 0.40, 1.0);
instance uniform vec4 shirt : source_color = vec4(0.9, 0.3, 0.3, 1.0);
instance uniform vec4 shorts : source_color = vec4(0.2, 0.3, 0.6, 1.0);
instance uniform vec4 hair : source_color = vec4(0.1, 0.07, 0.05, 1.0);
uniform vec4 sandals : source_color = vec4(0.25, 0.15, 0.08, 1.0);
// v0.9.3: calçados (zona 4 = cabedal/tira, zona 5 = sola)
instance uniform vec4 shoes : source_color = vec4(0.25, 0.15, 0.08, 1.0);
instance uniform vec4 sole : source_color = vec4(0.95, 0.93, 0.88, 1.0);
// v0.7.3: estampa da camisa (0 lisa, 1 listras, 2 bolinhas, 3 floral havaiana, 4 xadrez) e cor secundária
instance uniform float pattern = 0.0;
instance uniform vec4 shirt2 : source_color = vec4(1.0, 1.0, 1.0, 1.0);
instance uniform float shorts_pattern = 0.0;
varying float zone;
varying vec3 opos;
uniform float garment_zone = -1.0;
uniform bool use_fabric = false;
uniform sampler2D fabric_texture : source_color;
void vertex(){ zone = garment_zone >= 0.0 ? garment_zone : COLOR.r * 255.0 / 32.0; opos = VERTEX; }

float flower(vec2 p) {
	vec2 g = fract(p) - 0.5;
	float a = atan(g.y, g.x);
	float r = length(g);
	float petals = 0.22 + 0.09 * cos(a * 5.0);
	float f = 1.0 - smoothstep(petals - 0.02, petals, r);
	float center = 1.0 - smoothstep(0.06, 0.08, r);
	return max(f, center * 2.0);
}
void fragment(){
	vec3 c = skin.rgb;
	float r = 0.6;
	if (zone > 0.5 && zone < 1.5) {
		c = shirt.rgb; r = 0.85;
		int pt = int(pattern + 0.5);
		if (pt == 1) {
			c = mix(c, shirt2.rgb, step(0.5, fract(opos.y * 14.0)));
		} else if (pt == 2) {
			vec2 q = vec2(opos.x * 18.0 + opos.z * 18.0, opos.y * 18.0);
			c = mix(c, shirt2.rgb, 1.0 - step(0.28, length(fract(q) - 0.5)));
		} else if (pt == 3) {
			vec2 q = vec2(opos.x * 9.0 + opos.z * 9.0, opos.y * 9.0);
			float f = flower(q) + flower(q + vec2(0.5, 0.37));
			c = mix(c, shirt2.rgb, clamp(f, 0.0, 1.0));
			c = mix(c, vec3(1.0, 0.92, 0.3), step(1.5, f));
		} else if (pt == 4) {
			float a = step(0.5, fract(opos.x * 8.0 + opos.z * 8.0));
			float b = step(0.5, fract(opos.y * 8.0));
			c = mix(c, shirt2.rgb, (a + b) * 0.35);
		}
	}
	else if (zone > 1.5 && zone < 2.5) {
		c = shorts.rgb; r = 0.9;
		if (shorts_pattern > 0.5) {
			c = mix(c, c * 0.7 + vec3(0.25), step(0.82, fract((opos.x + opos.z) * 6.0)) );
		}
	}
	else if (zone > 2.5 && zone < 3.5) { c = hair.rgb; r = 0.5; }
	else if (zone > 3.5 && zone < 4.5) { c = shoes.rgb; r = 0.7; }
	else if (zone > 4.5) { c = sole.rgb; r = 0.8; }
	if (use_fabric) {
		vec3 fabric = texture(fabric_texture, UV).rgb;
		float detail = dot(fabric, vec3(0.3, 0.59, 0.11));
		c *= clamp(detail * 1.5, 0.45, 1.15);
	}
	// v0.7 cartoon: cores um pouco mais saturadas
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	ALBEDO = mix(vec3(l), c, 1.2);
	ROUGHNESS = r;
	RIM = 0.3;
	RIM_TINT = 0.5;
	SPECULAR = 0.3;
}

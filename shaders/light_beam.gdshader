shader_type spatial;
// v0.9.5: facho do farol visível na névoa: aditivo, mais forte perto da lente e no meio do cone, some nas bordas e na ponta.
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform vec4 col : source_color = vec4(1.0, 0.93, 0.7, 1.0);
uniform float strength = 0.5;
uniform float night = 1.0;
void fragment() {
	float along = UV.y;                       // 0 na boca larga, 1 junto da lente (CylinderMesh: topo = v 0)
	float edge = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float a = pow(edge, 1.6) * pow(clamp(along, 0.0, 1.0), 1.3) * strength * night;
	ALBEDO = col.rgb * a;
}

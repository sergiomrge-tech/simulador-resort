shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled;
void fragment() {
    vec2 p=UV;
    float taper=smoothstep(0.0,.12,p.x)*(1.0-smoothstep(.72,1.0,p.x));
    float width=1.0-abs(p.y*2.0-1.0);
    float foam=.4+.6*sin(p.x*65.0+sin(p.y*25.0)-TIME*3.0);
    ALBEDO=vec3(.78,.84,.80);
    ALPHA=taper*width*foam*.28;
}

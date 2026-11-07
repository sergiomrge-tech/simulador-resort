shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
uniform float age=0.0;
void fragment(){
 vec2 p=(UV-.5)*2.0;float d=length(p);float ring=1.0-smoothstep(.025,.10,abs(d-(.12+age*.13)));
 float ring2=1.0-smoothstep(.02,.07,abs(d-(.07+age*.095)));
 float churn=(1.0-smoothstep(.1,.40,d))*(.6+.4*sin(p.x*65.0+sin(p.y*47.0)));
 ALBEDO=vec3(.85,.92,.90);ALPHA=max(max(ring,ring2)*.7,churn)*clamp(1.0-age/6.0,0.0,1.0);
}

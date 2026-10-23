shader_type spatial;
render_mode unshaded, cull_disabled;
void fragment() {
    vec2 uv=UV;
    float wave=.012*sin(uv.x*24.0+TIME*.8)+.008*sin(uv.x*45.0-TIME);
    float horizon=.53+wave;
    vec3 sky=mix(vec3(.72,.80,.78),vec3(.33,.53,.64),smoothstep(.53,1.0,uv.y));
    vec3 sea=mix(vec3(.10,.28,.31),vec3(.24,.48,.51),uv.y*1.5);
    float foam=1.0-smoothstep(.0,.018,abs(fract(uv.y*7.0+wave+TIME*.035)-.5));
    sea+=foam*.10;
    vec3 color=mix(sea,sky,smoothstep(horizon-.003,horizon+.003,uv.y));
    color=mix(vec3(.65,.58,.42),color,smoothstep(.02,.13+sin(uv.x*4.0)*.06,uv.y));
    ALBEDO=color*(.97+.03*sin(uv.y*720.0));
    EMISSION=color*.35;
}

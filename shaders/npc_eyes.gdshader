shader_type spatial;
render_mode diffuse_burley;
uniform sampler2D eye_texture : source_color;
uniform bool textured = false;
uniform vec4 tint : source_color = vec4(1.0);
uniform float center_y = 1.69;
uniform float blink_offset = 0.0;
void vertex() {
    float t = mod(TIME + blink_offset, 4.7);
    float blink = smoothstep(0.0,0.075,t) * (1.0-smoothstep(0.105,0.20,t));
    VERTEX.y = center_y + (VERTEX.y-center_y)*(1.0-0.94*blink);
}
void fragment() {
    ALBEDO = tint.rgb * (textured ? texture(eye_texture, UV).rgb : vec3(1.0));
    ROUGHNESS = 0.36;
    SPECULAR = 0.22;
}

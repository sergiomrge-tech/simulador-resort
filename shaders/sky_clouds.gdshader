shader_type sky;
uniform float clock=0.0;
uniform vec3 cloud_color:source_color=vec3(.91,.92,.90);
uniform vec3 top_color:source_color=vec3(.1,.5,.9);
uniform vec3 horizon_color:source_color=vec3(.7,.85,.9);
uniform vec3 sun_dir=vec3(0,1,0);
uniform vec3 sun_color:source_color=vec3(1,.95,.8);
uniform float sun_energy=1.0;
void sky(){
 float h=max(EYEDIR.y,0.0);
 vec3 base=mix(horizon_color,top_color,pow(h,.6));
 float density=0.0;
 for(int i=0;i<14;i++){
  float a=float(i)*2.39996+clock*.0004;
  float elevation=.23+.40*(.5+.5*sin(float(i)*7.13));
  vec3 center=normalize(vec3(cos(a),elevation,sin(a)));
  vec3 tangent=vec3(-sin(a),0,cos(a));
  for(int j=0;j<5;j++){
   float k=float(j)-2.0;
   vec3 lobe=normalize(center+tangent*k*.055+vec3(0,.025*cos(k*2.1+float(i)),0));
   float d=max(0.0,1.0-dot(EYEDIR,lobe));
   density+=exp(-d*(210.0+float(j%2)*90.0))*.38;
  }
 }
 float cloud=smoothstep(.16,.78,density)*smoothstep(.025,.12,h);
 base+=sun_color*pow(max(0.0,dot(EYEDIR,normalize(sun_dir))),500.0)*sun_energy;
 COLOR=mix(base,cloud_color*mix(.79,1.0,smoothstep(.15,.9,density)),cloud*.92);
}

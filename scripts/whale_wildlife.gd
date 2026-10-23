extends Node3D
var clock := 0.0
var whales: Array = []
var clouds: Node3D
var cloud_mat: ShaderMaterial
var last_phase: Array = [-1.0,-1.0]
func _ready() -> void:
	name = "WhaleWildlife"
	for i in 2:
		var pivot := Node3D.new()
		add_child(pivot)
		Real.place(pivot,"g:humpback_whale",Vector3.ZERO,-1.4,0,Color.WHITE,0,false)
		var foam := MeshInstance3D.new()
		var plane := PlaneMesh.new()
		plane.size = Vector2(28,28)
		foam.mesh = plane
		var material := ShaderMaterial.new()
		material.shader = load("res://shaders/whale_foam.gdshader")
		foam.material_override = material
		add_child(foam)
		var spray := MultiMeshInstance3D.new()
		var multi := MultiMesh.new()
		multi.transform_format = MultiMesh.TRANSFORM_3D
		var droplet := SphereMesh.new()
		droplet.radius=.22
		droplet.height=.8
		droplet.radial_segments=8
		droplet.rings=4
		droplet.material=B.flat(Color(.80,.89,.89),.3)
		multi.mesh=droplet
		multi.instance_count=100
		spray.multimesh=multi
		add_child(spray)
		var sound:=AudioStreamPlayer3D.new()
		sound.stream=load("res://assets/audio/whale_splash.wav")
		sound.bus="SFX"
		sound.volume_db=-12
		sound.unit_size=40
		sound.max_distance=220
		add_child(sound)
		whales.append({"body":pivot,"foam":foam,"spray":spray,"sound":sound,"origin":Vector3(-12+i*83,-.3,-139-i*17)})
	clouds=Node3D.new()
	clouds.name="CloudSky"
	add_child(clouds)
	cloud_mat=ShaderMaterial.new()
	cloud_mat.shader=load("res://shaders/sky_clouds.gdshader")
	get_parent().day.env.sky.sky_material=cloud_mat
	update_scene(0)
func _process(delta: float) -> void:
	if Core.in_game and not Core.paused and not get_tree().paused:
		clock+=delta
	update_scene(clock)
func update_scene(time: float) -> void:
	var day=get_parent().day
	cloud_mat.set_shader_parameter("top_color",day.sky_mat.sky_top_color)
	cloud_mat.set_shader_parameter("horizon_color",day.sky_mat.sky_horizon_color)
	cloud_mat.set_shader_parameter("sun_dir",day.sun.global_basis.z)
	cloud_mat.set_shader_parameter("sun_color",day.sun.light_color)
	cloud_mat.set_shader_parameter("sun_energy",day.sun.light_energy)
	var night:=1.0 if Core.minutes<360 or Core.minutes>=19*60 else 0.0
	cloud_mat.set_shader_parameter("clock",time)
	cloud_mat.set_shader_parameter("cloud_color",Color(.20,.23,.29) if night>0 else (Color(.49,.52,.55) if Core.weather=="rain" else Color(.91,.92,.90)))
	for i in whales.size():
		var item: Dictionary=whales[i]
		var p:=fposmod(time+float(i)*13.0,32.0)
		var origin: Vector3=item.origin
		# Four-second launch and fall, followed by six seconds of water response.
		var u:=clampf(p/4.0,0,1)
		item.body.visible=p<4
		item.body.position=origin+Vector3(lerpf(-6,6,u),-5+14*sin(PI*u),0)
		item.body.rotation=Vector3(.22*sin(u*PI),.25+i*.4,lerpf(1.1,-.22,u))
		var impact:=p-4.0
		item.foam.visible=impact>=0 and impact<6
		item.foam.position=origin+Vector3(6,.36,0)
		item.foam.material_override.set_shader_parameter("age",maxf(0,impact))
		item.spray.visible=impact>=0 and impact<2.4
		item.spray.position=origin+Vector3(6,.20,0)
		if item.spray.visible:
			for k in 100:
				var a:=float(k)*2.39996
				var speed:=2.0+float(k%9)*.42
				var t:=maxf(0,impact-float(k%7)*.022)
				var pos:=Vector3(cos(a)*speed*t,maxf(0,(8.0+float(k%5))*t-4.9*t*t),sin(a)*speed*t)
				var size:=maxf(.15,1-t/2.4)
				item.spray.multimesh.set_instance_transform(k,Transform3D(Basis.from_scale(Vector3.ONE*size),pos))
		if p>=4 and last_phase[i]>=0 and last_phase[i]<4 and not Core.paused and not get_parent().audio.muted:
			item.sound.position=origin
			item.sound.play()
		if get_parent().audio.muted: item.sound.stop()
		last_phase[i]=p

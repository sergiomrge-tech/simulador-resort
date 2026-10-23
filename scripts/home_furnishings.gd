extends Node3D
## CC0 furniture, relative to HOME_C; origin at the floor surface.
var tv: Node3D
var stereo: Node3D
var speaker: AudioStreamPlayer3D
var screen: MeshInstance3D
var off_glass: MeshInstance3D
var tv_on := false
var stereo_on := false
var tv_control: Interactable
var stereo_control: Interactable
var sofa: Node3D
var console: Node3D
var coffee: Node3D
var _main

func _ready() -> void:
	_main = get_parent().get_parent()
	sofa = _place("g:home_sofa",Vector3(-1.65,0,2.55),0,PI,2.30,"HomeSofa")
	console = _place("g:home_tv_console",Vector3(-1.65,0,.12),0,0,1.35,"TVConsole")
	var top: float = Real._aabb(console).end.y
	tv = _place("g:home_tv",Vector3(-1.94,top,.12),.60,0,0,"HomeTV",false)
	stereo = _place("g:home_stereo",Vector3(-1.25,top,.12),0,0,.48,"HomeStereo",false)
	coffee = _place("g:home_coffee_table",Vector3(-1.65,0,1.37),0,0,.80,"CoffeeTable")
	var table_top: float = Real._aabb(coffee).end.y
	_place("g:home_wood_carving",Vector3(-1.80,table_top,1.35),.13,.3,0,"WoodCarving",false)
	Real.place(self,"book_encyclopedia_set_01",Vector3(-1.47,table_top,1.40),.10,.6)
	var storage := _place("g:home_storage_cabinet",Vector3(-3.10,0,1.05),1.65,PI*.5,0,"HomeStorage")
	for shelf_y in [.753,1.016,1.215,1.408]:
		Real.place(self,"book_encyclopedia_set_01",Vector3(-3.02,shelf_y,1.05),.16,PI*.5)
	var storage_top: float = 1.575 # broad shelf top, below the decorative cornice
	Real.place(self,"potted_plant_04",Vector3(-3.10,storage_top,1.05),.30,.2)
	_place("g:home_clock",Vector3(.65,2.22,-3.25),.44,0,0,"HomeClock",false)
	for mi in tv.find_children("*","MeshInstance3D",true,false):
		if str(mi.name).contains("HomeTVGlassOff"):
			off_glass = mi
		if str(mi.name).contains("HomeTVScreen"):
			screen = mi
			var mat := ShaderMaterial.new()
			mat.shader = load("res://shaders/home_tv.gdshader")
			screen.material_override = mat
			screen.hide()
	tv_control = _control(tv,Vector3(0,.30,0),Vector3(.65,.62,.55),_tv_prompt,toggle_tv)
	stereo_control = _control(stereo,Vector3(0,.16,0),Vector3(.50,.35,.22),_stereo_prompt,toggle_stereo)
	speaker = AudioStreamPlayer3D.new()
	speaker.name = "HomeSpeaker"
	speaker.stream = load("res://assets/audio/music_relax.ogg").duplicate()
	speaker.stream.loop = true
	speaker.bus = "Music"
	speaker.volume_db = -18
	speaker.unit_size = 2.5
	speaker.max_distance = 8
	add_child(speaker)
	speaker.position = stereo.position + Vector3(0,.18,0)

func _place(key: String, at: Vector3, height: float, rot: float, width: float, title: String, solid: bool = true) -> Node3D:
	var tint := Color(1.6,1.5,1.35) if title == "HomeSofa" else Color.WHITE
	var node := Real.place(self,key,at,height,rot,tint,width)
	node.name = title
	if solid:
		var bb: AABB = Real._aabb(node)
		var size := bb.size
		size.x = maxf(.08,size.x-.06)
		size.z = maxf(.08,size.z-.06)
		var body := B.wall(self,size,node.position+node.basis*bb.get_center(),node.rotation.y)
		body.name = title+"Collision"
	return node

func _control(parent: Node3D, at: Vector3, size: Vector3, prompt: Callable, action: Callable) -> Interactable:
	var node := Interactable.new()
	parent.add_child(node)
	node.position = at
	node.prompt_fn = prompt
	node.action_fn = action
	var shape := BoxShape3D.new()
	shape.size = size
	var collision := CollisionShape3D.new()
	collision.shape = shape
	node.add_child(collision)
	return node

func _tv_prompt() -> String:
	return "TV · desligar" if tv_on else "TV · ligar"
func _stereo_prompt() -> String:
	return "Som · desligar" if stereo_on else "Som · ligar"
func toggle_tv() -> void:
	tv_on = not tv_on
	if is_instance_valid(screen): screen.visible = tv_on
	if is_instance_valid(off_glass): off_glass.visible = not tv_on
func toggle_stereo() -> void:
	stereo_on = not stereo_on
	_update_audio()
func _process(_delta: float) -> void:
	_update_audio()
func _update_audio() -> void:
	var audible: bool = stereo_on and not _main.audio.muted
	if audible and not speaker.playing:
		speaker.play(_main.audio.music.get_playback_position())
	elif not audible and speaker.playing:
		speaker.stop()
	var distance: float = _main.player.global_position.distance_to(speaker.global_position) if is_instance_valid(_main.player) else 100.0
	_main.audio.home_duck = 22.0*clampf(1.0-distance/8.0,0,1) if audible else 0.0
func _exit_tree() -> void:
	if is_instance_valid(_main) and is_instance_valid(_main.audio):
		_main.audio.home_duck = 0

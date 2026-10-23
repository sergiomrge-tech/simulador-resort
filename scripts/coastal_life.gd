extends Node3D
## Ambient life, separate from customers, orders and player stock.
const COURT := Vector3(26,0,-23)
var main
var court: Node3D
var ball: Node3D
var players: Array = []
var yacht: Node3D
var cruise: Node3D
var sea_time := 0.0
var rally_time := 0.0
var contacts := [Vector3(-1.25,1.70,-2.25),Vector3(1.25,1.70,2.25),Vector3(1.25,1.70,-2.25),Vector3(-1.25,1.70,2.25)]

func _ready() -> void:
	name = "CoastalLife"
	main = get_parent()
	tree_exiting.connect(_on_tree_exiting)
	court = Node3D.new()
	court.name = "BeachVolleyball"
	add_child(court)
	court.position = Vector3(COURT.x,main.world._height(COURT.x,COURT.z),COURT.z)
	Real.place(court,"g:volley_net",Vector3.ZERO,-1.0,0,Color.WHITE,0,false)
	ball = Real.place(court,"g:volleyball",Vector3.ZERO,.22)
	for side in [-1.0,1.0]:
		B.box(court,Vector3(8,.012,.05),Vector3(0,.015,side*4),B.flat(Color(.66,.57,.41),.95))
		B.box(court,Vector3(.05,.012,8),Vector3(side*4,.015,0),B.flat(Color(.66,.57,.41),.95))
	# Sem o corpo UBC o guest.setup falha; não chame _make só para ambientação.
	var bodies_ready: bool = ResourceLoader.exists("res://assets/models/ubc/Superhero_Male_FullBody.gltf") \
		and ResourceLoader.exists("res://assets/models/ubc/Superhero_Female_FullBody.gltf")
	if bodies_ready:
		for i in 4:
			var g = main.village._make()
			if not is_instance_valid(g) or not is_instance_valid(g._skel):
				if is_instance_valid(g):
					g.queue_free()
				continue
			g.reparent(self)
			g.name = "VolleyPlayer"+str(i+1)
			g.state = "beach_volleyball"
			g.go([])
			g.play("Idle_Loop")
			var arms := SkeletonModifier3D.new()
			arms.set_script(load("res://scripts/volley_arm.gd"))
			arms.guest = g
			g._skel.add_child(arms)
			players.append(g)
	yacht = Real.place(self,"g:pirate_sailship",Vector3.ZERO,-1.0,PI*.5,Color.WHITE,0,false)
	if is_instance_valid(yacht):
		yacht.name = "PassingYacht"
		_wake(yacht,-12,21,4.8)
	var windows := StandardMaterial3D.new()
	windows.albedo_color = Color(.88,.81,.65)
	windows.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	windows.emission_enabled = true
	windows.emission = Color(1,.82,.56)
	windows.emission_energy_multiplier = 1.6
	cruise = Real.place_glow(self,"g:coastal_cruise",Vector3.ZERO,-1.6,PI-.12,windows,false)
	if is_instance_valid(cruise):
		cruise.name = "NightCruise"
	# Anchored cruise ship has no propulsion wake.
	_update_visibility()
	_advance(0)

func _on_tree_exiting() -> void:
	# Evita _process em nós já liberados no encerramento (AV no Windows).
	set_process(false)
	yacht = null
	cruise = null
	ball = null
	players.clear()

func _wake(parent: Node3D, offset: float, length: float, width: float) -> void:
	if not is_instance_valid(parent):
		return
	var wake := MeshInstance3D.new()
	wake.name = "Wake"
	var plane := PlaneMesh.new()
	plane.size = Vector2(length,width)
	wake.mesh = plane
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/coastal_wake.gdshader")
	wake.material_override = mat
	parent.add_child(wake)
	wake.position = Vector3(0,2.5 if parent==yacht else 1.9,offset)
	wake.rotation.y = -PI*.5
	wake.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _process(delta: float) -> void:
	if not is_inside_tree():
		return
	_update_visibility()
	if Core.in_game and not Core.paused and not get_tree().paused:
		_advance(delta)

func _alive(node: Node) -> bool:
	return is_instance_valid(node) and not node.is_queued_for_deletion()

func _update_visibility() -> void:
	var hour: float = Core.minutes/60.0
	var day: bool = hour>=6 and hour<19
	if _alive(yacht):
		yacht.visible = day
	if _alive(cruise):
		cruise.visible = not day
	var playing: bool = hour>=8 and hour<18.5 and Core.weather!="rain"
	if _alive(ball):
		ball.visible = playing
	for g in players:
		if _alive(g):
			g.visible = playing

func _advance(delta: float) -> void:
	sea_time += delta
	rally_time += delta
	if not is_instance_valid(main) or not is_instance_valid(main.world):
		return
	var water_y: float = main.world.WATER_Y
	if _alive(yacht):
		yacht.position = Vector3(-120+fposmod(160+sea_time*.50,360),water_y-2.4+.035*sin(sea_time*1.2),-78)
		yacht.rotation.z = .008*sin(sea_time*.8)
	if _alive(cruise):
		cruise.position = Vector3(40,water_y-5.60,-210)
	if not _alive(ball) or not _alive(court):
		return
	var leg := int(floor(rally_time/1.65))%4
	var t := fposmod(rally_time,1.65)/1.65
	var start: Vector3 = contacts[leg]
	var finish: Vector3 = contacts[(leg+1)%4]
	ball.position = start.lerp(finish,t)+Vector3.UP*(4*2.7*t*(1-t))
	ball.rotation += Vector3(.9,1.1,.4)*delta
	for i in players.size():
		var g = players[i]
		if not _alive(g):
			continue
		var base: Vector3 = court.position+Vector3(contacts[i].x,0,contacts[i].z)
		base.y = main.world._height(base.x,base.z)
		var active: float = (1.0-smoothstep(0,.22,t)) if i==leg else (smoothstep(.80,1,t) if i==(leg+1)%4 else 0.0)
		g.position = base+Vector3(.12*sin(rally_time*1.3+i),.16*sin(active*PI),0)
		var toward: Vector3 = ball.global_position-g.global_position
		g.rotation.y = atan2(toward.x,toward.z)
		g.set_meta("volley_target",court.global_position+contacts[i])
		g.set_meta("volley_weight",active)

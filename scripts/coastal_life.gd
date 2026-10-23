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
	court = Node3D.new()
	court.name = "BeachVolleyball"
	add_child(court)
	court.position = Vector3(COURT.x,main.world._height(COURT.x,COURT.z),COURT.z)
	Real.place(court,"g:volley_net",Vector3.ZERO,-1.0,0,Color.WHITE,0,false)
	ball = Real.place(court,"g:volleyball",Vector3.ZERO,.22)
	for side in [-1.0,1.0]:
		B.box(court,Vector3(8,.012,.05),Vector3(0,.015,side*4),B.flat(Color(.66,.57,.41),.95))
		B.box(court,Vector3(.05,.012,8),Vector3(side*4,.015,0),B.flat(Color(.66,.57,.41),.95))
	for i in 4:
		var g = main.village._make()
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
	yacht.name = "PassingYacht"
	var windows := StandardMaterial3D.new()
	windows.albedo_color = Color(.88,.81,.65)
	windows.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	windows.emission_enabled = true
	windows.emission = Color(1,.82,.56)
	windows.emission_energy_multiplier = 1.6
	cruise = Real.place_glow(self,"g:coastal_cruise",Vector3.ZERO,-1.6,PI-.12,windows,false)
	cruise.name = "NightCruise"
	_wake(yacht,-12,21,4.8)
	# Anchored cruise ship has no propulsion wake.
	_update_visibility()
	_advance(0)
func _wake(parent: Node3D, offset: float, length: float, width: float) -> void:
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
	_update_visibility()
	if Core.in_game and not Core.paused and not get_tree().paused:
		_advance(delta)
func _update_visibility() -> void:
	var hour: float = Core.minutes/60.0
	var day: bool = hour>=6 and hour<19
	yacht.visible = day
	cruise.visible = not day
	var playing: bool = hour>=8 and hour<18.5 and Core.weather!="rain"
	ball.visible = playing
	for g in players: g.visible = playing
func _advance(delta: float) -> void:
	sea_time += delta
	rally_time += delta
	yacht.position = Vector3(-120+fposmod(160+sea_time*.50,360),main.world.WATER_Y-2.4+.035*sin(sea_time*1.2),-78)
	yacht.rotation.z = .008*sin(sea_time*.8)
	cruise.position = Vector3(40,main.world.WATER_Y-5.60,-210)
	var leg := int(floor(rally_time/1.65))%4
	var t := fposmod(rally_time,1.65)/1.65
	var start: Vector3 = contacts[leg]
	var finish: Vector3 = contacts[(leg+1)%4]
	ball.position = start.lerp(finish,t)+Vector3.UP*(4*2.7*t*(1-t))
	ball.rotation += Vector3(.9,1.1,.4)*delta
	for i in players.size():
		var g = players[i]
		var base: Vector3 = court.position+Vector3(contacts[i].x,0,contacts[i].z)
		base.y = main.world._height(base.x,base.z)
		var active: float = (1.0-smoothstep(0,.22,t)) if i==leg else (smoothstep(.80,1,t) if i==(leg+1)%4 else 0.0)
		g.position = base+Vector3(.12*sin(rally_time*1.3+i),.16*sin(active*PI),0)
		var toward: Vector3 = ball.global_position-g.global_position
		g.rotation.y = atan2(toward.x,toward.z)
		g.set_meta("volley_target",court.global_position+contacts[i])
		g.set_meta("volley_weight",active)

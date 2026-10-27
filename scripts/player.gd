extends CharacterBody3D


const SPEED: = 3.4
const SPRINT: = 1.7
const PAD_LOOK: = 2.6
const EYE: = 1.65
var yaw: = 0.0
var pitch: = 0.0
var move_input: = Vector2.ZERO
var look_sens_touch: = 0.0045
var look_sens_mouse: = 0.0025
var cam: Camera3D
var ray: RayCast3D
var focus: Interactable = null
var _step_acc: = 0.0
var _step_variant := 0
var world: Node3D
var swimming: = false
var _safe_position := Vector3.ZERO
var _has_safe_position := false

func _ready() -> void :
	var cs: = CollisionShape3D.new()
	var cap: = CapsuleShape3D.new()
	cap.radius = 0.32
	cap.height = 1.75
	cs.shape = cap
	cs.position.y = 0.875
	add_child(cs)
	collision_layer = 1
	collision_mask = 1
	floor_snap_length = 0.4
	floor_max_angle = deg_to_rad(50)
	cam = Camera3D.new()
	cam.position.y = EYE
	cam.fov = Quality.fov if Quality.hd else 72.0
	Quality.changed.connect( func(): cam.fov = Quality.fov if Quality.hd else 72.0)
	cam.near = 0.05
	cam.far = 1100.0
	add_child(cam)
	cam.current = true
	ray = RayCast3D.new()
	ray.target_position = Vector3(0, 0, -3.0)
	ray.collision_mask = 3
	ray.collide_with_bodies = true
	cam.add_child(ray)

func set_view(p: Vector3, yaw_deg: float, pitch_deg: = 0.0) -> void :
	global_position = p
	yaw = deg_to_rad(yaw_deg)
	pitch = deg_to_rad(pitch_deg)
	_apply_look()

func look_delta(d: Vector2, touch: = true) -> void :
	var s: = (look_sens_touch if touch else look_sens_mouse) * Quality.sensitivity
	var dy: = - d.y if Quality.invert_y else d.y
	yaw -= d.x * s
	pitch = clampf(pitch - dy * s, deg_to_rad(-80), deg_to_rad(75))
	_apply_look()

func _apply_look() -> void :
	rotation.y = yaw
	if cam:
		cam.rotation = Vector3(pitch,0,0)

func _unhandled_input(e: InputEvent) -> void :
	if e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		look_delta(e.relative, false)

func _physics_process(delta: float) -> void :
	var phone = get_tree().get_first_node_in_group("phone")
	var writing: bool = phone != null and phone.visible
	var inp: = Vector2.ZERO if writing else move_input
	var k: = Vector2(Input.get_axis("move_left", "move_right"), Input.get_axis("move_back", "move_forward"))
	if k.length() > 0.1 and not writing:
		inp = k.limit_length(1.0)
	var fwd: = - global_transform.basis.z
	var right: = global_transform.basis.x
	var dir: = (right * inp.x + fwd * inp.y)
	dir.y = 0
	var sp: = SPEED * (SPRINT if Input.is_action_pressed("sprint") else 1.0)
	# v0.9.5: nado/snorkel no mar fundo (mais de 1 m de água): boia com a máscara logo abaixo da superfície; Shift mergulha até o fundo
	var ground: = float(world.call("_height", global_position.x, global_position.z)) if world and world.has_method("_height") else 0.0
	# Recupera também saves gravados durante uma queda abaixo do mapa.
	if global_position.y < minf(ground - 4.0, -6.0):
		global_position = _safe_position if _has_safe_position else (world.home_wake if world else Vector3(38, 0.5, -18))
		velocity = Vector3.ZERO
		ground = float(world.call("_height", global_position.x, global_position.z)) if world and world.has_method("_height") else 0.0
	# A profundidade do mar não torna quem está SOBRE o cais um nadador.
	swimming = global_position.z < -24.0 and ground < -1.1 and global_position.y < -0.6
	if swimming:
		sp = 2.1
	velocity.x = dir.x * sp
	velocity.z = dir.z * sp

	var lk: = Input.get_vector("look_left", "look_right", "look_up", "look_down", 0.15)
	if lk.length() > 0.0 and not writing:
		var kk: = PAD_LOOK * Quality.sensitivity * delta
		yaw -= lk.x * kk
		pitch = clampf(pitch - ( - lk.y if Quality.invert_y else lk.y) * kk * 0.75, deg_to_rad(-80), deg_to_rad(75))
		_apply_look()
	if swimming:
		var dive: = Input.is_action_pressed("sprint")
		var cam_y: = maxf((ground + 0.6) if dive else -0.48, ground + 0.45)   # superfície do mar em y = -0,3
		velocity.y = clampf((cam_y - EYE - global_position.y) * 3.0, -1.6, 1.6)
	elif not is_on_floor():
		velocity.y -= 18.0 * delta
	else:
		velocity.y = -0.5
	move_and_slide()
	if is_on_floor() and not swimming:
		_safe_position = global_position
		_has_safe_position = true
	var hv: = Vector2(velocity.x, velocity.z).length()
	if hv > 0.5 and is_on_floor() and not swimming:
		_step_acc += hv * delta
		if _step_acc > (1.85 if sp > SPEED else 1.5):
			_step_acc = 0.0
			_step_variant = (_step_variant + randi_range(1, 4)) % 5
			var surface := _footstep_surface()
			get_tree().call_group("audio", "sfx", "footstep_%s_%03d" % [surface, _step_variant], -18.0)

	refresh_focus()

func refresh_focus() -> void:
	focus = null
	ray.force_raycast_update()
	if ray.is_colliding():
		var c: = ray.get_collider()
		if c is Interactable and c.get_prompt() != "": focus = c
	var ops = get_parent().get("operations")
	if is_instance_valid(ops):
		focus = ops.resolve_computer_focus(cam,focus)
		focus = ops.resolve_customer_focus(cam,focus)
	var refinements=get_parent().get_node_or_null("Refinements")
	if refinements:focus=refinements.resolve_resident_focus(cam,focus)

func interact() -> void :
	if focus:
		focus.use()

# Identifica o piso tocado, em vez de supor madeira pela altura do jogador.
func _footstep_surface() -> String:
	var query := PhysicsRayQueryParameters3D.create(global_position + Vector3(0, 0.25, 0), global_position - Vector3(0, 0.65, 0), 1, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return "carpet" # impacto abafado para areia/terra, sem raspagem longa
	var body: Node = hit.collider
	if str(body.name).begins_with("Pier"):
		return "wood"
	var mesh_node := body.get_parent() as MeshInstance3D
	if mesh_node:
		var material := mesh_node.get_active_material(0) as StandardMaterial3D
		if material:
			var texture_path := material.albedo_texture.resource_path if material.albedo_texture else ""
			var key := (material.resource_name + texture_path).to_lower()
			for wood in ["wood", "plank", "bamboo"]:
				if wood in key:
					return "wood"
			return "concrete"
	return "carpet"

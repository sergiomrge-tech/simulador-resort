extends CharacterBody3D
## Jogador em primeira pessoa: joystick/WASD para andar, arrastar/mouse para olhar.

const SPEED := 3.4
const SPRINT := 1.7          # multiplicador ao correr (Shift / L3)
const PAD_LOOK := 2.6        # rad/s no analógico direito
const EYE := 1.65
var yaw := 0.0
var pitch := 0.0
var move_input := Vector2.ZERO      # do joystick virtual (x direita, y frente)
var look_sens_touch := 0.0045
var look_sens_mouse := 0.0025
var cam: Camera3D
var ray: RayCast3D
var focus: Interactable = null
var _step_acc := 0.0
var _step_flip := false

func _ready() -> void:
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
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
	Quality.changed.connect(func(): cam.fov = Quality.fov if Quality.hd else 72.0)
	cam.near = 0.05
	cam.far = 600.0
	add_child(cam)
	cam.current = true
	ray = RayCast3D.new()
	ray.target_position = Vector3(0, 0, -3.0)
	ray.collision_mask = 3
	ray.collide_with_bodies = true
	cam.add_child(ray)

func set_view(p: Vector3, yaw_deg: float, pitch_deg := 0.0) -> void:
	global_position = p
	yaw = deg_to_rad(yaw_deg)
	pitch = deg_to_rad(pitch_deg)
	_apply_look()

func look_delta(d: Vector2, touch := true) -> void:
	var s := (look_sens_touch if touch else look_sens_mouse) * Quality.sensitivity
	var dy := -d.y if Quality.invert_y else d.y
	yaw -= d.x * s
	pitch = clampf(pitch - dy * s, deg_to_rad(-80), deg_to_rad(75))
	_apply_look()

func _apply_look() -> void:
	rotation.y = yaw
	if cam:
		cam.rotation.x = pitch

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		look_delta(e.relative, false)

func _physics_process(delta: float) -> void:
	var inp := move_input
	var k := Vector2(Input.get_axis("move_left", "move_right"), Input.get_axis("move_back", "move_forward"))
	if k.length() > 0.1:
		inp = k.limit_length(1.0)
	var fwd := -global_transform.basis.z
	var right := global_transform.basis.x
	var dir := (right * inp.x + fwd * inp.y)
	dir.y = 0
	var sp := SPEED * (SPRINT if Input.is_action_pressed("sprint") else 1.0)
	velocity.x = dir.x * sp
	velocity.z = dir.z * sp
	# analógico direito (controle)
	var lk := Input.get_vector("look_left", "look_right", "look_up", "look_down", 0.15)
	if lk.length() > 0.0:
		var kk := PAD_LOOK * Quality.sensitivity * delta
		yaw -= lk.x * kk
		pitch = clampf(pitch - (-lk.y if Quality.invert_y else lk.y) * kk * 0.75, deg_to_rad(-80), deg_to_rad(75))
		_apply_look()
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	else:
		velocity.y = -0.5
	move_and_slide()
	var hv := Vector2(velocity.x, velocity.z).length()
	if hv > 0.5 and is_on_floor():
		_step_acc += hv * delta
		if _step_acc > (0.95 if sp > SPEED else 0.75):
			_step_acc = 0.0
			_step_flip = not _step_flip
			var wood := global_position.y > 0.08
			get_tree().call_group("audio", "sfx", ("step_wood" if wood else "step") + ("1" if _step_flip else "2"), -14.0)
	# foco de interação
	focus = null
	ray.force_raycast_update()
	if ray.is_colliding():
		var c := ray.get_collider()
		if c is Interactable and c.get_prompt() != "":
			focus = c

func interact() -> void:
	if focus:
		focus.use()

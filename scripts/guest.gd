extends Node3D
## Hóspede: segue rotas de waypoints e troca de animação conforme o estado.

signal arrived

const SKINS := [Color(0.95, 0.78, 0.62), Color(0.80, 0.58, 0.42), Color(0.62, 0.42, 0.28), Color(0.42, 0.28, 0.18)]
const SHIRTS := [Color(0.95, 0.45, 0.2), Color(0.15, 0.55, 0.75), Color(0.95, 0.85, 0.3), Color(0.9, 0.9, 0.88), Color(0.85, 0.25, 0.35), Color(0.3, 0.7, 0.45), Color(0.55, 0.35, 0.7)]
const SHORTS := [Color(0.15, 0.25, 0.5), Color(0.85, 0.8, 0.65), Color(0.2, 0.2, 0.22), Color(0.3, 0.55, 0.65), Color(0.75, 0.3, 0.2)]
const HAIRS := [Color(0.08, 0.06, 0.05), Color(0.3, 0.18, 0.08), Color(0.75, 0.6, 0.35), Color(0.55, 0.55, 0.55)]
const NAMES := ["Ana", "João", "Maria", "Pedro", "Luiza", "Rafael", "Camila", "Bruno", "Juliana", "Thiago", "Beatriz", "Lucas", "Fernanda", "Gabriel", "Larissa", "Diego"]

static var _scene: PackedScene
static var _mat: ShaderMaterial

var gid := 0
var gname := "Hóspede"
var state := "arrive"
var room := -1
var wait_min := 0.0       # tempo de espera na fila (min de jogo)
var timer := 0.0          # min de jogo restantes no estado atual
var plan: Array = []      # atividades restantes
var spot: Dictionary = {}
var queue_idx := -1
var speed := 1.35
var _route: Array = []
var _anim: AnimationPlayer
var _cur_anim := ""
var _mesh_insts: Array = []

func setup(id: int, rng: RandomNumberGenerator) -> void:
	gid = id
	gname = NAMES[rng.randi() % NAMES.size()]
	if _scene == null:
		_scene = load("res://assets/models/ual/guest.glb")
		_mat = ShaderMaterial.new()
		_mat.shader = load("res://shaders/guest.gdshader")
	var m: Node3D = _scene.instantiate()
	add_child(m)
	for mi in m.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = _mat
		_mesh_insts.append(mi)
	set_colors(SKINS[rng.randi() % SKINS.size()], SHIRTS[rng.randi() % SHIRTS.size()], SHORTS[rng.randi() % SHORTS.size()], HAIRS[rng.randi() % HAIRS.size()])
	var aps := m.find_children("*", "AnimationPlayer", true, false)
	if aps.size() > 0:
		_anim = aps[0]
		for an in _anim.get_animation_list():
			if an.ends_with("_Loop"):
				_anim.get_animation(an).loop_mode = Animation.LOOP_LINEAR
	speed = rng.randf_range(1.2, 1.5)
	play("Idle_Loop")

func set_colors(skin: Color, shirt: Color, shorts: Color, hair: Color) -> void:
	for mi in _mesh_insts:
		mi.set_instance_shader_parameter("skin", skin)
		mi.set_instance_shader_parameter("shirt", shirt)
		mi.set_instance_shader_parameter("shorts", shorts)
		mi.set_instance_shader_parameter("hair", hair)

func play(an: String) -> void:
	if _anim == null:
		return
	# o importador do Godot remove o sufixo _Loop (e já marca a animação como loop)
	if not _anim.has_animation(an) and an.ends_with("_Loop"):
		an = an.trim_suffix("_Loop")
	if an == _cur_anim:
		return
	if _anim.has_animation(an):
		_anim.play(an, 0.25)
		_cur_anim = an
		_anim.speed_scale = clampf(Core.speed_mult, 1.0, 4.0)

func go(route: Array) -> void:
	_route = route.duplicate()
	if not _route.is_empty():
		play("Walk_Loop")

func is_moving() -> bool:
	return not _route.is_empty()

func _process(delta: float) -> void:
	if _route.is_empty():
		return
	var target: Vector3 = _route[0]
	var to := target - position
	var step := speed * delta * Core.speed_mult
	var flat := Vector3(to.x, 0, to.z)
	if flat.length() > 0.05:
		var yaw := atan2(flat.x, flat.z)
		rotation.y = lerp_angle(rotation.y, yaw, minf(1.0, delta * 8.0 * Core.speed_mult))
	if to.length() <= step:
		position = target
		_route.pop_front()
		if _route.is_empty():
			arrived.emit()
	else:
		position += to.normalized() * step

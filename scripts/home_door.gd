extends Node3D
## Porta física da casa: E alterna; fecha após sair e liberar a folha.
var opened := false
var moving := false
var was_inside := false
var hinge: Node3D
var collider: CollisionShape3D
var tween: Tween

func _ready() -> void:
	name = "PlayerHomeDoor"
	hinge = Node3D.new()
	add_child(hinge)
	var leaf := Real.place(hinge, "g:player_home_door", Vector3.ZERO, -1.0, 0, Color.WHITE, 0, false)
	if leaf != null:
		_warm_door_wood(leaf)
	var body := StaticBody3D.new()
	hinge.add_child(body)
	collider = CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.15,2.2,.065)
	collider.shape = shape
	collider.position = Vector3(-.575,1.1,0)
	body.add_child(collider)
	var action := Interactable.new()
	hinge.add_child(action)
	action.position = Vector3(-.575,1.1,0)
	var target := CollisionShape3D.new()
	var target_shape := BoxShape3D.new()
	target_shape.size = Vector3(1.15,2.2,.20)
	target.shape = target_shape
	action.add_child(target)
	action.prompt_fn = func(): return "Porta da casa · " + ("fechar" if opened else "abrir")
	action.action_fn = toggle

func player() -> Node3D:
	var scene = get_tree().current_scene
	return scene.player if scene != null and scene.get("player") != null else null

func clear_to_close() -> bool:
	var hero := player()
	if hero == null: return true
	var p := hero.global_position-global_position
	# A folha abre para fora: esperar o jogador sair de todo o arco de varredura.
	return not (p.x> -1.5 and p.x<.4 and p.z>-.45 and p.z<1.55)

func toggle() -> void:
	if moving: return
	if opened and not clear_to_close():
		Core.toast.emit("Afaste-se um pouco da porta para fechar.","info")
		return
	set_open(not opened)

func set_open(value: bool) -> void:
	if moving or opened==value: return
	var hero := player()
	if value and hero!=null and hero.global_position.z<global_position.z:
		was_inside=true
	opened=value
	moving=true
	collider.set_deferred("disabled",true)
	tween=create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(hinge,"rotation:y",PI*.5 if opened else 0.0,.45)
	tween.finished.connect(func():
		moving=false
		collider.set_deferred("disabled",false))

func _process(_delta: float) -> void:
	if not Core.in_game or Core.paused: return
	check_exit()

func check_exit() -> void:
	var hero := player()
	if hero==null: return
	var p := hero.global_position-global_position
	if p.x> -5.8 and p.x<1.2 and p.z> -7.0 and p.z<-.4:
		was_inside=true
	if was_inside and opened and not moving and p.z>1.55 and clear_to_close():
		was_inside=false
		set_open(false)

## Mantém carvalho/latão naturais — evita o toon clarear demais a folha.
func _warm_door_wood(root: Node3D) -> void:
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = mi
		if mesh.mesh == null:
			continue
		for si in mesh.mesh.get_surface_count():
			var src: Material = mesh.get_active_material(si)
			if src == null:
				continue
			var name := String(src.resource_name).to_lower()
			var mat: StandardMaterial3D = src.duplicate() as StandardMaterial3D
			if mat == null:
				continue
			if name.find("brass") >= 0 or name.find("lathe") >= 0 or name.find("handle") >= 0:
				mat.albedo_color = Color(0.72, 0.52, 0.28)
				mat.metallic = 0.45
				mat.roughness = 0.35
			elif name.find("shadow") >= 0 or name.find("panel") >= 0:
				mat.albedo_color = Color(0.38, 0.26, 0.16)
				mat.roughness = 0.78
			else:
				mat.albedo_color = Color(0.62, 0.44, 0.28)
				mat.roughness = 0.72
			mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
			mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
			mesh.set_surface_override_material(si, mat)

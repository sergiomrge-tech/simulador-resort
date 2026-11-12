extends Node3D
## Porta física da casa: E alterna; fecha após sair e liberar a folha.
var door_label: String="Porta da casa"
var auto_close: bool=true
var opened := false
var moving := false
var was_inside := false
var hinge: Node3D
var collider: CollisionShape3D
var tween: Tween

func _ready() -> void:
	name = "PlayerHomeDoor" if door_label=="Porta da casa" else "BathroomDoor"
	hinge = Node3D.new()
	add_child(hinge)
	Real.place(hinge,"g:player_home_door",Vector3.ZERO,-1.0,0,Color.WHITE,0,false)
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
	action.prompt_fn = func(): return door_label+" · " + ("fechar" if opened else "abrir")
	action.action_fn = toggle

func player() -> Node3D:
	var scene = get_tree().current_scene
	return scene.player if scene != null and scene.get("player") != null else null

func clear_to_close() -> bool:
	var hero := player()
	if hero == null: return true
	var p := to_local(hero.global_position)
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
	if not auto_close or not Core.in_game or Core.paused: return
	check_exit()

func check_exit() -> void:
	var hero := player()
	if hero==null: return
	var p := to_local(hero.global_position)
	if p.x> -5.8 and p.x<1.2 and p.z> -7.0 and p.z<-.4:
		was_inside=true
	if was_inside and opened and not moving and p.z>1.55 and clear_to_close():
		was_inside=false
		set_open(false)

extends Node
## v0.9.5: câmera de fotos (tecla P). A foto vai para o álbum do celular (user://album). Cada tema fotografado pela 1ª vez
## paga um prêmio: festa, pôr do sol, farol, peixes no mergulho, gaivota e quiosque à noite.

const DIR: = "user://album"
const THEMES: = {
	"festa": ["Festa na praia", 40], "por_do_sol": ["Pôr do sol", 30], "farol": ["O farol", 25],
	"peixes": ["Peixes do recife", 40], "gaivota": ["Gaivota de perto", 20], "quiosque_noite": ["Quiosque iluminado", 30],
}
var world: Node3D
var data: = {"fotos": [], "temas": {}}

func _ready() -> void:
	if not InputMap.has_action("photo"):
		InputMap.add_action("photo")
		var ev: = InputEventKey.new()
		ev.physical_keycode = KEY_P
		InputMap.action_add_event("photo", ev)
	DirAccess.make_dir_recursive_absolute(DIR)
	var f: = FileAccess.open(DIR + "/album.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			data = d

func _save() -> void:
	var f: = FileAccess.open(DIR + "/album.json", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(data))

func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("photo") and Core.in_game and not get_tree().paused:
		snap()

func _themes_in_view(cam: Camera3D) -> Array:
	var out: Array = []
	var p: = cam.global_position
	var fwd: = - cam.global_transform.basis.z
	var h: = Core.minutes / 60.0
	if Core.is_party() and p.distance_to(Vector3(52, 0, -23)) < 28.0 and cam.is_position_in_frustum(Vector3(52, 1.5, -23)):
		out.append("festa")
	if h >= 16.8 and h <= 18.6 and fwd.y > -0.3 and p.z < 10.0:
		out.append("por_do_sol")
	if p.distance_to(Vector3(108, 8, -40)) < 90.0 and cam.is_position_in_frustum(Vector3(108, 10, -40)):
		out.append("farol")
	var reef: = world.get_node_or_null("Reef") if world else null
	if reef and p.y < -0.3:
		for f in reef.get_children():
			if f is Node3D and (f as Node3D).global_position.distance_to(p) < 6.0 and cam.is_position_in_frustum((f as Node3D).global_position):
				out.append("peixes")
				break
	for b in get_tree().get_nodes_in_group("gull"):
		if (b as Node3D).global_position.distance_to(p) < 6.0 and cam.is_position_in_frustum((b as Node3D).global_position):
			out.append("gaivota")
			break
	if (h >= 18.5 or h < 5.0) and p.distance_to(Vector3(38, 1, -13)) < 25.0 and cam.is_position_in_frustum(Vector3(38, 2, -13)):
		out.append("quiosque_noite")
	return out

func snap() -> void:
	var cam: = get_viewport().get_camera_3d()
	if cam == null:
		return
	var themes: = _themes_in_view(cam)
	get_tree().call_group("hud", "set", "visible", false)
	await RenderingServer.frame_post_draw
	var img: = get_viewport().get_texture().get_image()
	get_tree().call_group("hud", "set", "visible", true)
	img.resize(480, 270, Image.INTERPOLATE_BILINEAR)
	var name: = "foto_%d_%d.png" % [Core.day, int(Time.get_unix_time_from_system())]
	img.save_png(DIR + "/" + name)
	data.fotos.append({"arq": name, "dia": Core.day, "temas": themes})
	if data.fotos.size() > 40:
		data.fotos.pop_front()
	get_tree().call_group("audio", "sfx", "click", -4.0, 0.6)
	var paid: = false
	Core.prog.on_photo("")
	for t in themes:
		Core.prog.chapter_photo[t] = true
		if not data.temas.has(t):
			Core.prog.add_fame(PD.XP.photo)
			data.temas[t] = Core.day
			Core.book(int(THEMES[t][1]), tr("Foto para o álbum: %s") % tr(str(THEMES[t][0])), "missao", false)
			Core.toast.emit(tr("Foto nova no álbum: %s! +%s") % [tr(str(THEMES[t][0])), Core.fmt_money(int(THEMES[t][1]))], "good")
			paid = true
	if not paid:
		Core.toast.emit(tr("Foto salva no álbum do celular.") if themes.is_empty() else tr("Foto salva (esse tema já está no álbum)."), "info")
	_save()

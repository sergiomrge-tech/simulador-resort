extends Node
## Carregador de atualizações (patch) do Maré Alta Resort.
## O instalador do patch registra este script como autoload no override.cfg ao lado do .exe.
## Ele monta, por cima do pacote principal, todos os arquivos patch_*.pck da pasta do jogo (em ordem de versão).

func _init() -> void:
	var dir: = OS.get_executable_path().get_base_dir()
	var files: = Array(DirAccess.get_files_at(dir))
	files.sort()
	for f in files:
		if f.begins_with("patch_") and f.ends_with(".pck"):
			var ok: = ProjectSettings.load_resource_pack(dir.path_join(f), true)
			print("[patch] ", f, " ", "ok" if ok else "FALHOU")

## v0.9.5: escreve diagnostico.txt na pasta do jogo (placa de vídeo, API, modo gráfico, versão e patches) para conferir bugs.
func _ready() -> void:
	get_tree().create_timer(6.0).timeout.connect(_diag)

func _diag() -> void:
	var dir: = OS.get_executable_path().get_base_dir()
	var q: = get_node_or_null("/root/Quality")
	var lines: = PackedStringArray([
		"Maré Alta Resort " + str(ProjectSettings.get_setting("application/config/version", "?")),
		"Data: " + Time.get_datetime_string_from_system(),
		"Sistema: %s %s" % [OS.get_name(), OS.get_version()],
		"Placa de vídeo: %s (%s)" % [RenderingServer.get_video_adapter_name(), RenderingServer.get_video_adapter_vendor()],
		"API: %s %s" % [RenderingServer.get_current_rendering_driver_name(), RenderingServer.get_video_adapter_api_version()],
		"Renderizador: " + RenderingServer.get_current_rendering_method(),
		"Tela: %s  janela: %s" % [str(DisplayServer.screen_get_size()), str(get_viewport().get_visible_rect().size)],
		"Qualidade (preset): " + (str(q.get("preset")) if q else "?"),
		"Memória de vídeo usada: %d MB" % int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576),
		"FPS: " + str(Engine.get_frames_per_second()),
	])
	for f in DirAccess.get_files_at(dir):
		if f.begins_with("patch_") and f.ends_with(".pck"):
			lines.append("Patch: " + f)
	var fa: = FileAccess.open(dir.path_join("diagnostico.txt"), FileAccess.WRITE)
	if fa:
		fa.store_string("\n".join(lines) + "\n")

## O jogo antigo regrava o override.cfg inteiro ao trocar a API gráfica: ao sair, garante que o carregador continua registrado.
func _exit_tree() -> void:
	var path: = OS.get_executable_path().get_base_dir().path_join("override.cfg")
	var cf: = ConfigFile.new()
	cf.load(path)
	var me: String = get_script().resource_path
	if not cf.has_section_key("autoload", "Patch") and me != "":
		cf.set_value("autoload", "Patch", "*" + me)
		cf.save(path)

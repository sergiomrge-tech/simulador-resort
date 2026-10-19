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

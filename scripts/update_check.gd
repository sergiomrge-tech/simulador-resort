extends Node
## v0.9.5: ao abrir o jogo, consulta no GitHub a última versão publicada (docs/latest_version.txt).
## Se houver patch novo, avisa no topo da tela e no computador (botão que abre a pasta de patches no navegador).
## Sem internet ou sem resposta, não faz nada.

const URL: = "https://raw.githubusercontent.com/sergiomrge-tech/simulador-resort/main/docs/latest_version.txt"
const PAGE: = "https://github.com/sergiomrge-tech/simulador-resort/tree/main/patches"

func _ready() -> void:
	var http: = HTTPRequest.new()
	http.timeout = 8.0
	add_child(http)
	http.request_completed.connect(_done)
	if http.request(URL) != OK:
		queue_free()

static func _num(v: String) -> int:
	var p: = v.strip_edges().split(".")
	var n: = 0
	for i in 3:
		n = n * 1000 + (int(p[i]) if i < p.size() else 0)
	return n

func _done(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if result == HTTPRequest.RESULT_SUCCESS and code == 200:
		var latest: = body.get_string_from_utf8().strip_edges().split("\n")[0]
		var mine: = str(ProjectSettings.get_setting("application/config/version", "0.0.0"))
		if _num(latest) > _num(mine):
			Engine.set_meta("update_ver", latest)
			Engine.set_meta("update_page", PAGE)
			Core.toast.emit(tr("Atualização %s disponível! Veja no computador (app inicial).") % latest, "info")
	queue_free()

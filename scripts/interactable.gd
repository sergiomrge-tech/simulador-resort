extends StaticBody3D
class_name Interactable
## Objeto que o jogador pode usar (botão Interagir / tecla E).

var prompt_fn: Callable      # () -> String  (vazio = não interagível agora)
var action_fn: Callable      # () -> void

func _init() -> void:
	collision_layer = 2
	collision_mask = 0
	add_to_group("interactables")

func get_prompt() -> String:
	if prompt_fn.is_valid():
		return prompt_fn.call()
	return ""

func use() -> void:
	if action_fn.is_valid():
		action_fn.call()

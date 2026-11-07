extends RefCounted
## Não captura Nodes em lambdas: clientes podem sair e ser liberados durante o await.
static func until_state(tree: SceneTree, target: WeakRef, wanted: String, timeout_s: float) -> bool:
	var deadline: int = Time.get_ticks_msec() + int(timeout_s * 1000.0)
	while true:
		var node = target.get_ref()
		if node == null or node.is_queued_for_deletion():
			return false
		if node.state == wanted:
			return true
		if node.state == "kleave" or Time.get_ticks_msec() >= deadline:
			return false
		await tree.process_frame
	return false

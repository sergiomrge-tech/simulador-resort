extends SkeletonModifier3D
## Deixa os personagens caricatos (v0.7): aumenta a cabeça e engorda um pouco o tronco depois da animação.

var head_scale: = 1.38
var chest_scale: = 1.0
var _head: = -1
var _chest: = -1

func _ready() -> void :
	var sk: = get_skeleton()
	if sk:
		_head = sk.find_bone("Head")
		_chest = sk.find_bone("spine_03")

func _process_modification() -> void :
	var sk: = get_skeleton()
	if sk == null:
		return
	if _head >= 0:
		sk.set_bone_pose_scale(_head, Vector3.ONE * head_scale)
	if _chest >= 0 and chest_scale != 1.0:
		sk.set_bone_pose_scale(_chest, Vector3(chest_scale, 1.0, chest_scale))

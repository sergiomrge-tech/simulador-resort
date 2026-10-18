extends SkeletonModifier3D



var guest: Node3D
var _upper: = -1
var _lower: = -1
var _hand: = -1
var _head: = -1
var _len_u: = 0.2744
var _len_f: = 0.2726

func _process_modification() -> void :
	if guest == null or not guest._eating:
		return
	var sk: = get_skeleton()
	if sk == null:
		return
	if _upper < 0:
		_upper = sk.find_bone("upperarm_r")
		_lower = sk.find_bone("lowerarm_r")
		_hand = sk.find_bone("hand_r")
		_head = sk.find_bone("Head")
		if _upper < 0 or _lower < 0 or _hand < 0:
			return
		var ru: = sk.get_bone_global_rest(_upper).origin
		var rl: = sk.get_bone_global_rest(_lower).origin
		var rh: = sk.get_bone_global_rest(_hand).origin
		_len_u = ru.distance_to(rl)
		_len_f = rl.distance_to(rh)
	var up: = sk.get_bone_global_pose(_upper)
	var lo: = sk.get_bone_global_pose(_lower)
	var ha: = sk.get_bone_global_pose(_hand)
	var head: = sk.get_bone_global_pose(_head) if _head >= 0 else up
	var chew: = 0.5 + 0.5 * sin(guest._eat_t * 4.2)
	var mouth: = head.origin + Vector3(0.02, -0.05, 0.09)
	var low: = head.origin + Vector3(0.04, -0.16, 0.14)
	var target: Vector3 = low.lerp(mouth, 0.4 + chew * 0.6)
	var shoulder: Vector3 = up.origin
	var reach: = _len_u + _len_f - 0.012
	var to: = target - shoulder
	var dist: = clampf(to.length(), 0.08, reach)
	if to.length() < 0.001:
		return
	var dir: = to / to.length()
	var adj: = (_len_u * _len_u + dist * dist - _len_f * _len_f) / (2.0 * dist)
	var off: = sqrt(maxf(_len_u * _len_u - adj * adj, 0.0))
	var pole: = shoulder + Vector3(-0.85, -0.35, -0.15)
	var bend: = pole - shoulder
	bend = bend - dir * bend.dot(dir)
	if bend.length() < 0.001:
		bend = Vector3.UP.cross(dir)
	bend = bend.normalized()
	var elbow: Vector3 = shoulder + dir * adj + bend * off
	var wrist: Vector3 = shoulder + dir * dist
	sk.set_bone_global_pose(_upper, _aim(up, shoulder, elbow))
	sk.set_bone_global_pose(_lower, _aim(lo, elbow, wrist))
	sk.set_bone_global_pose(_hand, _aim(ha, wrist, wrist + (wrist - elbow).normalized() * 0.08))

func _aim(pose: Transform3D, origin: Vector3, toward: Vector3) -> Transform3D:
	var y: = toward - origin
	if y.length() < 0.0001:
		return Transform3D(pose.basis, origin)
	y = y.normalized()
	var x: = pose.basis.x - y * pose.basis.x.dot(y)
	if x.length() < 0.001:
		x = pose.basis.z.cross(y)
	x = x.normalized()
	var z: = x.cross(y).normalized()
	return Transform3D(Basis(x, y, z), origin)

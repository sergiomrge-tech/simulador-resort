extends "res://scripts/eat_arm.gd"
## Bounded two-bone reach using the actual imported limb lengths.
func _process_modification() -> void:
	if guest == null or not guest.has_meta("work_target"): return
	if guest.is_moving() and str(guest.get_meta("work_kind", "")) != "carry": return
	var sk := get_skeleton()
	if sk == null: return
	if _upper < 0:
		_upper = sk.find_bone("upperarm_r")
		_lower = sk.find_bone("lowerarm_r")
		_hand = sk.find_bone("hand_r")
		if mini(_upper,mini(_lower,_hand)) < 0: return
		_len_u = sk.get_bone_global_rest(_upper).origin.distance_to(sk.get_bone_global_rest(_lower).origin)
		_len_f = sk.get_bone_global_rest(_lower).origin.distance_to(sk.get_bone_global_rest(_hand).origin)
	var up := sk.get_bone_global_pose(_upper)
	var lo := sk.get_bone_global_pose(_lower)
	var ha := sk.get_bone_global_pose(_hand)
	var point: Vector3 = guest.get_meta("work_target")
	var kind: String = str(guest.get_meta("work_kind", ""))
	if guest.get_meta("hand_carry",false): point = guest.global_position + guest.global_transform.basis * Vector3(-.19,1.18,.25)
	elif kind == "carry": point = guest.global_position + guest.global_transform.basis * Vector3(-.18,1.07,.36)
	elif kind == "prepare": point += Vector3(.04*sin(Time.get_ticks_msec()*.006),.015,0)
	var target := sk.to_local(point)
	var shoulder := up.origin
	var delta := target-shoulder
	var distance := clampf(delta.length(),.08,_len_u+_len_f-.012)
	var direction := delta.normalized()
	var adj := (_len_u*_len_u+distance*distance-_len_f*_len_f)/(2*distance)
	var off := sqrt(maxf(0,_len_u*_len_u-adj*adj))
	var pole := Vector3(0,-1,-.5)
	var bend := (pole-direction*pole.dot(direction)).normalized()
	var elbow := shoulder+direction*adj+bend*off
	var wrist := shoulder+direction*distance
	sk.set_bone_global_pose(_upper,_rotate_limb(up,shoulder,lo.origin-up.origin,elbow-shoulder))
	sk.set_bone_global_pose(_lower,_rotate_limb(lo,elbow,ha.origin-lo.origin,wrist-elbow))
	sk.set_bone_global_pose(_hand,_rotate_limb(ha,wrist,ha.origin-lo.origin,wrist-elbow))

	if guest.get_meta("carry_tray",false):
		_support_tray(sk)

func _rotate_limb(pose: Transform3D, origin: Vector3, current: Vector3, desired: Vector3) -> Transform3D:
	if current.length_squared() < .00001 or desired.length_squared() < .00001: return pose
	var rotation := Quaternion(current.normalized(),desired.normalized())
	return Transform3D(Basis(rotation)*pose.basis,origin)

var _lu: int=-1
var _ll: int=-1
var _lh: int=-1
func _support_tray(sk: Skeleton3D) -> void:
	if _lu<0:
		_lu=sk.find_bone("upperarm_l")
		_ll=sk.find_bone("lowerarm_l")
		_lh=sk.find_bone("hand_l")
	if mini(_lu,mini(_ll,_lh))<0: return
	var up:=sk.get_bone_global_pose(_lu)
	var lo:=sk.get_bone_global_pose(_ll)
	var ha:=sk.get_bone_global_pose(_lh)
	var target:=sk.to_local(guest.global_position+guest.global_basis*Vector3(.19,1.18,.25))
	var delta:=target-up.origin
	var distance:=clampf(delta.length(),.08,_len_u+_len_f-.012)
	var direction:=delta.normalized()
	var adj:=(_len_u*_len_u+distance*distance-_len_f*_len_f)/(2*distance)
	var pole:=Vector3(0,-1,-.5)
	var bend:=(pole-direction*pole.dot(direction)).normalized()
	var elbow:=up.origin+direction*adj+bend*sqrt(maxf(0,_len_u*_len_u-adj*adj))
	var wrist:=up.origin+direction*distance
	sk.set_bone_global_pose(_lu,_rotate_limb(up,up.origin,lo.origin-up.origin,elbow-up.origin))
	sk.set_bone_global_pose(_ll,_rotate_limb(lo,elbow,ha.origin-lo.origin,wrist-elbow))
	sk.set_bone_global_pose(_lh,_rotate_limb(ha,wrist,ha.origin-lo.origin,wrist-elbow))

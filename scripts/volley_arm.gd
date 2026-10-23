extends "res://scripts/work_arm.gd"
## Two arm contact pose layered over the existing idle animation.
func _process_modification() -> void:
	if guest==null: return
	var weight: float = guest.get_meta("volley_weight",0.0)
	if weight<.01: return
	var sk := get_skeleton()
	if sk==null: return
	for side in ["r","l"]:
		var upper := sk.find_bone("upperarm_"+side)
		var lower := sk.find_bone("lowerarm_"+side)
		var hand := sk.find_bone("hand_"+side)
		if mini(upper,mini(lower,hand))<0: continue
		var up := sk.get_bone_global_pose(upper)
		var lo := sk.get_bone_global_pose(lower)
		var ha := sk.get_bone_global_pose(hand)
		var len_u := sk.get_bone_global_rest(upper).origin.distance_to(sk.get_bone_global_rest(lower).origin)
		var len_f := sk.get_bone_global_rest(lower).origin.distance_to(sk.get_bone_global_rest(hand).origin)
		var point: Vector3 = guest.get_meta("volley_target")
		point += guest.global_basis.x*(.08 if side=="r" else -.08)
		var target := sk.to_local(point)
		var diff := target-up.origin
		var distance := clampf(diff.length(),.08,len_u+len_f-.012)
		var direction := diff.normalized()
		var adj := (len_u*len_u+distance*distance-len_f*len_f)/(2*distance)
		var off := sqrt(maxf(0,len_u*len_u-adj*adj))
		var pole := Vector3(.4 if side=="r" else -.4,-.4,-.3)
		var bend := (pole-direction*pole.dot(direction)).normalized()
		var elbow := up.origin+direction*adj+bend*off
		var wrist := up.origin+direction*distance
		sk.set_bone_global_pose(upper,up.interpolate_with(_rotate_limb(up,up.origin,lo.origin-up.origin,elbow-up.origin),weight))
		sk.set_bone_global_pose(lower,lo.interpolate_with(_rotate_limb(lo,elbow,ha.origin-lo.origin,wrist-elbow),weight))
		sk.set_bone_global_pose(hand,ha.interpolate_with(_rotate_limb(ha,wrist,ha.origin-lo.origin,wrist-elbow),weight))

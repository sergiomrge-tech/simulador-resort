extends Node3D
## Passeio curto em área livre; rig e clipes originais CC0 preservados.
var kind := "cat"
var tint := Color.WHITE
var origin: Vector3
var target: Vector3
var wait := 1.0
var rng := RandomNumberGenerator.new()
var animation: AnimationPlayer
var idle_clip := ""
var walk_clip := ""
var moving := false
var walking_partner: WeakRef

func _ready() -> void:
	name="VillageAnimal_"+kind
	add_to_group("village_animals")
	rng.seed=int(position.x*113+position.z*97)
	origin=position
	target=position
	var model=Real.place(self,"g:"+kind,Vector3.ZERO,.42 if kind=="cat" else .62,-PI/2)
	if model==null: return
	for child in model.find_children("*","AnimationPlayer",true,false):
		animation=child
		break
	if animation:
		for clip in animation.get_animation_list():
			animation.get_animation(clip).loop_mode=Animation.LOOP_LINEAR
			if "idle" in clip.to_lower(): idle_clip=clip
			if "walk" in clip.to_lower(): walk_clip=clip
		_play(false)
	wait=rng.randf_range(1,4)
	call_deferred("_settle")

func _settle() -> void:
	origin=_safe_origin(position)
	position=origin
	target=origin

func _safe_origin(p: Vector3) -> Vector3:
	var q:=p
	for pass_index in 3:
		for rect in get_parent().block_rects:
			var r: Rect2=(rect as Rect2).grow(.3)
			if not r.has_point(Vector2(q.x,q.z)): continue
			var sides: Array=[Vector3(r.position.x-.04,q.y,q.z),Vector3(r.end.x+.04,q.y,q.z),Vector3(q.x,q.y,r.position.y-.04),Vector3(q.x,q.y,r.end.y+.04)]
			sides.sort_custom(func(a,b): return a.distance_squared_to(q)<b.distance_squared_to(q))
			q=sides[0]
	return q

func _clear_segment(a: Vector3,b: Vector3) -> bool:
	for i in 13:
		var p:=a.lerp(b,i/12.0)
		for rect in get_parent().block_rects:
			if (rect as Rect2).grow(.28).has_point(Vector2(p.x,p.z)): return false
	return true

func _play(walking: bool) -> void:
	moving=walking
	if animation:
		var clip:=walk_clip if walking else idle_clip
		if not clip.is_empty() and animation.current_animation!=clip: animation.play(clip,.2)

func _process(delta: float) -> void:
	var running:=Core.in_game and not Core.paused
	if animation: animation.active=running
	if not running: return
	if walking_partner!=null:
		var owner=walking_partner.get_ref()
		if is_instance_valid(owner) and owner.visible and Core.weather!="rain" and position.distance_to(owner.position)<18:
			var follow: Vector3=owner.position+owner.basis.x*.85
			if position.distance_to(follow)>1.4 and _clear_segment(position,follow):
				target=follow
				_play(true)
	if moving:
		var offset:=target-position
		offset.y=0
		if offset.length()<.045:
			_play(false)
			wait=rng.randf_range(3,7)
		else:
			rotation.y=lerp_angle(rotation.y,atan2(offset.x,offset.z),minf(1,delta*5))
			position+=offset.normalized()*minf(offset.length(),delta*(1.15 if walking_partner!=null else (.36 if kind=="cat" else .48)))
	else:
		wait-=delta
		if wait<=0:
			for attempt in 12:
				var candidate:=origin+Vector3(rng.randf_range(-1.7,1.7),0,rng.randf_range(-1.3,1.3))
				if candidate.distance_to(position)>.6 and _clear_segment(position,candidate):
					target=candidate
					_play(true)
					break
			wait=3
	var query:=PhysicsRayQueryParameters3D.create(position+Vector3(0,.35,0),position-Vector3(0,.8,0),1)
	if is_instance_valid(Core.player_ref): query.exclude=[Core.player_ref.get_rid()]
	var hit:=get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty(): position.y=hit.position.y

extends Node
## Música bossa nova, mar, grilos à noite, pássaros de dia, vila (murmúrio, cachorro, gaivotas, sino) e efeitos.
## Todos CC0 (ver assets/audio/CREDITS.txt). Buses: Master / Music / SFX (volumes nas Configurações).

var music: AudioStreamPlayer
var ocean: AudioStreamPlayer
var crickets: AudioStreamPlayer
var murmur: AudioStreamPlayer
var player: Node3D
var _cache := {}
var _bird_t := 8.0
var _gull_t := 5.0
var _dog_t := 20.0
var _night := 0.0
var _last_bell_hour := -1
var muted := false

const VILLAGE := Vector3(70, 0, 30)

static func ensure_buses() -> void:
	for b in ["Music", "SFX"]:
		if AudioServer.get_bus_index(b) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "Master")

func _ready() -> void:
	add_to_group("audio")
	ensure_buses()
	music = _loop("music_bossa", -13.0, "Music")
	ocean = _loop("ocean_loop", -8.0)
	crickets = _loop("crickets_loop", -60.0)
	murmur = _loop("village_murmur", -60.0)

func _loop(n: String, db: float, bus := "SFX") -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	var s: AudioStreamOggVorbis = load("res://assets/audio/%s.ogg" % n)
	s.loop = true
	p.stream = s
	p.volume_db = db
	p.bus = bus
	add_child(p)
	if not muted:
		p.play()
	return p

func set_night(n: float) -> void:
	_night = n

func _process(delta: float) -> void:
	var village_k := 0.0
	var beach_k := 0.0
	if player:
		var pp := player.global_position
		var dz := clampf((pp.z + 30.0) / 60.0, 0.0, 1.0)
		ocean.volume_db = lerpf(-4.0, -17.0, dz)
		village_k = clampf(1.0 - (Vector2(pp.x, pp.z) - Vector2(VILLAGE.x, VILLAGE.z)).length() / 45.0, 0.0, 1.0)
		beach_k = clampf((-pp.z - 5.0) / 15.0, 0.0, 1.0)
	crickets.volume_db = lerpf(-50.0, -12.0, _night)
	music.volume_db = lerpf(-13.0, -17.0, _night) - village_k * 3.0
	var day_k := 1.0 - _night
	murmur.volume_db = linear_to_db(maxf(0.0005, village_k * lerpf(0.15, 1.0, day_k) * 0.55))
	if get_tree().paused:
		return
	_bird_t -= delta
	if _bird_t <= 0.0:
		_bird_t = randf_range(6.0, 16.0)
		if _night < 0.3:
			sfx("bird1" if randf() < 0.5 else "bird2", -18.0)
	_gull_t -= delta
	if _gull_t <= 0.0:
		_gull_t = randf_range(8.0, 22.0)
		if _night < 0.3 and beach_k > 0.2:
			sfx("seagull1" if randf() < 0.5 else "seagull2", lerpf(-22.0, -12.0, beach_k))
	_dog_t -= delta
	if _dog_t <= 0.0:
		_dog_t = randf_range(25.0, 60.0)
		if village_k > 0.15:
			sfx("dog", lerpf(-26.0, -14.0, village_k))
	# sino da igreja ao meio-dia e às 18h
	var h := int(Core.minutes / 60.0)
	if (h == 12 or h == 18) and h != _last_bell_hour and int(Core.minutes) % 60 < 5:
		_last_bell_hour = h
		_church_bell(village_k)
	elif h != 12 and h != 18:
		_last_bell_hour = -1

func _church_bell(k: float) -> void:
	for i in 3:
		get_tree().create_timer(i * 1.4).timeout.connect(func(): sfx("bell", lerpf(-26.0, -10.0, k), 0.55))

func sfx(n: String, db := -6.0, pitch := 1.0) -> void:
	if muted:
		return
	if not _cache.has(n):
		_cache[n] = load("res://assets/audio/%s.ogg" % n)
	var p := AudioStreamPlayer.new()
	p.stream = _cache[n]
	p.volume_db = db
	p.bus = "SFX"
	p.pitch_scale = randf_range(0.95, 1.05) * pitch
	add_child(p)
	p.play()
	p.finished.connect(p.queue_free)

extends Node



var music: AudioStreamPlayer
var ocean: AudioStreamPlayer
var crickets: AudioStreamPlayer
var murmur: AudioStreamPlayer
var player: Node3D
var _cache: = {}
var _bird_t: = 8.0
var _gull_t: = 5.0
var _dog_t: = 20.0
var _night: = 0.0
var _last_bell_hour: = -1
var muted: = false
# v0.9.3: sons de evento (sintetizados em tools/gen_audio.py)
var rain_snd: AudioStreamPlayer
var wind_snd: AudioStreamPlayer
var party_snd: AudioStreamPlayer3D
var _party_kind: = ""
const PARTY_C: = Vector3(52.0, 1.5, -23.0)

const VILLAGE: = Vector3(70, 0, 30)

static func ensure_buses() -> void :
	for b in ["Music", "SFX"]:
		if AudioServer.get_bus_index(b) == -1:
			AudioServer.add_bus()
			var i: = AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "Master")

func _ready() -> void :
	add_to_group("audio")
	ensure_buses()
	music = _loop("music_bossa", -13.0, "Music")
	ocean = _loop("ocean_loop", -8.0)
	crickets = _loop("crickets_loop", -60.0)
	murmur = _loop("village_murmur", -60.0)
	rain_snd = _loop("rain_loop", -80.0)
	wind_snd = _loop("wind_loop", -80.0)
	party_snd = AudioStreamPlayer3D.new()
	party_snd.position = PARTY_C
	party_snd.unit_size = 9.0
	party_snd.max_distance = 70.0
	party_snd.bus = "Music"
	party_snd.volume_db = -4.0
	add_child(party_snd)

func _loop(n: String, db: float, bus: = "SFX") -> AudioStreamPlayer:
	var p: = AudioStreamPlayer.new()
	var s: AudioStreamOggVorbis = load("res://assets/audio/%s.ogg" % n)
	s.loop = true
	p.stream = s
	p.volume_db = db
	p.bus = bus
	add_child(p)
	if not muted:
		p.play()
	return p

func set_night(n: float) -> void :
	_night = n

func _process(delta: float) -> void :
	var village_k: = 0.0
	var beach_k: = 0.0
	if player:
		var pp: = player.global_position
		var dz: = clampf((pp.z + 30.0) / 60.0, 0.0, 1.0)
		ocean.volume_db = lerpf(-4.0, -17.0, dz)
		village_k = clampf(1.0 - (Vector2(pp.x, pp.z) - Vector2(VILLAGE.x, VILLAGE.z)).length() / 45.0, 0.0, 1.0)
		beach_k = clampf(( - pp.z - 5.0) / 15.0, 0.0, 1.0)
	crickets.volume_db = lerpf(-50.0, -12.0, _night)
	music.volume_db = lerpf(-13.0, -17.0, _night) - village_k * 3.0
	var day_k: = 1.0 - _night
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

	# sino da igreja de hora em hora (7h às 21h), uma badalada por hora do relógio
	var h: = int(Core.minutes / 60.0)
	if h >= 7 and h <= 21 and h != _last_bell_hour and int(Core.minutes) % 60 < 5:
		_last_bell_hour = h
		_church_bell(village_k, ((h - 1) % 12) + 1)
	_event_sounds()

func _event_sounds() -> void :
	var storm: = Core.weather == "rain"
	var hard: = Core.day_event == "tempestade"
	var tgt_rain: = (-6.0 if hard else -12.0) if storm else -80.0
	var tgt_wind: = -8.0 if hard else (-20.0 if Core.day_event == "mare" else -80.0)
	rain_snd.volume_db = lerpf(rain_snd.volume_db, tgt_rain, 0.02)
	wind_snd.volume_db = lerpf(wind_snd.volume_db, tgt_wind, 0.02)
	# música da festa: forró na junina, batida eletrônica no show do DJ, forró mais baixo na quermesse; só das 16h às 23h
	var kind: = ""
	if Core.is_party() and Core.minutes >= 16.0 * 60.0 and Core.minutes < 23.0 * 60.0:
		kind = "dj_loop" if Core.day_event in ["show_dj", "carnaval"] else "forro_loop"
	if kind != _party_kind:
		_party_kind = kind
		if kind == "":
			party_snd.stop()
		else:
			var st: AudioStreamOggVorbis = load("res://assets/audio/%s.ogg" % kind)
			st.loop = true
			party_snd.stream = st
			party_snd.volume_db = -8.0 if Core.day_event == "quermesse" else -3.0
			if not muted:
				party_snd.play()

func _church_bell(k: float, strikes: = 3) -> void :
	for i in strikes:
		get_tree().create_timer(i * 1.6).timeout.connect( func(): sfx("bell", lerpf(-26.0, -10.0, k), 0.55))

func sfx(n: String, db: = -6.0, pitch: = 1.0) -> void :
	if muted:
		return
	if not _cache.has(n):
		_cache[n] = load("res://assets/audio/%s.ogg" % n)
	var p: = AudioStreamPlayer.new()
	p.stream = _cache[n]
	p.volume_db = db
	p.bus = "SFX"
	p.pitch_scale = randf_range(0.95, 1.05) * pitch
	add_child(p)
	p.play()
	p.finished.connect(p.queue_free)

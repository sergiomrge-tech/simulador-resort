extends Node



var music: AudioStreamPlayer
var ocean: AudioStreamPlayer
var crickets: AudioStreamPlayer
var player: Node3D
var _cache: = {}
var _bird_t: = 2.5
var bird_voice: AudioStreamPlayer3D
const BIRD_TREES := [Vector3(42,5,17),Vector3(53,5,36),Vector3(69,6,37),Vector3(83,5,18),Vector3(33,5,-10),Vector3(-15,5,7),Vector3(9,5,-9)]
var _gull_t: = 5.0
var _dog_t: = 20.0
var _night: = 0.0
var _last_bell_hour: = -1
var muted: = false
var home_duck := 0.0
# v0.9.3: sons de evento (sintetizados em tools/gen_audio.py)
var rain_snd: AudioStreamPlayer
var wind_snd: AudioStreamPlayer
var party_snd: AudioStreamPlayer3D
var _party_kind: = ""
const PARTY_C: = Vector3(52.0, 1.5, -23.0)

const VILLAGE: = Vector3(70, 0, 30)

static func ensure_buses() -> void :
	for b in ["Music", "SFX", "Ambiente"]:
		if AudioServer.get_bus_index(b) == -1:
			AudioServer.add_bus()
			var i: = AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "SFX" if b=="Ambiente" else "Master")

func _ready() -> void :
	add_to_group("audio")
	ensure_buses()
	bird_voice = AudioStreamPlayer3D.new()
	bird_voice.name = "AmbientBirds"
	bird_voice.process_mode = Node.PROCESS_MODE_PAUSABLE
	bird_voice.bus = "Ambiente"
	bird_voice.unit_size = 14.0
	bird_voice.max_db = 0.0
	bird_voice.max_distance = 50.0
	bird_voice.max_polyphony = 1
	add_child(bird_voice)
	music = _loop("reggae_praia", -20.0, "Music")
	ocean = _loop("ocean_loop", -8.0)
	crickets = _loop("crickets_loop", -60.0)
	rain_snd = _loop("rain_loop", -80.0)
	wind_snd = _loop("wind_loop", -80.0)
	for natural in [ocean,crickets,rain_snd,wind_snd]:natural.bus="Ambiente"
	party_snd = AudioStreamPlayer3D.new()
	party_snd.position = PARTY_C
	party_snd.unit_size = 9.0
	party_snd.max_distance = 70.0
	party_snd.bus = "Music"
	party_snd.volume_db = -4.0
	add_child(party_snd)

func _loop(n: String, db: float, bus: = "SFX") -> AudioStreamPlayer:
	var p: = AudioStreamPlayer.new()
	var s: AudioStream=load("res://assets/audio/%s.%s" % [n,"wav" if n=="reggae_praia" else "ogg"])
	if s is AudioStreamOggVorbis:s.loop=true
	elif s is AudioStreamWAV:
		s.loop_mode=AudioStreamWAV.LOOP_FORWARD
		s.loop_end=roundi(s.get_length()*s.mix_rate)
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
	music.volume_db = lerpf(-20.0, -24.0, _night) - village_k * 3.0 - home_duck
	_tick_birds(delta)
	if get_tree().paused:
		return
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

func _tick_birds(delta: float) -> void:
	if get_tree().paused:
		bird_voice.stop()
		return
	var silent := muted or not Core.in_game or _night>=.6 or Core.weather=="rain" or Core.day_event=="tempestade"
	for bus in ["Master","SFX","Ambiente"]:
		var index := AudioServer.get_bus_index(bus)
		if index>=0 and AudioServer.is_bus_mute(index): silent=true
	if silent or not is_instance_valid(player):
		bird_voice.stop()
		_bird_t=maxf(_bird_t,2.0)
		return
	# Cantos saem das árvores, não de um som plano preso à câmera.
	var nearby: Array[Vector3] = []
	var nearest_distance := INF
	for tree in BIRD_TREES:
		var distance: float=player.global_position.distance_to(tree)
		if distance<38.0:
			nearby.append(tree)
			nearest_distance=minf(nearest_distance,distance)
	if nearby.is_empty():
		bird_voice.stop()
		return
	var origins: Array[Vector3] = []
	for tree in nearby:
		if player.global_position.distance_to(tree)<=nearest_distance+8.0: origins.append(tree)
	if bird_voice.playing: return
	_bird_t-=delta
	if _bird_t>0: return
	_bird_t=randf_range(4.0,9.0)
	var sound := "bird1" if randf()<.5 else "bird2"
	if not _cache.has(sound): _cache[sound]=load("res://assets/audio/"+sound+".ogg")
	bird_voice.stream=_cache[sound]
	bird_voice.global_position=origins.pick_random()+Vector3(randf_range(-2,2),0,randf_range(-2,2))
	bird_voice.pitch_scale=randf_range(.94,1.06)
	var p: Vector3=player.global_position
	var indoors := p.x>42.5 and p.x<49.5 and p.z>17.5 and p.z<24.5
	bird_voice.volume_db=randf_range(-13.0,-10.0)-(8.0 if indoors else 0.0)
	bird_voice.play()

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

var _kiosk_cooldowns: Dictionary = {}
func kiosk_sfx(kind: String, pos: Vector3) -> void:
	if muted or get_tree().paused: return
	var now := Time.get_ticks_msec()
	if now - int(_kiosk_cooldowns.get(kind, -1000)) < 400: return
	_kiosk_cooldowns[kind] = now
	var sound := AudioStreamPlayer3D.new()
	sound.stream = load("res://assets/audio/kiosk_" + kind + ".wav")
	sound.position = pos
	sound.bus = "SFX"
	sound.volume_db = -18.0
	sound.unit_size = 2.0
	sound.max_distance = 12.0
	add_child(sound)
	sound.play()
	sound.finished.connect(sound.queue_free)

func at_position(sound_name: String,point: Vector3,db: float=-24.0,bus: String="SFX") -> void:
	if muted or get_tree().paused:return
	var voice:=AudioStreamPlayer3D.new()
	voice.stream=load("res://assets/audio/"+sound_name+(".wav" if sound_name=="leaves_soft" else ".ogg"))
	voice.bus=bus
	voice.position=point
	voice.volume_db=db
	voice.unit_size=3
	voice.max_distance=22
	voice.process_mode=Node.PROCESS_MODE_PAUSABLE
	add_child(voice)
	voice.play()
	voice.finished.connect(voice.queue_free)

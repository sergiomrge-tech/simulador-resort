extends Node
## Ciclo dia/noite. O céu usa Sky.PROCESS_MODE_INCREMENTAL e só é atualizado
## a cada 10 minutos de jogo (céu em tempo real trava em GPU fraca/llvmpipe).

var sun: DirectionalLight3D
var moon: DirectionalLight3D
var env: Environment
var sky_mat: ProceduralSkyMaterial
var world: Node3D
var _last_slot := -1

# chaves: hora -> [topo do céu, horizonte, cor do sol, energia do sol, ambiente]
const KEYS := [
	[0.0, Color(0.02, 0.04, 0.10), Color(0.06, 0.09, 0.16), Color(0.5, 0.6, 1.0), 0.0, 0.25],
	[5.0, Color(0.03, 0.05, 0.12), Color(0.10, 0.12, 0.2), Color(0.6, 0.6, 0.9), 0.0, 0.28],
	[6.0, Color(0.25, 0.35, 0.6), Color(0.98, 0.62, 0.42), Color(1.0, 0.6, 0.35), 0.5, 0.5],
	[8.0, Color(0.22, 0.48, 0.85), Color(0.75, 0.85, 0.95), Color(1.0, 0.9, 0.75), 1.15, 0.8],
	[12.0, Color(0.16, 0.45, 0.88), Color(0.68, 0.83, 0.96), Color(1.0, 0.97, 0.9), 1.35, 0.9],
	[16.0, Color(0.2, 0.46, 0.85), Color(0.78, 0.84, 0.92), Color(1.0, 0.88, 0.7), 1.2, 0.85],
	[17.6, Color(0.28, 0.36, 0.65), Color(1.0, 0.58, 0.32), Color(1.0, 0.55, 0.28), 0.7, 0.6],
	[18.6, Color(0.1, 0.12, 0.3), Color(0.55, 0.3, 0.3), Color(0.9, 0.4, 0.3), 0.05, 0.35],
	[19.5, Color(0.02, 0.04, 0.10), Color(0.06, 0.09, 0.16), Color(0.5, 0.6, 1.0), 0.0, 0.25],
	[24.0, Color(0.02, 0.04, 0.10), Color(0.06, 0.09, 0.16), Color(0.5, 0.6, 1.0), 0.0, 0.25],
]

func setup(parent: Node3D) -> void:
	sky_mat = ProceduralSkyMaterial.new()
	sky_mat.sun_angle_max = 20.0
	sky_mat.sun_curve = 0.12
	sky_mat.ground_bottom_color = Color(0.1, 0.25, 0.3)
	sky_mat.ground_horizon_color = Color(0.6, 0.75, 0.85)
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.1
	env.fog_enabled = true
	env.fog_light_color = Color(0.7, 0.82, 0.92)
	env.fog_density = 0.0016
	env.fog_sky_affect = 0.25
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.12
	env.adjustment_contrast = 1.04
	var we := WorldEnvironment.new()
	we.environment = env
	parent.add_child(we)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 45.0
	sun.shadow_bias = 0.04
	sun.shadow_normal_bias = 1.2
	sun.shadow_blur = 1.2
	parent.add_child(sun)
	moon = DirectionalLight3D.new()
	moon.light_color = Color(0.55, 0.65, 1.0)
	moon.light_energy = 0.0
	moon.shadow_enabled = false
	moon.rotation_degrees = Vector3(-50, 30, 0)
	parent.add_child(moon)
	if not Core.weather_changed.is_connected(_on_weather):
		Core.weather_changed.connect(_on_weather)

func _on_weather(_kind: String) -> void:
	apply()

func _bell(h: float, a: float, b: float) -> float:
	var mid := (a + b) * 0.5
	var half := maxf(0.2, (b - a) * 0.5)
	return clampf(1.0 - absf(h - mid) / half, 0.0, 1.0)

func _process(_d: float) -> void:
	var slot := int(Core.minutes / 10.0) + Core.day * 1000
	if slot != _last_slot:
		_last_slot = slot
		apply()

func force_update() -> void:
	_last_slot = -1
	apply()

func _sample(h: float) -> Array:
	for i in KEYS.size() - 1:
		var a: Array = KEYS[i]
		var b: Array = KEYS[i + 1]
		if h >= a[0] and h <= b[0]:
			var t: float = (h - a[0]) / maxf(0.001, b[0] - a[0])
			return [a[1].lerp(b[1], t), a[2].lerp(b[2], t), a[3].lerp(b[3], t), lerpf(a[4], b[4], t), lerpf(a[5], b[5], t)]
	return [KEYS[0][1], KEYS[0][2], KEYS[0][3], KEYS[0][4], KEYS[0][5]]

func apply() -> void:
	var h := Core.minutes / 60.0
	var k := _sample(h)
	# sol nasce a leste (+X) às 6h e se põe a oeste às 18h, passando pelo norte (mar)
	var t := clampf((h - 6.0) / 12.0, -0.1, 1.1)
	var elev := sin(t * PI) * 75.0
	# luz vem do leste de manhã, do sul (quase a pino, outubro no Nordeste) ao meio-dia e do oeste à tarde
	var yaw := 90.0 - 180.0 * t
	sun.rotation_degrees = Vector3(-maxf(elev, 4.0), yaw, 0)
	sun.light_color = k[2]
	sun.light_energy = k[3]
	sun.visible = k[3] > 0.01
	sky_mat.sky_top_color = k[0]
	sky_mat.sky_horizon_color = k[1]
	sky_mat.ground_horizon_color = k[1].darkened(0.1)
	sky_mat.sun_angle_max = 20.0
	env.ambient_light_energy = k[4]
	var night := clampf(1.0 - k[3] / 0.6, 0.0, 1.0)
	var golden := _bell(h, 16.4, 18.5)
	var rain := Core.weather == "rain"
	var fog_c: Color = k[1].lerp(Color(0.72, 0.82, 0.9), 0.35)
	if rain:
		fog_c = Color(0.55, 0.6, 0.66)
		sun.light_energy *= 0.42
		sun.light_color = sun.light_color.lerp(Color(0.75, 0.78, 0.82), 0.65)
	elif golden > 0.05:
		sun.light_color = sun.light_color.lerp(Color(1.0, 0.62, 0.32), golden * 0.55)
		sun.light_energy *= lerpf(1.0, 0.82, golden)
	env.fog_light_color = fog_c
	env.fog_density = 0.0048 if rain else lerpf(0.0014, 0.0028, golden)
	env.fog_aerial_perspective = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = (1.12 if not rain else 0.9) * lerpf(1.0, 1.08, golden)
	env.adjustment_enabled = true
	env.adjustment_saturation = (0.82 if rain else lerpf(1.05, 1.28, golden))
	env.adjustment_contrast = lerpf(1.04, 1.1, golden)
	env.adjustment_brightness = 0.94 if rain else 1.0
	env.volumetric_fog_albedo = fog_c
	env.volumetric_fog_density = 0.012 if rain else lerpf(0.004, 0.008, maxf(golden, night * 0.7))
	env.volumetric_fog_emission = fog_c * (0.15 if rain else 0.05)
	env.glow_intensity = 0.22 if rain else lerpf(0.4, 0.75, night)
	env.glow_bloom = 0.08 if night > 0.4 else 0.05
	moon.light_energy = (0.15 if rain else 0.42) * night
	moon.light_color = Color(0.65, 0.74, 1.0)
	env.ambient_light_sky_contribution = 0.35 if rain else 0.55
	env.ambient_light_color = Color(0.55, 0.58, 0.62) if rain else (k[2].lerp(Color(1.0, 0.86, 0.62), golden * 0.45) if k[3] > 0.05 else Color(0.22, 0.28, 0.45))
	if world:
		world.set_night(night)
	get_tree().call_group("audio", "set_night", night)

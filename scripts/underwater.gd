extends Node
## v0.9.5: efeito de mergulho (snorkel). Quando a câmera ativa fica abaixo da superfície do mar, liga um quad de tela inteira
## (shaders/underwater.gdshader: tinta azul, névoa pela distância, cáusticas) e bolhas subindo; desliga ao emergir.

var quad: MeshInstance3D
var bubbles: GPUParticles3D
var _cam: Camera3D
var world: Node3D

func _ready() -> void:
	quad = MeshInstance3D.new()
	var qm: = QuadMesh.new()
	qm.size = Vector2(1, 1)
	quad.mesh = qm
	var sm: = ShaderMaterial.new()
	sm.shader = load("res://shaders/underwater.gdshader")
	quad.material_override = sm
	quad.extra_cull_margin = 16384.0
	quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	quad.visible = false
	bubbles = GPUParticles3D.new()
	bubbles.amount = 40
	bubbles.lifetime = 2.5
	var pm: = ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(1.2, 0.4, 1.2)
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 12.0
	pm.initial_velocity_min = 0.3
	pm.initial_velocity_max = 0.7
	pm.gravity = Vector3(0, 0.6, 0)
	pm.scale_min = 0.4
	pm.scale_max = 1.2
	bubbles.process_material = pm
	var bq: = QuadMesh.new()
	bq.size = Vector2(0.04, 0.04)
	var bmat: = StandardMaterial3D.new()
	bmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	bmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	var gt: = GradientTexture2D.new()
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.0, 0.5)
	var g: = Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.55, 0.75, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 0.08), Color(1, 1, 1, 0.15), Color(1, 1, 1, 0.75), Color(1, 1, 1, 0.0)])
	gt.gradient = g
	bmat.albedo_texture = gt
	bq.material = bmat
	bubbles.draw_pass_1 = bq
	bubbles.emitting = false
	bubbles.visible = false

func water_level() -> float:
	var om: ShaderMaterial = world.get("ocean_mat") if world else null
	var tide: float = float(om.get_shader_parameter("tide")) if om and om.get_shader_parameter("tide") != null else 0.0
	return -0.3 + tide   # WATER_Y do world.gd

func _process(_d: float) -> void:
	var cam: = get_viewport().get_camera_3d()
	if cam == null:
		return
	if cam != _cam:
		_cam = cam
		if quad.get_parent():
			quad.get_parent().remove_child(quad)
		if bubbles.get_parent():
			bubbles.get_parent().remove_child(bubbles)
		cam.add_child(quad)
		cam.add_child(bubbles)
		bubbles.position = Vector3(0, -0.6, -1.2)
	var p: = cam.global_position
	var under: = p.y < water_level() - 0.05 and p.z < -24.0
	if world and world.has_method("_height"):
		under = under and float(world.call("_height", p.x, p.z)) < p.y
	quad.visible = under
	bubbles.visible = under
	bubbles.emitting = under

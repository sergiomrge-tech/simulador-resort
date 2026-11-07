extends SceneTree
## Executável também em projeto mínimo, sem downloads de assets/autoloads.
const StateWaiter = preload("res://tests/support/state_waiter.gd")
const People = preload("res://scripts/people.gd")
var failed := false

class Customer extends Node:
	var state := "kwalk"

func check(ok: bool, message: String) -> void:
	print("LIFECYCLE_TEST ", "OK " if ok else "FAIL ", message)
	failed = failed or not ok

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var customer := Customer.new()
	root.add_child(customer)
	customer.set_deferred("state", "kwait")
	check(await StateWaiter.until_state(self, weakref(customer), "kwait", 1.0), "chegada assíncrona")
	customer.state = "kleave"
	check(not await StateWaiter.until_state(self, weakref(customer), "kwait", 1.0), "saída encerra espera")
	customer.state = "kwalk"
	check(not await StateWaiter.until_state(self, weakref(customer), "kwait", 0.02), "timeout sem pedido")
	customer.queue_free()
	check(not await StateWaiter.until_state(self, weakref(customer), "kwait", 1.0), "exclusão agendada")
	await process_frame
	customer = Customer.new()
	root.add_child(customer)
	var reference: WeakRef = weakref(customer)
	customer.call_deferred("queue_free")
	check(not await StateWaiter.until_state(self, reference, "kwait", 1.0), "cliente liberado durante espera")
	await process_frame
	check(reference.get_ref() == null, "referência fraca expirada")
	check(not await StateWaiter.until_state(self, reference, "kwait", 1.0), "cliente já liberado")

	# Simula as cenas importadas mantendo owners, animações, mesh e skin.
	var body := Node3D.new()
	var body_scene := PackedScene.new()
	body_scene.pack(body)
	body.free()
	People._scenes["m"] = body_scene
	var source := Node3D.new()
	var ap := AnimationPlayer.new()
	ap.name = "AnimationPlayer"
	source.add_child(ap)
	ap.owner = source
	var library := AnimationLibrary.new()
	library.add_animation("Idle", Animation.new())
	ap.add_animation_library("", library)
	People._anim_src = PackedScene.new()
	People._anim_src.pack(source)
	source.free()
	var model: Node3D = People.build_body(false)
	root.add_child(model)
	var player: AnimationPlayer = model.get_node("AnimationPlayer")
	check(player.owner == null and player.has_animation("Idle"), "enxerto preserva animação sem owner antigo")
	var hair_source := Node3D.new()
	var mesh := MeshInstance3D.new()
	mesh.mesh = BoxMesh.new()
	mesh.skin = Skin.new()
	hair_source.add_child(mesh)
	mesh.owner = hair_source
	var child := Node3D.new()
	mesh.add_child(child)
	child.owner = hair_source
	var hair_scene := PackedScene.new()
	hair_scene.pack(hair_source)
	People._hairs["Fixture"] = hair_scene
	hair_source.free()
	var hair: MeshInstance3D = People.hair_mesh("Fixture")
	model.add_child(hair)
	check(hair.owner == null and hair.get_child(0).owner == null, "cabelo e descendentes sem owner antigo")
	check(hair.mesh != null and hair.skin != null, "mesh e skin preservados")
	model.queue_free()
	await process_frame
	People._scenes.clear()
	People._hairs.clear()
	People._anim_src = null
	print("LIFECYCLE_TEST ", "FAIL" if failed else "PASS")
	quit(1 if failed else 0)

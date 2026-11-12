extends Node
var failed:=false
func check(ok: bool,message: String) -> void:
	failed=failed or not ok
	print("[optimization] ","ok " if ok else "FAIL ",message)
func run(main) -> void:
	Core.paused=true
	Core.in_game=false
	main.allow_faint=false
	main.guests.enabled=false
	main.village.enabled=false
	# Deixar a inicialização diferida concluir antes de iniciar o encerramento.
	for i in 30: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var source:=StandardMaterial3D.new()
	source.albedo_color=Color(.7,.8,.9)
	source.resource_name="tint_test"
	var first: Material=Real.styled_material(source,Color.WHITE,false)
	check(first==Real.styled_material(source,Color.WHITE,false),"objetos iguais compartilham material")
	check(first!=Real.styled_material(source,Color(.8,.2,.1),false),"cores diferentes continuam independentes")
	check(source.albedo_color==Color(.7,.8,.9),"cache preserva o material original")
	check(first!=Real.styled_material(source,Color(1.2,1.2,1.2),false),"tons HDR de iluminação não colidem com branco no cache")
	# Recursos de teste pertencem à cena, para o encerramento reter/liberar o renderer.
	var roots: Array=[]
	for i in 2:
		var root:=Node3D.new()
		main.add_child(root)
		var instance:=MeshInstance3D.new()
		var mesh:=BoxMesh.new()
		mesh.material=source
		instance.mesh=mesh
		instance.set_surface_override_material(0,first)
		root.add_child(instance)
		roots.append(root)
	Real.tint_named(roots[0],Color(.8,.1,.1))
	check(roots[0].get_child(0).get_active_material(0)!=roots[1].get_child(0).get_active_material(0),"pintura de uma instância não vaza para as outras")
	var guest=preload("res://scripts/guest.gd").new()
	main.add_child(guest)
	guest.set_process(false)
	var rng:=RandomNumberGenerator.new()
	rng.seed=8080
	for i in 80:
		guest.block_rects.append(Rect2(rng.randf_range(-30,30),rng.randf_range(-30,30),rng.randf_range(.1,12),rng.randf_range(.1,12)))
	var equal:=true
	for i in 1200:
		var from:=Vector3(rng.randf_range(-30,30),0,rng.randf_range(-30,30))
		var to:=from+Vector3(rng.randf_range(-3,3),0,rng.randf_range(-3,3))
		guest._route=[Vector3(rng.randf_range(-30,30),0,rng.randf_range(-30,30))]
		guest._local_block_frame=-1
		guest.use_block_cache=false
		var expected: Vector3=guest._slide_out_of_blocks(from,to)
		guest.use_block_cache=true
		var actual: Vector3=guest._slide_out_of_blocks(from,to)
		if not actual.is_equal_approx(expected): equal=false
	check(equal,"busca local mantém a mesma colisão em 1200 trajetos, inclusive destinos e blocos sobrepostos")
	check(main.operations.find_child("CounterDisplay",true,false)==null,"PC removido não mantém SubViewport desenhando em segundo plano")
	print("OPTIMIZATION_TEST FAIL" if failed else "OPTIMIZATION_TEST PASS")
	Core.quit_game(1 if failed else 0)

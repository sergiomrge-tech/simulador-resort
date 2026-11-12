extends Node
var failed:=false
func check(ok: bool,message: String) -> void:
	failed=failed or not ok
	print("[single-staff] ","ok " if ok else "FAIL ",message)
func run(main) -> void:
	Core.new_game()
	Core.paused=true
	Core.in_game=false
	main.allow_faint=false
	main.village.enabled=false
	main.guests.enabled=false
	Core.configure_company("Atendimento Único","praia")
	Core.money=10000
	Core.staff.garcom=true
	Core.staff.caixa=true
	Core.staff.limpeza=true
	Core.prog.staff_rec("garcom").lvl=3
	Core.prog.staff_rec("garcom").xp=150
	Core.company.sim.shifts.garcom={"start":8,"end":18}
	Core.company.sim.management.profiles.garcom={"kind":1,"morale":85.0}
	var cash: int=Core.money
	Core.consolidate_kiosk_staff()
	check(Core.staff.atendente and not Core.staff.garcom and not Core.staff.caixa and not Core.staff.limpeza,"contratações antigas viram um atendente")
	check(Core.prog.staff_rec("atendente").lvl==3 and Core.prog.staff_rec("atendente").xp==150,"experiência do funcionário mais treinado preservada")
	check(Core.company.sim.shifts.atendente.end==18 and Core.company.sim.management.profiles.atendente.kind==1,"turno e perfil preservados")
	check(Core.prog.staff_info.has("garcom") and Core.money==cash,"histórico preservado sem rescisão ou nova cobrança")
	Core.consolidate_kiosk_staff()
	check(Core.money==cash and Core.prog.staff_rec("atendente").lvl==3,"migração repetida não duplica custos nem treinamento")
	var path: String=Core.SAVE_PATH
	Core.SAVE_PATH="user://single_staff_tmp.json"
	Core.save_game()
	Core.staff.atendente=false
	check(Core.load_game() and Core.staff.atendente and not Core.staff.garcom,"save recarrega um único funcionário")
	var wage: int=Core.prog.staff_wage("atendente")
	Core._pay_wages(true)
	check(Core.money==cash-wage,"folha cobra apenas um salário")
	Core._pay_wages(true)
	check(Core.money==cash-wage,"salário não é cobrado duas vezes no mesmo dia")
	Core.staff.atendente=false
	Core.staff_changed.emit()
	Core.money=10000
	check(Core.hire("atendente"),"contrata atendente único")
	var paid: int=Core.money
	check(not Core.hire("caixa") and not Core.hire("garcom") and not Core.hire("limpeza") and not Core.hire("cozinheiro") and not Core.hire("atendente") and Core.money==paid,"não permite cargos duplicados nem cobra tentativas recusadas")
	Core.minutes=17*60
	check(Core.prog.staff_eff("atendente")>0,"novo atendente cobre todo o expediente por padrão")
	main.hud.phone.open("equipe")
	for i in 5: await get_tree().process_frame
	var roles:=0
	for actor in main.operations.actors.values():
		if actor.visible: roles+=1
	check(roles==1 and main.operations.actors.atendente.visible,"apenas um funcionário aparece no quiosque")
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
		get_viewport().get_texture().get_image().save_png("user://qa_shots/atendente_unico.png")
	main.hud.phone.close()
	Core.delete_save()
	Core.SAVE_PATH=path
	print("SINGLE_STAFF_TEST FAIL" if failed else "SINGLE_STAFF_TEST PASS")
	Core.quit_game(1 if failed else 0)

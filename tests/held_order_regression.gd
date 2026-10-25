extends Node3D
var failed:=false
func check(ok: bool,message: String) -> void:
 failed=failed or not ok
 print("[held-order] ","ok " if ok else "FAIL ",message)
func frames(count: int) -> void:
 for i in count: await get_tree().process_frame
func shot(main,g,label: String) -> void:
 main.player.position=g.global_position+Vector3(0,0,2.0)
 main.player.cam.look_at(g.global_position+Vector3(0,1.05,0))
 await frames(30)
 await RenderingServer.frame_post_draw
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
 get_viewport().get_texture().get_image().save_png("user://qa_shots/"+label+".png")
func run(main) -> void:
 Core.new_game()
 Core.set_process(false)
 Core.in_game=false
 Core.paused=false
 Core.configure_company("Sorvetes da Praia","praia")
 Core.minutes=11*60
 Core.time_changed.emit(Core.day,Core.minutes)
 Core.money=10000
 main.allow_faint=false
 main.player.set_physics_process(false)
 main.village.enabled=false
 main.village.set_process(false)
 main.guests.enabled=false
 main.operations.set_process(false)
 main.day.force_update()
 var presentation=load("res://scripts/dish_presentation.gd")
 for id in ["sorvete_morango","sorvete_chocolate"]:
  check(id in Core.kiosk_menu() and presentation.is_chilled(id) and not presentation.is_drink(id),"sorvete disponível na geladeira sem receita secreta: "+id)
  Core.stock[id]=0
  var quote: Dictionary=Core.company_restock_quote(id,10)
  var money: int=Core.money
  check(Core.restock_company_dish(id,10) and Core.money==money-int(quote.cost),"reposição usa cotação real e uma cobrança: "+id)
  var amount: int=Core.company_available(id)
  check(Core.pickup_company_dish(id) and Core.company_available(id)==amount-1,"retira pronto com um desconto: "+id)
  check(Core.return_company_dish() and Core.company_available(id)==amount,"devolução não duplica unidades: "+id)
  var used: Node3D=presentation.build_used(self,id)
  check(used.get_meta("container")=="g:used_icecream_cup","consumo deixa pote vazio com colher: "+id)
 main.operations._sync_products()
 for id in ["sorvete_morango","sorvete_chocolate"]:
  check(main.operations.products.has_node("Shelf_"+id),"geladeira exibe "+id)
 var g=main.village._make()
 g.global_position=Vector3(45,.1,-23)
 g.go([])
 g.set_process(false)
 await frames(10)
 for items in [["sorvete_morango"],["suco"],["coco_gelado","sorvete_chocolate","suco"]]:
  g.hold_order(items)
  await frames(10)
  g.play("Walk_Loop")
  var exact:=true
  for i in 40:
   g.rotation.y=float(i)*.06
   g.position.x+=.005
   await RenderingServer.frame_post_draw
   if g._held_root.global_position.distance_to(g._held_anchor.global_position)>.008: exact=false
  check(exact,"produtos seguem a mão em cada quadro durante giro/deslocamento: "+str(items))
  check(g._held_tray==(items.size()>1),"bandeja apoiada para pedido misto")
  g.rotation.y=0
  g.play("Idle_Loop")
  await shot(main,g,"held_"+str(items[0])+"_"+str(items.size()))
  g.clear_held_order()
  await frames(3)
  check(not g.has_node("CustomerTray") and not g.has_meta("hand_carry"),"remove transporte ao sentar/sair sem órfãos")
 g.consume_dish("sorvete_chocolate")
 await shot(main,g,"icecream_dining")
 g._set_eating(false)
 var prior: Dictionary=Core.stock.duplicate()
 var path: String=Core.SAVE_PATH
 Core.SAVE_PATH="user://icecream_tmp.json"
 Core.save_game()
 Core.stock.sorvete_morango=0
 check(Core.load_game() and Core.stock==prior,"estoque de sorvete preservado ao salvar/carregar")
 Core.delete_save()
 Core.SAVE_PATH=path
 print("HELD_ORDER_TEST FAIL" if failed else "HELD_ORDER_TEST PASS")
 Core.quit_game(1 if failed else 0)


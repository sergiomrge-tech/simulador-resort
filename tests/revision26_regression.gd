extends Node
var failed:=false
func check(ok: bool,message: String) -> void:
 failed=failed or not ok
 print("[revision26] ","ok " if ok else "FAIL ",message)
func frames(count: int) -> void:
 for i in count:await get_tree().process_frame
func shot(main,name: String,pos: Vector3,look: Vector3) -> Image:
 main.player.position=pos
 main.player.cam.look_at(look)
 main.player.refresh_focus()
 main.day.force_update()
 await frames(18)
 await RenderingServer.frame_post_draw
 var image: Image=get_viewport().get_texture().get_image()
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
 image.save_png("user://qa_shots/"+name+".png")
 return image
func run(main) -> void:
 Core.new_game()
 Core.set_process(false)
 Core.paused=false
 Core.in_game=false
 Core.minutes=11*60
 main.allow_faint=false
 main.village.enabled=false
 main.village.set_process(false)
 main.guests.enabled=false
 main.operations.set_process(false)
 main.player.set_physics_process(false)
 var world=main.world
 var ops=main.operations
 var C=Core.prog.Campaign
 check(C.current(Core.prog).id=="chegada" and not C.claim(Core.prog,"chegada"),"campanha começa com criação da empresa, sem recompensa grátis")
 Core.money=10000
 Core.configure_company("Uma Nova Maré","praia")
 for mission in C.MAIN:
  match str(mission.kind):
   "company":pass
   "open":Core.company.kiosk_open=true
   "sales":Core.kiosk_sales_count=8
   "expansion":Core.unlocked[str(mission.item)]=true
   "staff":Core.staff.atendente=true
   "chapter":Core.prog.chapters[str(mission.item)]=3
  var cash: int=Core.money
  check(C.claim(Core.prog,str(mission.id)) and Core.money==cash+int(mission.reward),"campanha progride e paga uma vez: "+str(mission.id))
  check(not C.claim(Core.prog,str(mission.id)),"missão principal não repete prêmio")
 check(C.current(Core.prog).is_empty(),"campanha tem final após dez capítulos")
 Core.prog.campaign.fish=5
 var cash: int=Core.money
 check(C.claim(Core.prog,"pescador",true) and not C.claim(Core.prog,"pescador",true) and Core.money==cash+80,"secundária independente, sem repetir prêmio")
 var data: Dictionary=Core.prog.to_dict()
 Core.prog.from_dict(data)
 check(Core.prog.campaign.stage==10 and "pescador" in Core.prog.campaign.side_done,"campanha e secundárias persistem no save")
 Core.prog.from_dict({})
 check(Core.prog.campaign.stage==0,"save antigo recebe campanha sem apagar dados externos")
 Core.prog.campaign.stage=2
 Core.staff.atendente=false
 Core.company.kiosk_open=true
 Core.minutes=11*60
 for ingredient in Core.stock:Core.stock[ingredient]=100
 for dish in ["batata_frita","porcao_peixe"]:
  var stock: Dictionary=Core.stock.duplicate()
  var money: int=Core.money
  var price: int=Core.price_of(dish)
  check(dish in Core.kiosk_menu() and Core.pickup_company_dish(dish),"porção pronta liberada: "+dish)
  var after: Dictionary=Core.stock.duplicate()
  check(Core.sell_company_dish(dish)==price and Core.money==money+price and Core.stock==after and Core.company.receivables.is_empty(),"retirada desconta uma vez e entrega já paga: "+dish)
  check(Core.sell_company_dish(dish)==-1 and Core.collect_company_payments()==0 and Core.money==money+price,"entrega não pode pagar duas vezes")
 var save_path: String=Core.SAVE_PATH
 Core.SAVE_PATH="user://revision26_tmp.json"
 Core.company.receivables=[{"dish":"suco","value":7}]
 cash=Core.money
 Core.save_game()
 check(Core.load_game() and Core.money==cash+7 and Core.company.receivables.is_empty(),"conta histórica liquidada automaticamente ao carregar")
 Core.save_game()
 check(Core.load_game() and Core.money==cash+7,"recarregar não duplica pagamento histórico")
 Core.delete_save()
 Core.SAVE_PATH=save_path
 Core.company.kiosk_open=true
 var boundary_ok:=true
 for occ in world.find_children("*","OccluderInstance3D",true,false):
  if occ.occluder is BoxOccluder3D:
   var bounds:=AABB(occ.global_position-occ.occluder.size*.5,occ.occluder.size)
   if bounds.has_point(world.HOME_C+Vector3(0,1.3,0)):boundary_ok=false
 check(boundary_ok,"nenhuma caixa sólida de oclusão preenche a casa acessível")
 main.hud.root.visible=false
 Core.set_weather("sun")
 var dry: Image=await shot(main,"praia_sol",Vector3(26,.15,-24),Vector3(26,.1,-13))
 Core.set_weather("rain")
 var rainy: Image=await shot(main,"praia_chuva",Vector3(26,.15,-24),Vector3(26,.1,-13))
 var dry_white:=0
 var rain_white:=0
 var samples:=0
 for y in range(int(dry.get_height()*.5),dry.get_height(),4):
  for x in range(0,dry.get_width(),4):
   var a: Color=dry.get_pixel(x,y)
   var b: Color=rainy.get_pixel(x,y)
   if minf(a.r,minf(a.g,a.b))>.80:dry_white+=1
   if minf(b.r,minf(b.g,b.b))>.80:rain_white+=1
   samples+=1
 check(float(rain_white-dry_white)/maxi(1,samples)<.08,"chuva não espalha espuma branca pelo chão: excesso "+str(float(rain_white-dry_white)/maxi(1,samples)))
 check(world.rain.emitting and float(world.sand_mat.get_shader_parameter("rain_wet"))>0,"chuva mantém gotas e areia úmida")
 Core.set_weather("sun")
 main.hud.root.visible=false
 var home: Vector3=world.HOME_C
 get_viewport().use_occlusion_culling=false
 var control: Image=await shot(main,"casa_janela_controle",home+Vector3(-1.7,.12,4.3),home+Vector3(-1.1,1.65,-.2))
 get_viewport().use_occlusion_culling=true
 var optimized: Image=await shot(main,"casa_janela_corrigida",home+Vector3(-1.7,.12,4.3),home+Vector3(-1.1,1.65,-.2))
 var error:=0.0
 var count:=0
 for y in range(int(control.get_height()*.25),int(control.get_height()*.80),5):
  for x in range(int(control.get_width()*.25),int(control.get_width()*.75),5):
   var a: Color=control.get_pixel(x,y)
   var b: Color=optimized.get_pixel(x,y)
   error+=absf(a.r-b.r)+absf(a.g-b.g)+absf(a.b-b.b)
   count+=3
 check(error/maxi(1,count)<.025,"imagem da janela mantém o interior com oclusão ligada: erro "+str(error/maxi(1,count)))
 await shot(main,"casa_interior",home+Vector3(1.4,.18,2.8),home+Vector3(-1,1.2,-1))
 var coast=main.get_node("CoastalLife")
 check(coast.yacht.position.z<=-220,"navio passa ao fundo a mais de 190 m da praia")
 await shot(main,"navio_distante",Vector3(38,.15,-29),coast.yacht.position+Vector3(0,8,0))
 await shot(main,"rua_principal",Vector3(12,.15,30),Vector3(80,1.4,30))
 await shot(main,"rua_fundos",Vector3(9,.15,64),Vector3(78,1.4,64))
 await shot(main,"passeio_vila",Vector3(103,.15,48),Vector3(84,1.4,48))
 main.hud.root.visible=true
 check(ops.computer==null and ops.computer_target==null and ops.find_child("CounterDisplay",true,false)==null,"PC, alvo e tela física removidos")
 main.player.position=world.HOME_C
 main.hud.toggle_shop()
 check(main.hud.phone.visible and main.hud.phone._phone.size.x<main.hud.phone._phone.size.y,"celular portátil vertical abre longe do balcão")
 main.hud.phone.close()
 var guests: Array=[]
 for slot in 2:
  var g=main.village.spawn_customer()
  check(g!=null,"cliente disponível na retirada "+str(slot+1))
  if g==null:continue
  g.go([])
  g.set_process(false)
  g.position=g.spot.pos
  g.set_meta("items",["suco","batata_frita"])
  g.set_meta("delivered",0)
  main.village._order(g)
  ops._process(0)
  guests.append(g)
  main.player.position=world.kiosk_point(Vector3(-.7+slot*1.4,.1,.15))
  main.player.cam.look_at(g.global_position+Vector3(0,1.2,0))
  await frames(6)
  main.player.refresh_focus()
  check(main.player.focus!=null and main.player.focus.has_meta("customer_ref"),"mira alcança cliente pelo lado interno "+str(slot+1))
  main.player.interact()
  check(bool(g.get_meta("order_taken",false)),"E anota pelo balcão "+str(slot+1))
  check(not g._bubble.text.contains("#00"),"pedido usa número da reserva, sem #00")
 main.hud._update_orders()
 main.player.position=world.HOME_C
 main.hud._update_orders()
 check(not main.hud.orders_text.text.is_empty(),"pedidos persistem ao sair de perto e olhar para outro lado")
 Core.service_station="bebidas"
 main.player.position=world.kiosk_point(Vector3(-1.2,.1,-.7))
 main.hud.phone.open("servico")
 await frames(8)
 main.hud._process(0)
 check(main.hud.orders_panel.visible and main.hud.orders_panel.global_position.x<40,"pedidos continuam à esquerda com estação aberta")
 check(main.hud.phone._phone.get_global_rect().position.x>main.hud.orders_panel.get_global_rect().end.x,"estação compacta deixa pedidos livres à esquerda")
 for button in main.hud.phone.find_children("*","Button",true,false):
  if button.text=="Pegar":check(button.size.x<200,"botão Pegar compacto")
 await shot(main,"geladeira_hud_compacto",main.player.position,ops.stations.bebidas.global_position+Vector3(0,.9,0))
 main.hud.phone.close()
 Core.service_station="pratos"
 main.player.position=world.kiosk_point(Vector3(0,.1,-.65))
 ops._sync_products()
 for id in ["batata_frita","porcao_peixe"]:
  var display=ops.products.get_node_or_null("Shelf_"+id)
  check(display!=null and not display.find_children("*","MeshInstance3D",true,false).is_empty(),"expositor tem modelo detalhado distinto: "+id)
 main.hud.phone.open("servico")
 await shot(main,"porcoes_retirada",main.player.position,ops.stations.pratos.global_position+Vector3(0,.55,0))
 main.hud.phone.close()
 await shot(main,"porcoes_expositor",main.player.position,ops.stations.pratos.global_position+Vector3(0,.55,0))
 main.hud.phone.open("missoes")
 await shot(main,"campanha_principal_secundarias",main.player.position,world.kiosk_point(Vector3(0,1.4,2)))
 for button in main.hud.phone.find_children("*","Button",true,false):
  if button.text.begins_with("Concluir"):check(button.size.x<240,"Concluir ocupa apenas a largura do texto e margens")
 main.hud.phone.close()
 for slot in guests.size():
  var g=guests[slot]
  var number: String=ops.order_number(g)
  main.player.position=world.kiosk_point(Vector3(-.7+slot*1.4,.1,.15))
  main.player.cam.look_at(g.global_position+Vector3(0,1.2,0))
  for dish in ["suco","batata_frita"]:
   check(Core.pickup_company_dish(dish),"retira produto para entrega interna")
   await frames(3)
   main.player.refresh_focus()
   main.player.interact()
   main.hud._update_orders()
   check(int(g.get_meta("delivered",0))==(1 if dish=="suco" else 2),"E entrega pelo lado interno nos dois lugares")
   check(main.hud.orders_text.text.contains(number)==(dish=="suco"),"pedido permanece na entrega parcial e some após último item")
 check(Core.company.receivables.is_empty(),"todas as entregas terminam pagas, sem receber no caixa")
 for g in guests:main.village._leave(g)
 print("REVISION26_TEST FAIL" if failed else "REVISION26_TEST PASS")
 Core.quit_game(1 if failed else 0)

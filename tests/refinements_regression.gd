extends "res://tests/revision26_regression.gd"
func run(main) -> void:
 Core.new_game()
 Core.set_process(false)
 Core.money=10000
 Core.configure_company("Maré Serena","praia")
 Core.minutes=11*60
 Core.time_changed.emit(Core.day,Core.minutes)
 Core.company.kiosk_open=true
 Core.paused=false
 Core.in_game=false
 main.allow_faint=false
 main.village.enabled=false
 main.village.set_process(false)
 main.guests.enabled=false
 main.operations.set_process(false)
 main.player.set_physics_process(false)
 main.menu_cam.current=false
 main.player.cam.current=true
 var ref=main.get_node("Refinements")
 var phone=main.hud.phone
 await frames(30)
 check("missoes" in phone.HOME_APPS and phone.HOME_APPS.size()==6,"Missões em aba direta, seis áreas")
 phone.open("painel")
 await frames(8)
 check(phone.company_open_button.text=="Fechar quiosque" and phone.company_open_button.size.x>140 and phone.company_open_button.size.y<70,"Fechar quiosque tem largura de texto e altura compacta")
 Core.company.kiosk_open=false
 phone._refresh_kiosk_controls()
 await frames(8)
 check(phone.company_open_button.text=="Abrir quiosque" and phone.company_open_button.size.x>140,"Abrir recalcula largura")
 Core.company.kiosk_open=true
 phone.open("compras")
 await frames(8)
 var pictures: Array=phone.find_children("*","TextureRect",true,false).filter(func(n):return n.texture!=null and str(n.texture.resource_path).contains("products/"))
 check(pictures.size()==Core.kiosk_menu().size(),"compras mostra imagem de cada produto")
 var cash: int=Core.money
 for id in ref.DECOR:
  check(ref.buy_decor(id),"compra melhoria visual: "+str(id))
  check(not ref.buy_decor(id),"melhoria não cobra duas vezes")
  check(ref.decor_nodes[id].visible,"melhoria aparece no cenário")
 check(Core.money==cash-360,"custos reais das três melhorias")
 var saved: Dictionary=Core.prog.to_dict()
 Core.prog.from_dict(saved)
 check(Core.prog.experience.decor.size()==3,"melhorias persistem")
 var resident=main.village.get_children().filter(func(n):return n.has_meta("resident_name") and n.get_meta("resident_name")=="Dona Rita")[0]
 main.player.position=resident.global_position+Vector3(0,.1,-2.0)
 main.player.cam.look_at(resident.global_position+Vector3(0,1.6,0))
 await frames(4)
 main.player.refresh_focus()
 check(main.player.focus!=null and main.player.focus.get_prompt().contains("Dona Rita"),"mira E encontra conversa da moradora")
 main.player.interact()
 await frames(8)
 check(phone.app=="conversa" and Core.prog.experience.greeted.has("Dona Rita"),"conversa física apresenta campanha no celular")
 var claim=phone.find_children("*","Button",true,false).filter(func(b):return b.text=="Concluir etapa")[0]
 var before_claim: int=Core.money
 claim.pressed.emit()
 await frames(6)
 check(Core.prog.campaign.stage==1 and Core.money==before_claim+40,"conversa conclui etapa e paga uma vez")
 check(not Core.prog.Campaign.claim(Core.prog,"chegada"),"conversa não duplica recompensa")
 phone.close()
 check(not phone.visible,"conversa fecha com celular")
 check(main.audio.music.stream is AudioStreamWAV and main.audio.music.stream.get_length()>47.9 and main.audio.music.stream.loop_mode==AudioStreamWAV.LOOP_FORWARD,"reggae original 48s em loop")
 check(main.audio.bird_voice.bus=="Ambiente" and main.audio.ocean.bus=="Ambiente","ambiente e música em volumes separados")
 var old: Dictionary={"shadows":Quality.shadows,"vegetation":Quality.vegetation,"population":Quality.population,"detail_distance":Quality.detail_distance,"show_fps":Quality.show_fps}
 Quality.set_detail("shadows",0)
 check(not ref.find_child("KioskContactShadows",true,false).shadow_enabled,"sombras desligam pelo controle")
 Quality.set_detail("shadows",2)
 check(ref.find_child("KioskContactShadows",true,false).shadow_enabled and main.day.sun.shadow_normal_bias<.5,"sombras de contato habilitadas, bias moderado")
 Quality.set_detail("vegetation",.35)
 var vegetation: Array=get_tree().get_nodes_in_group("scalable_vegetation")
 check(not vegetation.is_empty() and vegetation.any(func(n):return n.multimesh.visible_instance_count<n.multimesh.instance_count),"controle reduz vegetação real")
 Quality.set_detail("population",4)
 check(main.village.walkers.size()==4,"controle reduz pedestres reais")
 Quality.set_detail("population",12)
 check(main.village.walkers.size()==12,"pedestres podem voltar sem reconstruir mapa")
 Quality.set_detail("detail_distance",.7)
 Quality.set_detail("show_fps",true)
 await frames(8)
 var cfg:=ConfigFile.new()
 cfg.load(Quality.CFG)
 check(ref.fps.visible and cfg.get_value("video","show_fps",false) and is_equal_approx(float(cfg.get_value("video","detail_distance",0)),.7),"opções e FPS persistem em settings isolado")
 for key in old:Quality.set_detail(key,old[key])
 var a=main.village.walkers[0]
 var b=main.village.walkers[1]
 a.go([])
 b.go([])
 a.position=Vector3(54,.15,30)
 b.position=Vector3(55.4,.15,30)
 a.set_meta("routine_cooldown",0.0)
 check(main.village._day_routine(a,1,.1) and a.get_meta("routine_kind","")=="conversa","pedestres alternam caminhada e conversa")
 a.remove_meta("routine_until")
 a.set_meta("routine_cooldown",0.0)
 var seat: Dictionary=main.world.bench_spots[-1]
 a.position=seat.pos+Vector3(0,0,.85).rotated(Vector3.UP,seat.rot)
 check(main.village._day_routine(a,0,.1) and a.has_meta("routine_seat"),"morador caminha até banco livre")
 a.go([])
 check(main.village._day_routine(a,0,.1) and a.get_meta("routine_kind","")=="banco","morador senta após chegar à abordagem")
 var saved_day: int=Core.day
 var saved_minute: float=Core.minutes
 Core.day+=1
 Core.minutes=6*60+30
 main.village._day_routine(a,0,.1)
 check(not a.has_meta("routine_until"),"descanso expira mesmo ao dormir e voltar ao amanhecer")
 var stand: Vector3=a.position
 a.set_meta("routine_until",Core.day*1440.0+Core.minutes-1)
 a.set_meta("routine_return",stand+Vector3(12,0,0))
 main.village._day_routine(a,0,.1)
 check(a.position.is_equal_approx(stand),"rotina expirada não teleporta quem já voltou para casa")
 Core.day=saved_day
 Core.minutes=saved_minute
 var dogs: Array=get_tree().get_nodes_in_group("village_animals").filter(func(animal):return animal.kind=="dog")
 if not dogs.is_empty():
  a.position=dogs[0].position+Vector3(1.7,0,0)
  ref._dog_walk()
  check(dogs[0].walking_partner!=null and dogs[0].walking_partner.get_ref()!=null,"cachorro pode acompanhar morador existente")
 for i in 4:
  var guest=main.village.spawn_customer()
  if guest!=null:check(guest.get_meta("preference","") in ["refrescos","sorvetes","porcoes"] and guest.gname.contains(" "),"cliente tem perfil e nome identificável")
 var c: Vector3=main.world.HOME_C
 var bathroom=main.world.get_node("HomeBathroom")
 check(bathroom.find_children("*","MeshInstance3D",true,false).size()>8,"banheiro tem modelos detalhados e arquitetura")
 var door=bathroom.get_node("BathroomDoor")
 main.player.position=bathroom.to_global(Vector3(-2.3,0,-.075))
 main.player.cam.look_at(door.to_global(Vector3(-.575,1.1,0)))
 await frames(4)
 main.player.refresh_focus()
 check(main.player.focus!=null and main.player.focus.get_prompt().contains("banheiro"),"mira encontra porta do banheiro")
 main.player.interact()
 await get_tree().create_timer(.6).timeout
 check(door.opened and not door.moving,"porta do banheiro abre")
 for i in 42:
  main.player.move_and_collide(bathroom.basis*Vector3(.04,0,0))
  await get_tree().physics_frame
 check(bathroom.to_local(main.player.position).x>-.9,"jogador atravessa abertura entre cozinha e banheiro")
 await shot(main,"banheiro",bathroom.to_global(Vector3(-1.15,.02,.9)),bathroom.to_global(Vector3(.45,1.15,-.45)))
 await shot(main,"casa_praia",c+Vector3(1.3,.13,2.1),c+Vector3(-1.2,1.3,-1.5))
 phone.open("painel")
 await shot(main,"celular_inicio",main.world.kiosk_point(Vector3(0,.15,.2)),main.world.kiosk_point(Vector3(0,1.5,4)))
 phone.open("missoes")
 await shot(main,"celular_missoes",main.player.position,main.world.kiosk_point(Vector3(0,1.5,4)))
 phone.close()
 await shot(main,"quiosque_detalhes",main.world.kiosk_point(Vector3(.2,.15,-.2)),main.world.kiosk_point(Vector3(-1.0,1.35,1.2)))
 await shot(main,"gramado_sol",Vector3(40,.15,3),Vector3(40,.1,-4))
 Core.set_weather("rain")
 await shot(main,"gramado_chuva",Vector3(40,.15,3),Vector3(40,.1,-4))
 Core.set_weather("sun")
 var spot: Dictionary=main.world.kiosk_spots[2]
 var customer=main.village._make()
 customer.gname="Ana Costa"
 customer.spot=spot
 customer.position=spot.pos
 customer.rotation.y=spot.rot
 customer.set_meta("dish","suco")
 customer.set_meta("items",["suco","batata_frita"])
 customer.set_meta("delivered",0)
 customer.set_meta("order_taken",true)
 customer.state="kwait"
 main.village.customers.append(customer)
 main.hud._update_orders()
 check(main.hud.orders_text.text.contains("Ana Costa") and main.hud.orders_text.text.contains("Suco") and not main.hud.orders_text.text.contains("#") and not main.hud.orders_text.text.contains("PEDIDOS"),"HUD só nomes e itens, sem números ou legendas")
 customer.service_reaction("receber")
 check(customer._service_time>0,"cliente reage ao receber")
 customer.consume_dish("suco")
 await shot(main,"cliente_mesa_sem_sobreposicao",spot.pos+Vector3(2,.15,2),spot.pos+Vector3(0,1.0,0))
 phone.open("conversa")
 await shot(main,"campanha_morador",main.player.position,spot.pos+Vector3(0,1.0,0))
 phone.close()
 for node in main.village.walkers:node.set_process(false)
 await frames(30)
 print("REFINEMENTS_TEST FAIL" if failed else "REFINEMENTS_TEST PASS")
 Core.quit_game(1 if failed else 0)

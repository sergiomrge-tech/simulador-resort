extends RefCounted
## Campanha principal e objetivos opcionais; sem cobranças ou alterações ao consultar o HUD.
const MAIN=[
 {"id":"chegada","title":"Uma nova maré","story":"Seu avô confiou a você o quiosque da família. Dê um nome a ele e continue essa história.","task":"Criar sua empresa no celular","kind":"company","qty":1,"reward":40},
 {"id":"portas","title":"Portas abertas","story":"O primeiro expediente começa com uma decisão sua: abrir o quiosque para a praia.","task":"Abrir o quiosque pela placa vermelha","kind":"open","qty":1,"reward":30},
 {"id":"primeiros","title":"O sabor da primeira manhã","story":"Conquiste os primeiros fregueses: anote, retire pronto e entregue no balcão.","task":"Vender 8 produtos no quiosque","kind":"sales","qty":8,"reward":100},
 {"id":"mesas","title":"Um lugar para ficar","story":"Transforme uma parada rápida em um ponto de encontro da comunidade.","task":"Comprar Mesas e guarda-sóis","kind":"expansion","item":"kiosk_tables","qty":1,"reward":80},
 {"id":"equipe","title":"Uma parceria de verdade","story":"Uma pessoa de confiança pode cuidar de todo o atendimento enquanto você explora a vila.","task":"Contratar o atendente único","kind":"staff","qty":1,"reward":80},
 {"id":"comunidade","title":"O quiosque e o mar","story":"Seu Zé precisa de ajuda para o píer. Conclua os três passos da história dele.","task":"Concluir O píer do Seu Zé em Histórias da vila","kind":"chapter","item":"pier","qty":1,"reward":150},
 {"id":"encontro","title":"O encontro dos viajantes","story":"A vila já conhece seu trabalho. Amplie o negócio com o Bar do Coqueiro.","task":"Comprar o Bar do Coqueiro","kind":"expansion","item":"bar","qty":1,"reward":200},
 {"id":"hospedar","title":"Fique mais um dia","story":"Os visitantes querem conhecer a vila com calma. Receba-os na sua pousada.","task":"Abrir a pousada","kind":"expansion","item":"pousada","qty":1,"reward":300},
 {"id":"verao","title":"Um verão inesquecível","story":"Ofereça descanso aos hóspedes e dê mais um motivo para voltar.","task":"Construir a piscina","kind":"expansion","item":"pool","qty":1,"reward":400},
 {"id":"marealta","title":"A Maré Alta da vila","story":"Do primeiro coco ao resort: faça da vila um destino sem perder sua identidade.","task":"Construir o Grand Hotel Maré Alta","kind":"expansion","item":"grand_hotel","qty":1,"reward":1000}
]
const SIDE=[
 {"id":"pescador","title":"Um dia com os pescadores","story":"Seu Zé ensina que peixe bom pede paciência.","task":"Pescar 5 peixes no píer","kind":"fish","qty":5,"reward":80},
 {"id":"gelados","title":"O verão pede sorvete","story":"Dona Rita quer apresentar os dois sabores aos visitantes.","task":"Vender 12 sorvetes no quiosque","kind":"icecream","qty":12,"reward":100},
 {"id":"faroleiro","title":"Cartão-postal da vila","story":"Registre o farol para guardar a memória da comunidade.","task":"Fotografar o farol com P","kind":"photo","item":"farol","qty":1,"reward":50},
 {"id":"entardecer","title":"As cores do entardecer","story":"Encontre um bom ângulo para o sol se despedir do mar.","task":"Fotografar o pôr do sol com P","kind":"photo","item":"por_do_sol","qty":1,"reward":50}
]
static func defaults() -> Dictionary:
 return {"stage":0,"side_done":[],"fish":0,"icecream":0}
static func sanitize(value: Variant) -> Dictionary:
 var out:=defaults()
 if not value is Dictionary: return out
 out.stage=clampi(int(value.get("stage",0)),0,MAIN.size())
 for key in ["fish","icecream"]: out[key]=clampi(int(value.get(key,0)),0,1000000)
 if value.get("side_done",[]) is Array:
  for id in value.get("side_done",[]):
   if SIDE.any(func(q):return q.id==id) and id not in out.side_done: out.side_done.append(id)
 return out
static func current(p) -> Dictionary:
 return MAIN[int(p.campaign.stage)] if int(p.campaign.stage)<MAIN.size() else {}
static func amount(p,q: Dictionary) -> int:
 match str(q.kind):
  "company":return int(bool(Core.company.created))
  "open":return int(bool(Core.company.kiosk_open) or Core.kiosk_sales_count>0)
  "sales":return Core.kiosk_sales_count
  "expansion":return int(Core.has(str(q.item)))
  "staff":return int(bool(Core.staff.get("atendente",false)))
  "chapter":return int(p.chapter_done(str(q.item)))
  "fish","icecream":return int(p.campaign.get(str(q.kind),0))
  "photo":return int(bool(p.chapter_photo.get(str(q.item),false)))
 return 0
static func ready(p,q: Dictionary) -> bool:
 return not q.is_empty() and amount(p,q)>=int(q.qty)
static func claim(p,id: String,side: bool=false) -> bool:
 var q: Dictionary={}
 if side:
  if id in p.campaign.side_done:return false
  for row in SIDE:
   if row.id==id:q=row
 else:
  q=current(p)
  if q.get("id","")!=id:return false
 if not ready(p,q):return false
 # Marcar primeiro impede reentrada e recompensa duplicada.
 if side:p.campaign.side_done.append(id)
 else:p.campaign.stage+=1
 Core.book(int(q.reward),"Missão concluída: "+str(q.title),"missao",true)
 p.add_fame(20 if side else 40)
 p.chapters_changed.emit()
 Core.toast.emit("Missão concluída: "+str(q.title),"good")
 Core.save_game()
 return true
static func tracker(p) -> String:
 var lines: Array[String]=[]
 var q: Dictionary=current(p)
 if not q.is_empty():lines.append("PRINCIPAL · "+str(q.title)+"\n"+str(q.task)+" · %d/%d" % [mini(amount(p,q),int(q.qty)),int(q.qty)]+(" · concluir no celular" if ready(p,q) else ""))
 for row in SIDE:
  if row.id not in p.campaign.side_done:
   lines.append("SECUNDÁRIA · "+str(row.task)+" · %d/%d" % [mini(amount(p,row),int(row.qty)),int(row.qty)])
   break
 return "\n".join(lines)

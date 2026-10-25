extends RefCounted
## Um ID do cardápio = uma apresentação própria; nenhuma primitiva genérica.
const RECIPES = {
	"sorvete_morango": {"model":"g:icecream_strawberry", "height":.15, "drink":false,"handheld":true,"chilled":true},
	"sorvete_chocolate": {"model":"g:icecream_chocolate", "height":.15, "drink":false,"handheld":true,"chilled":true},
	"coco_gelado": {"model": "g:coconut_open", "height": 0.29, "drink": true},
	"suco": {"model": "g:glass_juice", "height": 0.26, "drink": true},
	"caipirinha": {"model": "g:cocktail", "height": 0.27, "drink": true},
	"batida": {"model": "g:dish_batida", "height": 0.26, "drink": true},
	"petiscos": {"model": "g:dish_petiscos", "deep": false, "drink": false},
	"tapioca": {"model": "g:dish_tapioca", "deep": false, "drink": false},
	"pastel": {"model": "g:dish_pastel", "deep": false, "drink": false},
	"acai": {"model": "g:dish_acai", "deep": true, "drink": false},
	"moqueca": {"model": "g:dish_moqueca", "deep": true, "drink": false},
}

static func is_drink(id: String) -> bool:
	return bool(RECIPES.get(id, {}).get("drink", false))

static func is_chilled(id: String) -> bool:
	return is_drink(id) or bool(RECIPES.get(id,{}).get("chilled",false))
static func is_handheld(id: String) -> bool:
	return is_drink(id) or bool(RECIPES.get(id,{}).get("handheld",false))

static func build_used(parent: Node3D, id: String) -> Node3D:
	var root:=Node3D.new()
	root.name="Used_"+id
	root.set_meta("dish_id",id)
	root.set_meta("used",true)
	parent.add_child(root)
	var containers: Dictionary={"suco":"g:used_glass_juice","coco_gelado":"g:coconut_open","caipirinha":"g:used_cocktail","batida":"g:used_dish_batida","sorvete_morango":"g:used_icecream_cup","sorvete_chocolate":"g:used_icecream_cup"}
	if containers.has(id):
		root.set_meta("container",str(containers[id]))
		Real.place(root,str(containers[id]),Vector3.ZERO,(.095 if id.begins_with("sorvete_") else float(RECIPES[id].height)*(.63865543 if id=="caipirinha" else 1.0)))
	else:
		var deep: bool=bool(RECIPES.get(id,{}).get("deep",false))
		var container: String="g:table_bowl" if deep else "g:table_plate"
		root.set_meta("container",container)
		Real.place(root,container,Vector3.ZERO,0.0,0.0,Color.WHITE,.28)
		Real.place(root,"k:utensil-spoon" if deep else "k:utensil-fork",Vector3(.105,.018,0),0.0,.25,Color.WHITE,.105)
	return root

static func build(parent: Node3D, id: String) -> Node3D:
	if not RECIPES.has(id):
		push_error("ORDER_VISUAL unknown dish: " + id)
		return null
	var spec: Dictionary = RECIPES[id]
	var root := Node3D.new()
	root.name = "Dish_" + id
	root.set_meta("dish_id", id)
	parent.add_child(root)
	if is_handheld(id):
		Real.place(root, str(spec.model), Vector3.ZERO, float(spec.height))
	else:
		var deep: bool = bool(spec.deep)
		var plate: Node3D = Real.place(root, "g:table_bowl" if deep else "g:table_plate", Vector3.ZERO, 0.0, 0.0, Color.WHITE, 0.28)
		var top: float = 0.018
		if plate != null:
			var bounds: AABB = Real._aabb(plate)
			top = bounds.position.y + bounds.size.y
		var food_y: float = top * 0.55 if deep else maxf(0.0, top - 0.003)
		Real.place(root, str(spec.model), Vector3(0, food_y, 0), 0.0, 0.0, Color.WHITE, 0.215)
		Real.place(root, "k:utensil-spoon" if deep else "k:utensil-fork", Vector3(0.105, top, 0), 0.0, 0.25, Color.WHITE, 0.105)
	return root

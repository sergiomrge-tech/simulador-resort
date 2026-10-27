extends Node
## Tela física do notebook mostra dados reais, sem blocos de decoração vazios.
var laptop: Node3D
var viewport: SubViewport
var title: Label
var status: Label
var money: Label
var stock: Label
func _ready() -> void:
	viewport=SubViewport.new()
	viewport.size=Vector2i(480,280)
	viewport.disable_3d=true
	viewport.gui_disable_input=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ONCE
	add_child(viewport)
	var panel:=PanelContainer.new()
	panel.size=Vector2(480,280)
	var style:=StyleBoxFlat.new()
	style.bg_color=Color(.045,.08,.075)
	style.set_content_margin_all(18)
	panel.add_theme_stylebox_override("panel",style)
	viewport.add_child(panel)
	var column:=VBoxContainer.new()
	column.add_theme_constant_override("separation",13)
	panel.add_child(column)
	title=_label(column,28)
	status=_label(column,22)
	money=_label(column,25)
	stock=_label(column,20)
	_label(column,18).text="E ou clique · abrir gestão"
	for mesh in laptop.find_children("*","MeshInstance3D",true,false):
		for surface in mesh.mesh.get_surface_count():
			var original: Material=mesh.mesh.surface_get_material(surface)
			if original and str(original.resource_name)=="classic_laptop_screen":
				var lcd:=StandardMaterial3D.new()
				lcd.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
				lcd.albedo_texture=viewport.get_texture()
				lcd.uv1_offset=Vector3(-1,0,0)
				lcd.emission_enabled=true
				lcd.emission=Color.WHITE
				lcd.emission_texture=viewport.get_texture()
				lcd.emission_energy_multiplier=.6
				lcd.roughness=.7
				mesh.set_surface_override_material(surface,lcd)
	Core.company_changed.connect(refresh)
	Core.stock_changed.connect(refresh)
	Core.time_changed.connect(func(_day,_minutes): refresh())
	Core.money_changed.connect(func(_amount): refresh())
	refresh()
func _label(parent: Node, size: int) -> Label:
	var label:=Label.new()
	label.add_theme_font_override("font",UiTheme.font())
	label.add_theme_font_size_override("font_size",size)
	label.add_theme_color_override("font_color",Color(.85,.93,.87))
	label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(label)
	return label
var _last_content: String=""
func refresh() -> void:
	title.text=str(Core.company.name) if Core.company.created else "MARÉ ALTA · GESTÃO"
	status.text="ABERTO" if Core.kiosk_accepting_customers() else "QUIOSQUE FECHADO"
	money.text="Caixa: "+Core.fmt_money(Core.money)
	stock.text="Pagamento automático na entrega"
	var content: String=title.text+status.text+money.text+stock.text
	if content!=_last_content:
		_last_content=content
		viewport.render_target_update_mode=SubViewport.UPDATE_ONCE

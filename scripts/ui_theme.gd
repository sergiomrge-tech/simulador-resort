class_name UiTheme
extends RefCounted





const SAND: = Color(0.985, 0.955, 0.885)
const SAND_DARK: = Color(0.93, 0.87, 0.76)
const CARD: = Color(1.0, 0.985, 0.95)
const WOOD: = Color(0.56, 0.36, 0.18)
const WOOD_DARK: = Color(0.36, 0.22, 0.1)
const TEAL: = Color(0.05, 0.47, 0.49)
const TEAL_DARK: = Color(0.03, 0.3, 0.33)
const CORAL: = Color(0.89, 0.42, 0.27)
const TEXT: = Color(0.2, 0.15, 0.09)
const TEXT_SOFT: = Color(0.38, 0.3, 0.2)
const GOOD: = Color(0.1, 0.48, 0.22)
const BAD: = Color(0.7, 0.2, 0.12)


const FS_SMALL: = 19
const FS_BODY: = 22
const FS_H2: = 26
const FS_TITLE: = 36

static var _theme: Theme
static var _font: Font
static var _bold: Font
static var _icons: = {}

static func font() -> Font:
	if _font == null:
		var f: = FontVariation.new()
		f.base_font = load("res://assets/fonts/Nunito.ttf")
		f.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 650}
		_font = f
	return _font

static func bold() -> Font:
	if _bold == null:
		var f: = FontVariation.new()
		f.base_font = load("res://assets/fonts/Nunito.ttf")
		f.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 850}
		_bold = f
	return _bold

static func icon(id: String) -> Texture2D:
	if not _icons.has(id):
		var p: = "res://assets/ui/icons/%s.svg" % id
		_icons[id] = load(p) if ResourceLoader.exists(p) else null
	return _icons[id]


static func box(bg: Color, radius: = 16, border: = Color(0, 0, 0, 0), bw: = 0, shadow: = 10, pad: = 14) -> StyleBoxFlat:
	var s: = StyleBoxFlat.new()
	s.bg_color = bg
	s.set_corner_radius_all(radius)
	s.corner_detail = 10
	s.anti_aliasing = true
	if bw > 0:
		s.border_color = border
		s.set_border_width_all(bw)
	if shadow > 0:
		s.shadow_color = Color(0.05, 0.03, 0.0, 0.28)
		s.shadow_size = shadow
		s.shadow_offset = Vector2(0, 4)
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad * 0.7
	s.content_margin_bottom = pad * 0.7
	return s

static func get_theme() -> Theme:
	if _theme:
		return _theme
	var t: = Theme.new()
	t.default_font = font()
	t.default_font_size = FS_BODY
	t.set_font("font", "Label", font())
	t.set_color("font_color", "Label", TEXT)

	t.set_font("font", "Button", bold())
	t.set_font_size("font_size", "Button", FS_BODY)
	var bn: = box(TEAL, 14, TEAL_DARK, 0, 4, 16)
	bn.border_width_bottom = 4
	bn.border_color = TEAL_DARK
	var bh: = bn.duplicate()
	bh.bg_color = TEAL.lightened(0.12)
	var bp: = bn.duplicate()
	bp.bg_color = TEAL_DARK
	bp.border_width_bottom = 1
	bp.shadow_size = 1
	var bd: = bn.duplicate()
	bd.bg_color = Color(0.62, 0.6, 0.55)
	bd.border_color = Color(0.48, 0.46, 0.42)
	var bf: = bh.duplicate()
	bf.border_color = Color(1.0, 0.85, 0.4)
	bf.set_border_width_all(3)
	t.set_stylebox("normal", "Button", bn)
	t.set_stylebox("hover", "Button", bh)
	t.set_stylebox("pressed", "Button", bp)
	t.set_stylebox("disabled", "Button", bd)
	t.set_stylebox("focus", "Button", bf)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		t.set_color(c, "Button", Color.WHITE)
	t.set_color("font_disabled_color", "Button", Color(0.95, 0.93, 0.9, 0.8))
	t.set_constant("h_separation", "Button", 10)
	t.set_constant("icon_max_width", "Button", 30)

	t.set_type_variation("TabButton", "Button")
	var tn: = box(SAND_DARK, 14, WOOD, 0, 0, 14)
	var th: = tn.duplicate()
	th.bg_color = SAND_DARK.lightened(0.25)
	var ts: = box(WOOD, 14, WOOD_DARK, 0, 4, 14)
	ts.border_width_bottom = 4
	ts.border_color = WOOD_DARK
	t.set_stylebox("normal", "TabButton", tn)
	t.set_stylebox("hover", "TabButton", th)
	t.set_stylebox("pressed", "TabButton", ts)
	t.set_stylebox("hover_pressed", "TabButton", ts)
	t.set_stylebox("focus", "TabButton", bf)
	for c in ["font_color", "font_hover_color", "font_focus_color"]:
		t.set_color(c, "TabButton", WOOD_DARK)
	t.set_color("font_pressed_color", "TabButton", Color.WHITE)
	t.set_color("font_hover_pressed_color", "TabButton", Color.WHITE)
	t.set_color("icon_normal_color", "TabButton", WOOD_DARK)
	t.set_color("icon_hover_color", "TabButton", WOOD_DARK)
	t.set_color("icon_pressed_color", "TabButton", Color.WHITE)
	t.set_color("icon_hover_pressed_color", "TabButton", Color.WHITE)
	t.set_font_size("font_size", "TabButton", FS_H2)

	t.set_type_variation("SoftButton", "Button")
	var sn: = box(CARD, 12, WOOD, 2, 2, 14)
	var sh: = sn.duplicate()
	sh.bg_color = Color(1, 0.95, 0.85)
	var sp: = sn.duplicate()
	sp.bg_color = SAND_DARK
	t.set_stylebox("normal", "SoftButton", sn)
	t.set_stylebox("hover", "SoftButton", sh)
	t.set_stylebox("pressed", "SoftButton", sp)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		t.set_color(c, "SoftButton", WOOD_DARK)

	t.set_stylebox("panel", "PanelContainer", box(SAND, 22, WOOD, 3, 18, 22))
	t.set_stylebox("panel", "Panel", box(SAND, 22, WOOD, 3, 18, 22))
	t.set_type_variation("Card", "PanelContainer")
	t.set_stylebox("panel", "Card", box(CARD, 14, SAND_DARK.darkened(0.08), 2, 0, 14))
	t.set_type_variation("Chip", "PanelContainer")
	var chip: = box(SAND_DARK, 12, Color(0, 0, 0, 0), 0, 0, 10)
	chip.content_margin_top = 4
	chip.content_margin_bottom = 4
	t.set_stylebox("panel", "Chip", chip)

	var grab: = box(WOOD.lightened(0.15), 8, Color(), 0, 0, 0)
	var track: = box(SAND_DARK, 8, Color(), 0, 0, 0)
	t.set_stylebox("grabber", "VScrollBar", grab)
	t.set_stylebox("grabber_highlight", "VScrollBar", box(WOOD, 8, Color(), 0, 0, 0))
	t.set_stylebox("grabber_pressed", "VScrollBar", box(WOOD_DARK, 8, Color(), 0, 0, 0))
	t.set_stylebox("scroll", "VScrollBar", track)

	t.set_font_size("font_size", "OptionButton", FS_BODY)
	t.set_font_size("font_size", "CheckButton", FS_BODY)
	t.set_font_size("font_size", "PopupMenu", FS_BODY)
	t.set_font("font", "PopupMenu", font())
	t.set_stylebox("panel", "PopupMenu", box(SAND, 12, WOOD, 2, 8, 10))
	t.set_color("font_color", "PopupMenu", TEXT)
	t.set_color("font_hover_color", "PopupMenu", Color.WHITE)
	t.set_stylebox("hover", "PopupMenu", box(TEAL, 8, Color(), 0, 0, 6))
	t.set_stylebox("normal", "LineEdit", box(CARD, 10, WOOD, 2, 0, 10))
	t.set_font_size("font_size", "LineEdit", FS_BODY)
	t.set_font("font", "TooltipLabel", font())
	t.set_font_size("font_size", "TooltipLabel", FS_SMALL)
	_theme = t
	return t


static func apply_scale(tree: SceneTree, s: float) -> void :
	if tree and tree.root:
		tree.root.content_scale_factor = clampf(s, 0.75, 1.5)

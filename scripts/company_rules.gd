extends RefCounted
## Dados versionados do negócio. Sem class_name para manter patches compatíveis.
const Simulation = preload("res://scripts/kiosk_simulation.gd")
const MAX_NAME := 24
const MAX_READY := 9999
const FONTS := {"praia": "Nunito · Praia", "classica": "Sans · Clássica", "elegante": "Nunito · Itálica"}
const COLORS := {"creme": Color(1.0, 0.94, 0.78), "branco": Color.WHITE, "dourado": Color(1.0, 0.81, 0.35)}
static var _fonts: Dictionary = {}

static func defaults() -> Dictionary:
	return {"created": false, "name": "Maré Alta", "font": "praia", "color": "creme", "physical": true, "kiosk_open": true, "sim": Simulation.defaults(),
		"ready": {}, "carry": "", "staff_carry": "", "production": {}, "receivables": [], "dirty_seats": []}

static func valid_name(value: String) -> bool:
	if value != value.strip_edges() or value.length() < 1 or value.length() > MAX_NAME:
		return false
	for ch in value:
		if ch.unicode_at(0) < 32 or ch.unicode_at(0) == 127:
			return false
	return true

static func sanitize(value: Variant) -> Dictionary:
	var out := defaults()
	if not value is Dictionary:
		return out
	out.created = bool(value.get("created", false))
	var title: String = str(value.get("name", out.name)).strip_edges().replace("\n", " ").replace("\r", " ").replace("\t", " ").left(MAX_NAME)
	out.name = title if valid_name(title) else "Maré Alta"
	out.font = str(value.get("font", "praia")) if FONTS.has(str(value.get("font", ""))) else "praia"
	out.color = str(value.get("color", "creme")) if COLORS.has(str(value.get("color", ""))) else "creme"
	out.physical = bool(value.get("physical", true))
	out.kiosk_open = bool(value.get("kiosk_open", true))
	out.sim = Simulation.sanitize(value.get("sim", {}))
	var ready: Variant = value.get("ready", {})
	if ready is Dictionary:
		for id in Economy.KIOSK_MENU:
			var n: Variant = ready.get(id, 0)
			out.ready[id] = clampi(int(n), 0, MAX_READY) if (n is int or n is float) and is_finite(float(n)) else 0
	var carry: String = str(value.get("carry", ""))
	out.carry = carry if carry in Economy.KIOSK_MENU else ""
	var held: String = str(value.get("staff_carry", ""))
	out.staff_carry = held if held in Economy.KIOSK_MENU else ""
	var production: Variant = value.get("production", {})
	if production is Dictionary and str(production.get("dish", "")) in Economy.KIOSK_MENU:
		var id: String = str(production.dish)
		out.ready[id] = int(out.ready.get(id, 0)) + 1
	var bills: Variant = value.get("receivables", [])
	if bills is Array:
		for bill in bills.slice(0, 256):
			if bill is Dictionary and str(bill.get("dish", "")) in Economy.KIOSK_MENU:
				var amount: Variant = bill.get("value", 0)
				if amount is int or amount is float:
					out.receivables.append({"dish": str(bill.dish), "value": clampi(int(amount), 0, 10000)})
	var dirty: Variant = value.get("dirty_seats", [])
	if dirty is Array:
		for index in dirty:
			if (index is int or index is float) and int(index) >= 0 and int(index) < 8 and int(index) not in out.dirty_seats:
				out.dirty_seats.append(int(index))
	return out

static func font_for(id: String) -> Font:
	if _fonts.has(id):
		return _fonts[id]
	var f: Font
	if id == "classica":
		f = ThemeDB.fallback_font
	else:
		var variant := FontVariation.new()
		variant.base_font = load("res://assets/fonts/Nunito.ttf")
		variant.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 800}
		if id == "elegante":
			variant.variation_transform = Transform2D(Vector2(1, 0), Vector2(0.18, 1), Vector2.ZERO)
		f = variant
	_fonts[id] = f
	return f

static func fit_sign(label: Label3D, title: String, font_id: String, color_id: String, width: float) -> void:
	label.text = title
	label.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	label.font = font_for(font_id)
	label.modulate = COLORS.get(color_id, COLORS.creme)
	var pixels: float = label.font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, label.font_size).x + 2.0 * label.outline_size
	label.pixel_size = minf(0.005, width / maxf(pixels, 1.0))

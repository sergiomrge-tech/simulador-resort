extends Node
var failed := false
func check(ok: bool, label: String) -> void:
 failed = failed or not ok
 print("[phone] ", "ok " if ok else "FAIL ", label)
func frames(count: int) -> void:
 for i in count: await get_tree().process_frame
func run(main) -> void:
 Core.paused = true
 main.allow_faint = false
 main.guests.enabled = false
 main.village.enabled = false
 Core.money = 1000000
 Core.configure_company("W".repeat(24), "praia")
 Core.unlock_all()
 Core.reset_rooms(Economy.BUNGALOW_MAX)
 for role in Core.CompanyRules.Simulation.ROLES:
  if not Core.staff.get(role, false): Core.hire(role)
 var apps: Array = [""]
 for info in PhoneUI.APPS: apps.append(info[0])
 for viewport_size in [Vector2i(1280, 720), Vector2i(800, 600), Vector2i(360, 640)]:
  var viewport := SubViewport.new()
  viewport.size = viewport_size
  viewport.disable_3d = true
  add_child(viewport)
  var phone := PhoneUI.new()
  viewport.add_child(phone)
  phone.visible = true
  await frames(4)
  for app in apps:
   phone.app = app
   phone.refresh()
   phone._place()
   await frames(5)
   var frame := phone._phone.get_global_rect()
   var margin := 12.0 * phone._phone.scale.x
   var bad: Array = []
   for child in phone.screen.find_children("*", "Control", true, false):
    if not child.is_visible_in_tree(): continue
    var rect: Rect2 = child.get_global_rect()
    if rect.position.x < frame.position.x + margin - 1 or rect.end.x > frame.end.x - margin + 1:
     bad.append("%s %s %.1f..%.1f" % [child.get_class(), str(child.get("text")).left(42), rect.position.x, rect.end.x])
   check(bad.is_empty(), "%s %s sem corte lateral %s" % [viewport_size, app if app != "" else "início", str(bad.slice(0, 5))])
   check(frame.position.x >= 0 and frame.end.x <= viewport_size.x + 1 and frame.position.y >= 0 and frame.end.y <= viewport_size.y + 1, "aparelho cabe na janela")
  viewport.queue_free()
  await frames(2)
 print("PHONE_LAYOUT_TEST ", "FAIL" if failed else "PASS")
 get_tree().quit(1 if failed else 0)

"""Grand Hotel guest floor (CHECKLIST 5.1): imports tools/ue58/gen_hotel_rooms.py (corridor, standard room 302, luxury
room 303 and the linen room, east of the suite on the 3rd floor) and furnishes it with library models.
Re-runnable: place() removes every actor tagged MareHotelRoomsPart first.
  mare_hotel_rooms.run('import')   -> /Game/Custom/HotelRooms/mare_hotel_rooms (no Nanite: shower glass is translucent)
  mare_hotel_rooms.run('place')    -> room mesh, furniture, interior volume (PIE stopped)
  mare_hotel_rooms.run('sizes', 'slug,slug')  -> library mesh sizes in cm
Room frame: UE world axes in metres from ORIGIN (floor slab of the 3rd storey), as in gen_hotel_rooms.py.
"""
import json
import math
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DATA = ROOT / 'Content/Data'
GLB = Path('D:/Assets/Mare/mare_hotel_rooms/mare_hotel_rooms.glb')
DEST = '/Game/Custom/HotelRooms/mare_hotel_rooms'
ORIGIN = (-1236.0, 6342.0, 851.0)
FLOOR = ORIGIN[2] + 3.0      # top of the room floor boards (3 cm)
TAG = 'MareHotelRoomsPart'

# Local axis each model faces: the bpy beds, TVs and the AC face +Y (headboard / wall side at -Y), the Poly Haven
# nightstand +X; the rest is checked in the photos.
FRONT_Y = {'mare_bed_upholstered', 'mare_bed_king', 'mare_tv_flat43', 'mare_tv_smart55', 'mare_tv_oled65', 'mare_ac_unit', 'dining_chair_02',
           'mid_century_lounge_chair'}
# (slug, x, y, facing (dx, dy), z above the floor or None = standing on the floor)
FURNITURE_OLD = [
    # Standard 302: queen bed against the padded west wall, nightstands, TV on the minibar console, desk chair.
    ('mare_bed_upholstered', -3.25, -1.6, (1, 0), None),
    ('ClassicNightstand_01', -3.98, -.35, (1, 0), None),
    ('ClassicNightstand_01', -3.98, -2.85, (1, 0), None),
    ('mare_tv_flat43', -.62, -1.45, (-1, 0), .73),
    ('WoodenChair_01', -1.05, -4.55, (1, 0), None),
    ('potted_plant_02', -3.85, -5.25, (1, 0), None),
    ('mare_ac_unit', -.36, -3.3, (-1, 0), 2.35),
    # Luxury 303: king bed against the slatted wall facing the sea, nightstands, TV on the west console, reading corner.
    ('mare_bed_king', 5.35, -.85, (0, -1), None),
    ('ClassicNightstand_01', 3.95, .05, (0, -1), None),
    ('ClassicNightstand_01', 6.75, .05, (0, -1), None),
    ('mare_tv_smart55', .06, -1.85, (1, 0), .73),
    ('mid_century_lounge_chair', 3.2, -4.6, (-.5, 1), None),
    ('modern_coffee_table_01', 2.2, -4.8, (0, 1), None),
    ('Ottoman_01', 6.3, -2.9, (0, 1), None),
    ('potted_plant_01', 6.65, -5.3, (0, 1), None),
    ('mare_ac_unit', .0, -4.2, (1, 0), 2.35),
    # Corridor: plants by the elevator.
    ('potted_plant_02', -6.6, 5.45, (0, -1), None),
]
FURNITURE = [
    # Standard 302 (x -4.28..-0.28): queen bed against the padded west wall (panel face x -4.10), nightstands, TV on the
    # minibar console (top 0.73 m, centre x -0.60), desk chair and lamp, AC high on the east partition (face x -0.34).
    ('mare_bed_upholstered', -2.95, -1.6, (1, 0), None),
    ('ClassicNightstand_01', -3.87, -.30, (1, 0), None),
    ('ClassicNightstand_01', -3.87, -2.90, (1, 0), None),
    ('mare_tv_flat43', -.62, -1.6, (-1, 0), .73),
    ('dining_chair_02', -1.25, -4.55, (1, 0), None),
    ('desk_lamp_arm_01', -.72, -4.15, (-1, 0), .77),
    ('potted_plant_02', -.62, -3.45, (-1, 0), None),
    ('mare_ac_unit', -.34, -3.3, (-1, 0), 2.35),
    # Luxury 303 (x -0.28..7.06): king bed against the slatted wall (face y 0.21) looking at the sea, nightstands,
    # ottoman at its foot, TV on the west console (centre x 0.04), lounge chair and table by the window, AC on the west wall.
    ('mare_bed_king', 5.30, -.98, (0, -1), None),
    ('ClassicNightstand_01', 3.90, .0, (0, -1), None),
    ('ClassicNightstand_01', 6.70, .0, (0, -1), None),
    ('Ottoman_01', 5.30, -2.42, (1, 0), None),
    ('mare_tv_smart55', .06, -2.0, (1, 0), .73),
    ('mid_century_lounge_chair', 1.75, -4.35, (0, -1), None),
    ('modern_coffee_table_01', 2.85, -4.4, (1, 0), None),
    ('potted_plant_01', 3.72, -5.3, (0, 1), None),
    ('mare_ac_unit', -.22, -4.2, (1, 0), 2.35),
    # Suite 301 (gen_suite.py, x -24.34..-7.06 in this frame): air conditioner high on the bedroom's north wall, so its
    # complaint ("Ar-condicionado quebrado", hotel_rooms.json spots) has something to fix.
    ('mare_ac_unit', -23.14, 5.6, (0, -1), 2.35),
    # Suite TV on the living-room console (gen_suite.py tvconsole: centre x -0.5, y -0.95, top 0.525 in the suite frame).
    ('mare_tv_oled65', -16.14, -.95, (0, 1), .525),
]


def _game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def _world_xy(x, y):
    return ORIGIN[0] + x * 100.0, ORIGIN[1] + y * 100.0


def _mesh(slug):
    """Catalogue model (custom_assets.json, already imported) or a lobby library model (imported on first use)."""
    import mare_hotel_lobby
    if slug.startswith('/'):
        return unreal.load_asset(slug)
    assets = json.loads((DATA / 'custom_assets.json').read_text(encoding='utf-8'))
    if slug in assets and unreal.load_asset(assets[slug]):
        return unreal.load_asset(assets[slug])
    return mare_hotel_lobby._lib_mesh(slug)


def sizes(slugs):
    out = {}
    for slug in slugs.split(','):
        mesh = _mesh(slug)
        b = mesh.get_bounding_box()
        out[slug] = {'min': [round(b.min.x), round(b.min.y), round(b.min.z)], 'max': [round(b.max.x), round(b.max.y), round(b.max.z)]}
    return out


def import_mesh():
    import mare_hotel_lobby
    if _game_world():
        raise RuntimeError('Stop PIE first')
    mesh = mare_hotel_lobby._import(GLB, DEST, 'mare_hotel_rooms', False, False)
    mare_hotel_lobby._complex_collision(mesh)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    path = DATA / 'custom_assets.json'
    assets = json.loads(path.read_text(encoding='utf-8'))
    assets['mare_hotel_rooms'] = mesh.get_path_name()
    path.write_text(json.dumps(assets, indent=1) + '\n', encoding='utf-8')
    b = mesh.get_bounding_box()
    return {'mesh': mesh.get_path_name(), 'tris': mesh.get_num_triangles(0), 'materials': len(mesh.static_materials),
            'min': [round(b.min.x), round(b.min.y), round(b.min.z)], 'max': [round(b.max.x), round(b.max.y), round(b.max.z)]}


def place():
    import importlib
    import mare_hotel_lobby
    import mare_materials
    importlib.reload(mare_hotel_lobby)
    if _game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if TAG in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name(TAG)]
    room = actors.spawn_actor_from_object(unreal.load_asset(DEST + '/mare_hotel_rooms.mare_hotel_rooms'), unreal.Vector(*ORIGIN), unreal.Rotator(roll=0, pitch=0, yaw=0))
    room.set_actor_label('Hotel · andar de quartos')
    room.tags = tags + [unreal.Name('MareHotelRooms')]
    room.set_folder_path('Hotel/Rooms')
    comp = room.static_mesh_component
    daylight = mare_materials.build_suite_daylight()
    for i, slot in enumerate(comp.static_mesh.static_materials):
        if slot.material_interface and 'DaylightPanel' in slot.material_interface.get_name():
            comp.set_material(i, daylight)
    placed = []
    for slug, x, y, face, z in FURNITURE:
        mesh = _mesh(slug)
        b = mesh.get_bounds()
        wx, wy = _world_xy(x, y)
        base = FLOOR if z is None else ORIGIN[2] + z * 100.0
        yaw = math.degrees(math.atan2(face[1], face[0])) - (90.0 if slug in FRONT_Y else 0.0)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(wx, wy, base - (b.origin.z - b.box_extent.z)),
                                              unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_label('Hotel quartos · ' + slug)
        actor.tags = tags
        actor.set_folder_path('Hotel/Rooms')
        placed.append(slug)
    # Interior volume: the night eye of every room (UMareVisualWorld, tag MareInterior).
    vol = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(ORIGIN[0], ORIGIN[1], ORIGIN[2] + 154))
    vol.set_actor_scale3d(unreal.Vector(7.06, 5.77, 1.54))
    vol.set_editor_property('unbound', False)
    vol.set_editor_property('priority', 5.0)
    vol.set_editor_property('blend_radius', 60.0)
    vol.set_actor_label('Interior · quartos do hotel')
    vol.tags = [unreal.Name('MareInterior'), unreal.Name(TAG)]
    vol.set_folder_path('Interiors')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'room': True, 'furniture': placed}


def cmd(text):
    """One-argument entry for mare_hud 'module': "action:arg" (python mcp.py mod mare_hotel_rooms.cmd "sizes:a,b")."""
    action, _, arg = text.partition(':')
    return run(action, arg)


def run(action, arg=''):
    if action == 'sizes':
        return sizes(arg)
    if action == 'import':
        return import_mesh()
    if action == 'place':
        return place()
    raise ValueError(action)

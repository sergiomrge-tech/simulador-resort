"""Grand Hotel reception in marble (11/11, Sergio: "na recepção principal do hotel faça esse acabamento em mármore...
bastante detalhes e cores em mármore"). The dressing is one model (tools/ue58/gen_hotel_lobby_marble.py) laid over the
lobby shell at the tower's own transform (origin -2100, 6300, yaw 180: the model is in the tower's Blender frame).
place('dry'|'apply'): spawns it (tags Region_grand_hotel so it appears with the hotel, MareLobbyMarble), no collision
(the walkable floor is still the shell's, 1.2 cm below), and brings the two hanging pictures of the side walls 6 cm
in, onto the new 7 cm cladding. Re-runnable; PIE stopped."""
import json
from pathlib import Path
import unreal

TAG = 'MareLobbyMarble'
ORIGIN = (-2100.0, 6300.0, 0.0)


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def place(arg='dry'):
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    mesh = unreal.load_asset(data.get('mare_lobby_marble', ''))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    every = unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.StaticMeshActor)
    mine = [a for a in every if TAG in [str(t) for t in a.tags]]
    frames = []
    for a in every:
        m = a.static_mesh_component.static_mesh
        if m and 'hanging_picture_frame' in m.get_name() and 'MareHotelLobby' in [str(t) for t in a.tags]:
            l = a.get_actor_location()
            side = 1 if l.x > ORIGIN[0] else -1            # world x = origin - blender x: the west wall is at origin + 1550
            wall = ORIGIN[0] + side * 1550
            if abs(l.x - wall) < 12:
                frames.append((a, l, side))
    out = {'mesh': bool(mesh), 'mine': len(mine), 'frames': [[a.get_actor_label(), round(l.x), round(l.y), round(l.z)] for a, l, s in frames]}
    if arg.strip() != 'apply' or not mesh:
        return json.dumps(out)
    for a in mine:
        actors.destroy_actor(a)
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*ORIGIN), unreal.Rotator(roll=0, pitch=0, yaw=180))
    a.set_actor_label('Grand Hotel · recepção em mármore')
    a.tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name(TAG)]
    a.set_folder_path('Hotel/Lobby')
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_collision_profile_name('NoCollision')
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for f, l, side in frames:
        f.set_actor_location(unreal.Vector(ORIGIN[0] + side * (1550 - 8.5), l.y, l.z), False, False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    out['placed'] = True
    return json.dumps(out)

"""Boat tour (CHECKLIST_EXPANSOES 2.2): import the models of tools/ue58/gen_tour_boat.py (SourceArt/Models/TourBoat) to
/Game/Custom/TourBoat/<name>, each in a fresh folder, and give every opaque material the Nanite/ISM usage flags
(without them the cooked game shows the default material). PIE must be stopped."""
import json

import unreal


def _editor_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def fix_usage(folder):
    fixed = []
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        a = unreal.load_asset(p)
        if not isinstance(a, unreal.Material) or a.get_editor_property('blend_mode') != unreal.BlendMode.BLEND_OPAQUE:
            continue
        changed = False
        for flag in ('used_with_nanite', 'used_with_instanced_static_meshes'):
            if not a.get_editor_property(flag):
                a.set_editor_property(flag, True)
                changed = True
        if changed:
            unreal.MaterialEditingLibrary.recompile_material(a)
            unreal.EditorAssetLibrary.save_loaded_asset(a, False)
            fixed.append(a.get_name())
    return fixed


def import_models(arg=''):
    import mare_hotel_lobby as hl
    from pathlib import Path
    if _game_world():
        raise RuntimeError('Stop PIE first')
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/TourBoat'
    names = [n for n in arg.split(',') if n] or sorted(p.stem for p in src.glob('*.glb'))
    out = {}
    for name in names:
        folder = f'/Game/Custom/TourBoat/{name}'
        if unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.delete_directory(folder)
        mesh = hl._import(src / f'{name}.glb', folder, name, True, search=False)
        b = mesh.get_bounds()
        out[name] = [round(b.origin.x), round(b.origin.y), round(b.origin.z), round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)]
    out['fixed'] = len(fix_usage('/Game/Custom/TourBoat'))
    return json.dumps(out)


def qa(arg=''):
    """PIE: 'start' (guide the boat tour now), 'throttle=1;steer=0.3;secs=4' drives for a while (QA), 'vest:<i>',
    'story', 'state'."""
    world = _game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    log = []
    for cmd in [c for c in arg.split(';') if c]:
        log.append([cmd, pc.boat_tour_qa(cmd)])
    return json.dumps(log)


def view(arg='0,0'):
    """PIE: control rotation 'pitch,yaw_relative_to_boat_heading' (QA captures from the helm)."""
    pitch, yaw = [float(v) for v in arg.split(',')]
    world = _game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    boats = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
             if a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name() == 'TourBoat_lancha']
    base = boats[0].get_actor_rotation().yaw - 90 if boats else 0
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=base + yaw))
    return 'ok'


def who(arg=''):
    world = _game_world()
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        sid = p.get_editor_property('save_id')
        if not str(sid).startswith('boat_'):
            continue
        l = p.get_actor_location()
        par = p.get_attach_parent_actor()
        out.append([str(sid), round(l.x), round(l.y), round(l.z), par.get_name() if par else None])
    pawn = unreal.GameplayStatics.get_player_controller(world, 0).get_controlled_pawn()
    l = pawn.get_actor_location()
    par = pawn.get_attach_parent_actor()
    out.append(['hero', round(l.x), round(l.y), round(l.z), par.get_name() if par else None])
    return json.dumps(out)


def dolphins(arg=''):
    world = _game_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh
        if m and m.get_name() == 'TourBoat_dolphin':
            l = a.get_actor_location()
            out.append([round(l.x), round(l.y), round(l.z), a.is_hidden_ed() if hasattr(a, 'is_hidden_ed') else None])
    return json.dumps(out)


def sea_params(arg=''):
    """Adds the Boat* scalars to MPC_MareTime (restart the editor before building materials that read them)."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    mpc = mare_materials.time_collection()
    return json.dumps([str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('scalar_parameters')])


def sea_material(arg=''):
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    m = mare_materials.build_water()
    unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    return m.get_path_name()

"""Small island (06/11/2026, Sergio: "transformar o mapa numa ILHA PEQUENA"): survey of the current map, then the
re-executable generator (terrain, sea floor, vegetation). Entry through the MCP: hotel_lobby hud_module
"mare_island.<function>|<arg>"."""
import json
import math
from pathlib import Path

import unreal

OUT = Path(r'D:/CodexTemp/island')


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def survey(arg=''):
    """Bounds of the terrain and of every built thing, so the island can be drawn around them without moving any."""
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    ground = None
    for a in _actors():
        label = a.get_actor_label()
        try:
            origin, ext = a.get_actor_bounds(False)
        except Exception:
            continue
        tags = [str(t) for t in a.tags]
        cls = a.get_class().get_name()
        meshes = []
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh:
                n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
                meshes.append([c.static_mesh.get_path_name(), n])
        rows.append({'label': label, 'name': a.get_name(), 'class': cls, 'tags': tags,
                     'o': [round(origin.x), round(origin.y), round(origin.z)], 'e': [round(ext.x), round(ext.y), round(ext.z)],
                     'meshes': meshes[:6], 'nmesh': len(meshes)})
        if a.get_name() == 'World_0000' or label == 'Ground':
            ground = a
    info = {}
    if ground:
        c = ground.get_components_by_class(unreal.StaticMeshComponent)[0]
        sm = c.static_mesh
        info = {'label': ground.get_actor_label(), 'mesh': sm.get_path_name(), 'loc': str(ground.get_actor_location()),
                'rot': str(ground.get_actor_rotation()), 'scale': str(ground.get_actor_scale3d()),
                'bounds': str(sm.get_bounding_box()), 'mats': [m.get_path_name() if m else None for m in c.get_materials()],
                'nanite': sm.get_editor_property('nanite_settings').enabled,
                'verts': unreal.EditorStaticMeshLibrary.get_number_verts(sm, 0) if hasattr(unreal, 'EditorStaticMeshLibrary') else -1}
    (OUT / 'actors.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    xs = [r for r in rows if r['e'][0] < 30000 and r['e'][1] < 30000]
    return json.dumps({'actors': len(rows), 'ground': info,
                       'x': [min(r['o'][0] - r['e'][0] for r in xs), max(r['o'][0] + r['e'][0] for r in xs)],
                       'y': [min(r['o'][1] - r['e'][1] for r in xs), max(r['o'][1] + r['e'][1] for r in xs)],
                       'big': [[r['label'], r['o'], r['e']] for r in rows if r['e'][0] >= 30000 or r['e'][1] >= 30000][:20]},
                      ensure_ascii=False)


def heights(arg='-40000,40000,-20000,40000,500'):
    """Height grid of the terrain by vertical traces (only the Ground actor counts): x0,x1,y0,y1,step in cm."""
    x0, x1, y0, y1, step = [float(v) for v in arg.split(',')]
    world = _world()
    ground = [a for a in _actors() if a.get_name() == 'World_0000' or a.get_actor_label() == 'Ground']
    grid = []
    y = y0
    while y <= y1:
        row = []
        x = x0
        while x <= x1:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 60000), unreal.Vector(x, y, -60000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            z = None
            if hit:
                t = hit.to_tuple()
                actor = t[9] if len(t) > 9 else None
                z = round(t[4].z) if actor and ground and actor == ground[0] else ('B' + str(round(t[4].z)))
            row.append(z)
            x += step
        grid.append(row)
        y += step
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'heights.json').write_text(json.dumps({'arg': arg, 'grid': grid}), encoding='utf-8')
    return json.dumps({'rows': len(grid), 'cols': len(grid[0]) if grid else 0})


def land(arg='-45000,45000,-20000,60000,500'):
    """Height of the first blocking surface at every grid point (any actor except water and people), with the label of
    what was hit, for drawing the island contour around ALL existing land: x0,x1,y0,y1,step in cm.
    Writes D:/CodexTemp/island/land.json {arg, z: rows of height or null, who: rows of label index, labels}."""
    x0, x1, y0, y1, step = [float(v) for v in arg.split(',')]
    world = _world()
    skip = [a for a in _actors() if 'Oceano' in a.get_actor_label() or 'nata' in a.get_actor_label()]
    labels, index, zs, who = [], {}, [], []
    y = y0
    while y <= y1:
        zr, wr = [], []
        x = x0
        while x <= x1:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -30000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, skip,
                                                         unreal.DrawDebugTrace.NONE, True)
            z, w = None, -1
            if hit:
                t = hit.to_tuple()
                actor = t[9] if len(t) > 9 else None
                z = round(t[4].z)
                name = actor.get_actor_label() if actor else '?'
                if name not in index:
                    index[name] = len(labels)
                    labels.append(name)
                w = index[name]
            zr.append(z)
            wr.append(w)
            x += step
        zs.append(zr)
        who.append(wr)
        y += step
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'land.json').write_text(json.dumps({'arg': arg, 'z': zs, 'who': who, 'labels': labels}, ensure_ascii=False), encoding='utf-8')
    return json.dumps({'rows': len(zs), 'cols': len(zs[0]) if zs else 0, 'labels': len(labels)})


def seabed(_=''):
    """Step 2 (08/11): the island's sand floor (tools/ue58/gen_island_seabed.py) in place of the four straight
    planes of mare_water.ensure_seabed (same tag MareSeabed, same wet-sand material, no collision: swimming uses
    UMareReefWorld::SeabedZ). PIE stopped; saves the level."""
    import mare_hotel_lobby as hl
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    folder = '/Game/World/Island/mare_island_seabed'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    mesh = hl._import(Path('D:/Assets/Mare/mare_island_seabed/mare_island_seabed.glb'), folder, 'mare_island_seabed', False, search=False)
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    ground = mare_materials.build_ground(seabed=True)   # M_IslandSeabed_PBR: all wet sand
    mesh.set_material(0, ground)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = []
    for a in actors.get_all_level_actors():
        if 'MareSeabed' in [str(t) for t in a.tags]:
            removed.append(a.get_actor_label())
            actors.destroy_actor(a)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label('Mar · fundo de areia · ilha')
    a.tags = ['MareGenerated', 'MareSeabed']
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('cast_shadow', False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    b = mesh.get_bounds()
    return json.dumps({'removed': removed, 'mesh': mesh.get_path_name(), 'tris': mesh.get_num_triangles(0),
                       'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)]}, ensure_ascii=False)

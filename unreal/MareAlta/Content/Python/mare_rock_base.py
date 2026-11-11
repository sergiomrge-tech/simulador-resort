"""Rock under the lighthouse slabs (11/11, Sergio's photo: "rochas ainda suspensas na água? faça que a rocha comece na
água e suba até a superfície"). The Poly Haven coast slabs round the lighthouse are thin plates: over the water their
rim hangs in the air with a dark gap under it. Every slab gets a solid FOOT of rock: scan() measures the plate from
above on a 30 cm grid (D:/CodexTemp/rock_base.json), tools/ue58/gen_rock_base.py builds one mesh per slab from that
footprint (its top just under the plate's surface, walls that widen down to 4 m under the sea level with a rough
face), place() puts the meshes in the level with the slab's own material. Editor, PIE stopped."""
import json
from pathlib import Path
import unreal

TAG = 'MareRockBase'
OUT = Path('D:/CodexTemp/rock_base.json')
SLABS = ('coast_rocks_02', 'coast_land_rocks_03', 'coast_rocks_05', 'coast_land_rocks_02', 'coast_rocks_03')
NEAR = (10800.0, -4000.0, 2600.0)       # the lighthouse and how far from it a slab counts
STEP = 30.0


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _slabs():
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        label = a.get_actor_label()
        name = next((s for s in SLABS if label.endswith(s)), None)
        if not name:
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            o, e = c.get_local_bounds()
            b = unreal.SystemLibrary.get_component_bounds(c)
            if (b[0].x - NEAR[0]) ** 2 + (b[0].y - NEAR[1]) ** 2 < NEAR[2] ** 2:
                out.append((name, a, c, b[0], b[1]))
    return out


def scan(_=''):
    world = _world()
    rows = []
    for name, actor, comp, origin, ext in _slabs():
        x0, y0 = origin.x - ext.x - STEP, origin.y - ext.y - STEP
        nx, ny = int((2 * ext.x) / STEP) + 3, int((2 * ext.y) / STEP) + 3
        grid = []
        for j in range(ny):
            line = []
            for i in range(nx):
                x, y = x0 + i * STEP, y0 + j * STEP
                hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(x, y, origin.z + ext.z + 200), unreal.Vector(x, y, origin.z - ext.z - 200),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True) or []
                top = None
                for h in hits:
                    t = h.to_tuple()
                    if t[9] == actor:
                        top = round(t[4].z, 1)
                        break
                line.append(top)
            grid.append(line)
        mat = comp.get_material(0)
        rows.append({'name': name, 'x0': x0, 'y0': y0, 'step': STEP, 'grid': grid, 'material': mat.get_path_name() if mat else '',
                     'cells': sum(1 for l in grid for v in l if v is not None), 'z': [round(origin.z - ext.z), round(origin.z + ext.z)]})
    OUT.write_text(json.dumps(rows), encoding='utf-8')
    return json.dumps([[r['name'], r['cells'], r['z'], len(r['grid'][0]), len(r['grid'])] for r in rows])


def place(arg='dry'):
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    rows = json.loads(OUT.read_text(encoding='utf-8'))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mine = [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.StaticMeshActor) if TAG in [str(t) for t in a.tags]]
    out = {'mine': len(mine), 'placed': []}
    if arg.strip() != 'apply':
        return json.dumps(out)
    for a in mine:
        actors.destroy_actor(a)
    for k, r in enumerate(rows):
        mesh = unreal.load_asset(data.get(f'mare_rock_base_{k}', ''))
        if not mesh:
            continue
        # the model is in world metres with Blender y = -UE y: placed at the origin, no rotation
        a = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
        a.set_actor_label('Farol · base de rocha ' + r['name'])
        a.tags = [unreal.Name('MareGenerated'), unreal.Name(TAG)]
        a.set_folder_path('Praia/Farol')
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.STATIC)
        mat = unreal.load_asset(r['material']) if r['material'] else None
        if mat:
            for s in range(c.get_num_materials()):
                c.set_material(s, mat)
        out['placed'].append(r['name'])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)

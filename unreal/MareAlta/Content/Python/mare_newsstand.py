"""Village newsstand (11/11): the Godot export (actor "... newsstand", mesh World_2200, a plain green box with flat
colour cards) is replaced by the bpy model mare_newsstand (tools/ue58/gen_newsstand.py: ribbed steel body, open front
with the shutter rolled up, counter with newspaper piles, magazine racks, open door leaves, striped awning).
swap('dry'|'apply'): removes the old instance actor and places the new mesh at the same spot, front to -Y (where the
translated "BANCA" TextRender already hangs, 86 cm in front of the centre at 2.37 m). Re-runnable; PIE stopped."""
import json
from pathlib import Path
import unreal

TAG = 'MareNewsstand'
AT = (8240.0, 3595.0, 10.0)


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def swap(arg='dry'):
    apply = arg.strip() == 'apply'
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    mesh = unreal.load_asset(data['mare_newsstand'])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old, mine = [], []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        if TAG in [str(t) for t in a.tags]:
            mine.append(a)
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() == 'World_2200':
                t = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())]
                old.append((a, c, [[round(x.translation.x), round(x.translation.y), round(x.translation.z), round(x.rotation.rotator().yaw)] for x in t]))
    out = {'old': [[a.get_actor_label(), t] for a, c, t in old], 'mine': len(mine), 'mesh': bool(mesh)}
    if not apply or not mesh:
        return out
    for a, c, t in old:
        actors.destroy_actor(a)
    for a in mine:
        actors.destroy_actor(a)
    n = actors.spawn_actor_from_object(mesh, unreal.Vector(*AT), unreal.Rotator(roll=0, pitch=0, yaw=180))
    n.set_actor_label('Banca de jornal')
    n.tags = [TAG]
    n.set_folder_path('Vila/Banca')
    n.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    out['placed'] = [round(v) for v in AT]
    return out


def tidy(arg='dry'):
    """What the old solid box hid or touched: the street lamp standing INSIDE the footprint (post at 8280,3555: its pole
    crossed the open front and the lantern came out of the roof) moves to the back left corner, the planter box at the
    front right corner moves beside the right wall, and the "BANCA" sign comes 3 cm in front of the new fascia in a
    cream paint that reads on the dark steel. 'dry' lists, 'apply' moves and saves. Re-runnable (moves only what is
    still at the old spot)."""
    apply = arg.strip() == 'apply'
    moves = (((8280.0, 3555.0), (8085.0, 3665.0), 45.0), ((8320.0, 3520.0), (8400.0, 3650.0), 30.0))
    out = {'moved': [], 'sign': None}
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                for (fx, fy), (tx, ty), r in moves:
                    if (t.translation.x - fx) ** 2 + (t.translation.y - fy) ** 2 < r * r and t.translation.z < 600:
                        out['moved'].append([a.get_actor_label(), i, round(t.translation.x), round(t.translation.y), round(t.translation.z)])
                        if apply:
                            t.translation = unreal.Vector(t.translation.x + tx - fx, t.translation.y + ty - fy, t.translation.z)
                            c.update_instance_transform(i, t, True, True, True)
        if isinstance(a, unreal.TextRenderActor) and str(a.text_render.get_editor_property('text')) == 'BANCA':
            tr = a.text_render
            col = tr.get_editor_property('text_render_color')
            out['sign'] = {'at': [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)],
                           'yaw': round(a.get_actor_rotation().yaw), 'colour': [col.r, col.g, col.b], 'size': tr.get_editor_property('world_size'),
                           'hidden': a.is_hidden_ed(), 'tags': [str(t) for t in a.tags]}
            if apply:
                # the fascia plane is found by a trace (complex collision of the model), the sign goes 2 cm in front of it
                hit = unreal.SystemLibrary.line_trace_single(_world(), unreal.Vector(8240.0, AT[1] - 400.0, 237.0), unreal.Vector(8240.0, AT[1], 237.0),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
                y = hit.to_tuple()[4].y if hit else AT[1] - 90.0
                out['fascia_y'] = round(y, 1)
                a.set_actor_location(unreal.Vector(8240.0, y - 2.0, 237.0), False, False)
                tr.set_editor_property('text_render_color', unreal.Color(r=236, g=226, b=196, a=255))
    if apply:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out

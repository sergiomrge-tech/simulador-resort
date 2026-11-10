"""Sunbathers against their towels (10/11, Sergio's photo: the face-down bather lying half off her towel).

towels(): the towel meshes of the level against Content/Data/sunbathers.json (the data must be the towel's centre).
bathers(): PIE, every MareBather lying down: head, pelvis and feet against the towel centre of the data."""
import json
import math
from pathlib import Path

import unreal

DATA = Path(unreal.Paths.project_content_dir()) / 'Data' / 'sunbathers.json'


def _spots():
    return json.loads(DATA.read_text(encoding='utf-8'))['towels']


def towels(arg=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rows = []
    cands = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m:
                continue
            bb = m.get_bounding_box()
            ts = ([c.get_instance_transform(i, True) for i in range(c.get_instance_count())]
                  if isinstance(c, unreal.InstancedStaticMeshComponent) else [c.get_world_transform()])
            for t in ts:
                size = (bb.max - bb.min) * t.scale3d
                dims = sorted([abs(size.x), abs(size.y)])
                # a towel: flat (under 12 cm), 70-130 by 150-240 cm
                if abs(size.z) < 12 and 70 < dims[0] < 130 and 150 < dims[1] < 240:
                    ctr = t.transform_location((bb.min + bb.max) * .5)
                    cands.append((m.get_name(), a.get_actor_label(), ctr, t.rotation.rotator().yaw, [round(abs(size.x)), round(abs(size.y))], c.is_visible() and not a.is_hidden_ed()))
    for i, s in enumerate(_spots()):
        near = sorted(cands, key=lambda k: (k[2].x - s[0]) ** 2 + (k[2].y - s[1]) ** 2)[:2]
        rows.append({'spot': i, 'data': s, 'nearest': [{'mesh': n[0], 'actor': n[1], 'centre': [round(n[2].x), round(n[2].y), round(n[2].z)], 'yaw': round(n[3]), 'size': n[4],
                                                       'off_cm': round(math.hypot(n[2].x - s[0], n[2].y - s[1])), 'visible': n[5]} for n in near]})
    return json.dumps({'towel_like': len(cands), 'rows': rows}, ensure_ascii=False)


def bathers(arg=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return json.dumps({'pie': False})
    spots = _spots()
    rows = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        if 'MareBather' not in [str(t) for t in p.tags]:
            continue
        mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
        head, pel = mesh.get_socket_location('head'), mesh.get_socket_location('pelvis')
        fl, fr = mesh.get_socket_location('foot_l'), mesh.get_socket_location('foot_r')
        mid = (fl + fr) * .5
        ctr = (head + mid) * .5
        loc = p.get_actor_location()
        i, s = min(enumerate(spots), key=lambda k: (k[1][0] - loc.x) ** 2 + (k[1][1] - loc.y) ** 2)
        if math.hypot(s[0] - loc.x, s[1] - loc.y) > 400:
            continue
        rows.append({'spot': i, 'actor': [round(loc.x), round(loc.y), round(loc.z)], 'head': [round(head.x), round(head.y), round(head.z)],
                     'pelvis': [round(pel.x), round(pel.y), round(pel.z)], 'feet': [round(mid.x), round(mid.y), round(mid.z)],
                     'body_cm': round((head - mid).length()), 'centre_off_cm': round(math.hypot(ctr.x - s[0], ctr.y - s[1])),
                     'pelvis_above_towel_cm': round(pel.z - s[2]), 'hidden': bool(p.get_editor_property('hidden'))})
    return json.dumps(rows, ensure_ascii=False)

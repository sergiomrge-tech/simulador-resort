"""Lamp posts along the island trails (08/11, Sergio: "postes iluminados por todo o percurso da trilha, a cada 10 m"):
the village street lamp (Poly Haven street_lamp_01, 3.9 m) every 10 m on the summit, West and North trails, on
alternate sides 1.7 m (x the path's width) from the centre line, standing on the ground found by a trace (not in the
water, not on a building). Written as lighting.json fixtures (MareVisualWorld::BuildLamps: a warm light pointing down
from the head that comes on at dusk, culled beyond mare.LightDrawDistance, shadows only for the nearest few by
mare.LightShadowBudget). Re-runnable: the old "Trilha ·" entries are replaced. PIE stopped (editor world traces)."""
import json
import math
from pathlib import Path

import unreal

DATA = Path(unreal.Paths.project_dir()).resolve() / 'Content/Data'
PREFIX = 'Trilha · poste'
MESH = '/Game/World/Models/World_1391/World_1391/StaticMeshes/World_1391.World_1391'
SPACING, SIDE, HEAD = 1000.0, 170.0, 360.0


def _resample(pts, step):
    out, carry = [], 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        t = carry
        while t <= seg:
            f = t / seg if seg else 0
            out.append((ax + (bx - ax) * f, ay + (by - ay) * f, (bx - ax) / (seg or 1), (by - ay) / (seg or 1)))
            t += step
        carry = t - seg
    return out


def run(_=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    trails = {k: ([(p[0], p[1]) for p in t['points']], t.get('w')) for k, t in
              json.loads((DATA / 'island_trails.json').read_text(encoding='utf-8'))['trails'].items()}
    summit = json.loads(Path('D:/CodexTemp/tsunami/trail.json').read_text(encoding='utf-8'))
    trails['cume'] = ([(p[0], p[1]) for p in summit], None)
    lamps, skipped = [], {}
    for key, (pts, _) in trails.items():
        for n, (x, y, dx, dy) in enumerate(_resample(pts, SPACING)):
            side = 1 if n % 2 == 0 else -1
            px, py = x + dy * SIDE * side, y - dx * SIDE * side
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(px, py, 30000), unreal.Vector(px, py, -3000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            label = t[9].get_actor_label() if t and t[9] else ''
            if not t or t[4].z < 20:
                skipped['water'] = skipped.get('water', 0) + 1
                continue
            if t[7].z < .75 or not ('trilha' in label or 'terreno' in label or 'Ground' in label or '@MeshInstance3D' in label or 'Preenchimento' in label):
                skipped[label[:30] or 'steep'] = skipped.get(label[:30] or 'steep', 0) + 1
                continue
            # the lamp's arm over the path: yaw so its +x points back to the centre line
            yaw = math.degrees(math.atan2(y - py, x - px))
            lamps.append({'name': f'{PREFIX} {key} {n + 1}', 'mesh': MESH, 'at': [round(px), round(py), round(t[4].z - 3, 1)], 'yaw': round(yaw, 1),
                          'light_up': HEAD, 'candela': 150, 'radius': 1600, 'kelvin': 2900, 'glow': .2})
    path = DATA / 'lighting.json'
    raw = path.read_text(encoding='utf-8-sig')
    d = json.loads(raw)
    d['fixtures'] = [f for f in d['fixtures'] if not f.get('name', '').startswith(PREFIX)] + lamps
    path.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')
    return json.dumps({'lamps': len(lamps), 'per_trail': {k: sum(1 for l in lamps if f' {k} ' in l['name']) for k in trails}, 'skipped': skipped})

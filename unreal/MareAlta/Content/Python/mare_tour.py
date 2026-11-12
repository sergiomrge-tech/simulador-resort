"""Whole-game visual tour for audits: one editor camera per expansion/business region plus fixed
village, beach and landmark views. Returns CaptureViewport transforms (editor, PIE stopped)."""
import math
import unreal

FIXED = {
    'vila-rua': ((4800, 2780, 180), (-4, 0)),
    'vila-praca': ((6200, 3600, 900), (-25, 200)),
    'casas-fachada': ((5600, 1400, 220), (-3, 90)),
    'casa-jogador': ((4520, 2700, 200), (-8, -60)),
    'quiosque-frente': ((3800, -2350, 200), (-4, 90)),
    'quiosque-alto': ((3800, -3600, 1100), (-28, 90)),
    'praia-leste': ((7600, -2600, 300), (-6, 160)),
    'praia-oeste': ((300, -2600, 300), (-6, 20)),
    'pier': ((7200, -3800, 250), (-6, -90)),
    'farol': ((1500, -900, 400), (6, 200)),
    'hotel-fachada': ((-2100, 3600, 400), (2, 90)),
    'hotel-terraco': ((-2400, 2200, 900), (-25, 60)),
    'vila-noroeste': ((1000, 5200, 400), (-8, 30)),
    'vila-aerea': ((4000, -6000, 6000), (-38, 90)),
}


def regions():
    groups = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for tag in a.tags:
            t = str(tag)
            if (t.startswith('Region_') and t != 'Region_') or t.startswith('Biz_'):
                o, e = a.get_actor_bounds(False)
                if e.length() < 1 or e.x > 20000:
                    continue
                g = groups.setdefault(t, [1e9, 1e9, 1e9, -1e9, -1e9, -1e9])
                g[0], g[1], g[2] = min(g[0], o.x - e.x), min(g[1], o.y - e.y), min(g[2], o.z - e.z)
                g[3], g[4], g[5] = max(g[3], o.x + e.x), max(g[4], o.y + e.y), max(g[5], o.z + e.z)
    return groups


def views():
    out = {name: {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': p, 'yaw': yw, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
           for name, ((x, y, z), (p, yw)) in FIXED.items()}
    for tag, (x0, y0, z0, x1, y1, z1) in regions().items():
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        size = max(x1 - x0, y1 - y0, 600)
        dist = min(size * 1.2, 6000)
        cam = (cx, cy - dist, max(z1, 300) + size * 0.25)
        pitch = -math.degrees(math.atan2(cam[2] - (z0 + z1) / 2, dist))
        out['regiao-' + tag.split('_', 1)[1].lower()] = {'location': {'x': cam[0], 'y': cam[1], 'z': cam[2]},
                                                        'rotation': {'pitch': pitch, 'yaw': 90, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
    return out


def run(action, arg=''):
    if action == 'regions':
        return {k: [round(v) for v in b] for k, b in regions().items()}
    if action == 'views':
        return views()
    raise ValueError(action)

"""Inflatable beach ball replacing the Godot export World_0137 (392 triangles). Built in the old mesh's frame: 1 m
across, pivot at the centre; the level instances scale it to 44 and 32 cm. Six gores alternating colour and white,
white polar caps, sunken seams, a valve plug. D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_beach_ball.py
Output: unreal/MareAlta/SourceArt/Models/Props/beach_ball_hd.glb (material names prefixed beach_ball_)."""
import math
from pathlib import Path
import bpy
import bmesh

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/Props'
RADIUS = .5
GORES = [(.86, .12, .10), (.95, .95, .92), (.10, .38, .85), (.95, .95, .92), (1.0, .74, .08), (.95, .95, .92)]


def material(name, colour, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Specular IOR Level'].default_value = .6          # glossy vinyl
    return m


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = [material(f'beach_ball_gore{i}', c, .28) for i, c in enumerate(GORES)]
    cap = material('beach_ball_cap', (.95, .95, .92), .3)
    plug = material('beach_ball_valve', (.92, .92, .9), .45)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=RADIUS, segments=96, ring_count=48)
    ob = bpy.context.active_object
    me = ob.data
    for m in mats + [cap, plug]:
        me.materials.append(m)
    bm = bmesh.new()
    bm.from_mesh(me)
    # Seams: vertices on a gore boundary sink (about 3 mm in game); the inflated vinyl bulges a little between seams.
    for v in bm.verts:
        lon = math.atan2(v.co.y, v.co.x) % (2 * math.pi)
        f = (lon / (2 * math.pi) * len(GORES)) % 1.0
        d = min(f, 1 - f)
        lat = math.asin(max(-1, min(1, v.co.z / RADIUS)))
        bulge = 1 + .012 * math.sin(math.pi * f) * math.cos(lat)
        if d < .012 and abs(lat) < math.radians(79):
            bulge -= .0067
        v.co *= bulge
    for f in bm.faces:
        c = f.calc_center_median()
        lat = math.asin(max(-1, min(1, c.z / c.length)))
        lon = math.atan2(c.y, c.x) % (2 * math.pi)
        f.material_index = len(GORES) if abs(lat) > math.radians(79) else int(lon / (2 * math.pi) * len(GORES)) % len(GORES)
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    # Valve: a short plug on one gore near the equator.
    bpy.ops.mesh.primitive_cylinder_add(radius=.02, depth=.026, vertices=24, location=(RADIUS * .99, 0, .066))
    valve = bpy.context.active_object
    valve.rotation_euler = (0, math.pi / 2, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    valve.data.materials.append(plug)
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.join()
    ob.name = me.name = 'beach_ball_hd'
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / 'beach_ball_hd.glb'), export_format='GLB', export_apply=True)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print('beach_ball_hd', tris, 'triangles')


if __name__ == '__main__':
    main()

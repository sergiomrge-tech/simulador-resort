"""Mountain range across the sea (07/11, Sergio, pointing at a hazy blue ridge behind a bay in the reference game:
"montanhas ao fundo, coloque isso no nosso jogo"). A long ridged band generated like terrain (no free model of a whole
mountain range at this scale with a clear licence), textured in UE by mare_mountains.py (forest low, rock high, aerial
haze by distance). Two layers: a nearer, lower ridge and a taller one behind it, both seen across the sea.

  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_mountains.py
Outputs unreal/MareAlta/SourceArt/Models/Mountains/Mountains_Near.glb and Mountains_Far.glb (metres, Z up, the band runs
along X, its foot at y=0 faces -Y toward the beach after placement; z=0 = sea level, the foot dips below it).
UV1.u = ridge mask 0..1 (rock on crests), UV1.v = height 0..1 (for the material)."""
import os
import sys

import bpy  # noqa: F401  (bpy before bmesh/mathutils in this package)
import bmesh
import math
from mathutils import noise, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'unreal', 'MareAlta', 'SourceArt', 'Models', 'Mountains')


def ridged(p, octaves=6, lac=2.05, gain=.5):
    """Ridged multifractal: sharp crests and valleys, like eroded tropical mountains."""
    amp, freq, total, norm = 1.0, 1.0, 0.0, 0.0
    for _ in range(octaves):
        n = 1.0 - abs(noise.noise(p * freq))
        total += amp * n * n
        norm += amp
        amp *= gain
        freq *= lac
    return total / norm


PEAKS = {}


def peaks(name, length, seed, count):
    import random
    rnd = random.Random(seed)
    out = []
    for k in range(count):
        px = length * ((k + rnd.uniform(.15, .85)) / count - .5)
        out.append((px, rnd.uniform(1500.0, 4000.0), rnd.uniform(.35, 1.0)))
    PEAKS[name] = out


def band(name, length, depth, peak, seed, nx, ny):
    """Height field over [-length/2, length/2] x [0, depth] (m): rises from below the sea at y=0 to the crest and falls
    away behind it; the crest line wanders and the peaks vary along the band."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv0 = bm.loops.layers.uv.new('UVMap')
    uv1 = bm.loops.layers.uv.new('UVMask')
    off = Vector((seed * 13.7, seed * 7.3, seed * 3.1))
    rows = []
    masks = {}
    for j in range(ny + 1):
        y = depth * j / ny
        row = []
        for i in range(nx + 1):
            x = length * (i / nx - .5)
            q = Vector((x / 9000.0, y / 9000.0, 0)) + off
            crest_y = depth * (.42 + .18 * noise.noise(Vector((x / 14000.0, seed, 0))))
            # 07/11 first try read as a flat brown wall from the beach: the skyline now is a row of individual peaks
            # (cones 1.5-4 km wide, 35-100 % of the peak height), with ridged detail carving them.
            top = 0.0
            for (px, pw, ph) in PEAKS[name]:
                dx = (x - px) / pw
                dy = (y - crest_y) / (pw * 1.15)
                top = max(top, ph * max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy)) ** 1.25)
            r = ridged(q * 2.2)
            h = peak * top * (.72 + .28 * r)
            # the sea side: a gentle foothill skirt that dips below the waterline
            if y < crest_y:
                h *= min(1.0, (y + depth * .04) / (crest_y * .9)) ** .8
            h -= 60.0 * (1.0 - min(1.0, y / (depth * .08)))
            # fade the band's two ends into the sea so no cut edge shows
            end = min(1.0, (length * .5 - abs(x)) / (length * .12))
            h = h * end - 80.0 * (1.0 - end)
            v = bm.verts.new((x, y, h))
            masks[v] = (max(0.0, min(1.0, (r - .55) * 2.5)), max(0.0, min(1.0, h / peak)))
            row.append(v)
        rows.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bm.normal_update()
    # Open surface: make sure the faces point up (UE culls back faces; see gen_volcano.py).
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.normal_update()
    for f in bm.faces:
        for loop in f.loops:
            v = loop.vert
            loop[uv0].uv = (v.co.x / length + .5, v.co.y / depth)
            loop[uv1].uv = masks[v]
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    me.materials.append(bpy.data.materials.new(name + '_Rock'))
    return obj


def export(obj, name):
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + '.glb'), export_format='GLB', use_selection=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
peaks('Mountains_Near', 42000.0, 3, 13)
near = band('Mountains_Near', 42000.0, 7000.0, 750.0, 3, 600, 110)
export(near, 'Mountains_Near')
peaks('Mountains_Far', 60000.0, 11, 15)
far = band('Mountains_Far', 60000.0, 9000.0, 1300.0, 11, 700, 110)
export(far, 'Mountains_Far')
print('MOUNTAINS', len(near.data.vertices), len(far.data.vertices))
sys.stdout.flush()

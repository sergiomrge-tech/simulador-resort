"""Volcanic island far out at sea (pedido do Sergio, 04/11): rocky cone with a crater, erosion gullies and a lava-rock
shore, plus the ash plume rising from the crater. No free volcano with a clear licence exists (Free3D/CGTrader are
royalty-free, Poly Haven has none), so the landform is generated here like terrain and textured in UE with Poly Haven
CC0 rock_face + burned_ground_01 (vertex colour R = ash cover, G = wet shore).

  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_volcano.py
Outputs D:/CodexTemp/volcano/Volcano_Island.glb and Volcano_Plume.glb (metres, Z up; base of the cone at z=0 = sea level).
"""
import bpy
import bmesh
import math
import random
from mathutils import noise, Vector

OUT = 'D:/CodexTemp/volcano/'
random.seed(7)

R_SHORE = 230.0     # metres
R_OUT = 270.0       # sea floor ring
PEAK = 190.0
RIM = 42.0          # crater rim radius
CRATER_FLOOR = 128.0
PHASES = [(random.uniform(0, math.tau), random.uniform(5, 13), random.uniform(0.4, 1.0)) for _ in range(9)]


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


LAVA_DIR = -math.pi / 2     # Blender -Y becomes UE +Y (towards the beach): the glowing night flows face it


def angdist(a, b):
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def surface(r, th):
    """Height (m), gully depth 0..1 and night-lava mask 0..1 at polar (r, th). Stratovolcano like Arenal:
    concave cone, steep summit, dozens of sharp radial ravines with knife-edge ridges between them."""
    shore = R_SHORE * (1 + 0.10 * math.sin(th * 2 + 1.3) + 0.06 * math.sin(th * 5 + 0.4))
    p = Vector((math.cos(th) * r, math.sin(th) * r, 0))
    notch = math.exp(-(angdist(th, 4.1) / 0.35) ** 2)
    if r <= RIM:
        bowl = CRATER_FLOOR + (PEAK + 4 - CRATER_FLOOR) * (r / RIM) ** 3.2   # deep bowl, sharp rim
        return bowl - 30 * notch * (r / RIM) ** 2 + 3 * noise.noise(p * 0.05), 0.0, 0.0
    if r > shore:
        # Underwater the cone keeps going down (a ramp, not a wall): -1.6 m per metre to -45 m.
        return max(-45.0, 0.4 - 1.6 * (r - shore)) + 1.0 * noise.noise(p * 0.03), 0.0, 0.0
    t = (r - RIM) / (shore - RIM)
    h = PEAK * (1 - t) ** 1.75 + 14 * (1 - t) * t
    env = min(1.0, 0.35 + t * 6) * math.sin(math.pi * min(0.999, 0.08 + t * 1.0)) ** 0.5   # ravines reach the rim, fade at the shore
    # Two families of ravines, angle warped by noise so they meander and branch.
    a1 = th + 0.45 * noise.noise(p * 0.004) + 0.10 * noise.noise(p * 0.016)
    v1 = (1 - abs(math.sin(a1 * 15))) ** 3                         # ~30 narrow V valleys
    a2 = th + 0.6 * noise.noise(p * 0.0028 + Vector((7, 3, 0)))
    v2 = (1 - abs(math.sin(a2 * 6.5))) ** 2.2                      # ~13 broad valleys
    # Each ravine has its own depth and starts at its own height (irregular, not curtain pleats).
    k1 = 0.45 + 0.9 * (0.5 + 0.5 * noise.noise(Vector((math.cos(a1) * 3, math.sin(a1) * 3, 1.7))))
    k2 = 0.5 + 0.8 * (0.5 + 0.5 * noise.noise(Vector((math.cos(a2) * 2, math.sin(a2) * 2, 5.3))))
    start1 = smooth(0.0 + 0.25 * abs(noise.noise(Vector((math.cos(a1) * 4, math.sin(a1) * 4, 9.1)))), 0.35, t + 0.04)
    depth = env * (28 * v1 * k1 * start1 + 20 * v2 * k2)
    h -= depth
    h += 4 * max(0, 1 - t * 4) * noise.noise(p * 0.07)                # rugged summit
    h += 5 * noise.noise(p * 0.012) + 2.4 * noise.noise(p * 0.045) + 1.0 * noise.noise(p * 0.15) + 0.4 * noise.noise(p * 0.45)
    # Older parasitic cone on the north-west flank and a collapsed notch in the crater rim.
    dx, dy = p.x - math.cos(2.3) * 125, p.y - math.sin(2.3) * 125
    h += 55 * math.exp(-(dx * dx + dy * dy) / (2 * 36.0 ** 2))
    h -= 34 * notch * max(0, 1 - (r - RIM) / 70)
    h += 3.5 * max(0, 1 - t * 6) * abs(noise.noise(p * 0.08))      # blocky lava-rock shore
    gully = min(1.0, depth / 26.0)
    # Night lava: a few thin streaks from the rim down the upper third of the beach side, fading downwards.
    lava = math.exp(-(angdist(th, LAVA_DIR) / 0.42) ** 2) * smooth(0.62, 0.92, v1) * (1 - smooth(0.25, 0.6, t + 0.15 * noise.noise(p * 0.01)))
    lava = min(1.0, lava * 1.6)
    return max(h, 0.6), gully, lava


def height(r, th):
    return surface(r, th)[0]


def build_island():
    me = bpy.data.meshes.new('Volcano_Island')
    bm = bmesh.new()
    NA, NR = 720, 240
    rings, data = [], {}
    h0 = surface(0, 0)
    centre = bm.verts.new((0, 0, h0[0]))
    data[centre] = h0
    for i in range(1, NR + 1):
        r = R_OUT * (i / NR) ** 1.1
        row = []
        for j in range(NA):
            th = j / NA * math.tau
            sv = surface(r, th)
            v = bm.verts.new((math.cos(th) * r, math.sin(th) * r, sv[0]))
            data[v] = sv
            row.append(v)
        rings.append(row)
    for j in range(NA):
        bm.faces.new((centre, rings[0][j], rings[0][(j + 1) % NA]))
    for i in range(NR - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(NA):
            k = (j + 1) % NA
            bm.faces.new((a[j], b[j], b[k], a[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    # An open surface has no inside: recalc may pick the downward orientation, and UE culls those back faces
    # (04/11: from the side we saw the inside of the crater as a dome, and the whole slope dark). Faces point up.
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.normal_update()
    # Masks in a second UV channel (UE's glTF importer drops this mesh's vertex colours): UV1.u = ravine depth
    # (dark rock), UV1.v = night lava channel. glTF stores v flipped, so UE reads 1 - lava. UV0 is a plain top
    # projection (the material projects its textures in world space anyway).
    uv0 = bm.loops.layers.uv.new('UVMap')
    uv1 = bm.loops.layers.uv.new('UVMask')
    for f in bm.faces:
        for loop in f.loops:
            v = loop.vert
            _, gully, lava = data[v]
            loop[uv0].uv = (v.co.x / 540 + 0.5, v.co.y / 540 + 0.5)
            loop[uv1].uv = (gully, lava)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new('Volcano_Island', me)
    bpy.context.collection.objects.link(obj)
    mat = bpy.data.materials.new('Volcano_Island_Rock')
    me.materials.append(mat)
    return obj


def build_plume():
    """Ash column: widening tube bent downwind, UV v = 0 at the crater to 1 at the top."""
    me = bpy.data.meshes.new('Volcano_Plume')
    bm = bmesh.new()
    NA, NH, H = 40, 72, 420.0
    uv_rows, rows = [], []
    for i in range(NH + 1):
        t = i / NH
        z = CRATER_FLOOR + 10 + H * t
        rad = 18 + 150 * t ** 1.3
        cx = 160 * t ** 1.8                     # wind bends it to +X
        cy = 25 * math.sin(t * 3)
        row = []
        for j in range(NA + 1):
            th = j / NA * math.tau
            wob = 1 + 0.18 * noise.noise(Vector((math.cos(th) * 2, math.sin(th) * 2, t * 6)))
            row.append(bm.verts.new((cx + math.cos(th) * rad * wob, cy + math.sin(th) * rad * wob, z)))
        rows.append(row)
    uv = bm.loops.layers.uv.new('UVMap')
    for i in range(NH):
        for j in range(NA):
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            for loop, (u, v) in zip(f.loops, ((j / NA, i / NH), ((j + 1) / NA, i / NH), ((j + 1) / NA, (i + 1) / NH), (j / NA, (i + 1) / NH))):
                loop[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new('Volcano_Plume', me)
    bpy.context.collection.objects.link(obj)
    me.materials.append(bpy.data.materials.new('Volcano_Plume_Ash'))
    return obj


def build_sparks():
    """Night eruption: ballistic spark trails from the crater (thin tubes; UV u runs along each arc, the material
    moves bright dashes along it). Shown only on eruption nights (MPC_MareTime.Volcano)."""
    me = bpy.data.meshes.new('Volcano_Sparks')
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rnd = random.Random(11)
    for k in range(70):
        az = rnd.uniform(0, math.tau)
        speed = rnd.uniform(30, 58)                  # m/s, 9.8 m/s2: apex 60-250 m above the vent
        tilt = math.radians(rnd.uniform(3, 15))
        vx, vy, vz = speed * math.sin(tilt) * math.cos(az), speed * math.sin(tilt) * math.sin(az), speed * math.cos(tilt)
        z0 = PEAK - 6
        T = (vz + math.sqrt(vz * vz + 2 * 9.8 * 60)) / 9.8   # until 60 m below the vent (onto the slope)
        seg, sides, rad = 28, 4, rnd.uniform(0.35, 0.8)
        rings = []
        for i in range(seg + 1):
            t = T * i / seg
            c = Vector((vx * t, vy * t, z0 + vz * t - 4.9 * t * t))
            rings.append([bm.verts.new(c + Vector((math.cos(a) * rad, math.sin(a) * rad, 0))) for a in (j / sides * math.tau for j in range(sides))])
        phase = rnd.random()
        for i in range(seg):
            for j in range(sides):
                jj = (j + 1) % sides
                f = bm.faces.new((rings[i][j], rings[i][jj], rings[i + 1][jj], rings[i + 1][j]))
                for loop, (u, v) in zip(f.loops, ((i / seg, phase), (i / seg, phase), ((i + 1) / seg, phase), ((i + 1) / seg, phase))):
                    loop[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('Volcano_Sparks', me)
    bpy.context.collection.objects.link(obj)
    me.materials.append(bpy.data.materials.new('Volcano_Sparks_Glow'))
    return obj


def export(obj, name):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=OUT + name + '.glb', export_format='GLB', use_selection=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
island = build_island()
plume = build_plume()
export(island, 'Volcano_Island')
export(plume, 'Volcano_Plume')
sparks = build_sparks()
export(sparks, 'Volcano_Sparks')
print('VOLCANO', len(island.data.vertices), 'verts island,', len(plume.data.vertices), 'verts plume')

"""The tsunami (04/11, Sergio: "uma onda gigante, 100 m de altura... precisa ser um evento épico"): one breaking wave
3 km wide at full size, 100 m tall, a long back slope, the crest and a lip curling forward over a hollow face.
Blender metres, Z up; the wave runs towards Blender -Y (= UE +Y, towards the beach); origin at the crest's foot on the
sea surface. UV0: u along the front (1 per 40 m), v along the profile (0 = far back foot, 1 = front foot); UV1.x = 1 at
the lip, 0 at the feet (foam mask for M_TsunamiWave); UV1.y = height / crest height (08/11: the break in the material
bends the upper part forward and down by it). Width varies (+-8 % height) so it is not a ruler-straight wall.
08/11 (Sergio: references of a dark wall with a white crest and spray breaking over the beach): a second material slot
(M_TsunamiSpray) holds two spray curtains above the crest, one rising over the lip, one blown back off the top; their
UV0.y runs 0 (at the crest) .. 1 (top of the curtain), UV1.y > 1.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_tsunami_wave.py"""
import math

import bpy
import bmesh

OUT = 'D:/Projetos/MareAltaUE58/unreal/MareAlta/SourceArt/Models/Summit/TsunamiWave.glb'
# Profile (forward = -Y in Blender, metres): back foot -> crest -> lip tip -> under the lip -> hollow face -> front foot.
PROFILE = [(320, -6), (240, 4), (170, 18), (115, 38), (75, 60), (45, 79), (22, 92), (6, 99), (-8, 101), (-20, 99),
           (-29, 93), (-33, 85), (-31, 78), (-24, 75), (-17, 77), (-12, 74), (-9, 64), (-8, 50), (-10, 36), (-15, 22),
           (-24, 10), (-38, 1), (-60, -6)]
LIP = {9: .6, 10: 1.0, 11: 1.0, 12: 1.0, 13: .9, 14: .7, 15: .5, 8: .35, 16: .3}
WIDTH, SEGS = 3000.0, 240
# Spray curtains (profile coordinates, forward = -x): over the lip, and blown back off the top.
SPRAY = [[(2, 99), (-5, 107), (-12, 115), (-19, 122), (-26, 127)],
         [(14, 97), (22, 105), (33, 113), (46, 119), (62, 123)]]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    uv0 = bm.loops.layers.uv.new('UVMap')
    uv1 = bm.loops.layers.uv.new('UVFoam')
    cum = [0.0]
    for a, b in zip(PROFILE, PROFILE[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    rows = []
    for i in range(SEGS + 1):
        x = -WIDTH / 2 + WIDTH * i / SEGS
        # Height and lead vary slowly along the front; both ends sink into the sea.
        h = 1 + .06 * math.sin(x * .0041 + 1.3) + .04 * math.sin(x * .0113)
        end = min(1.0, (WIDTH / 2 - abs(x)) / 260)
        h *= .25 + .75 * math.sin(end * math.pi / 2)
        lead = 12 * math.sin(x * .0027 + .4)
        rows.append([bm.verts.new((x, -(p[0] - lead) * (.6 + .4 * h), p[1] * h)) for p in PROFILE])
    for i in range(SEGS):
        for k in range(len(PROFILE) - 1):
            f = bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]))
            f.smooth = True
            for loop, (a, b) in zip(f.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                loop[uv0].uv = (a * WIDTH / SEGS / 40.0, cum[b] / cum[-1])
                loop[uv1].uv = (LIP.get(b, 0.0), max(0.0, PROFILE[b][1]) / 101.0)
    bm.normal_update()
    # The outside of the wave (sky side of the back, sea side of the face) must face out: sample the back slope.
    back = [f for f in bm.faces if f.calc_center_median().y > 100]
    if sum(f.normal.z for f in back) < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    wave_faces = len(bm.faces)
    for sheet in SPRAY:
        srows = []
        for i in range(SEGS + 1):
            x = -WIDTH / 2 + WIDTH * i / SEGS
            h = 1 + .06 * math.sin(x * .0041 + 1.3) + .04 * math.sin(x * .0113)
            end = min(1.0, (WIDTH / 2 - abs(x)) / 260)
            h *= .25 + .75 * math.sin(end * math.pi / 2)
            lead = 12 * math.sin(x * .0027 + .4)
            srows.append([bm.verts.new((x, -(p[0] - lead) * (.6 + .4 * h), p[1] * h)) for p in sheet])
        for i in range(SEGS):
            for k in range(len(sheet) - 1):
                f = bm.faces.new((srows[i][k], srows[i + 1][k], srows[i + 1][k + 1], srows[i][k + 1]))
                f.smooth = True
                f.material_index = 1
                for loop, (a, b) in zip(f.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                    loop[uv0].uv = (a * WIDTH / SEGS / 40.0, b / (len(sheet) - 1))
                    loop[uv1].uv = (0.0, sheet[b][1] / 101.0)
    bm.normal_update()
    me = bpy.data.meshes.new('TsunamiWave')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('TsunamiWave', me)
    bpy.context.collection.objects.link(o)
    for name in ('TsunamiWave_M', 'TsunamiSpray_M'):
        me.materials.append(bpy.data.materials.new(name))
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_apply=True)
    print('wave verts', len(me.vertices), 'wave faces', wave_faces, 'profile', round(cum[-1]), 'm')


if __name__ == '__main__':
    build()

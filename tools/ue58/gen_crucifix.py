"""Crucifix of the village church (11/11, Sergio: "no altar Jesus na cruz, como nas igrejas católicas").
The corpus is a carved-statue reading of a real human figure: a MetaHuman body + head (exported with
mare_metahuman.export / export_face, any male build with the whole body) posed on the cross with its own skeleton
(arms raised, head fallen on the right shoulder, knees bent, feet crossed), frozen into a static mesh, with carved hair,
beard, a crown of thorns and a loincloth modelled here. Polychrome wood finish; dark timber cross with gilded end caps,
the INRI tablet (Latin, not a UI text) and three nails. No free realistic crucifix with a usable licence was found
without a login (Sketchfab/Fab), hence modelled.
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_crucifix.py -- <body.fbx> <face.fbx> [preview]
Output: D:/Assets/Mare/mare_church_crucifix/mare_church_crucifix.glb. Origin: centre of the cross foot, back of the
cross on y = 0 (it hangs on a wall), front -Y; the cross is 1.9 m tall, the figure about 1.05 m."""
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:]
BODY, FACE = ARGS[0], ARGS[1]
PREVIEW = len(ARGS) > 2
SLUG = 'mare_church_crucifix'
OUT = Path('D:/Assets/Mare') / SLUG
FIGURE = 1.05 / 1.80        # the statue is a little over life-size / 1.7: scale of the posed body


def rot_world(arm, bone, axis, deg):
    """Rotate a pose bone about a world axis through its head (children follow)."""
    pb = arm.pose.bones.get(bone)
    if not pb:
        return
    bpy.context.view_layer.update()
    head = arm.matrix_world @ pb.head
    r = Matrix.Translation(head) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-head)
    pb.matrix = arm.matrix_world.inverted() @ r @ arm.matrix_world @ pb.matrix
    bpy.context.view_layer.update()


def pose(arm):
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    # the figure faces -Y; its left is +X. Arms up into a wide Y, the body sagging from them.
    for side, s in (('l', 1), ('r', -1)):
        rot_world(arm, f'clavicle_{side}', Y, -s * 14)
        rot_world(arm, f'upperarm_{side}', Y, -s * 58)
        rot_world(arm, f'lowerarm_{side}', Y, -s * 6)
        rot_world(arm, f'hand_{side}', Y, s * 10)
        # palms forward
        if f'lowerarm_{side}' in arm.pose.bones:     # (the face armature has no arms)
            rot_world(arm, f'upperarm_{side}', (arm.matrix_world @ arm.pose.bones[f'lowerarm_{side}'].head - arm.matrix_world @ arm.pose.bones[f'upperarm_{side}'].head).normalized(), -s * 60)
    # torso slightly bowed forward and to its right, head fallen on the right shoulder
    rot_world(arm, 'spine_03', X, 6)
    rot_world(arm, 'spine_05', X, 7)
    rot_world(arm, 'neck_01', X, 10)
    rot_world(arm, 'neck_01', Y, 9)
    rot_world(arm, 'head', X, 12)
    rot_world(arm, 'head', Y, 12)
    rot_world(arm, 'head', Z, 12)
    # legs: knees forward and together, turned a little to the figure's left, right foot over the left
    for side, s in (('l', 1), ('r', -1)):
        rot_world(arm, f'thigh_{side}', X, -26)
        rot_world(arm, f'thigh_{side}', Y, s * 5)
        rot_world(arm, f'thigh_{side}', Z, 10)
        rot_world(arm, f'calf_{side}', X, 44)
        rot_world(arm, f'foot_{side}', X, 42)
    rot_world(arm, 'thigh_r', Y, -3)
    rot_world(arm, 'foot_r', Z, 12)
    rot_world(arm, 'foot_l', Z, -6)


def load(path):
    known = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in known]
    return next(o for o in new if o.type == 'ARMATURE'), [o for o in new if o.type == 'MESH']


def frozen(meshes):
    """Posed meshes as one world-space bmesh."""
    deps = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in meshes:
        tmp = bpy.data.meshes.new_from_object(o.evaluated_get(deps))
        tmp.transform(o.matrix_world)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    bm.normal_update()
    return bm


def new_obj(name, bm, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    return o


def plain(name, colour, rough=.6, metal=0.0):
    m = bpy.data.materials.new(f'{SLUG}_{name}')
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*colour, 1)
    return m


def tube(bm, pts, r0, r1, sides=6):
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = d.cross(Vector((0, 0, 1)))
        a = a.normalized() if a.length > 1e-4 else Vector((1, 0, 0))
        b = d.cross(a).normalized()
        r = r0 + (r1 - r0) * i / max(1, len(pts) - 1)
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r) for k in range(sides)])
    for ra, rb in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new((ra[k], ra[(k + 1) % sides], rb[(k + 1) % sides], rb[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])


def box(bm, c, size):
    vs = [bm.verts.new(Vector(c) + Vector((dx * size[0] / 2, dy * size[1] / 2, dz * size[2] / 2))) for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
    for a, b, c2, d in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        bm.faces.new((vs[a], vs[b], vs[c2], vs[d]))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(33)
    arm_b, body = load(BODY)
    arm_f, face = load(FACE)
    for arm in (arm_b, arm_f):
        pose(arm)
    skin_bm = frozen(body + face)
    for o in body + face + [arm_b, arm_f]:
        bpy.data.objects.remove(o, do_unlink=True)
    # keep the skin only (the face mesh also carries teeth, eyes, lashes: tiny islands are dropped)
    skin_bm.verts.ensure_lookup_table()
    tree = BVHTree.FromBMesh(skin_bm)
    zs = [v.co.z for v in skin_bm.verts]
    top, low = max(zs), min(zs)
    head_c = Vector((sum(v.co.x for v in skin_bm.verts if v.co.z > top - .12) / max(1, sum(1 for v in skin_bm.verts if v.co.z > top - .12)),
                     sum(v.co.y for v in skin_bm.verts if v.co.z > top - .12) / max(1, sum(1 for v in skin_bm.verts if v.co.z > top - .12)), top - .11))
    print('FIGURE', round(top, 3), round(low, 3), [round(c, 3) for c in head_c])

    # 11/11 (Sergio: "Jesus feito de mármore"): the whole figure is one white marble statue (body, hair, crown, cloth),
    # veined like the church's marble (the same picture generator), projected from the front
    import numpy as np
    import gen_church_nave as nave_gen
    img = nave_gen._save(f'{SLUG}_Marmore', nave_gen.marble_image((.93, .92, .90), (.45, .45, .48), 31, 1024, second=(.78, .64, .36), veins=.55), OUT)
    skin = bpy.data.materials.new(f'{SLUG}_Marble')
    skin.use_nodes = True
    tex = skin.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    bsdf = skin.node_tree.nodes['Principled BSDF']
    skin.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .13      # polished
    skin.diffuse_color = (.9, .89, .86, 1)
    hair_m = linen = thorn = skin
    wood = plain('Wood', (.10, .055, .03), .5)
    gold = plain('Gold', (1.0, .76, .33), .28, 1.0)
    parts = [new_obj('corpus', skin_bm.copy(), skin)]

    def surf(p):
        q, n = tree.find_nearest(p)[:2]
        return q, n

    # carved hair: thick locks from the scalp down to the shoulders, and a short beard
    hb = bmesh.new()
    for i in range(420):
        a = rnd.uniform(0, 2 * math.pi)
        e = rnd.uniform(-.25, 1.0)                       # elevation on the skull: back and sides more than the front
        d = Vector((math.sin(a) * math.cos(e * 1.3), math.cos(a) * math.cos(e * 1.3), math.sin(e * 1.3)))
        if d.y < -.2 and d.z < .8:                       # nothing grows on the face or the forehead: the hair is parted
            continue                                     # on top and falls behind the ears and down the back
        start, n = surf(head_c + d * .2)
        if start.z < top - .2:
            continue
        pts = [start + n * .006]
        side = Vector((n.x, n.y, 0))
        side = side.normalized() if side.length > .05 else Vector((0, 1, 0))
        length = rnd.uniform(.22, .33)
        ph, amp = rnd.uniform(0, 6.28), rnd.uniform(.006, .013)
        tang = Vector((-side.y, side.x, 0))
        for k in range(1, 12):
            t = k / 11
            p = start + side * (.012 + .034 * t + amp * .5 * math.sin(t * 9 + ph + 1.3)) + tang * (amp * math.sin(t * 9 + ph)) + Vector((0, 0, -length * t))
            if p.y < head_c.y - .035:                    # never in front of the face
                p.y = head_c.y - .035
                p.x += math.copysign(.02 * t, p.x - head_c.x)
            q, qn = surf(p)
            if (p - q).dot(qn) < .008:
                p = q + qn * .008
            pts.append(p)
        tube(hb, pts, rnd.uniform(.011, .016), .006, 6)
    chin, _ = surf(head_c + Vector((0, -.2, -.115)))
    for i in range(46):
        u, w = rnd.uniform(-1, 1), rnd.uniform(0, 1)
        start, n = surf(chin + Vector((u * .055, .012 + abs(u) * .03, .012 + w * .03 - abs(u) * -.03)))
        tube(hb, [start + n * .002, start + n * .012 + Vector((0, -.004, -.014)), start + n * .012 + Vector((0, -.004, -.03 - rnd.uniform(0, .012)))], .0095, .005, 5)
    # the scalp under the locks: the head's own skin lifted 9 mm where hair grows, so no skull shows between them
    cap = skin_bm.copy()
    bmesh.ops.delete(cap, geom=[f for f in cap.faces if not (f.calc_center_median().z > top - .17 and f.calc_center_median().y > head_c.y - .045
                                                              and (f.calc_center_median() - head_c).length < .16)], context='FACES')
    for v in cap.verts:
        v.co += v.normal * .009
    tmp = bpy.data.meshes.new('cap_tmp')
    cap.to_mesh(tmp)
    cap.free()
    hb.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    hair_o = new_obj('hair', hb, hair_m)
    # 11/11 (Sergio: "com acabamento como Michelangelo"): the locks are FUSED into one carved mass (voxel remesh) and
    # smoothed, like hair cut in marble: flowing ridges and grooves, no separate strands
    bpy.context.view_layer.objects.active = hair_o
    rm = hair_o.modifiers.new('fuse', 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = .0032
    rm.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier='fuse')
    sm = hair_o.modifiers.new('polish', 'LAPLACIANSMOOTH')
    sm.iterations = 6
    sm.lambda_factor = .35
    bpy.ops.object.modifier_apply(modifier='polish')
    parts.append(hair_o)

    # crown of thorns: three twisted strands round the brow, with spikes
    cb = bmesh.new()
    for strand in range(3):
        pts = []
        for k in range(41):
            a = 2 * math.pi * k / 40
            d = Vector((math.sin(a), math.cos(a), 0))
            q, n = surf(head_c + d * .25 + Vector((0, 0, .055 + .012 * math.sin(a * 3 + strand * 2.1))))
            pts.append(q + n * (.014 + .006 * math.sin(a * 7 + strand)))
        tube(cb, pts, .0045, .0045, 5)
    for k in range(34):
        a = 2 * math.pi * k / 34 + rnd.uniform(-.05, .05)
        d = Vector((math.sin(a), math.cos(a), 0))
        q, n = surf(head_c + d * .25 + Vector((0, 0, .055)))
        o = q + n * .016
        tube(cb, [o, o + (n + Vector((rnd.uniform(-.6, .6), rnd.uniform(-.6, .6), rnd.uniform(-.2, .8)))).normalized() * .028], .0028, .0004, 4)
    parts.append(new_obj('thorns', cb, thorn))

    # loincloth: rings round the hips following the body, a knot and a fall on the figure's right
    crotch = min((v.co for v in skin_bm.verts if abs(v.co.x) < .03 and top - 1.05 < v.co.z < top - .7), key=lambda c: c.z)
    lb = bmesh.new()
    n_ring, rows = 144, 26
    cx, cy = crotch.x, crotch.y + .01
    rings = []
    for k in range(rows):
        z = crotch.z + .16 - k * .0105
        ring = []
        for i in range(n_ring):
            a = 2 * math.pi * i / n_ring
            d = Vector((math.sin(a), -math.cos(a), 0))
            hit = tree.ray_cast(Vector((cx, cy, z)) + d * .6, -d)[0]
            fold = .007 * math.sin(a * 13 + k * .55) + .004 * math.sin(a * 29 - k * .9)       # deep drapery folds, running slightly on the bias
            r = (Vector((hit.x - cx, hit.y - cy, 0)).length if hit else .14) + .014 + fold * (.4 + .6 * k / rows) + .008 * (k / rows)
            ring.append(r)
        rings.append((z, ring))
    for _ in range(6):   # cloth spans the gap between the thighs
        rings = [(z, [max(r[i], (r[i - 3] + r[(i + 3) % n_ring]) / 2 - .004) for i in range(n_ring)]) for z, r in rings]
    vr = [[lb.verts.new(Vector((cx + math.sin(2 * math.pi * i / n_ring) * r, cy - math.cos(2 * math.pi * i / n_ring) * r, z - .012 * math.sin(2 * math.pi * i / n_ring * 2))))
           for i, r in enumerate(ring)] for z, ring in rings]
    for ra, rb in zip(vr, vr[1:]):
        for i in range(n_ring):
            lb.faces.new((ra[i], rb[i], rb[(i + 1) % n_ring], ra[(i + 1) % n_ring]))
    knot = Vector((cx - .15, cy - .03, crotch.z + .13))
    kq, kn = surf(knot)
    for j in range(5):
        s = Vector((rnd.uniform(-.02, .0), rnd.uniform(-.015, .01), 0))
        tube(lb, [kq + kn * .02, kq + kn * .035 + s + Vector((-.01, 0, -.08)), kq + kn * .03 + s * 2 + Vector((-.015, 0, -.2 - .03 * j))], .02, .012, 6)
    cloth_o = new_obj('loincloth', lb, linen)
    bpy.context.view_layer.objects.active = cloth_o
    rm = cloth_o.modifiers.new('fuse', 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = .004
    rm.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier='fuse')
    sm = cloth_o.modifiers.new('polish', 'LAPLACIANSMOOTH')
    sm.iterations = 3
    sm.lambda_factor = .3
    bpy.ops.object.modifier_apply(modifier='polish')
    parts.append(cloth_o)

    # scale the figure, hang it on the cross: hands at the arms of the cross, back of the figure 2 cm off the wood
    fig = parts[:]
    bpy.context.view_layer.update()
    allv = [o.matrix_world @ v.co for o in fig for v in o.data.vertices]
    back = max(v.y for v in allv if v.z > top - .9 and abs(v.x) < .2)
    hands_z = sum(v.z for v in allv if abs(v.x) > max(abs(w.x) for w in allv) - .06) / max(1, sum(1 for v in allv if abs(v.x) > max(abs(w.x) for w in allv) - .06))
    span = max(abs(w.x) for w in allv)
    H = 1.9
    arm_z = 1.48                                   # height of the cross arm on the post
    m = Matrix.Translation(Vector((0, -.045, arm_z))) @ Matrix.Scale(FIGURE, 4) @ Matrix.Translation(Vector((-0.0, -back, -hands_z)))
    for o in fig:
        o.data.transform(m)
    span *= FIGURE
    for o in fig:                                     # the marble picture, seen from the front (1.3 m across)
        uv = o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
        for other in [l for l in o.data.uv_layers if l != uv]:
            o.data.uv_layers.remove(other)
        uv = o.data.uv_layers[0]
        for loop in o.data.loops:
            co = o.data.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (co.x / 1.3 + .5, co.z / 1.3)
    print('SPAN', round(span, 3), 'HANDS_Z', round(hands_z, 3), 'BACK', round(back, 3))

    wb = bmesh.new()
    box(wb, (0, -.02, H / 2), (.10, .04, H))                       # post
    box(wb, (0, -.02, arm_z), (2 * span + .16, .04, .10))            # arm
    parts.append(new_obj('cross', wb, wood, smooth=False))
    gb = bmesh.new()
    for c, s in (((0, -.02, H + .012), (.13, .055, .03)), ((span + .09, -.02, arm_z), (.03, .055, .13)), ((-span - .09, -.02, arm_z), (.03, .055, .13)),
                 ((0, -.02, .015), (.13, .055, .03))):
        box(gb, c, s)
    box(gb, (0, -.046, H - .13), (.19, .008, .075))                 # the tablet
    ty, tz, lh = -.052, H - .13, .046                              # I N R I as raised strokes
    stroke = lambda x, z, w, h: box(gb, (x, ty, z), (w, .004, h))
    stroke(-.066, tz, .008, lh)                                     # I
    stroke(-.040, tz, .007, lh)                                     # N
    stroke(-.014, tz, .007, lh)
    for k in range(5):
        stroke(-.036 + k * .0048, tz + lh / 2 - .005 - k * .009, .008, .011)
    stroke(.012, tz, .007, lh)                                      # R
    stroke(.024, tz + lh / 2 - .004, .022, .007)
    stroke(.024, tz + .002, .022, .007)
    stroke(.034, tz + lh / 4, .007, lh / 2)
    for k in range(3):
        stroke(.022 + k * .006, tz - .006 - k * .007, .008, .009)
    stroke(.066, tz, .008, lh)                                      # I
    for c in ((span - .035, -.075, arm_z + .005), (-span + .035, -.075, arm_z + .005)):   # nails
        box(gb, c, (.014, .03, .014))
    feet = min((o.matrix_world @ v.co for o in fig[:1] for v in o.data.vertices), key=lambda c: c.z)
    box(gb, (feet.x, feet.y - .012, feet.z + .05), (.014, .03, .014))
    parts.append(new_obj('gilt', gb, gold, smooth=False))
    # the foot rest under the feet
    sb = bmesh.new()
    box(sb, (0, -.075, feet.z - .012), (.16, .07, .03))
    parts.append(new_obj('rest', sb, wood, smooth=False))

    if PREVIEW:
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_WORKBENCH'
        sc.display.shading.light = 'STUDIO'
        sc.display.shading.color_type = 'MATERIAL'
        sc.display.shading.show_cavity = True
        sc.render.resolution_x, sc.render.resolution_y = 700, 1000
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
        sc.collection.objects.link(cam)
        sc.camera = cam
        cam.data.lens = 70
        for name, az, dist, h in (('frente', 0, 4.2, 1.0), ('tq', 35, 4.2, 1.0), ('lado', 90, 4.2, 1.0), ('rosto', 12, 1.3, 1.5)):
            a = math.radians(az)
            cam.location = Vector((math.sin(a) * dist, -math.cos(a) * dist, h))
            cam.rotation_euler = (math.radians(90), 0, a)
            sc.render.filepath = f'D:/CodexTemp/claude/crucifix/prev_{name}.png'
            bpy.ops.render.render(write_still=True)
    for o in bpy.data.objects:
        o.select_set(o.type == 'MESH')
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    bpy.context.active_object.name = SLUG
    tris = sum(len(p.vertices) - 2 for p in bpy.context.active_object.data.polygons)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{SLUG}.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    (OUT / 'info.json').write_text('{\n "slug": "%s",\n "name": "Crucifixo da igreja (bpy)",\n "gltf": "%s.glb",\n "license": "Original model; figure posed from a MetaHuman body"\n}\n' % (SLUG, SLUG), encoding='utf-8')
    print('TRIS', tris, 'WROTE', OUT / f'{SLUG}.glb')


if __name__ == '__main__':
    main()

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


def emaciate(arm, meshes):
    """11/11 (Sergio: "mais detalhes no tórax, como as costelas, peito; detalhes dos ossos nos braços e pernas; como
    pessoa magra"). In the rest pose (A pose, facing -Y), on a once-subdivided skin: the limbs lose flesh round their
    bones (the joints keep their width, so knees, elbows, wrists and ankles stand out), the belly sinks under the
    costal arch, the ribs are carved as ridges that slope down from the breastbone, the breastbone, the collarbones
    and the hip bones stand proud. The weights are untouched: the pose still drives it."""
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    bones = {b.name: (mw @ b.head_local, mw @ b.tail_local) for b in arm.data.bones}
    for o in meshes:
        if len(o.data.vertices) < 8000 or o.vertex_groups.get('pelvis') is None:       # only the body skin
            continue
        bpy.context.view_layer.objects.active = o
        sub = o.modifiers.new('fine', 'SUBSURF')
        sub.levels = 2          # 8.5k vertices in the Medium build: two levels give ~7 mm on the chest, enough for ribs 3 cm apart
        while o.modifiers[0] != sub:
            bpy.ops.object.modifier_move_to_index(modifier='fine', index=0)
        bpy.ops.object.modifier_apply(modifier='fine')
        me = o.data
        gi = {g.name: g.index for g in o.vertex_groups}
        wm = o.matrix_world
        inv = wm.inverted()
        cos = [wm @ v.co for v in me.vertices]
        nrm = [(wm.to_3x3() @ v.normal).normalized() for v in me.vertices]
        top = max(c.z for c in cos if abs(c.x) < .05)
        crotch = min((c for c in cos if abs(c.x) < .015 and .55 < c.z < 1.0), key=lambda c: c.z).z
        front = min(c.y for c in cos if abs(c.x) < .05 and top - .3 < c.z < top - .15)       # breastbone plane
        limb = {'thigh': .76, 'calf': .80, 'upperarm': .76, 'lowerarm': .82}
        new = []
        for v, c, n in zip(me.vertices, cos, nrm):
            w = {o.vertex_groups[g.group].name: g.weight for g in v.groups}
            q = c.copy()
            # limbs: towards the bone axis, least at the two ends of each bone (the joints)
            for name, keep in limb.items():
                for side in ('l', 'r'):
                    # the MetaHuman skin is weighted to helper bones (thigh_in_l, calf_kneeBack_l, upperarm_bicep_l...), not to the limb bone itself
                    bw = sum(x for k, x in w.items() if k.startswith(name) and k.endswith(f'_{side}'))
                    if bw < .05 or f'{name}_{side}' not in bones:
                        continue
                    a, b = bones[f'{name}_{side}']
                    d = b - a
                    t = max(0.0, min(1.0, (c - a).dot(d) / d.length_squared))
                    axis = a + d * t
                    joint = math.sin(math.pi * t) ** .7                     # 0 at the joints, 1 mid-bone
                    f = 1 - (1 - keep) * joint * min(1.0, bw * 1.3)
                    q = axis + (q - axis) * f
            torso = sum(x for k, x in w.items() if k.startswith('spine') or k.startswith('pelvis') or k.startswith('clavicle'))
            if torso > .3 and n.y < .35:
                dz = top - c.z
                ax = abs(c.x)
                # the costal arch: an inverted V whose apex is 30 cm under the neck on the axis, 47 cm at the flanks
                arch = .30 + .9 * ax
                belly = max(0.0, min(1.0, (dz - arch) / .05)) * max(0.0, min(1.0, (top - .02 - crotch - dz + .12) / .1))
                if n.y < 0:
                    q.y += .030 * belly * (1 - min(1.0, ax / .17) ** 2)                      # sunken belly
                    q.x *= 1 - .07 * belly                                                    # a narrower waist
                # ribs: between the collarbone and the arch; ridges 2.7 cm apart sloping down and out from the breastbone
                cage = max(0.0, min(1.0, (dz - .10) / .04)) * max(0.0, min(1.0, (arch + .012 - dz) / .03))
                if cage > 0:
                    s_ = dz - .30 * ax
                    ridge = math.cos(2 * math.pi * (s_ + .004 * math.sin(c.x * 40 + dz * 23)) / .031)      # not ruler-straight
                    side_gain = .45 + .55 * min(1.0, ax / .10)                               # shallower over the breastbone and the pectorals
                    upper = .5 + .5 * min(1.0, max(0.0, (dz - .16) / .08))                   # the chest muscle hides the upper ribs
                    q += n * (.0048 * ridge * cage * side_gain * upper - .0035 * cage * side_gain)
                # the lower edge of the rib cage stands out over the belly
                edge = math.exp(-((dz - arch) / .012) ** 2)
                q += n * (.0032 * edge * min(1.0, ax / .04)) if n.y < .2 else Vector()
                # breastbone and collarbones
                if n.y < -.3:
                    q += n * (.004 * math.exp(-(ax / .014) ** 2) * max(0.0, min(1.0, (dz - .06) / .03)) * max(0.0, min(1.0, (.27 - dz) / .03)))
                    q += n * (.006 * math.exp(-((dz - .055 - .12 * ax) / .011) ** 2) * min(1.0, ax / .03) * max(0.0, min(1.0, (.2 - ax) / .03)))
                # hip bones
                hip = math.exp(-((ax - .115) / .03) ** 2) * math.exp(-((c.z - (crotch + .17)) / .035) ** 2)
                if n.y < 0:
                    q += n * (.009 * hip)
            new.append(inv @ q)
        moved = [(wm @ q - c).length for q, c in zip(new, cos)]
        print('EMACIATE', o.name, 'verts', len(new), 'moved>1mm', sum(1 for d in moved if d > .001), 'max', round(max(moved), 4), 'top', round(top, 3), 'crotch', round(crotch, 3))
        for v, q in zip(me.vertices, new):
            v.co = q
        me.update()


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
    emaciate(arm_b, body)
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
    vine_green = plain('VineGreen', (.13, .22, .07), .6)        # 11/11 (Sergio): the crown "verde com cor madeira, como vinhas com espinhos"
    vine_wood = plain('VineWood', (.26, .15, .07), .65)
    copper = plain('Copper', (.95, .48, .28), .32, 1.0)          # "nas mãos pregos cor de cobre"
    gold = plain('Gold', (1.0, .76, .33), .28, 1.0)
    corpus = new_obj('corpus', skin_bm.copy(), skin)
    bpy.context.view_layer.objects.active = corpus
    dc = corpus.modifiers.new('light', 'DECIMATE')          # the sculpting mesh (190k vertices) down to what the statue needs
    dc.ratio = .16
    bpy.ops.object.modifier_apply(modifier='light')
    parts = [corpus]

    def surf(p):
        q, n = tree.find_nearest(p)[:2]
        return q, n

    # carved hair: thick locks from the scalp down to the shoulders, and a short beard
    hb = bmesh.new()
    for i in range(420):
        a = rnd.uniform(0, 2 * math.pi)
        e = rnd.uniform(-.25, 1.0)                       # elevation on the skull: back and sides more than the front
        d = Vector((math.sin(a) * math.cos(e * 1.3), math.cos(a) * math.cos(e * 1.3), math.sin(e * 1.3)))
        if d.y < .12 and d.z < .86:                      # nothing grows on the face, the forehead or the temples: the hair is parted
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
            if p.y < head_c.y + .015:                    # never in front of the ears
                p.y = head_c.y + .015
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
    bmesh.ops.delete(cap, geom=[f for f in cap.faces if not (f.calc_center_median().z > top - .17 and f.calc_center_median().y > head_c.y - .005
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
    dc = hair_o.modifiers.new('light', 'DECIMATE')
    dc.ratio = .22
    bpy.ops.object.modifier_apply(modifier='light')
    parts.append(hair_o)

    # crown of thorns: three twisted strands round the brow, with spikes
    cb = bmesh.new()
    cw = bmesh.new()                                             # the woody strand and the thorns
    for strand in range(3):
        pts = []
        for k in range(41):
            a = 2 * math.pi * k / 40
            d = Vector((math.sin(a), math.cos(a), 0))
            q, n = surf(head_c + d * .25 + Vector((0, 0, .055 + .012 * math.sin(a * 3 + strand * 2.1))))
            pts.append(q + n * (.014 + .006 * math.sin(a * 7 + strand)))
        tube(cw if strand == 1 else cb, pts, .0048, .0048, 6)
    for k in range(34):
        a = 2 * math.pi * k / 34 + rnd.uniform(-.05, .05)
        d = Vector((math.sin(a), math.cos(a), 0))
        q, n = surf(head_c + d * .25 + Vector((0, 0, .055)))
        o = q + n * .016
        tube(cw, [o, o + (n + Vector((rnd.uniform(-.6, .6), rnd.uniform(-.6, .6), rnd.uniform(-.2, .8)))).normalized() * .03], .003, .0004, 4)
    crown_parts = [new_obj('vine', cb, vine_green), new_obj('thorns', cw, vine_wood)]
    parts += crown_parts

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
    # (a voxel remesh of this open, single-wall cloth returned NOTHING: the figure came out without it. It keeps its
    # own rings, with a real thickness.)
    cloth_o = new_obj('loincloth', lb, linen)
    bpy.context.view_layer.objects.active = cloth_o
    so = cloth_o.modifiers.new('thick', 'SOLIDIFY')
    so.thickness = .008
    so.offset = 1
    bpy.ops.object.modifier_apply(modifier='thick')
    assert len(cloth_o.data.polygons) > 3000, 'the loincloth is missing'
    parts.append(cloth_o)

    # scale the figure, hang it on the cross: hands at the arms of the cross, back of the figure 2 cm off the wood
    fig = parts[:]
    bpy.context.view_layer.update()
    allv = [o.matrix_world @ v.co for o in fig for v in o.data.vertices]
    back = max(v.y for v in allv if v.z > top - .9 and abs(v.x) < .2)
    span = max(abs(w.x) for w in allv)
    hands = [v.z for v in allv if abs(v.x) > span - .06]
    hands_z = sum(hands) / max(1, len(hands))
    H = 1.9
    arm_z = 1.48                                   # height of the cross arm on the post
    m = Matrix.Translation(Vector((0, -.045, arm_z))) @ Matrix.Scale(FIGURE, 4) @ Matrix.Translation(Vector((-0.0, -back, -hands_z)))
    for o in fig:
        o.data.transform(m)
    span *= FIGURE
    for o in [o for o in fig if o not in crown_parts]:   # the marble picture, seen from the front (1.3 m across)
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
    # copper nails: a domed head on a square shank, through each palm and through the crossed feet
    body_v = [fig[0].matrix_world @ v.co for v in fig[0].data.vertices]
    nb = bmesh.new()

    def nail(c):
        box(nb, (c.x, c.y - .004, c.z), (.007, .05, .007))
        for k, (r, dy) in enumerate(((.012, -.026), (.010, -.031), (.006, -.034))):
            box(nb, (c.x, c.y + dy, c.z), (2 * r, .005, 2 * r))
    for side in (1, -1):
        hand = [v for v in body_v if v.x * side > span - .075]
        palm = sum(hand, Vector()) / len(hand)
        nail(Vector((palm.x - side * .015, min(v.y for v in hand) + .012, palm.z - .01)))
    feet = min(body_v, key=lambda c: c.z)
    foot = [v for v in body_v if v.z < feet.z + .09]
    nail(Vector((sum(v.x for v in foot) / len(foot), min(v.y for v in foot) + .012, feet.z + .06)))
    parts.append(new_obj('nails', nb, copper, smooth=False))
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
        for name, az, dist, h in (('frente', 0, 4.2, 1.0), ('tq', 35, 4.2, 1.0), ('torax', 18, 1.5, 1.22), ('rosto', 12, 1.3, 1.5)):
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

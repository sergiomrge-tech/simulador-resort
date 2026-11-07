"""Flat-screen TVs for the house customization (03/11, PENDENCIAS "personalização com 5 opções: casa (... TV)").
Poly Haven only has old sets (the CRT already in the house, a wooden console), so the modern ones are modelled here.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_tv_sets.py
Output: unreal/MareAlta/SourceArt/Models/HomeTV/<name>.glb (metres, base at z=0 centred, screen facing -Y in Blender).

mare_tv_flat32  32" (71 x 40 cm picture), 12 mm bezel, 7 cm body, two splayed feet.
mare_tv_flat43  43" (95 x 54 cm), 8 mm bezel, slim body with a ribbed back, centre pedestal.
mare_tv_smart55 55" (121 x 68 cm), 6 mm bezel, metal pedestal and a fabric soundbar in front.
mare_tv_oled65  65" (143 x 81 cm), 3 mm panel with a back module, wide low stand and a soundbar.
Every set keeps the picture in its own material slot, "mare_tv_screen", with 0..1 UVs across it, so the game can
switch it on with M_HomeTV_Flat (UMareHomeWorld).
"""
import math
from pathlib import Path
import bpy
import bmesh

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/HomeTV'


def mat(name, colour, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def rounded_box(name, w, d, h, r, loc, m, segs=4):
    """Box w (x) x d (y) x h (z) with all edges bevelled by r (real rounded corners, not a raw cube)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co.x *= w
        v.co.y *= d
        v.co.z *= h
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(r, w / 2 - 1e-4, d / 2 - 1e-4, h / 2 - 1e-4), segments=segs, affect='EDGES', profile=.5)
    for v in bm.verts:
        v.co.x += loc[0]
        v.co.y += loc[1]
        v.co.z += loc[2]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(m)
    for poly in me.polygons:
        poly.use_smooth = True
    return o


def leg(name, a, b, r, m):
    """Round bar between two points."""
    a, b = map(lambda t: __import__('mathutils').Vector(t), (a, b))
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def tv(name, pic_w, pic_h, bezel, body_d, stand, soundbar=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    frame = mat(f'{name}_frame', (.018, .018, .02), .55)
    back = mat(f'{name}_back', (.04, .04, .045), .55)
    screen = mat('mare_tv_screen', (.004, .005, .006), .22)
    metal = mat(f'{name}_metal', (.32, .33, .35), .3, 1.0)
    fabric = mat(f'{name}_fabric', (.06, .06, .065), .9)
    parts = []
    W, H = pic_w + 2 * bezel, pic_h + 2 * bezel
    lift = stand['lift']
    cz = lift + H / 2
    # panel: a bezel ring of four bars around the picture (front at y -.006), the picture recessed 2 mm behind it,
    # a back plate, a back module (deeper box) and the stand. A solid frame box with the picture in front of it
    # z-fought and showed a grey slab with a small dark patch (first version).
    b = max(bezel, .004)
    for nm, w, h, x, z in (('bez_top', W, b, 0, cz + pic_h / 2 + b / 2), ('bez_bot', W, b, 0, cz - pic_h / 2 - b / 2),
                           ('bez_l', b, pic_h, -pic_w / 2 - b / 2, cz), ('bez_r', b, pic_h, pic_w / 2 + b / 2, cz)):
        parts.append(rounded_box(nm, w, .012, h, min(.003, b / 2.2), (x, 0, z), frame, segs=2))
    parts.append(rounded_box('backplate', W - .002, .006, H - .002, .002, (0, .003, cz), frame, segs=2))
    scr = rounded_box('screen', pic_w + .001, .002, pic_h + .001, .0005, (0, -.003, cz), screen, segs=1)
    # Picture UVs 0..1 across the face (u along x, v up): M_HomeTV_Flat draws the coast landscapes from them.
    uv = scr.data.uv_layers.new(name='UVMap')
    for loop in scr.data.loops:
        co = scr.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((co.x + pic_w / 2) / pic_w, (co.z - (cz - pic_h / 2)) / pic_h)
    parts.append(scr)
    parts.append(rounded_box('back', W * .72, body_d, H * .62, .02, (0, .006 + body_d / 2, cz - H * .08), back))
    # ribbed vents on the back module (real grooves as thin bars)
    for k in range(9):
        parts.append(rounded_box(f'vent{k}', W * .5, .003, .006, .0015, (0, .006 + body_d + .0012, cz - H * .08 + (k - 4) * .018), back, segs=2))
    # power LED under the bottom bezel
    parts.append(rounded_box('led', .006, .004, .003, .001, (W * .38, -.007, lift + bezel * .5), mat(f'{name}_led', (.9, .25, .1), .3), segs=2))
    if stand['kind'] == 'feet':
        for s in (-1, 1):
            x = s * W * .38
            leg(f'foot_{s}_a', (x, .01, lift + .01), (x - s * .05, -.07, .004), .006, metal)
            leg(f'foot_{s}_b', (x, .01, lift + .01), (x + s * .03, .09, .004), .006, metal)
            parts.extend(o for o in bpy.data.objects if o.name.startswith(f'foot_{s}'))
            parts.append(rounded_box(f'pad_{s}', .05, .19, .008, .003, (x - s * .01, .01, .004), metal))
    else:
        bw = stand['base_w']
        parts.append(rounded_box('base', bw, .26, .016, .008, (0, .04, .008), metal))
        parts.append(rounded_box('neck', .06, .03, lift - .01, .008, (0, .02 + body_d / 2, .016 + (lift - .01) / 2), metal))
    if soundbar:
        sw = W * .62
        parts.append(rounded_box('soundbar', sw, .085, .062, .02, (0, -.20, .031), frame))
        parts.append(rounded_box('grille', sw - .02, .002, .046, .006, (0, -.2435, .031), fabric))
    parts = list(dict.fromkeys(parts))
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{name}.glb'), export_format='GLB', export_apply=True)
    o = bpy.context.view_layer.objects.active
    xs = [v.co for v in o.data.vertices]
    print('WROTE', name, 'size', round(max(v.x for v in xs) - min(v.x for v in xs), 3), round(max(v.y for v in xs) - min(v.y for v in xs), 3), round(max(v.z for v in xs), 3))


tv('mare_tv_flat32', .708, .398, .012, .07, {'kind': 'feet', 'lift': .075})
tv('mare_tv_flat43', .952, .536, .008, .055, {'kind': 'pedestal', 'lift': .085, 'base_w': .36})
tv('mare_tv_smart55', 1.21, .681, .006, .045, {'kind': 'pedestal', 'lift': .095, 'base_w': .44}, soundbar=True)
tv('mare_tv_oled65', 1.43, .806, .003, .038, {'kind': 'pedestal', 'lift': .07, 'base_w': .62}, soundbar=True)

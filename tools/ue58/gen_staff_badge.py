"""Staff name badge (crachá) worn on the uniform's chest: a rounded white plate with the resort's teal band and a
name line printed as raised strips, and a small metal clip behind. Origin at the back centre (the side that touches
the shirt), front = -Y (UE +Y after import), up = +Z. Real size 7.6 x 2.8 cm.

  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_staff_badge.py
  -> SourceArt/Models/Staff/mare_staff_badge.glb  (imported with mare_hud "staffmodels" into /Game/Custom/Staff)
"""
import os
import bpy
import bmesh

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'unreal', 'MareAlta', 'SourceArt', 'Models', 'Staff', 'mare_staff_badge.glb')


def material(name, rgb, rough=.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def rounded_box(name, w, d, h, radius, segs, mat, loc=(0, 0, 0)):
    """Box with rounded vertical edges (bevel on the 4 corners) and a small bevel on the faces' rims."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (w, d, h)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    corner = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > d * .9]
    bmesh.ops.bevel(bm, geom=corner, offset=radius, segments=segs, affect='EDGES', profile=.5)
    rim = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-6 and abs(e.verts[0].co.y) > d * .45]
    bmesh.ops.bevel(bm, geom=rim, offset=min(d * .35, .0006), segments=2, affect='EDGES', profile=.5)
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    plate_m = material('mare_badge_plate', (.93, .93, .9), .35)
    band_m = material('mare_badge_band', (.12, .5, .53), .4)
    ink_m = material('mare_badge_ink', (.08, .1, .12), .5)
    clip_m = material('mare_badge_clip', (.75, .76, .78), .25, 1.0)
    W, H, D = .076, .028, .003
    parts = [rounded_box('plate', W, D, H, .004, 6, plate_m, (0, -D / 2, 0))]
    # Teal band across the top third, slightly proud of the plate.
    parts.append(rounded_box('band', W - .002, .0006, .009, .0035, 5, band_m, (0, -D - .0002, H / 2 - .0055)))
    # Name and role lines: thin raised strips (no texture needed at this size).
    parts.append(rounded_box('name', .044, .0004, .0035, .0012, 3, ink_m, (-.006, -D - .0001, -.002)))
    parts.append(rounded_box('role', .03, .0004, .0022, .0008, 3, ink_m, (-.013, -D - .0001, -.0085)))
    # Resort logo dot on the right: a small rounded disc.
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=.0045, depth=.0007, location=(.026, -D - .0003, -.004), rotation=(1.5708, 0, 0))
    logo = bpy.context.object
    logo.data.materials.append(band_m)
    bpy.ops.object.shade_smooth()
    parts.append(logo)
    # Clip behind: a bent metal strip from the top edge down the back.
    clip = rounded_box('clip', .012, .0008, .022, .0015, 4, clip_m, (0, .0006, .003))
    parts.append(clip)
    bpy.ops.mesh.primitive_torus_add(major_radius=.0022, minor_radius=.0008, major_segments=24, minor_segments=10,
                                     location=(0, .0002, H / 2 + .0008), rotation=(0, 1.5708, 0))
    hinge = bpy.context.object
    hinge.data.materials.append(clip_m)
    bpy.ops.object.shade_smooth()
    parts.append(hinge)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    badge = bpy.context.object
    badge.name = 'mare_staff_badge'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(OUT), export_format='GLB', export_apply=True)
    print('WROTE', os.path.abspath(OUT), len(badge.data.vertices), 'verts')


if __name__ == '__main__':
    main()

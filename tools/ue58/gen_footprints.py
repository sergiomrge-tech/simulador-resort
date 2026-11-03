"""Wet-sand footprint for the shore trail (replaces the Godot export World_2262: flat 18 cm discs that read as coins).
A right-foot imprint 26 cm long: heel, narrow arch on the inner side, ball and five toes, drawn as a soft mask; a quad
with a dark damp-sand colour and that mask as alpha (glTF BLEND, translucent in UE), plus a normal map of the dent.
Origin at the footprint centre, toes toward +X, ground at z=0 (2 mm above it). The level mirrors every other one
for the left foot. D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_footprints.py
Output: unreal/MareAlta/SourceArt/Models/Beach/beach_footprint.glb (+ beach_footprint_*.png)."""
from pathlib import Path
import bpy
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/Beach'
LENGTH, WIDTH = .28, .14          # quad (m); the foot itself is 26 x 10 cm
W, H = 256, 512                   # texture: width across the foot, height along it (toes at the top)


def mask():
    """Soft imprint mask, 1 inside the foot; deeper under the heel and the ball like a real step."""
    img = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img)
    px = lambda u, v: (W / 2 + v * W / 2, H - u * H)           # u along the foot (0 heel .. 1 toes), v across (+ = big toe side)
    def ellipse(u, v, ru, rv, value):
        x, y = px(u, v)
        d.ellipse([x - rv * W / 2, y - ru * H, x + rv * W / 2, y + ru * H], fill=value)   # rv: of the half width
    ellipse(.17, -.05, .12, .55, 255)                            # heel
    # arch: the outer edge stays full, the inner (big toe) side narrows
    d.polygon([px(.20, -.55), px(.20, .45), px(.42, .10), px(.58, .62), px(.60, -.70), px(.40, -.60)], fill=205)
    ellipse(.64, .0, .10, .75, 255)                              # ball of the foot
    for u, v, ru, rv in ((.82, .48, .055, .24), (.80, .15, .040, .17), (.78, -.10, .035, .15),
                         (.755, -.32, .032, .13), (.72, -.52, .028, .11)):
        ellipse(u, v, ru, rv, 235)                               # big toe .. little toe
    img = img.filter(ImageFilter.GaussianBlur(3))
    return np.asarray(img).astype(np.float32) / 255


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m = mask()
    # Colour: damp sand, darker where the foot pressed; alpha follows the mask (soft edges, no sticker outline).
    damp = np.array([.30, .23, .16])
    rgba = np.zeros((H, W, 4), np.float32)
    rgba[..., :3] = damp * (1 - .25 * m[..., None])
    rgba[..., 3] = np.clip(m * 1.1, 0, .88)            # first try at .62 was invisible in game
    Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(OUT / 'beach_footprint_color.png')
    # Normal map (OpenGL, +Y up) of the dent: height = -mask.
    h = -m * 3.0
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * .5 + .5) * 255).astype(np.uint8), 'RGB').save(OUT / 'beach_footprint_normal.png')

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, .002))
    ob = bpy.context.active_object
    ob.scale = (LENGTH, WIDTH, 1)
    ob.rotation_euler = (0, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # UV: texture V runs along the foot (toes at the top of the image = +X)
    uv = ob.data.uv_layers.active.data
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            co = ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv[li].uv = (co.y / WIDTH + .5, co.x / LENGTH + .5)
    mat = bpy.data.materials.new('beach_footprint')
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    nodes = mat.node_tree.nodes
    p = nodes['Principled BSDF']
    col = nodes.new('ShaderNodeTexImage')
    col.image = bpy.data.images.load(str(OUT / 'beach_footprint_color.png'))
    nor = nodes.new('ShaderNodeTexImage')
    nor.image = bpy.data.images.load(str(OUT / 'beach_footprint_normal.png'))
    nor.image.colorspace_settings.name = 'Non-Color'
    nmap = nodes.new('ShaderNodeNormalMap')
    links = mat.node_tree.links
    links.new(col.outputs['Color'], p.inputs['Base Color'])
    links.new(col.outputs['Alpha'], p.inputs['Alpha'])
    links.new(nor.outputs['Color'], nmap.inputs['Color'])
    links.new(nmap.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = .95
    ob.data.materials.append(mat)
    ob.name = ob.data.name = 'beach_footprint'
    bpy.ops.export_scene.gltf(filepath=str(OUT / 'beach_footprint.glb'), export_format='GLB', export_apply=True)
    print('beach_footprint', round(float(m.mean()), 3), 'mask cover')


if __name__ == '__main__':
    main()

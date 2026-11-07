"""Cork notice board of the pousada reception (replaces the Godot export World_0067 board + World_0068-0072 squares,
which floated 19 cm off the wall and covered half of the east window). A framed cork board with three postcards
of the beach, two paper notes and push pins; cork and postcards are drawn in code (PIL), frame in Poly Haven
oak_wood_planks (CC0). Built in World_0067's frame (pivot at world x 280, y 1282, z 172): the board is centred
50 cm to the -X side (the wall strip between the door and the window) and its back touches the wall, 19 cm behind
the pivot on Blender +Y. D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_notice_board.py
Output: D:/Assets/Mare/pousada_notice_board/pousada_notice_board.glb."""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from gen_custom_furniture import box, export, lathe, material, reset  # noqa: E402

SLUG = 'pousada_notice_board'
OUT = Path('D:/Assets/Mare') / SLUG
CX, BACK = -.50, .19                 # board centre x and wall plane (Blender +Y)
W, H = .62, .48


def cork_texture(path):
    rng = np.random.default_rng(3)
    base = np.array([168, 120, 74], np.float32)
    n = rng.normal(0, 1, (512, 512)).astype(np.float32)
    img = Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    g = np.asarray(img).astype(np.float32) / 255
    rgb = base[None, None, :] * (.72 + .5 * g[..., None])
    speck = rng.random((512, 512)) > .985                     # dark granules
    rgb[speck] *= .55
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(path)


def postcard(path, seed):
    """A little beach postcard: sky, sea, sand, a palm and a white border."""
    rnd = random.Random(seed)
    w, h = 256, 176
    im = Image.new('RGB', (w, h), (250, 248, 240))
    d = ImageDraw.Draw(im)
    sky = [(120 + rnd.randint(-20, 20), 190, 235), (250, 200, 140)][seed % 2]
    d.rectangle([10, 10, w - 10, 95], fill=sky)
    d.rectangle([10, 95, w - 10, 125], fill=(30, 140, 170))
    d.rectangle([10, 125, w - 10, h - 30], fill=(232, 206, 150))
    sx = rnd.randint(40, 200)
    d.ellipse([sx - 14, 30, sx + 14, 58], fill=(255, 230, 120))
    px = rnd.randint(40, 210)
    d.line([px, h - 34, px + 10, 60], fill=(110, 75, 40), width=6)
    for a in range(-60, 61, 30):
        d.line([px + 10, 60, px + 10 + a, 50 + abs(a) // 3], fill=(40, 120, 50), width=5)
    d.text((14, h - 26), 'MARÉ ALTA', fill=(60, 60, 70))
    im.resize((256, 256), Image.LANCZOS).save(path)     # power of two for UE; the card's UV undoes the stretch


def main():
    reset()
    OUT.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(9)
    cork_texture(OUT / f'{SLUG}_cork.png')
    for i in range(3):
        postcard(OUT / f'{SLUG}_card{i}.png', i)
    frame = material('frame', 'oak_wood_planks', tint=(.36, .22, .13), rough=.5, out=OUT)

    def image_mat(name, file, rough=.85):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(str(OUT / file))
        p = m.node_tree.nodes['Principled BSDF']
        m.node_tree.links.new(t.outputs['Color'], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = rough
        return m

    def plain(name, colour, rough=.6, metal=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        p = m.node_tree.nodes['Principled BSDF']
        p.inputs['Base Color'].default_value = (*colour, 1)
        p.inputs['Roughness'].default_value = rough
        p.inputs['Metallic'].default_value = metal
        return m

    cork = image_mat('cork', f'{SLUG}_cork.png', .95)
    y_board = BACK - .008
    box('cork', (W, .016, H), (CX, y_board, 0), cork, bevel=.002, uv=.4)
    for name, size, loc in (('top', (W + .05, .03, .025), (CX, y_board - .006, H / 2 + .012)),
                            ('bottom', (W + .05, .03, .025), (CX, y_board - .006, -H / 2 - .012)),
                            ('left', (.025, .03, H + .05), (CX - W / 2 - .012, y_board - .006, 0)),
                            ('right', (.025, .03, H + .05), (CX + W / 2 + .012, y_board - .006, 0))):
        box(f'frame_{name}', size, loc, frame, bevel=.004, uv=1.5)
    front = y_board - .008
    pin_mats = [plain(f'pin{i}', c, .35) for i, c in enumerate([(.8, .1, .1), (.1, .3, .8), (.95, .75, .1)])]
    items = [('card0', (-.17, .1), (.15, .104)), ('card1', (.03, .12), (.15, .104)), ('card2', (.17, -.08), (.15, .104)),
             ('noteY', (-.15, -.11), (.1, .1)), ('noteP', (.0, -.1), (.09, .09))]
    paper = {'noteY': plain('note_yellow', (.95, .88, .45), .9), 'noteP': plain('note_pink', (.95, .62, .7), .9)}
    for k, (name, (x, z), (w, h)) in enumerate(items):
        mat = image_mat(name, f'{SLUG}_{name.replace("card", "card")}.png') if name.startswith('card') else paper[name]
        tilt = rnd.uniform(-.08, .08)
        box(name, (w, .0015, h), (CX + x, front - .001 - k * .0004, z), mat, rot=(0, tilt, 0), bevel=0, uv=1.0)
        # UV of the postcard face: fit the image to the card (box_uv maps by metres)
        ob = bpy.data.objects[name]
        if name.startswith('card'):
            uvl = ob.data.uv_layers.active.data
            for poly in ob.data.polygons:
                for li in poly.loop_indices:
                    co = ob.data.vertices[ob.data.loops[li].vertex_index].co
                    uvl[li].uv = ((co.x - (CX + x)) / w + .5, (co.z - z) / h + .5)
        lathe(f'pin{k}', [(.0005, 0), (.004, 0), (.006, -.004), (.006, -.009), (.0005, -.011)],
              (CX + x, front - .002, z + h / 2 - .012), pin_mats[k % 3], sides=12)
        pin = bpy.data.objects[f'pin{k}']
        for v in pin.data.vertices:              # lathe grows along Z: turn it to stick out of the board (-Y)
            dx, dy, dz = v.co.x - (CX + x), v.co.y - (front - .002), v.co.z - (z + h / 2 - .012)
            v.co.x, v.co.y, v.co.z = CX + x + dx, front - .002 + dz, z + h / 2 - .012 + dy
    for o in bpy.context.scene.objects:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active = bpy.data.objects['cork']
    bpy.ops.object.join()
    bpy.context.active_object.name = SLUG
    export(SLUG, 'Pousada notice board (bpy)')


if __name__ == '__main__':
    main()

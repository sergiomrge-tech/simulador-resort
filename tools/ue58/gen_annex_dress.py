"""Hero house bathroom annex dressing (09/11 visual checklist: "Anexo do banheiro: parede lisa, sem janela nem detalhe,
parecendo caixa"). The annex (Godot export, '@MeshInstance3D@2930/2933') is a plain cream box: south face at UE
y 1418, side faces at x 4613 and 4937, running north to the house (y ~1737), measured with traces (mare_probe_near.
cam_pick). This add-on, in the annex's own frame (origin UE (4775, 1418, 0), axes = UE axes), gives it:
  - a small top-hung bathroom window (basculante) on the south wall: white frame, frosted glass, stone sill, handle;
  - the grey base band of the house (45 cm, 2 cm proud) along the three exposed walls.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_annex_dress.py
Output: D:/Assets/Mare/mare_annex_dress/mare_annex_dress.glb (placed by mare_fix_0911.annex_dress)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, material, reset, tube  # noqa: E402

SLUG = 'mare_annex_dress'
HW = 1.62          # half width of the south wall (x 4613..4937)
DEPTH = 3.19       # side walls from the south face to the house (y 1418..1737)
BAND = .45


def B(x, y, z):
    """UE frame (metres, +y north) -> Blender (y flipped)."""
    return (x, -y, z)


def plain(name, color, rough=.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def main():
    reset()
    out = Path('D:/Assets/Mare') / SLUG
    out.mkdir(parents=True, exist_ok=True)
    band = material('Band', 'painted_plaster_wall', (.46, .46, .44), rough=.85, out=out)
    stone = material('Sill', 'plaster_stone_wall_01', (.80, .78, .74), rough=.6, out=out)
    frame = plain('Frame', (.92, .91, .88), .45)
    frosted = plain('Frosted', (.70, .76, .78), .22)
    metal = plain('Handle', (.75, .75, .74), .3, .9)
    # ---- base band on the south, east and west faces (2 cm proud, corners overlapped)
    t = .02
    box('band_s', (2 * HW + 2 * t, t, BAND), B(0, -t / 2, BAND / 2), band, bevel=.004, uv=1.2)
    for s in (-1, 1):
        box(f'band_side{s}', (t, DEPTH + t, BAND), B(s * (HW + t / 2), DEPTH / 2 - t / 2, BAND / 2), band, bevel=.004, uv=1.2)
    # ---- top-hung bathroom window, centred on the south wall, sill at 1.55 m
    w, h, z0 = .70, .50, 1.55
    d = .07
    fw = .055
    box('win_top', (w, d, fw), B(0, -d / 2 + .02, z0 + h - fw / 2), frame, bevel=.006, uv=.5)
    box('win_bottom', (w, d, fw), B(0, -d / 2 + .02, z0 + fw / 2), frame, bevel=.006, uv=.5)
    for s in (-1, 1):
        box(f'win_side{s}', (fw, d, h), B(s * (w - fw) / 2, -d / 2 + .02, z0 + h / 2), frame, bevel=.006, uv=.5)
    # recessed frosted pane with a slim sash, tilted open 6 cm at the bottom (top-hung)
    box('sash', (w - 2 * fw, .035, h - 2 * fw), B(0, -.02, z0 + h / 2), frame, rot=(-.12, 0, 0), bevel=.004, uv=.5)
    box('pane', (w - 2 * fw - .05, .012, h - 2 * fw - .05), B(0, -.04, z0 + h / 2), frosted, rot=(-.12, 0, 0), bevel=.002, uv=.5)
    box('mullion', (w - 2 * fw - .05, .02, .025), B(0, -.045, z0 + h / 2), frame, rot=(-.12, 0, 0), bevel=.003, uv=.5)
    # stone sill and a small stay arm
    box('sill', (w + .12, .13, .045), B(0, -.065, z0 - .0225), stone, bevel=.008, uv=.6)
    tube('stay', B(.2, -.06, z0 + .08), B(.2, -.02, z0 + .16), .006, metal, 8)
    export(SLUG, 'Hero house bathroom annex: window and base band')


if __name__ == '__main__':
    main()

"""Arcade games of the Grand Hotel game room (CHECKLIST 5.4 "2 fliperamas jogáveis em tela"): imports the sprites of
tools/ue58/gen_arcade_art.py (SourceArt/UI/Arcade/T_Arc_*.png) into /Game/UI/Arcade and builds M_ArcadeScreen, the
emissive material UMareArcade (Source/MareAlta/MareArcade.cpp) puts on each cabinet's screen with the game's render
target. The cabinets themselves (tools/ue58/gen_arcade_cabinet.py) are imported by mare_game_room ('import:mare_arcade_jangada,mare_arcade_siri').
  mare_arcade.cmd('import')     -> textures (pixel art of Pega-Siri and the font with nearest filtering) and the material
  mare_arcade.cmd('check')      -> every texture UMareArcade loads exists
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SRC = ROOT / 'SourceArt/UI/Arcade'
DEST = '/Game/UI/Arcade'
# Pixel art drawn at 2x/4x: nearest filtering keeps it crisp on the screen. The Jangada sprites are vector-like: bilinear.
NEAREST = ('T_Arc_S_', 'T_Arc_Font')


def import_textures():
    tasks = []
    for png in sorted(SRC.glob('T_Arc_*.png')):
        t = unreal.AssetImportTask()
        t.filename = str(png)
        t.destination_path = DEST
        t.destination_name = png.stem
        t.automated = True
        t.replace_existing = True
        t.save = False
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    out = {}
    for png in sorted(SRC.glob('T_Arc_*.png')):
        tex = unreal.load_asset(f'{DEST}/{png.stem}')
        if not tex:
            out[png.stem] = 'failed'
            continue
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)   # BGRA, no blocks
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('never_stream', True)
        tex.set_editor_property('filter', unreal.TextureFilter.TF_NEAREST if png.stem.startswith(NEAREST) else unreal.TextureFilter.TF_BILINEAR)
        # The water and sand tiles scroll and repeat; sprites never wrap (a clamped edge keeps a hairline off the border).
        wrap = png.stem in ('T_Arc_J_Water', 'T_Arc_J_Sand')
        addr = unreal.TextureAddress.TA_WRAP if wrap else unreal.TextureAddress.TA_CLAMP
        tex.set_editor_property('address_x', addr)
        tex.set_editor_property('address_y', addr)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[png.stem] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return out


def screen_material():
    """M_ArcadeScreen: unlit-looking CRT face. Emissive = Screen (render target) x Bright, a faint scanline every 2
    texels of the 720-line target, base colour black and a glossy glass on top so the room still reflects on it."""
    name = 'M_ArcadeScreen'
    mel = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(f'{DEST}/{name}')
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property('used_with_nanite', True)
    tex = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    tex.set_editor_property('parameter_name', 'Screen')
    title = unreal.load_asset(f'{DEST}/T_Arc_J_Title')
    if title:
        tex.set_editor_property('texture', title)
    bright = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 250)
    bright.set_editor_property('parameter_name', 'Bright')
    bright.set_editor_property('default_value', 4.0)
    # Scanlines: 1 - 0.18 * (0.5 + 0.5 sin(v * 720 * pi)).
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1100, 400)
    mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -950, 400)
    mask.set_editor_property('r', False)
    mask.set_editor_property('g', True)
    mel.connect_material_expressions(uv, '', mask, '')
    freq = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -800, 400)
    freq.set_editor_property('const_b', 720 * 3.14159265)
    mel.connect_material_expressions(mask, '', freq, 'A')
    sine = mel.create_material_expression(mat, unreal.MaterialExpressionSine, -650, 400)
    sine.set_editor_property('period', 6.28318530)
    mel.connect_material_expressions(freq, '', sine, '')
    lines = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -500, 400)
    lines.set_editor_property('const_b', .09)
    mel.connect_material_expressions(sine, '', lines, 'A')
    level = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -350, 400)
    level.set_editor_property('const_b', .91)
    mel.connect_material_expressions(lines, '', level, 'A')
    m1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 100)
    mel.connect_material_expressions(tex, 'RGB', m1, 'A')
    mel.connect_material_expressions(bright, '', m1, 'B')
    m2 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -200, 150)
    mel.connect_material_expressions(m1, '', m2, 'A')
    mel.connect_material_expressions(level, '', m2, 'B')
    mel.connect_material_property(m2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    for prop, value, y in ((unreal.MaterialProperty.MP_ROUGHNESS, .08, 600), (unreal.MaterialProperty.MP_SPECULAR, .35, 700),
                           (unreal.MaterialProperty.MP_METALLIC, 0.0, 800)):
        node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, y)
        node.set_editor_property('r', value)
        mel.connect_material_property(node, '', prop)
    black = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 900)
    black.set_editor_property('constant', unreal.LinearColor(.005, .005, .006, 1))
    mel.connect_material_property(black, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return mat.get_path_name()


def check():
    names = sorted(p.stem for p in SRC.glob('T_Arc_*.png'))
    missing = [n for n in names if not unreal.EditorAssetLibrary.does_asset_exist(f'{DEST}/{n}')]
    mat = unreal.EditorAssetLibrary.does_asset_exist(f'{DEST}/M_ArcadeScreen')
    return json.dumps({'textures': len(names), 'missing': missing, 'material': mat, 'pass': not missing and mat})


def pinball_cabinet():
    """06/11 (Sergio: "fliperama de pinball e corrida"): the second cabinet became "Pinball do Farol". Its marquee, title
    screen and side art are the textures the model was imported with: reimport the pinball images over them (same asset
    names, so the cabinet's materials keep pointing at them)."""
    folder = '/Game/Custom/GameRoom/mare_arcade_siri'
    swap = {'T_Arc_P_Marquee': ['mare_arcade_siri_T_Arc_S_Marquee', 'mare_arcade_siri_T_Arc_S_Marquee1'],
            'T_Arc_P_Title': ['mare_arcade_siri_T_Arc_S_Title', 'mare_arcade_siri_T_Arc_S_Title1'],
            'T_Arc_P_Side': ['mare_arcade_siri_T_Arc_S_Side']}
    tasks = []
    for src, names in swap.items():
        for n in names:
            if not unreal.EditorAssetLibrary.does_asset_exist(f'{folder}/{n}'):
                continue
            t = unreal.AssetImportTask()
            t.filename = str(SRC / f'{src}.png')
            t.destination_path = folder
            t.destination_name = n
            t.automated = True
            t.replace_existing = True
            t.save = True
            tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    return json.dumps([t.destination_name for t in tasks])


def cmd(text=''):
    action, _, arg = (text or 'import').partition(':')
    if action == 'import':
        return json.dumps({'textures': import_textures(), 'material': screen_material()})
    if action == 'material':
        return screen_material()
    if action == 'check':
        return check()
    if action == 'pinball':
        return pinball_cabinet()
    raise ValueError(action)

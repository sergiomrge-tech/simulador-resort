"""Fish of the pier fishing (11/11): the profile pictures of the species book.

No free realistic model with a commercial licence was found for the eight species (search of 11/11), so they are
modelled with bpy (tools/ue58/gen_fish.py), which also renders one profile picture per species to
D:/Assets/Mare/fish_icons/<id>.png (1024 x 512, transparent). icons(): imports those pictures as UI textures
/Game/UI/Fish/T_Fish_<id> (MareFishing.cpp loads them by that name; the folder is always cooked). Re-runnable, PIE stopped."""
import json
from pathlib import Path

import unreal

SRC = Path('D:/Assets/Mare/fish_icons')
DEST = '/Game/UI/Fish'


def icons(arg=''):
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    species = [s['id'] for s in json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'leisure.json').read_text(encoding='utf-8'))['species']]
    out = {}
    for fish in species:
        png = SRC / f'{fish}.png'
        if not png.exists():
            out[fish] = 'missing'
            continue
        task = unreal.AssetImportTask()
        task.filename = str(png)
        task.destination_path = DEST
        task.destination_name = f'T_Fish_{fish}'
        task.replace_existing = True
        task.automated = True
        task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f'{DEST}/T_Fish_{fish}')
        if not tex:
            out[fish] = 'import failed'
            continue
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)   # UI: no block compression
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('srgb', True)
        tex.set_editor_property('never_stream', True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        out[fish] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return json.dumps(out)

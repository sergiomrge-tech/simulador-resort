"""Story postcards of a new game (07/11, Sergio: "apresentação inicial do jogo"): in-game captures (1920x1080, taken with
the QA camera: kiosk, grandma's letter on the living-room table, the village street, the house street, the kiosk sign)
imported as UI textures into /Game/UI/Intro (always cooked, DefaultGame.ini). title.json "story" lists them with the
captions. Sources kept in SourceArt/UI/Intro. Editor, PIE stopped: mare_hud module "mare_story.run|D:/CodexTemp/story"."""
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DEST = '/Game/UI/Intro'
ORDER = ['story1', 'story2', 'story3', 'story4', 'story5']


def run(folder='D:/CodexTemp/story'):
    src = ROOT / 'SourceArt/UI/Intro'
    src.mkdir(parents=True, exist_ok=True)
    out = {}
    for i, name in enumerate(ORDER, 1):
        png = Path(folder) / (name + '.png')
        keep = src / f'T_Story_{i}.png'
        if png.exists():
            shutil.copyfile(png, keep)
        task = unreal.AssetImportTask()
        task.filename = str(keep)
        task.destination_path = DEST
        task.destination_name = f'T_Story_{i}'
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f'{DEST}/T_Story_{i}')
        if not isinstance(tex, unreal.Texture2D):
            raise RuntimeError('import failed ' + name)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property('never_stream', True)
        tex.set_editor_property('srgb', True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[f'T_Story_{i}'] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return json.dumps(out)

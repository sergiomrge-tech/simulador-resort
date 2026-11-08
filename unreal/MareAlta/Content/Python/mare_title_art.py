"""2D title screen art (08/11, Sergio: "tela inicial em 2d", "use o canva para fazer algo bastante detalhado"): the island
painting and the logo made in Canva (sources in SourceArt/UI/Title; the logo's painted checkerboard was cut out with a
script) imported as UI textures into /Game/UI/Title (always cooked, DefaultGame.ini). title.json "art"/"logo_image"
name them. Editor, PIE stopped: mare_hud module "mare_title_art.run|"."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DEST = '/Game/UI/Title'


def run(_=''):
    out = {}
    for name in ['T_TitleArt', 'T_TitleLogo']:
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'SourceArt/UI/Title' / (name + '.png'))
        task.destination_path = DEST
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f'{DEST}/{name}')
        if not isinstance(tex, unreal.Texture2D):
            raise RuntimeError('import failed ' + name)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('never_stream', True)
        tex.set_editor_property('srgb', True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[name] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return json.dumps(out)


def fx(_=''):
    """HUD feedback sprites (08/11, reference tip 4): coin and soft puff from SourceArt/UI/Fx -> /Game/UI/Icons (cooked)."""
    out = {}
    for name in ['T_Fx_Coin', 'T_Fx_Soft']:
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'SourceArt/UI/Fx' / (name + '.png'))
        task.destination_path = '/Game/UI/Icons'
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset('/Game/UI/Icons/' + name)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property('never_stream', True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[name] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return json.dumps(out)

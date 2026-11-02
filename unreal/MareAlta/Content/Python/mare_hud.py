"""HUD assets for the gameplay plan (docs/ue58/GAMEPLAY_PLANO_2026-11-02.md).
Run through the editor MCP: hotel_lobby action "hud_<name>" -> run(<name>, arg)."""
from pathlib import Path
import unreal

ICONS = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/UI/Icons'
DEST = '/Game/UI/Icons'


def import_icons():
    """White icons from tools/ue58/gen_hud_icons.py as UI textures (no mips, UI group, alpha kept)."""
    out = {}
    for png in sorted(ICONS.glob('T_Icon_*.png')):
        task = unreal.AssetImportTask()
        task.filename = str(png)
        task.destination_path = DEST
        task.destination_name = png.stem
        task.automated = True
        task.replace_existing = True
        task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f'{DEST}/{png.stem}')
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[png.stem] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return out


MODELS = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Models'


def import_models(folder, dest):
    """Every GLB of SourceArt/Models/<folder> as <dest>/<name>/<name> (one folder each), with local material search
    so generic names never pick up another model's material. RoomMess (gen_room_mess.py) -> /Game/Custom/RoomMess,
    GameRoom (gen_pool_table.py) -> /Game/Custom/GameRoom."""
    import mare_hotel_lobby
    out = {}
    for glb in sorted((MODELS / folder).glob('*.glb')):
        # Fresh folder: reimporting over an old import keeps stale materials and renamed meshes.
        if unreal.EditorAssetLibrary.does_directory_exist(f'{dest}/{glb.stem}'):
            unreal.EditorAssetLibrary.delete_directory(f'{dest}/{glb.stem}')
        mesh = mare_hotel_lobby._import(glb, f'{dest}/{glb.stem}', glb.stem, False, search=False)
        out[glb.stem] = mesh.get_path_name()
    return out


def import_sfx():
    """Action sounds of SourceArt/Audio/Actions (tools/ue58/fetch_action_sfx.py) -> /Game/Audio/Actions, listed in
    Content/Data/audio.json with their action group and volume (UMareAudioWorld::PlayAction)."""
    import json
    src = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Audio/Actions'
    manifest = json.loads((src / 'manifest.json').read_text(encoding='utf-8'))
    actions = manifest.get('actions', manifest)
    catalog_path = Path(unreal.Paths.project_content_dir()).resolve() / 'Data/audio.json'
    catalog = [row for row in json.loads(catalog_path.read_text(encoding='utf-8')) if not row.get('group')]
    done = 0
    for group, info in actions.items():
        for f in info['files']:
            name = Path(f['file'] if isinstance(f, dict) else f).stem
            task = unreal.AssetImportTask()
            task.filename = str(src / f'{name}.wav')
            task.destination_path = '/Game/Audio/Actions'
            task.destination_name = name
            task.automated = True
            task.replace_existing = True
            task.save = True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            wave = unreal.load_asset(f'/Game/Audio/Actions/{name}')
            if not isinstance(wave, unreal.SoundWave):
                raise RuntimeError(f'{name}: import gave {wave}')
            catalog.append({'id': name, 'path': f'/Game/Audio/Actions/{name}.{name}', 'duration': wave.get_editor_property('duration'),
                            'loop': False, 'group': group, 'volume': info['volume']})
            done += 1
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return {'imported': done, 'catalog': len(catalog)}


def run(action, arg=''):
    if action == 'sfx':
        return import_sfx()
    if action == 'icons':
        return import_icons()
    if action == 'mess':
        return import_models('RoomMess', '/Game/Custom/RoomMess')
    if action == 'pool':
        return import_models('GameRoom', '/Game/Custom/GameRoom')
    if action == 'boats':
        return import_models('Boats', '/Game/Custom/Boats')
    if action == 'desk':
        return import_models('Reception', '/Game/Custom/Reception')
    raise ValueError(action)

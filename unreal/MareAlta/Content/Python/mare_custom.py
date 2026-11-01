"""Customization assets: imports the Poly Haven / Fab models of every tier into /Game/Custom/<slug>
and writes Content/Data/custom_assets.json (slug -> static mesh path) read by UMareCustomWorld.
Materials for material tiers live in /Game/Custom/Materials (built by build_materials)."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DATA = ROOT / 'Content/Data'
LIBS = [Path('D:/Assets/PolyHaven'), Path('D:/Assets/Fab'), Path('D:/Assets/Mare')]


def _slugs():
    cat = json.loads((DATA / 'customization.json').read_text(encoding='utf-8'))
    out = []
    for place in cat['places'].values():
        for slot in place['slots']:
            for tier in slot['tiers']:
                for part in tier.get('parts', []):
                    if part['model'] not in out:
                        out.append(part['model'])
    return out


def _find(slug):
    for lib in LIBS:
        info = lib / slug / 'info.json'
        if info.exists():
            data = json.loads(info.read_text(encoding='utf-8'))
            if data.get('gltf'):
                return lib / slug / data['gltf']
    return None


def import_all(force=False, only=None, folder_suffix=''):
    import mare_hotel_lobby
    import importlib
    importlib.reload(mare_hotel_lobby)
    path = DATA / 'custom_assets.json'
    assets = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    report = {}
    for slug in only or _slugs():
        if slug in assets and not force and unreal.load_asset(assets[slug]):
            report[slug] = 'kept'
            continue
        src = _find(slug)
        if not src:
            report[slug] = 'missing source'
            continue
        dest = '/Game/Custom/' + slug + folder_suffix
        mesh = mare_hotel_lobby._import(src, dest, slug, True, not slug.startswith('mare_'))
        if not mesh:
            report[slug] = 'import failed'
            continue
        mare_hotel_lobby._complex_collision(mesh)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        assets[slug] = mesh.get_path_name()
        b = mesh.get_bounds()
        report[slug] = {'tris': mesh.get_num_triangles(0), 'size_cm': [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)],
                        'materials': len(mesh.static_materials)}
    path.write_text(json.dumps(assets, indent=1), encoding='utf-8')
    report['_usage'] = fix_usage()['fixed']
    return report


def fix_usage():
    """Tier parts are drawn as HISM instances: every material under /Game/Custom (and its parents)
    needs the InstancedStaticMeshes (+Nanite) usage, otherwise the game falls back to the grey
    default material."""
    fixed = []
    for path in unreal.EditorAssetLibrary.list_assets('/Game/Custom', recursive=True):
        asset = unreal.load_asset(path)
        while isinstance(asset, unreal.MaterialInstance):
            asset = asset.get_editor_property('parent')
        if not isinstance(asset, unreal.Material):
            continue
        changed = False
        for flag in ('used_with_instanced_static_meshes', 'used_with_nanite'):
            if not asset.get_editor_property(flag):
                asset.set_editor_property(flag, True)
                changed = True
        if changed:
            unreal.MaterialEditingLibrary.recompile_material(asset)
            unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
            fixed.append(asset.get_path_name())
    return {'fixed': len(fixed), 'materials': sorted(set(fixed))[:40]}


def run(action, arg=''):
    if action == 'fixusage':
        return fix_usage()
    if action == 'inspect':
        # Textures of an imported model: name, sRGB, compression, size; materials and their texture params.
        out = {}
        for path in unreal.EditorAssetLibrary.list_assets('/Game/Custom/' + arg, recursive=True):
            asset = unreal.load_asset(path)
            if isinstance(asset, unreal.Texture2D):
                out[asset.get_name()] = ['tex', asset.get_editor_property('srgb'), str(asset.get_editor_property('compression_settings'))]
            elif isinstance(asset, unreal.MaterialInstance):
                params = {str(p.parameter_info.name): (p.parameter_value.get_name() if p.parameter_value else None) for p in asset.get_editor_property('texture_parameter_values')}
                out[asset.get_name()] = ['mi', params]
        return out
    if action == 'purge':
        # Delete superseded model folders, but only when nothing outside them still references their assets.
        folders = ['/Game/Custom/' + f for f in arg.split(',') if f]
        deleted, kept = [], {}
        for folder in folders:
            outside = []
            for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
                pkg = path.split('.')[0]
                for ref in unreal.EditorAssetLibrary.find_package_referencers_for_asset(pkg, False):
                    if not any(str(ref).startswith(f) for f in folders):
                        outside.append(str(ref))
            if outside:
                kept[folder] = sorted(set(outside))[:5]
            elif unreal.EditorAssetLibrary.delete_directory(folder):
                deleted.append(folder)
        return {'deleted': len(deleted), 'kept': kept}
    if action == 'fresh':
        # New folder per model generation, so its materials/textures are created fresh (v2: unique names).
        return import_all(True, [arg], '_m5')
    if action == 'reimport':
        # Replace an existing model in place (level references stay valid).
        return import_all(True, [arg])
    if action == 'one':
        # Single props outside the catalogue (e.g. the hand-held phone 'realistic_smartphone').
        unreal.EditorAssetLibrary.delete_directory('/Game/Custom/' + arg)  # a failed import leaves an empty mesh behind
        return import_all(True, [arg])
    if action == 'import':
        return import_all(arg == 'force')
    if action == 'slugs':
        return _slugs()
    if action == 'materials':
        import mare_materials, importlib
        importlib.reload(mare_materials)
        return mare_materials.build_custom_materials()
    raise ValueError(action)

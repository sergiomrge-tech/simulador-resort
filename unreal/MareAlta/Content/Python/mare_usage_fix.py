"""Nanite/ISM usage flags for every opaque material under the given folders (comma separated), saved. Without them
the cooked game draws the default material (08/11: the summit trail's Trail_Earth/Trail_Log after its mesh turned
Nanite). PIE stopped."""
import json


def run(arg='/Game/Summit,/Game/World/Island'):
    import importlib
    import mare_boat_tour
    importlib.reload(mare_boat_tour)   # the engine keeps the old module cached
    return json.dumps({f: mare_boat_tour.fix_usage(f) for f in arg.split(',') if f})


def assets(arg=''):
    """The same flags for single materials by path (comma separated), e.g. a shared folder where only a few need them."""
    import unreal
    fixed = []
    for p in [x for x in arg.split(',') if x]:
        a = unreal.load_asset(p)
        if not isinstance(a, unreal.Material):
            fixed.append([p, 'not a material'])
            continue
        changed = False
        for flag in ('used_with_nanite', 'used_with_instanced_static_meshes'):
            if not a.get_editor_property(flag):
                a.set_editor_property(flag, True)
                changed = True
        if changed:
            unreal.MaterialEditingLibrary.recompile_material(a)
            fixed.append([p, unreal.EditorAssetLibrary.save_loaded_asset(a, False)])
    return json.dumps(fixed)


def force_save(arg='/Game/Nature/Mountain'):
    """Sets the flags and SAVES every opaque/masked material under the folders, even when the flag already reads True:
    the editor turns the usage on in memory when it first draws the material and never writes it (08/11: the forest
    debris looked fine in the editor and fell back to the checker in the cooked game)."""
    import unreal
    out = {}
    for folder in [f for f in arg.split(',') if f]:
        n = 0
        for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
            a = unreal.load_asset(p)
            if not isinstance(a, unreal.Material) or a.get_editor_property('blend_mode') not in (unreal.BlendMode.BLEND_OPAQUE, unreal.BlendMode.BLEND_MASKED):
                continue
            a.set_editor_property('used_with_nanite', True)
            a.set_editor_property('used_with_instanced_static_meshes', True)
            if unreal.EditorAssetLibrary.save_loaded_asset(a, False):
                n += 1
        out[folder] = n
    return json.dumps(out)

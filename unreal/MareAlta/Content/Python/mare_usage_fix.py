"""Nanite/ISM usage flags for every opaque material under the given folders (comma separated), saved. Without them
the cooked game draws the default material (08/11: the summit trail's Trail_Earth/Trail_Log after its mesh turned
Nanite). PIE stopped."""
import json


def run(arg='/Game/Summit,/Game/World/Island'):
    import mare_boat_tour
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

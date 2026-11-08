"""Kiosk ceiling lamp (08/11, Sergio: "quiosque continua escuro, coloque uma lâmpada no teto"): Poly Haven
hanging_industrial_lamp (CC0, Kuutti Siitonen) -> /Game/Custom/Lighting/hanging_industrial_lamp; lighting.json lists it
as a kiosk work fixture (on during the opening hours, by day too). Editor, PIE stopped:
mare_hud module "mare_kiosk_lamp.run|"."""
import json
from pathlib import Path
import unreal


def run(_=''):
    import mare_hotel_lobby as hl
    import mare_boat_tour as bt
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Lighting/hanging_industrial_lamp/hanging_industrial_lamp_1k.gltf'
    folder = '/Game/Custom/Lighting/hanging_industrial_lamp'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    mesh = hl._import(src, folder, 'hanging_industrial_lamp', True, search=False)
    # the lamp's glass is translucent: Nanite cannot draw it (log warning), the small mesh renders without Nanite
    import mare_hud
    mare_hud.nanite_off(mesh.get_path_name())
    b = mesh.get_bounds()
    return json.dumps({'mesh': mesh.get_path_name(), 'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)],
                       'size': [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)],
                       'usage': bt.fix_usage('/Game/Custom/Lighting')})


def fishing(_=''):
    """Fishing spot prop (tools/ue58/gen_fishing_spot.py) -> /Game/Custom/Leisure/mare_fishing_spot, placed by
    UMareToursWorld at leisure.json fishing_spot."""
    import mare_hotel_lobby as hl
    import mare_boat_tour as bt
    src = Path('D:/Assets/Mare/mare_fishing_spot/mare_fishing_spot.glb')
    folder = '/Game/Custom/Leisure/mare_fishing_spot'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    mesh = hl._import(src, folder, 'mare_fishing_spot', True, search=False)
    b = mesh.get_bounds()
    return json.dumps({'mesh': mesh.get_path_name(), 'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)],
                       'size': [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)],
                       'usage': bt.fix_usage('/Game/Custom/Leisure')})

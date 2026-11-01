"""Download CC0 Poly Haven models (glTF + textures) into the shared asset library on D:.

Each model lands in D:/Assets/PolyHaven/<slug>/ with info.json (authors, licence) so it can be
credited in CREDITS.md. Existing downloads are kept. Usage:
  python tools/ue58/fetch_polyhaven.py [--res 2k] slug [slug ...] | --set lobby|mountain|beach
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

LIB = Path('D:/Assets/PolyHaven')
API = 'https://api.polyhaven.com'
HEADERS = {'User-Agent': 'MareAltaResort-asset-fetch/1.0'}
SETS = {
    'lobby': ['sofa_03', 'Sofa_01', 'ArmChair_01', 'mid_century_lounge_chair', 'modern_arm_chair_01', 'Ottoman_01',
              'modern_coffee_table_01', 'modern_coffee_table_02', 'side_table_tall_01', 'modern_ceiling_lamp_01',
              'potted_plant_01', 'potted_plant_02', 'potted_plant_04', 'pachira_aquatica_01', 'calathea_orbifolia_01',
              'anthurium_botany_01', 'ceramic_vase_01', 'ceramic_vase_03', 'standing_picture_frame_01',
              'hanging_picture_frame_01', 'hanging_picture_frame_03', 'decorative_book_set_01'],
    'mountain': ['island_tree_01', 'island_tree_02', 'island_tree_03', 'tree_small_02', 'jacaranda_tree',
                 'shrub_01', 'shrub_02', 'shrub_03', 'shrub_04', 'fern_02', 'rock_face_01', 'rock_face_02',
                 'mountainside', 'coastal_cliff_01', 'coastal_cliff_02', 'coastal_cliff_04'],
    'beach': ['coast_rocks_01', 'coast_rocks_02', 'coast_rocks_03', 'coast_rocks_05', 'sand_rocks_small_01',
              'lambis_shell', 'grass_bermuda_01'],
}


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 3)


def fetch(slug, res):
    folder = LIB / slug
    marker = folder / 'info.json'
    if marker.exists():
        return 'kept'
    files = json.loads(get(f'{API}/files/{slug}'))
    gltf = files['gltf'].get(res) or files['gltf'][sorted(files['gltf'])[0]]
    entry = gltf['gltf']
    folder.mkdir(parents=True, exist_ok=True)
    (folder / Path(entry['url']).name).write_bytes(get(entry['url']))
    for rel, inc in entry.get('include', {}).items():
        dest = folder / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(get(inc['url']))
    info = json.loads(get(f'{API}/info/{slug}'))
    marker.write_text(json.dumps({'slug': slug, 'name': info.get('name'), 'authors': info.get('authors'),
                                  'license': 'CC0 1.0', 'source': f'https://polyhaven.com/a/{slug}',
                                  'resolution': res, 'gltf': Path(entry['url']).name}, indent=1), encoding='utf-8')
    return 'downloaded'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('slugs', nargs='*')
    p.add_argument('--set', action='append', default=[])
    p.add_argument('--res', default='2k')
    a = p.parse_args()
    slugs = list(a.slugs) + [s for name in a.set for s in SETS[name]]
    for slug in slugs:
        try:
            print(slug, fetch(slug, a.res), flush=True)
        except Exception as e:
            print(slug, 'FAILED', e, flush=True)


if __name__ == '__main__':
    main()

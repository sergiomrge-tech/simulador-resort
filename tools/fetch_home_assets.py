"""Targeted Poly Haven CC0 downloads; no unrelated regeneration.

Official pages: https://polyhaven.com/a/<slug>, license https://polyhaven.com/license
Run with the same Python environment used by fetch_assets.py.
"""
from concurrent.futures import ThreadPoolExecutor
import fetch_assets

HOME_ASSETS = {
    'sofa_02': 'home_sofa',
    'television_02': 'home_tv',
    'boombox': 'home_stereo',
    'coffee_table_round_01': 'home_coffee_table',
    'painted_wooden_cabinet_02': 'home_storage_cabinet',
    'small_wooden_table_01': 'home_tv_console',
    'wall_clock': 'home_clock',
    'carved_wooden_elephant': 'home_wood_carving',
}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda slug: fetch_assets.model(slug, '1k', 'models', True), HOME_ASSETS))
    print('HOME_ASSETS_DOWNLOAD PASS')

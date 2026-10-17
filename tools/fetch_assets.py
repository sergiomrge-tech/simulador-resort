#!/usr/bin/env python3
"""Baixa todos os assets CC0 do Maré Alta Resort para os caminhos exatos usados pelo jogo.

  Poly Haven (CC0)  -> assets/tex (1k + normal 512), assets/tex_hd (2k + rough 1k),
                       assets/models (glTF 1k, normal/ARM 512), assets/models_hd (glTF 2k)
  Procedurais       -> tools/gen_textures.py, tools/gen_hd.py, tools/gen_calcada.py
  Já no repositório -> assets/audio/*.ogg (CC0, OpenGameArt) e assets/models/ual/guest.glb
                       (Quaternius Universal Animation Library, CC0, com zonas de cor de tools/color_zones.py)

Uso:  python3 tools/fetch_assets.py [--force] [--only tex|models]
Requer: Python 3.8+, Pillow e numpy (pip install pillow numpy).
"""
import json, os, sys, time, urllib.request, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
UA = {"User-Agent": "MareAltaResort-fetch/0.2 (+https://github.com/sergiomrge-tech/simulador-resort)"}
API = "https://api.polyhaven.com/files/"

# texturas Poly Haven (slug == nome do arquivo no jogo, exceto grey_plaster_02 -> white_plaster via gerador)
TEXTURES = ["bamboo_wall", "blue_floor_tiles_01", "clay_roof_tiles_02", "coast_sand_01", "cobblestone_floor_04",
            "damp_beach_sand", "oak_wood_planks", "palm_tree_bark", "patio_tiles", "reed_roof_04", "rough_linen",
            "terracotta_floor_tiles", "weathered_planks", "white_stucco", "grey_plaster_02",
            # v0.4: tapete, piso interno e madeira escura dos móveis
            "fabric_pattern_07", "brown_planks_05", "dark_wooden_planks",
            # v0.6.1: serra (floresta, grama tropical, rocha)
            "forest_floor", "leafy_grass", "rock_face"]
MODELS = ["CashRegister_01", "CoffeeCart_01", "Shelf_01", "WoodenChair_01", "WoodenTable_01", "bar_chair_round_01",
          "electric_stove", "lambis_shell", "lifebuoy", "outdoor_table_chair_set_01", "painted_wooden_bench",
          "painted_wooden_cabinet", "planter_box_01", "planter_pot_clay", "plastic_crate_01", "plastic_monobloc_chair_01",
          "potted_plant_01", "potted_plant_02", "potted_plant_04", "shrub_01", "shrub_02", "shrub_03", "side_table_01",
          "street_lamp_01", "wicker_basket_01", "wicker_basket_02", "wooden_bucket_01", "wooden_crate_01",
          "wooden_lantern_01", "wooden_stool_01",
          # v0.4: mobília realista-estilizada dos bangalôs (Poly Haven, CC0)
          "GothicBed_01", "painted_wooden_nightstand", "ceiling_fan", "ornate_mirror_01",
          "ceramic_vase_02", "hanging_picture_frame_02", "Rockingchair_01", "throw_pillows_01",
          "vintage_oil_lamp", "pachira_aquatica_01"]
# ambientCG (CC0): materiais que a Poly Haven não tem (palha trançada/rattan)
AMBIENTCG = {"Wicker002": "rattan"}
MODELS_HD_ONLY = ["island_tree_01", "coast_rocks_01"]   # só PC (pesados)

FORCE = "--force" in sys.argv

def get(url, dst=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if dst:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(data)
            return data
        except Exception as e:
            if i == tries - 1:
                raise
            print("  retry", url, e)
            time.sleep(2 + i * 3)

def resize(path, size):
    from PIL import Image
    im = Image.open(path)
    if max(im.size) > size:
        im.resize((size, size), Image.LANCZOS).save(path, quality=90)

def cap(path, size=2048):
    from PIL import Image
    im = Image.open(path)
    if max(im.size) > size:
        w, h = im.size
        k = size / max(w, h)
        im.resize((int(w * k), int(h * k)), Image.LANCZOS).save(path, quality=92)

def texture(slug):
    files = json.loads(get(API + slug))
    def url(kind, res):
        if kind == "Diffuse" and kind not in files:
            kind = next(k for k in ("diff", "col_1", "col_01") if k in files)   # tecidos com variações de cor
        return files[kind][res]["jpg"]["url"]
    jobs = [
        (url("Diffuse", "1k"), f"{A}/tex/{slug}_diff.jpg", 1024),
        (url("nor_gl", "1k"), f"{A}/tex/{slug}_nor.jpg", 512),
        (url("Diffuse", "2k"), f"{A}/tex_hd/{slug}_diff.jpg", 2048),
        (url("nor_gl", "2k"), f"{A}/tex_hd/{slug}_nor.jpg", 2048),
        (url("Rough", "1k"), f"{A}/tex_hd/{slug}_rough.jpg", 1024),
    ]
    for u, dst, size in jobs:
        if os.path.exists(dst) and not FORCE:
            continue
        get(u, dst)
        resize(dst, size)
    print("tex  ok", slug)

def model(slug, res, base, small_maps=False):
    out = f"{A}/{base}/{slug}"
    gl = f"{out}/{slug}.gltf"
    if os.path.exists(gl) and not FORCE:
        print("model skip", base, slug)
        return
    files = json.loads(get(API + slug))
    g = files["gltf"][res]["gltf"]
    get(g["url"], gl)
    for rel, inc in g.get("include", {}).items():
        dst = os.path.join(out, rel)
        get(inc["url"], dst)
        if rel.endswith(".jpg") or rel.endswith(".png"):
            if small_maps and ("_nor_" in rel or "_arm_" in rel):
                resize(dst, 512)
            else:
                cap(dst, 2048)
    print("model ok", base, slug, res)

def ambientcg(asset, name):
    import zipfile, io
    dst = f"{A}/tex_hd/{name}_diff.jpg"
    if os.path.exists(dst) and not FORCE:
        return
    data = get(f"https://ambientcg.com/get?file={asset}_2K-JPG.zip")
    z = zipfile.ZipFile(io.BytesIO(data))
    for zn in z.namelist():
        kind = {"_Color.jpg": "diff", "_NormalGL.jpg": "nor", "_Roughness.jpg": "rough"}
        for suf, k in kind.items():
            if zn.endswith(suf):
                out = f"{A}/tex_hd/{name}_{k}.jpg"
                with open(out, "wb") as f:
                    f.write(z.read(zn))
                cap(out, 2048 if k != "rough" else 1024)
                if k in ("diff", "nor"):
                    from PIL import Image
                    small = f"{A}/tex/{name}_{k}.jpg"
                    im = Image.open(out).convert("RGB")
                    im.resize((1024, 1024) if k == "diff" else (512, 512), Image.LANCZOS).save(small, quality=90)
    print("tex  ok (ambientCG)", asset, "->", name)

def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
    with ThreadPoolExecutor(6) as ex:
        futs = []
        if only in ("", "tex"):
            futs += [ex.submit(texture, s) for s in TEXTURES]
            futs += [ex.submit(ambientcg, k, v) for k, v in AMBIENTCG.items()]
        if only in ("", "models"):
            futs += [ex.submit(model, s, "1k", "models", True) for s in MODELS]
            futs += [ex.submit(model, s, "2k", "models_hd") for s in MODELS + MODELS_HD_ONLY]
        errs = 0
        for f in futs:
            try:
                f.result()
            except Exception as e:
                errs += 1
                print("ERRO:", e)
    if only in ("", "tex"):
        # texturas procedurais / derivadas (reboco branco, pedra clara, folha do coqueiro, capim, arbusto, calçada, ícone)
        for t in ("gen_textures.py", "gen_hd.py", "gen_calcada.py"):
            print("gerando", t)
            subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", t)], cwd=ROOT)
        for s in ("diff", "nor"):
            p = f"{A}/tex/grey_plaster_02_{s}.jpg"
            if os.path.exists(p):
                os.remove(p)
    for need in ("assets/models/ual/guest.glb", "assets/audio/music_bossa.ogg"):
        if not os.path.exists(os.path.join(ROOT, need)):
            print("AVISO: faltando", need, "(vem no repositório; veja CREDITS.md)")
    print("PRONTO" if errs == 0 else f"TERMINOU COM {errs} ERRO(S)")
    print("Abra o projeto no Godot 4.5.1 (ele importa os assets na primeira abertura).")
    sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()

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
            # v0.6.1: serra (rocha, copa das árvores e chão de floresta)
            "rock_face", "leafy_grass", "forest_floor"]
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

# v0.8 (regra "nada de bolas e quadrados"): modelos reais do Poly Haven (CC0) para todos os objetos do jogo, só 1k para não pesar.
MODELS_EXTRA = [
    "painted_wooden_chair_01", "wooden_bowl_01",
    "boombox", "television_02", "lambis_shell", "lifebuoy", "ocean_buoy", "wicker_basket_01", "wicker_basket_02", "trashbag", "planter_pot_clay",
    "potted_plant_01", "potted_plant_02", "potted_plant_04", "vintage_oil_lamp", "vintage_radio_transceiver", "sweet_potato",
    # frutas, pães e cozinha
    "food_apple_01", "bananas", "lemon", "food_lime_01", "food_lychee_01", "food_kiwi_01", "food_avocado_01",
    "food_pomegranate_01", "food_pears_asian_01", "croissant", "hamburger_buns", "carrot_cake", "wooden_cutting_board",
    "wooden_bowl_02", "carved_wooden_plate", "wooden_spoon", "jug_01", "wine_bottles_01", "brass_goblets", "tea_set_01",
    "metal_jug", "modified_thermos", "pot_enamel_01", "brass_pan_01", "brass_pot_01", "ceramic_pot", "fish_knife",
    # recipientes
    "Barrel_01", "Barrel_02", "barrel_03", "wooden_barrels_01", "wine_barrel_01", "wooden_crate_02", "plastic_crate_02",
    "plastic_crate_03", "wooden_bucket_02", "metal_trash_can", "watering_can_metal_01", "treasure_chest", "cardboard_box_01",
    "ceramic_vase_01", "ceramic_vase_03", "ceramic_vase_04", "brass_vase_01", "antique_ceramic_vase_01", "planter_box_02", "planter_box_03",
    # móveis
    "WoodenTable_02", "wooden_table_02", "round_wooden_table_01", "round_wooden_table_02", "wooden_picnic_table",
    "painted_wooden_table", "dining_table", "folding_wooden_stool", "wooden_stool_02", "painted_wooden_chair_02",
    "dining_chair_02", "vintage_day_bed", "old_bed_frame", "painted_wooden_cabinet_02", "painted_wooden_shelves",
    "wooden_display_shelves_01", "vintage_cabinet_01", "wooden_bookshelf_worn", "ClassicNightstand_01",
    # v1.0.1: tronco de deriva na praia (no lugar do log_large da Kenney)
    "dead_tree_trunk",
    "small_wooden_table_01", "coffee_table_round_01", "side_table_tall_01", "painted_wooden_sofa", "sofa_02", "ArmChair_01",
    "Ottoman_01", "GreenChair_01", "metal_stool_01", "chinese_stool", "modular_street_seating", "painted_wooden_stool",
    # luz e decoração
    "Lantern_01", "street_lamp_02", "caged_hanging_light", "hanging_industrial_lamp", "wooden_candlestick", "brass_candleholders",
    "brass_diya_lantern", "lantern_chandelier_01", "Chandelier_03", "standing_chalkboard_01", "fancy_picture_frame_01",
    "hanging_picture_frame_01", "hanging_picture_frame_03", "wall_clock", "garden_gnome", "rubber_duck_toy", "Ukulele_01",
    "vintage_suitcase", "seadogs_compass", "vintage_binocular", "fishermans_hat", "life_jacket", "alarm_clock_01",
    "book_encyclopedia_set_01", "mantel_clock_01", "carved_wooden_elephant",
    # plantas e pedras
    "shrub_04", "grass_medium_01", "grass_medium_02", "grass_bermuda_01", "fern_02", "calathea_orbifolia_01",
    "Camera_01", "anthurium_botany_01", "flower_gazania", "flower_ursinia", "periwinkle_plant", "island_tree_02", 
    "tree_stump_01", "dry_branches_medium_01", "bark_debris_01",
    "coast_rocks_02", "coast_rocks_03", "coast_rocks_05", "boulder_01", "rock_07", "rock_09", "stone_01", "sand_rocks_small_01",
    "coast_land_rocks_02", "coast_land_rocks_03",
    # estruturas e navios
    "modular_wooden_pier", "stone_fire_pit", "utility_box_01", "fire_hydrant", "modular_electricity_poles", "ship_pinnace",
    "rollershutter_window_01",
]
# Kenney (CC0): só o que o Poly Haven não tem (coco, drinques, peixe, barcos, palmeiras, bandeiras). {zip: [arquivos .glb]}
KENNEY = {
    "https://kenney.nl/media/pages/assets/nature-kit/37ac38a37b-1677698939/kenney_nature-kit.zip": [
        "canoe", "canoe_paddle", "rock_largeB", "rock_largeC", "rock_smallA", "rock_smallB", "rock_smallC", "rock_smallF",
        "stone_largeB", "stone_largeC", "plant_bush", "plant_bushLarge", "plant_bushDetailed", "flower_redA", "flower_yellowB",
        "flower_purpleB", "log_large", "stump_round", "campfire_logs", "campfire_stones", "tent_smallOpen", "lily_large", "mushroom_red"],
    "https://kenney.nl/media/pages/assets/food-kit/83086fa91c-1719418518/kenney_food-kit.zip": [
        "coconut", "coconut-half", "cocktail", "frappe", "glass", "fish", "fish-bones", "loaf", "loaf-round", "bread",
        "pineapple", "watermelon", "orange", "bottle-oil", "ice-cream-cup", "cup", "cup-tea", "bowl",
        "plate-dinner", "plate-deep", "utensil-spoon", "utensil-fork"],
    "https://kenney.nl/media/pages/assets/pirate-kit/e6d4bb1525-1771333093/kenney_pirate-kit.zip": [
        "boat-row-small", "boat-row-large", "palm-detailed-bend", "palm-detailed-straight", "palm-bend", "palm-straight",
        "flag", "flag-pennant", "tool-paddle", "barrel", "crate-bottles", "bottle", "bottle-large", "ship-small", "ship-medium"],
}
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
    if slug == "leafy_grass":   # a copa da serra (shader mountain) usa o mesmo mosaico de folhas
        import shutil
        for d, suf in (("tex", "diff"), ("tex", "nor"), ("tex_hd", "diff"), ("tex_hd", "nor"), ("tex_hd", "rough")):
            src = f"{A}/{d}/leafy_grass_{suf}.jpg"
            if os.path.exists(src):
                shutil.copyfile(src, f"{A}/{d}/canopy_{suf}.jpg")

def model(slug, res, base, small_maps=False):
    out = f"{A}/{base}/{slug}"
    gl = f"{out}/{slug}.gltf"
    # Um .gltf pode existir mesmo se um download de .bin/.jpg falhou.
    # Nesse caso nunca considerar o modelo pronto: buscar só dependências faltantes.
    if os.path.isfile(gl) and not FORCE:
        try:
            from urllib.parse import unquote
            with open(gl, encoding="utf-8") as f:
                doc = json.load(f)
            links = [x.get("uri", "") for x in doc.get("buffers", [])]
            links += [x.get("uri", "") for x in doc.get("images", [])]
            missing = [u for u in links if u and not u.startswith("data:")
                       and not os.path.isfile(os.path.join(out, unquote(u)))]
            if not missing:
                print("model skip", base, slug)
                return
            print("model incompleto, recuperando", base, slug, missing)
        except (OSError, ValueError) as e:
            print("model danificado, baixando novamente", base, slug, e)
    files = json.loads(get(API + slug))
    g = files["gltf"][res]["gltf"]
    if FORCE or not os.path.isfile(gl):
        get(g["url"], gl)
    # Conferir binários e mapas mesmo no retry após um erro de download.
    for rel, inc in g.get("include", {}).items():
        dst = os.path.join(out, rel)
        if os.path.isfile(dst) and not FORCE:
            continue
        get(inc["url"], dst)
        if rel.endswith(".jpg") or rel.endswith(".png"):
            if small_maps and ("_nor_" in rel or "_arm_" in rel):
                resize(dst, 512)
            else:
                cap(dst, 2048)
    print("model ok", base, slug, res)


def kenney(url, names):
    """Baixa o pack Kenney (CC0), extrai num cache e suaviza no Blender (tools/smooth_kenney.py); sem bpy copia o GLB cru."""
    import zipfile, io, shutil, tempfile
    out = f"{A}/models/kenney"
    todo = [n for n in names if FORCE or not os.path.exists(f"{out}/{n}.glb")]
    if not todo:
        print("kenney skip", url.split("/")[-1])
        return
    tmp = tempfile.mkdtemp(prefix="kenney_")
    z = zipfile.ZipFile(io.BytesIO(get(url)))
    z.extractall(tmp)
    src = None
    for dp, dn, fn in os.walk(tmp):
        if os.path.basename(dp) in ("GLB format", "GLTF format"):
            src = dp
    os.makedirs(out, exist_ok=True)
    have = [n for n in todo if os.path.exists(f"{src}/{n}.glb")]
    for n in todo:
        if n not in have:
            print("  kenney: não achei", n)
    try:
        import bpy  # noqa: F401
        subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "smooth_kenney.py"), src, out] + have,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except ImportError:
        print("  AVISO: sem bpy, copiando GLB cru (facetado, textura externa)")
        for n in have:
            shutil.copyfile(f"{src}/{n}.glb", f"{out}/{n}.glb")
        shutil.copytree(f"{src}/Textures", f"{out}/Textures", dirs_exist_ok=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("kenney ok", url.split("/")[-1], len(have))


def quaternius_nature():
    """Stylized Nature MegaKit [Standard] (Quaternius, CC0) pelo itch.io: pasta glTF -> assets/models/qnat/ (chave "q:Nome")."""
    import zipfile, io, http.cookiejar, urllib.parse, re
    out = f"{A}/models/qnat"
    if os.path.exists(f"{out}/Bush_Common.gltf") and not FORCE:
        print("qnat skip")
        return
    base = "https://quaternius.itch.io/stylized-nature-megakit"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def call(url, data=None):
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data is not None else None, headers=UA)
        return op.open(req, timeout=120).read()
    def csrf(html):
        return re.search(r'csrf_token" value="([^"]+)', html.decode("utf-8", "ignore")).group(1)
    page = call(base)
    dl = json.loads(call(base + "/download_url", {"csrf_token": csrf(page)}))["url"]
    dlpage = call(dl)
    upload = re.search(r'data-upload_id="(\d+)"', dlpage.decode("utf-8", "ignore")).group(1)
    fj = json.loads(call(f"{base}/file/{upload}?source=view_game&as_props=1&after_download_lightbox=true", {"csrf_token": csrf(dlpage)}))
    z = zipfile.ZipFile(io.BytesIO(get(fj["url"])))
    os.makedirs(out, exist_ok=True)
    for n in z.namelist():
        parts = n.split("/")
        if "glTF" in parts and not n.endswith("/"):
            with open(f"{out}/{parts[-1]}", "wb") as f:
                f.write(z.read(n))
    print("qnat ok", len(os.listdir(out)))

def universal_base_characters():
    """Baixa personagens e cabelos CC0 da Quaternius usados em people.gd.

    Os glTF/.bin não estão versionados no Git (gitignore). Sem esta etapa, uma
    instalação nova do GitHub Actions tenta instanciar PackedScene nula para
    todos os clientes e moradores, apesar de já possuir as texturas .png.
    Fonte: https://quaternius.itch.io/universal-base-characters
    """
    import zipfile, io, http.cookiejar, urllib.parse, re, posixpath, shutil
    out = os.path.join(A, "models", "ubc")
    wanted = ["Superhero_Male_FullBody", "Superhero_Female_FullBody",
              "Hair_Beard", "Hair_Buns", "Hair_Buzzed",
              "Hair_BuzzedFemale", "Hair_Long", "Hair_SimpleParted"]
    def complete(stem):
        p = os.path.join(out, stem + ".gltf")
        if not os.path.isfile(p):
            return False
        try:
            with open(p, encoding="utf-8") as f:
                doc = json.load(f)
            refs = [x.get("uri", "") for x in doc.get("buffers", [])]
            refs += [x.get("uri", "") for x in doc.get("images", [])]
            return all(not ref or ref.startswith("data:") or os.path.isfile(
                os.path.normpath(os.path.join(out, urllib.parse.unquote(ref))))
                for ref in refs)
        except (OSError, ValueError):
            return False
    if not FORCE and all(complete(stem) for stem in wanted):
        print("ubc skip", len(wanted))
        return
    base = "https://quaternius.itch.io/universal-base-characters"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def call(url, data=None):
        req = urllib.request.Request(
            url, data=urllib.parse.urlencode(data).encode() if data is not None else None, headers=UA)
        return op.open(req, timeout=120).read()
    def csrf(html):
        m = re.search(r'csrf_token" value="([^"]+)', html.decode("utf-8", "ignore"))
        if not m:
            raise RuntimeError("UBC: itch.io nao forneceu csrf_token")
        return m.group(1)
    page = call(base)
    dl = json.loads(call(base + "/download_url", {"csrf_token": csrf(page)}))["url"]
    dlpage = call(dl)
    m = re.search(r'data-upload_id="(\d+)"', dlpage.decode("utf-8", "ignore"))
    if not m:
        raise RuntimeError("UBC: itch.io nao forneceu upload_id")
    upload = m.group(1)
    fj = json.loads(call(
        base + "/file/" + upload + "?source=view_game&as_props=1&after_download_lightbox=true",
        {"csrf_token": csrf(dlpage)}))
    with zipfile.ZipFile(io.BytesIO(get(fj["url"]))) as z:
        names = z.namelist()
        os.makedirs(out, exist_ok=True)
        for stem in wanted:
            candidates = [n for n in names
                          if n.lower().endswith("/" + stem.lower() + ".gltf")]
            candidates.sort(key=lambda n: (0 if "godot - ue" in n.lower() else 1, len(n)))
            if not candidates:
                raise RuntimeError("UBC: modelo ausente do ZIP: " + stem)
            entry = candidates[0]
            doc = json.loads(z.read(entry).decode("utf-8"))
            dst = os.path.join(out, stem + ".gltf")
            with open(dst, "wb") as f:
                f.write(z.read(entry))
            parent = posixpath.dirname(entry)
            refs = [x.get("uri", "") for x in doc.get("buffers", [])]
            refs += [x.get("uri", "") for x in doc.get("images", [])]
            for rel in refs:
                if not rel or rel.startswith("data:"):
                    continue
                rel = urllib.parse.unquote(rel).replace("\\", "/")
                normalized = posixpath.normpath(rel)
                if normalized.startswith("../") or normalized.startswith("/"):
                    raise RuntimeError("UBC: caminho fora do pacote: " + rel)
                source = posixpath.normpath(parent + "/" + normalized)
                dest = os.path.normpath(os.path.join(out, *normalized.split("/")))
                if not dest.startswith(os.path.abspath(out) + os.sep):
                    raise RuntimeError("UBC: destino inseguro: " + rel)
                # Texturas PNG da UBC estão preservadas no repositório.
                # A versão atual do ZIP usa nomes ligeiramente diferentes,
                # então a dependência já existente não precisa ser baixada.
                if os.path.isfile(dest) and not FORCE:
                    continue
                if source not in names:
                    if os.path.isfile(dest):
                        continue
                    # Em algumas versões do pack, o glTF referencia
                    # T_Hair_1_Normal_png.png, mas a textura existente
                    # chama-se T_Hair_1_Normal.png.
                    if normalized.endswith("_png.png"):
                        alt = normalized[:-8] + ".png"
                        alt_dst = os.path.normpath(os.path.join(out, *alt.split("/")))
                        alt_source = posixpath.normpath(parent + "/" + alt)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        if os.path.isfile(alt_dst):
                            shutil.copyfile(alt_dst, dest)
                            continue
                        if alt_source in names:
                            with open(dest, "wb") as f:
                                f.write(z.read(alt_source))
                            continue
                    raise RuntimeError("UBC: dependencia ausente: " + source)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(z.read(source))
    print("ubc ok", len(wanted))


def animals_gen():
    """Gato/cachorro (Quaternius Animal Pack Vol.2, CC0) e caranguejo ("methodical pixel", CC0) pelo OpenGameArt -> assets/models/gen/*.glb
    (suavizados no Blender por tools/smooth_animals.py / convert_crab.py); toalha e castelo de areia saem de tools/gen_beach_props.py."""
    import zipfile, io, tempfile
    gen = f"{A}/models/gen"
    os.makedirs(gen, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="animais_")
    if FORCE or not (os.path.exists(f"{gen}/cat.glb") and os.path.exists(f"{gen}/dog.glb")):
        z = zipfile.ZipFile(io.BytesIO(get("https://opengameart.org/sites/default/files/Animal%20Pack%20Vol.2%20by%20%40Quaternius.zip")))
        z.extractall(tmp)
        blends = os.path.join(tmp, "Animal Pack Vol.2 by @Quaternius", "Blends")
        subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "smooth_animals.py"), blends, gen, "Cat", "Dog"])
    if FORCE or not os.path.exists(f"{gen}/crab.glb"):
        z = zipfile.ZipFile(io.BytesIO(get("https://opengameart.org/sites/default/files/crab_0.zip")))
        z.extractall(tmp)
        subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "convert_crab.py"), os.path.join(tmp, "crab", "crab.blend"), f"{gen}/crab.glb"])

def generated_props():
    """Reconstrói todos os grupos Blender/bpy necessários após clone limpo.

    Os arquivos de assets/models/gen/ são ignorados pelo Git. Gerar só o
    primeiro grupo antigo deixava de fora frutas, negócios e Grand Hotel.
    Rodar após baixar texturas evita exportar GLBs sem materiais/texturas.
    """
    groups = [
        ("gen_whale_and_sailship.py", ("humpback_whale", "pirate_sailship")),
        ("import_closed_basket.py", ("wicker_basket_closed",)),
        ("gen_coastal_traffic.py", ("coastal_yacht", "coastal_cruise")),
        ("gen_counter_details.py", ("kiosk_counter_details",)),
        ("gen_kiosk_facade.py", ("kiosk_facade", "kiosk_neon_trim", "kiosk_roof", "kiosk_workbench", "kiosk_blender")),
        ("gen_kiosk_service.py", ("service_fridge", "service_fridge_door", "service_food_cabinet", "service_register")),
        ("gen_dishes.py", ("dish_petiscos", "dish_tapioca", "dish_pastel", "dish_acai", "dish_moqueca", "dish_batida")),
        ("gen_beach_props.py", ("towel", "sandcastle", "lounger")),
        ("gen_code_props.py", ("tiki_torch", "win_shutters", "trellis_planter", "newsstand", "boat_mast")),
        ("gen_business.py", ("biz_gelato", "biz_canopy", "biz_food_truck", "biz_barrier")),
        ("gen_hotel.py", ("hotel_tower", "hotel_restaurant", "water_slide")),
        ("gen_food.py", ("coconut_green", "coconut_open", "pineapple", "orange",
                         "frappe", "cup_plastic", "glass_juice", "cocktail", "campfire_logs",
                         "beach_flag", "beach_spade", "boat_hull")),
    ]
    gen = os.path.join(A, "models", "gen")
    os.makedirs(gen, exist_ok=True)
    for script, expected in groups:
        missing = [name for name in expected if not os.path.isfile(os.path.join(gen, name + ".glb"))]
        if FORCE or missing:
            print("gerando modelos Blender:", script, "(faltando:", ", ".join(missing) or "force", ")")
            subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", script)], cwd=ROOT)
        still_missing = [name for name in expected if not os.path.isfile(os.path.join(gen, name + ".glb"))]
        if still_missing:
            raise RuntimeError("%s não gerou: %s" % (script, ", ".join(still_missing)))


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

def kenney_smoke():
    """Sprite de fumaça (Kenney Smoke Particles, CC0) -> assets/tex/smoke_puff.png (RGBA 256 px)."""
    dst = f"{A}/tex/smoke_puff.png"
    if os.path.exists(dst) and not FORCE:
        return
    import zipfile, io
    from PIL import Image
    z = zipfile.ZipFile(io.BytesIO(get("https://kenney.nl/media/pages/assets/smoke-particles/23249a0d35-1677695171/kenney_smoke-particles.zip")))
    im = Image.open(io.BytesIO(z.read("PNG/White puff/whitePuff12.png"))).convert("RGBA")
    im.thumbnail((256, 256))
    im.save(dst)
    print("kenney smoke ok")

def footstep_audio():
    """Kenney Impact Sounds 1.0 (CC0): pisadas curtas, cinco variantes por piso."""
    names = [f"footstep_{surface}_{i:03d}.ogg"
             for surface in ("carpet", "concrete", "wood") for i in range(5)]
    if not FORCE and all(os.path.exists(f"{A}/audio/{n}") for n in names):
        return
    import zipfile, io
    url = "https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip"
    z = zipfile.ZipFile(io.BytesIO(get(url)))
    os.makedirs(f"{A}/audio", exist_ok=True)
    for name in names:
        with open(f"{A}/audio/{name}", "wb") as f:
            f.write(z.read("Audio/" + name))
    with open(f"{A}/audio/KENNEY_IMPACT_LICENSE.txt", "wb") as f:
        f.write(z.read("License.txt"))
    print("kenney footsteps ok")

def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
    with ThreadPoolExecutor(6) as ex:
        futs = []
        if only in ("", "audio"):
            if not all(os.path.isfile(os.path.join(A,"audio","kiosk_"+n+".wav")) for n in ("fridge","pickup","prepare","ready","cash")):
                subprocess.check_call([sys.executable,os.path.join(ROOT,"tools","gen_kiosk_soft_audio.py")],cwd=ROOT)
            futs.append(ex.submit(footstep_audio))
        if only in ("", "tex"):
            futs += [ex.submit(texture, s) for s in TEXTURES]
            futs += [ex.submit(ambientcg, k, v) for k, v in AMBIENTCG.items()]
        if only in ("", "models"):
            if not os.path.isfile(os.path.join(A, "models", "clothing", "outfit_male.glb")) or not os.path.isfile(os.path.join(A, "models", "clothing", "outfit_female.glb")):
                subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "fetch_compatible_outfits.py")], cwd=ROOT)
                subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "gen_compatible_clothing.py")], cwd=ROOT)
            futs += [ex.submit(model, s, "1k", "models", True) for s in MODELS + MODELS_EXTRA]
            futs += [ex.submit(model, s, "2k", "models_hd") for s in MODELS + MODELS_EXTRA + MODELS_HD_ONLY]
            futs += [ex.submit(kenney, u, n) for u, n in KENNEY.items()]
            futs.append(ex.submit(kenney_smoke))
            futs.append(ex.submit(quaternius_nature))
            futs.append(ex.submit(universal_base_characters))
            futs.append(ex.submit(animals_gen))
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
    if only in ("", "models"):
        generated_props()
    for need in ("assets/models/ual/guest.glb", "assets/audio/music_bossa.ogg"):
        if not os.path.exists(os.path.join(ROOT, need)):
            print("AVISO: faltando", need, "(vem no repositório; veja CREDITS.md)")
    print("PRONTO" if errs == 0 else f"TERMINOU COM {errs} ERRO(S)")
    print("Abra o projeto no Godot 4.5.1 (ele importa os assets na primeira abertura).")
    sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()

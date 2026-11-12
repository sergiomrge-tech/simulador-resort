"""Kiosk surfaces with real texture and wear (09/11, Sergio: "quiosque n tem textura, tudo liso, corrigir isso, tudo
precisa ter sinais de desgaste").

The kiosk came from Godot as one mesh per material (World_1215..1227, all at the kiosk origin); most of those materials
were a flat colour (facade_ivory, facade_paint, counter_neutral_gray, the tiles, the steel...) and the two wood ones had
only a colour map. Each mesh now gets a world-aligned PBR material (mare_materials._custom_pbr, Poly Haven CC0 maps:
old_planks_02, distressed_painted_planks, dark_planks, peeling_painted_wall, rough_linen) recoloured to the kiosk's
own colours, with wear in the maps (chipped paint showing the wood under it, grain, cracks in the glaze) and grime low
on every surface (splashes and dirt near the floor). PIE stopped; saves the meshes.
  u.py hud module "mare_kiosk_wear.run|"        (all)    "mare_kiosk_wear.run|World_1222"   (one)
  u.py hud module "mare_kiosk_wear.revert|"     (back to the exported materials)
"""
import importlib
import json

import unreal

LUM = 'float l=dot(A.rgb,float3(.2126,.7152,.0722)); '
# dirt and splashes low on every surface (the kiosk floor is at z ~10 cm)
GRIME = 'float grime=1-.26*(1-smoothstep(12.0,85.0,P.z)); '
# where the painted planks lose their paint (the map's rust-coloured spots: red above green)
CHIP = 'float chip=saturate((A.r-A.g)*7.0); '

# mesh -> (material, Poly Haven slug, tile size cm, colour code, constant roughness or None for the map)
KIOSK = {
    # back wall planks and posts: weathered planks, warm teak tone
    'World_1219': ('M_KioskTeak', 'old_planks_02', 180, LUM + GRIME + 'return A.rgb*float3(1.55,1.05,.68)*grime;', None),
    # teal frame and kitchen cabinet: painted planks, paint chipped to the wood
    'World_1222': ('M_KioskTealPaint', 'distressed_painted_planks', 160, LUM + GRIME + CHIP +
                   'float3 teal=float3(.09,.40,.38)*clamp(l/.42,.75,1.2); float3 bare=float3(.45,.33,.22)*(.7+l); return lerp(teal,bare,chip)*grime;', None),
    # cream shelf: the same paint in cream
    'World_1221': ('M_KioskCreamPaint', 'distressed_painted_planks', 140, LUM + GRIME + CHIP +
                   'float3 cream=float3(.86,.76,.58)*clamp(l/.42,.8,1.15); float3 bare=float3(.55,.40,.26)*(.7+l); return lerp(cream,bare,chip*.8)*grime;', None),
    # dark wood (counter sides, beams)
    'World_1218': ('M_KioskShadowWood', 'dark_planks', 160, LUM + GRIME + 'return A.rgb*float3(.8,.62,.48)*grime;', None),
    # counter top and front: dark oak planks, worn
    'World_1217': ('M_KioskCounterOak', 'dark_planks', 140, LUM + GRIME + 'return A.rgb*float3(.9,.66,.5)*grime;', None),
    # rope bands on the posts
    'World_1220': ('M_KioskRope', 'rough_linen', 40, LUM + 'return float3(.62,.5,.32)*(.75+.5*l);', None),
    # light grey paint (hood, fridge body): paint over plaster, cracked and flaking
    'World_1215': ('M_KioskGreyPaint', 'peeling_painted_wall', 150, LUM + GRIME +
                   'float paint=saturate((A.r-A.g)*5.0); float3 grey=float3(.74,.74,.72)*clamp(l/.5,.85,1.1); float3 under=float3(.56,.55,.52)*(.8+.4*l); return lerp(under,grey,paint)*grime;', None),
    # stove top steel: brushed streaks and smudges, almost flat relief
    'World_1227': ('M_KioskSteel', 'dark_planks', 900, LUM +
                   'float s=.5+.5*sin(P.x*1.7+sin(P.y*.31)*3.0); float smudge=saturate((l-.3)*2.0); return float3(.60,.61,.62)*(.84+.08*s+.12*smudge);', .32),
    # glazed tiles and grout: fine crazing of old glaze, darker low down
    'World_1226': ('M_KioskTileIvory', 'peeling_painted_wall', 300, LUM + GRIME + 'return float3(.88,.84,.74)*(.95+.12*(l-.45))*grime;', .3),
    'World_1225': ('M_KioskTileSand', 'peeling_painted_wall', 300, LUM + GRIME + 'return float3(.84,.74,.58)*(.95+.12*(l-.45))*grime;', .32),
    'World_1224': ('M_KioskGrout', 'peeling_painted_wall', 80, LUM + 'return float3(.50,.47,.42)*(.8+.3*l);', .85),
}
ORIGINAL = {
    'World_1219': 'facade_teak', 'World_1222': 'facade_paint', 'World_1221': 'facade_ivory', 'World_1218': 'facade_shadow_wood',
    'World_1217': 'counter_dark_oak', 'World_1220': 'facade_rope', 'World_1215': 'counter_neutral_gray',
    'World_1227': 'facade_kitchen_steel', 'World_1226': 'facade_glazed_ivory', 'World_1225': 'facade_glazed_sand',
    'World_1224': 'facade_tile_grout',
}


def _mesh(name):
    return unreal.load_asset(f'/Game/World/Models/{name}/{name}/StaticMeshes/{name}')


def run(arg=''):
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    import mare_materials
    importlib.reload(mare_materials)
    out = {}
    for name, (mat_name, slug, size, code, rough) in KIOSK.items():
        if arg and arg != name:
            continue
        path = mare_materials._custom_pbr(mat_name, slug, float(size), code, rough_const=rough)
        mesh = _mesh(name)
        mesh.set_material(0, unreal.load_asset(path))
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        out[name] = path
    return json.dumps(out)


def revert(arg=''):
    out = {}
    for name, old in ORIGINAL.items():
        if arg and arg != name:
            continue
        mesh = _mesh(name)
        mat = unreal.load_asset(f'/Game/World/Models/{name}/{name}/Materials/{old}')
        if mat:
            mesh.set_material(0, mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
            out[name] = mat.get_path_name()
    return json.dumps(out)


# Kitchen pieces modelled apart (fridge, pastry shelf, enamel cabinet and stove, hood): flat-colour glTF materials.
# Each keeps its own colour (BaseColorFactor) and gets wear: metal -> brushed streaks and smudges; paint/enamel ->
# chips showing the material under it and grime low down. Textured materials (wood, food) are left alone.
KITCHEN = [f'World_{n}' for n in list(range(2485, 2507)) + list(range(2508, 2541)) + list(range(2541, 2549))]
PAINT = LUM + GRIME + CHIP + 'float3 base=T*clamp(l/.42,.84,1.12); float3 bare=float3(.40,.35,.30)*(.7+l); return lerp(base,bare,chip*.55)*grime;'
# enamel and painted metal (fridge, cabinet): the peeling-paint map has no plank seams; where its paint is missing
# (grey plaster in the map) the darker metal under the enamel shows
PAINT_SMOOTH = LUM + GRIME + 'float paint=saturate((A.r-A.g)*5.0); float3 base=T*clamp(l/.5,.88,1.1); float3 under=float3(.30,.30,.29)*(.8+.4*l); return lerp(under,base,.45+.55*paint)*grime;'
WOOD_KEYS = ('MA_04bda993', 'MA_b5a052a1')   # pastry shelf: painted wood, keeps the painted planks
METAL = LUM + GRIME + 'float s=.5+.5*sin(P.x*1.7+sin(P.y*.31)*3.0); float smudge=saturate((l-.3)*2.0); return T*(.84+.08*s+.12*smudge)*grime;'


def _factors(mat):
    try:
        c = mat.get_vector_parameter_value('BaseColorFactor')
        m = mat.get_scalar_parameter_value('MetallicFactor')
        r = mat.get_scalar_parameter_value('RoughnessFactor')
    except Exception:
        return None
    return (c.r, c.g, c.b), m, r


def _has_texture(mat):
    try:
        return bool(mat.get_texture_parameter_value('BaseColorTexture')) and 'T_White' not in mat.get_texture_parameter_value('BaseColorTexture').get_name()
    except Exception:
        return True


def kitchen(arg=''):
    """Second pass: the kitchen pieces modelled apart. arg 'dry' lists what would change."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    import mare_materials
    importlib.reload(mare_materials)
    made, out = {}, []
    for name in KITCHEN:
        mesh = _mesh(name)
        if not mesh:
            continue
        for i, sm in enumerate(mesh.get_editor_property('static_materials')):
            mat = sm.material_interface
            if not mat or not isinstance(mat, unreal.MaterialInstanceConstant) or _has_texture(mat):
                continue
            parent = mat.get_editor_property('parent')
            if parent and 'Opaque' not in parent.get_name():   # glass (blend) and masked stay as they are
                continue
            f = _factors(mat)
            if not f:
                continue
            (r, g, b), metal, rough = f
            if mat.get_name().startswith('MA_30e6f977'):   # the cutting board already reads as wood
                continue
            lum = .2126 * r + .7152 * g + .0722 * b
            # steel exported without the metal flag (grey, smooth) and cast iron (near black) wear like metal
            metal = 1.0 if metal >= .5 or (rough <= .31 and max(r, g, b) - min(r, g, b) < .1 and lum < .6) or lum < .08 else metal
            key = mat.get_name()
            if key not in made:
                wood = key.startswith(WOOD_KEYS)
                code = ('float3 T=float3(%.4f,%.4f,%.4f); ' % (r, g, b)) + (METAL if metal > .5 else PAINT if wood else PAINT_SMOOTH)
                slug, size = ('dark_planks', 900.0) if metal > .5 else ('distressed_painted_planks', 120.0) if wood else ('peeling_painted_wall', 90.0)
                if arg == 'dry':
                    made[key] = 'dry'
                else:
                    made[key] = mare_materials._custom_pbr('M_KioskWear_' + key[3:11], slug, size, code, rough_const=max(.25, min(rough, .9)))
            out.append([name, i, key, 'metal' if metal > .5 else 'paint', [round(r, 2), round(g, 2), round(b, 2)]])
            if arg != 'dry':
                mesh.set_material(i, unreal.load_asset(made[key]))
        if arg != 'dry':
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return json.dumps({'materials': len(made), 'slots': out[:60]})


def kitchen_revert(arg=''):
    """Puts the exported glTF materials (World_n/World_n/Materials/MA_*) back on the kitchen meshes."""
    n = 0
    for name in KITCHEN:
        mesh = _mesh(name)
        if not mesh:
            continue
        folder = f'/Game/World/Models/{name}/{name}/Materials'
        mats = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(folder, False, False)]
        mats = [m for m in mats if isinstance(m, unreal.MaterialInterface)]
        changed = False
        for i, sm in enumerate(mesh.get_editor_property('static_materials')):
            cur = sm.material_interface
            if cur and cur.get_name().startswith('M_KioskWear_'):
                tag = cur.get_name()[len('M_KioskWear_'):]
                match = [m for m in mats if m.get_name()[3:11] == tag]
                if match:
                    mesh.set_material(i, match[0])
                    changed = True
        if changed:
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
            n += 1
    return json.dumps({'reverted_meshes': n})

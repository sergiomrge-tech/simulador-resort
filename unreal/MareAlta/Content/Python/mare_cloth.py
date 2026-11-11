"""Fabric on every garment of the game (11/11, Sergio: "corrigir todas as roupas do jogo, precisa ter textura de tecido").
survey(): every material used by a clothing mesh of the built MetaHumans (Clothing/ and _HiGarments), of the swimwear
folder and of the outfit folders: its base material, shading model, and which texture / scalar parameters it has
(does it already carry a weave normal or a detail map?). Written to D:/CodexTemp/cloth_survey.json. Read-only."""
import json
import unreal

ROOTS = ('/Game/People/MetaHumans', '/Game/People/Swimwear', '/Game/Outfits', '/Game/MetaOutfits')


def survey(_=''):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    bases = {}
    meshes = 0
    for root in ROOTS:
        for data in reg.get_assets_by_path(root, True):
            if str(data.asset_class_path.asset_name) != 'SkeletalMesh':
                continue
            path = str(data.package_name)
            cloth = '/Clothing/' in path or '/Swimwear/' in path or '_Outfits' in path or root in ('/Game/Outfits', '/Game/MetaOutfits')
            if not cloth or 'BodyMesh' in path or 'FaceMesh' in path:
                continue
            mesh = unreal.load_asset(path)
            meshes += 1
            for sm in mesh.materials:
                mi = sm.material_interface
                if not mi:
                    continue
                base = mi.get_base_material()
                key = base.get_path_name()
                row = bases.setdefault(key, {'users': 0, 'instances': set(), 'tex': set(), 'scalars': set(), 'example': path.split('/')[-1]})
                row['users'] += 1
                row['instances'].add(mi.get_name())
                for n in unreal.MaterialEditingLibrary.get_texture_parameter_names(base):
                    row['tex'].add(str(n))
                for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(base):
                    row['scalars'].add(str(n))
    out = {'meshes': meshes, 'bases': {k: {'users': v['users'], 'instances': len(v['instances']), 'some': sorted(v['instances'])[:4],
                                           'tex': sorted(v['tex']), 'scalars': sorted(v['scalars'])[:40], 'example': v['example']} for k, v in bases.items()}}
    open('D:/CodexTemp/cloth_survey.json', 'w', encoding='utf-8').write(json.dumps(out, indent=1))
    return json.dumps({'meshes': meshes, 'bases': {k.split('/')[-1]: v['users'] for k, v in out['bases'].items()}})


def detail(_=''):
    """For M_fabric_simpler instances: the values of the weave parameters (is the detail normal on, how strong)."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    mel = unreal.MaterialEditingLibrary
    seen, out = set(), []
    for data in reg.get_assets_by_path('/Game/People/MetaHumans', True):
        if str(data.asset_class_path.asset_name) != 'MaterialInstanceConstant':
            continue
        mi = unreal.load_asset(str(data.package_name))
        base = mi.get_base_material()
        if not base or base.get_name() != 'M_fabric_simpler' or mi.get_name() in seen:
            continue
        seen.add(mi.get_name())
        row = {'mi': mi.get_name()}
        for n in mel.get_scalar_parameter_names(base):
            s = str(n)
            if 'Detail' in s or 'detail' in s or 'Fuzz' in s or 'Rough' in s or 'Wrinkle' in s:
                row[s] = round(mel.get_material_instance_scalar_parameter_value(mi, n), 3)
        t = mel.get_material_instance_texture_parameter_value(mi, 'detailTex_normal')
        row['detail_tex'] = t.get_name() if t else None
        out.append(row)
        if len(out) >= 4:
            break
    return json.dumps(out)


SWIM = '/Game/People/Swimwear'


def swim_fabric(_=''):
    """M_MH_Swim (every swimsuit, beach top, board shorts, cover-up and shoe made by tools/ue58/gen_mh_swimwear.py /
    gen_mh_shoes.py: 48 meshes) was a flat colour. Rebuilt IN PLACE (the meshes keep pointing at it) as woven cloth:
    the plain weave of Poly Haven fabric_pattern_07 (CC0; normal + roughness) projected from the pre-skinned position
    (the garments have no UVs), one 10 cm tile; the threads shade the Tint a little lighter and darker, the normal map
    gives them relief, the cloth is matt. Params unchanged: Tint, Roughness."""
    mel = unreal.MaterialEditingLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tex = {}
    for kind in ('nor', 'rough'):
        path = f'{SWIM}/T_Weave_{kind}'
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            task = unreal.AssetImportTask()
            task.filename = f'D:/Assets/PolyHaven/fabric_pattern_07/fabric_pattern_07_{kind}_1k.jpg'
            task.destination_path = SWIM
            task.destination_name = f'T_Weave_{kind}'
            task.automated = True
            task.replace_existing = True
            task.save = True
            tools.import_asset_tasks([task])
        t = unreal.load_asset(path)
        t.set_editor_property('srgb', False)
        if kind == 'nor':
            t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        unreal.EditorAssetLibrary.save_loaded_asset(t, False)
        tex[kind] = t
    mat = unreal.load_asset(f'{SWIM}/M_MH_Swim')
    mel.delete_all_material_expressions(mat)

    def custom(code, out, names, x, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
        e.set_editor_property('output_type', out)
        e.set_editor_property('code', code)
        ins = []
        for name in names:
            i = unreal.CustomInput()
            i.set_editor_property('input_name', name)
            ins.append(i)
        e.set_editor_property('inputs', ins)
        return e
    pos = mel.create_material_expression(mat, unreal.MaterialExpressionPreSkinnedPosition, -1300, 0)
    nrm = mel.create_material_expression(mat, unreal.MaterialExpressionPreSkinnedNormal, -1300, 200)
    ip = mel.create_material_expression(mat, unreal.MaterialExpressionVertexInterpolator, -1100, 0)
    inn = mel.create_material_expression(mat, unreal.MaterialExpressionVertexInterpolator, -1100, 200)
    mel.connect_material_expressions(pos, '', ip, '')
    mel.connect_material_expressions(nrm, '', inn, '')
    uv = custom('float3 a = abs(N); float2 u = a.z > max(a.x, a.y) ? P.xy : (a.y > a.x ? P.xz : P.yz); return u / 10.0;',
                unreal.CustomMaterialOutputType.CMOT_FLOAT2, ('P', 'N'), -900, 0)
    mel.connect_material_expressions(ip, '', uv, 'P')
    mel.connect_material_expressions(inn, '', uv, 'N')

    def sample(t, y, sampler):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -600, y)
        e.set_editor_property('texture', t)
        e.set_editor_property('sampler_type', sampler)
        mel.connect_material_expressions(uv, '', e, 'UVs')
        return e
    n = sample(tex['nor'], 260, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    r = sample(tex['rough'], 520, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -600, -260)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', unreal.LinearColor(.75, .08, .14, 1))
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -600, 780)
    rough.set_editor_property('parameter_name', 'Roughness')
    rough.set_editor_property('default_value', .55)
    # the roughness map runs .49 .. .76 across the threads: +-14 % of tone, and the cloth never gets glossier than .7
    shade = custom('float l = saturate((D.g - .49) / .27); return T * lerp(.84, 1.14, l);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('D', 'T'), -250, -100)
    mel.connect_material_expressions(r, 'RGB', shade, 'D')
    mel.connect_material_expressions(tint, '', shade, 'T')
    rr = custom('return saturate(max(R, .7) + (D.g - .64) * .5);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('R', 'D'), -250, 600)
    mel.connect_material_expressions(rough, '', rr, 'R')
    mel.connect_material_expressions(r, 'RGB', rr, 'D')
    mel.connect_material_property(shade, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    errors = mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return json.dumps({'errors': [str(e) for e in errors] if errors else []})


def weave(arg='dry'):
    """The built garments of the MetaHumans (M_fabric_simpler instances: Epic's default shirt and shorts, the free Fab
    outfits) already carry a micro weave normal, but at a tiling of 220-380 with strength .2-.5 it cannot be seen at
    game distance. Every instance: tiling down to 95 (threads about three times larger), normal strength up to at
    least 1.3 (both layers), tone variation of the weave at least .8. And the Fab 'M_MasterMaterial' outfits: normal
    intensity at least 1.5. 'apply' saves the instances."""
    apply = arg.strip() == 'apply'
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    mel = unreal.MaterialEditingLibrary
    want = {'DetailTex_UVTtiling': ('max', 95.0), 'B_DetailTex_UVTtiling': ('max', 95.0), 'DetailTex_NormalStrength': ('min', 1.3),
            'B_DetailTex_NormalStrength': ('min', 1.3), 'DetailTex_VariationStrength': ('min', .8)}
    n = {'fabric': 0, 'master': 0, 'changed': 0}
    for root in ('/Game/People/MetaHumans', '/Game/Outfits', '/Game/MetaOutfits'):
        for data in reg.get_assets_by_path(root, True):
            if str(data.asset_class_path.asset_name) != 'MaterialInstanceConstant':
                continue
            mi = unreal.load_asset(str(data.package_name))
            base = mi.get_base_material()
            if not base:
                continue
            dirty = False
            if base.get_name() == 'M_fabric_simpler':
                n['fabric'] += 1
                for name, (rule, v) in want.items():
                    cur = mel.get_material_instance_scalar_parameter_value(mi, name)
                    new = min(cur, v) if rule == 'max' else max(cur, v)
                    if abs(new - cur) > 1e-4:
                        dirty = True
                        if apply:
                            mel.set_material_instance_scalar_parameter_value(mi, name, new)
            elif base.get_name() == 'M_MasterMaterial':
                n['master'] += 1
                cur = mel.get_material_instance_scalar_parameter_value(mi, 'NormalIntensity')
                if cur < 1.5:
                    dirty = True
                    if apply:
                        mel.set_material_instance_scalar_parameter_value(mi, 'NormalIntensity', 1.5)
            if dirty:
                n['changed'] += 1
                if apply:
                    mel.update_material_instance(mi)
                    unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
    return json.dumps(n)

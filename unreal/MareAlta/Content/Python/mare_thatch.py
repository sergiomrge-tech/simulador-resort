"""Thatch roof of the Bar do Coqueiro (B7, 09/11): the roof exported from Godot carried one 1024 px thatch picture
stretched over a whole face (~5 m: blurry and smeared from close by) and the hip ridges had radial UVs (the strands
swirled on their ends). M_ThatchRoof projects the same CC0 Poly Haven thatch (thatch_roof_angled, 1k) every ~1.2 m
along each face, with the strands running down the slope (u across the face, v with the height), and replaces the
material on every exported model that used that picture. PIE stopped (assets saved)."""
import json
import unreal

import mare_materials as mm

MEL = unreal.MaterialEditingLibrary
PICTURE = 'T_b074e124e572d1a382af15ba'   # the exported thatch picture (same name in each World_* model folder)
PATH = '/Game/Custom/Materials/M_ThatchRoof'


def material():
    mat = unreal.load_asset(PATH)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_ThatchRoof', '/Game/Custom/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    mat.set_editor_property('two_sided', True)
    diff = mm.expression(mat, unreal.MaterialExpressionTextureObject, texture=mm._custom_texture('thatch_roof_angled_diff_1k.jpg'))
    rough = mm.expression(mat, unreal.MaterialExpressionTextureObject, texture=mm._custom_texture('thatch_roof_angled_rough_1k.jpg', linear=True))
    pos = mm.expression(mat, unreal.MaterialExpressionWorldPosition)
    nrm = mm.expression(mat, unreal.MaterialExpressionVertexNormalWS)
    # Face-aligned UV: across the face along the horizontal axis it does not face, down the slope with the height
    # (x1.5 for the ~40 degree pitch, so the strands keep their proportions); 120 cm per tile.
    uv = mm.custom(mat, 'float3 n=abs(N); float2 uv=n.x>n.y?float2(P.y,-P.z*1.5):float2(P.x,-P.z*1.5); return uv/120.0;',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'P': pos, 'N': nrm})
    color = mm.custom(mat, 'float3 c=Texture2DSample(Tex,TexSampler,UV).rgb; float2 c2=UV*float2(.37,.23); '
                           'float3 b=Texture2DSample(Tex,TexSampler,c2+float2(.31,.57)).rgb; '
                           'c=lerp(c,c*(.85+.3*dot(b,float3(.33,.33,.33))),.6); '
                           'return c*float3(1.32,1.05,.66);',   # golden straw, keeping the strands (the picture is grey)
                      unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Tex': diff, 'UV': uv})
    rgh = mm.custom(mat, 'return lerp(.8,1,Texture2DSample(Tex,TexSampler,UV).r);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'Tex': rough, 'UV': uv})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rgh, '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def apply(arg=''):
    """Build M_ThatchRoof and put it on every slot of the exported models whose material used the thatch picture.
    arg 'dry' lists them only."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    dry = arg == 'dry'
    mat = None if dry else material()
    done = []
    for path in unreal.EditorAssetLibrary.list_assets('/Game/World/Models', recursive=True):
        if '/StaticMeshes/' not in path:
            continue
        mesh = unreal.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        mats = mesh.get_editor_property('static_materials')
        changed = []
        for i, sm in enumerate(mats):
            mi = sm.material_interface
            if isinstance(mi, unreal.MaterialInstance) and any(
                    p.parameter_value and PICTURE in p.parameter_value.get_name() for p in mi.get_editor_property('texture_parameter_values')):
                changed.append(i)
                if not dry:
                    mesh.set_material(i, mat)
        if changed:
            done.append([path.split('/')[-1].split('.')[0], changed])
            if not dry:
                unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return json.dumps(done)

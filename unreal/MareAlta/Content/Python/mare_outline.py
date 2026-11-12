"""Outline of the focused target (08/11, Resort Simulator reference tip 1: the bed the player looks at gets a coloured
edge). M_PP_Outline is a post-process material on the hero's camera (MareOutline.cpp adds it): pixels just outside a
mesh drawn into custom depth get a warm, softly pulsing edge. Editor, PIE stopped: mare_hud module "mare_outline.run|"."""
import unreal
import mare_materials as mm


def run(arg=''):
    mat = mm.material('M_PP_Outline')
    mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_POST_PROCESS)
    mat.set_editor_property('blendable_location', unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    depth = mm.expression(mat, unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_CUSTOM_DEPTH)
    color = mm.expression(mat, unreal.MaterialExpressionSceneTexture, scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    screen = mm.expression(mat, unreal.MaterialExpressionScreenPosition)
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    code = (
        'float2 uv = ViewportUVToBufferUV(UV);'
        'float2 px = View.BufferSizeAndInvSize.zw;'
        'float far = 1e6;'
        'float c = SceneTextureLookup(uv, 13, false).r;'
        'float edge = 0;'
        'if (c > far) {'
        ' for (int i = 0; i < 12; i++) {'
        '  float a = i * 0.5235988;'
        '  float2 o = float2(cos(a), sin(a)) * px * 3.0;'
        '  if (SceneTextureLookup(uv + o, 13, false).r < far) edge = 1;'
        ' }'
        '}'
        'float pulse = 0.8 + 0.2 * sin(T * 4.0);'
        'if (DEBUG > 1) return C.rgb * float3(1, 0.3, 0.3);'
        'if (DEBUG > 0) return lerp(C.rgb, float3(1, 0, 0), (c < far) * 0.6);'
        'return lerp(C.rgb, float3(1.0, 0.86, 0.36), edge * pulse * 0.9 + D.r * 0);'
    )
    code = code.replace('DEBUG', {'debug': '1', 'debug2': '2'}.get(arg, '0'))
    node = mm.custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                     {'UV': screen, 'C': color, 'T': time, 'D': depth})
    unreal.MaterialEditingLibrary.connect_material_property(node, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return 'ok ' + str(errors)

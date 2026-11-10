"""2D title screen art (08/11, Sergio: "tela inicial em 2d", "use o canva para fazer algo bastante detalhado"): the island
painting and the logo made in Canva (sources in SourceArt/UI/Title; the logo's painted checkerboard was cut out with a
script) imported as UI textures into /Game/UI/Title (always cooked, DefaultGame.ini). title.json "art"/"logo_image"
name them. Editor, PIE stopped: mare_hud module "mare_title_art.run|"."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DEST = '/Game/UI/Title'


def run(_=''):
    out = {}
    for name in ['T_TitleArt', 'T_TitleLogo']:
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'SourceArt/UI/Title' / (name + '.png'))
        task.destination_path = DEST
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f'{DEST}/{name}')
        if not isinstance(tex, unreal.Texture2D):
            raise RuntimeError('import failed ' + name)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('never_stream', True)
        tex.set_editor_property('srgb', True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[name] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return json.dumps(out)


def fx(_=''):
    """HUD feedback sprites (08/11, reference tip 4): coin and soft puff from SourceArt/UI/Fx -> /Game/UI/Icons (cooked)."""
    out = {}
    for name in ['T_Fx_Coin', 'T_Fx_Soft']:
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'SourceArt/UI/Fx' / (name + '.png'))
        task.destination_path = '/Game/UI/Icons'
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset('/Game/UI/Icons/' + name)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property('never_stream', True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[name] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return json.dumps(out)


def material25d(_=''):
    """2.5D title (10/11, Sergio: "a tela em 2.5d faça você"): imports the depth map of the painting
    (SourceArt/UI/Title/T_TitleDepth.png, tools/ue58/gen_title_depth.py; white = near) and builds the UI material
    /Game/UI/Title/M_Title25D: every pixel of the painting slides by Shift x (its depth - Focus), so the palm in front,
    the boat, the village and the sky move at different speeds as the title sways (SMareMainMenu sets Shift every frame;
    title.json "art_material"). Zoom hides the edges the slide would uncover. Editor, PIE stopped."""
    import mare_materials as mm
    MEL = unreal.MaterialEditingLibrary
    task = unreal.AssetImportTask()
    task.filename = str(ROOT / 'SourceArt/UI/Title/T_TitleDepth.png')
    task.destination_path = DEST
    task.destination_name = 'T_TitleDepth'
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    depth = unreal.load_asset(f'{DEST}/T_TitleDepth')
    if not isinstance(depth, unreal.Texture2D):
        raise RuntimeError('depth import failed')
    depth.set_editor_property('srgb', False)
    depth.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_GRAYSCALE)
    depth.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    depth.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    depth.set_editor_property('never_stream', True)
    unreal.EditorAssetLibrary.save_loaded_asset(depth, False)
    art = unreal.load_asset(f'{DEST}/T_TitleArt')
    name = 'M_Title25D'
    mat = unreal.load_asset(f'{DEST}/{name}')
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
    uv = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate)
    shift = mm.expression(mat, unreal.MaterialExpressionVectorParameter, parameter_name='Shift', default_value=unreal.LinearColor(0, 0, 0, 0))
    zoom = mm.expression(mat, unreal.MaterialExpressionScalarParameter, parameter_name='Zoom', default_value=1.035)
    focus = mm.expression(mat, unreal.MaterialExpressionScalarParameter, parameter_name='Focus', default_value=.42)
    dobj = mm.expression(mat, unreal.MaterialExpressionTextureObject, texture=depth)
    # three steps towards the pixel whose own depth lands here: sharper edges than a single look-up
    code = ('float2 uv=(UV-0.5)/Zoom+0.5; float2 p=uv; '
            'for(int i=0;i<3;i++){float d=Texture2DSampleLevel(Tex,TexSampler,p,0).r; p=uv-Shift.xy*(d-Focus);} return p;')
    warp = mm.custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': uv, 'Shift': shift, 'Zoom': zoom, 'Focus': focus, 'Tex': dobj})
    sample = mm.expression(mat, unreal.MaterialExpressionTextureSample, texture=art, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    mm.connect(warp, '', sample, 'UVs')
    MEL.connect_material_property(sample, 'RGB', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return json.dumps({'material': mat.get_path_name(), 'depth': [depth.blueprint_get_size_x(), depth.blueprint_get_size_y()]})

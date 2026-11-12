import unreal, json, traceback
out = r'D:/CodexTemp/ue58-calibration.json'
try:
    task=unreal.AssetImportTask()
    task.filename=r'D:/Projetos/MareAltaUE58/unreal/MareAlta/SourceArt/World/Calibration.glb'
    task.destination_path='/Game/Migration/Calibration'
    task.automated=True
    task.replace_existing=True
    task.save=True
    pipeline=unreal.InterchangeGenericAssetsPipeline()
    pipeline.mesh_pipeline.combine_static_meshes_behavior=unreal.InterchangeCombineStaticMeshesBehavior.ALL
    pipeline.common_meshes_properties.bake_meshes=True
    task.options=pipeline
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    data=[]
    for path in unreal.EditorAssetLibrary.list_assets('/Game/Migration/Calibration'):
        asset=unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset,unreal.StaticMesh):
            bounds=asset.get_bounds()
            data.append({'path':path,'center':str(bounds.origin),'extent':str(bounds.box_extent)})
    with open(out,'w') as f:json.dump(data,f,indent=2)
    unreal.log('MARE_CALIBRATION_PASS '+str(data))
except Exception:
    with open(out,'w') as f:f.write(traceback.format_exc())
    unreal.log_error(traceback.format_exc())
unreal.SystemLibrary.quit_editor()

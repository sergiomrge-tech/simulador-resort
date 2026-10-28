"""Import the game's existing attributed/original sounds as native SoundWave assets."""
import unreal,json
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve()
def import_radio():
    data=ROOT/'Content/Data/audio.json'
    report=json.loads(data.read_text(encoding='utf-8-sig'))
    report=[row for row in report if row['id'] not in ('music_bossa','music_relax')]
    for name in ('music_bossa','music_relax'):
        path='/Game/Audio/'+name;wave=unreal.load_asset(path)
        if not wave:
            task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/Audio'/(name+'.wav'));task.destination_path='/Game/Audio';task.destination_name=name;task.automated=True;task.save=True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);wave=unreal.load_asset(path)
        if not isinstance(wave,unreal.SoundWave):raise RuntimeError('Radio import failed: '+name)
        wave.set_editor_property('looping',True);wave.set_editor_property('virtualization_mode',unreal.VirtualizationMode.PLAY_WHEN_SILENT)
        unreal.EditorAssetLibrary.save_loaded_asset(wave,False)
        report.append({'id':name,'path':wave.get_path_name(),'duration':wave.get_editor_property('duration'),'loop':True})
    data.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return {'sounds':len(report),'radio':['reggae_praia','music_bossa','music_relax']}
def build():
    report=[]
    loops={'reggae_praia','music_bossa','music_relax','ocean_loop','wind_loop','rain_loop','crickets_loop','leaves_soft','underwater_loop'}
    for source in sorted((ROOT/'SourceArt/Audio').glob('*.wav')):
        path='/Game/Audio/'+source.stem
        wave=unreal.load_asset(path)
        if not wave:
            task=unreal.AssetImportTask();task.filename=str(source);task.destination_path='/Game/Audio';task.destination_name=source.stem;task.automated=True;task.save=True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);wave=unreal.load_asset(path)
        if not isinstance(wave,unreal.SoundWave):raise RuntimeError('Sound import failed: '+source.stem)
        wave.set_editor_property('looping',source.stem in loops)
        if source.stem in loops:wave.set_editor_property('virtualization_mode',unreal.VirtualizationMode.PLAY_WHEN_SILENT)
        unreal.EditorAssetLibrary.save_loaded_asset(wave,False)
        report.append({'id':source.stem,'path':wave.get_path_name(),'duration':wave.get_editor_property('duration'),'loop':source.stem in loops})
    (ROOT/'Content/Data/audio.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return {'sounds':len(report),'duration':sum(s['duration'] for s in report)}

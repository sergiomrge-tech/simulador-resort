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
    loops={'reggae_praia','radio_reggae_roots','radio_calypso','radio_beach_pop','radio_havaiana','radio_havaiana_lua','radio_havaiana_onda','music_tema','music_bossa','music_relax','ocean_loop','wind_loop','rain_loop','crickets_loop','leaves_soft','underwater_loop'}
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

def import_tracks(names):
    """Import (or reimport) looping music tracks from SourceArt/Audio by name; audio.json already lists them."""
    out={}
    for name in names:
        path='/Game/Audio/'+name
        task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/Audio'/(name+'.wav'));task.destination_path='/Game/Audio'
        task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);wave=unreal.load_asset(path)
        if not isinstance(wave,unreal.SoundWave):raise RuntimeError('Music import failed: '+name)
        wave.set_editor_property('looping',True);wave.set_editor_property('virtualization_mode',unreal.VirtualizationMode.PLAY_WHEN_SILENT)
        unreal.EditorAssetLibrary.save_loaded_asset(wave,False)
        out[name]=round(wave.get_editor_property('duration'),1)
    return out

def import_radio_cc0(folder='D:/Assets/Audio/radio/wav'):
    """The CC0 radio tracks (tools/ue58/radio_prepare.py: loudness-matched WAVs, outside the repository) as looping
    SoundWaves in /Game/Audio/Radio; audio.json and radio.json list them."""
    out={}
    for source in sorted(Path(folder).glob('*.wav')):
        path='/Game/Audio/Radio/'+source.stem
        task=unreal.AssetImportTask();task.filename=str(source);task.destination_path='/Game/Audio/Radio'
        task.destination_name=source.stem;task.automated=True;task.save=True;task.replace_existing=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);wave=unreal.load_asset(path)
        if not isinstance(wave,unreal.SoundWave):raise RuntimeError('Radio import failed: '+source.stem)
        wave.set_editor_property('looping',True);wave.set_editor_property('virtualization_mode',unreal.VirtualizationMode.PLAY_WHEN_SILENT)
        unreal.EditorAssetLibrary.save_loaded_asset(wave,False)
        out[source.stem]=round(wave.get_editor_property('duration'),1)
    return out

"""Controlled navigation preparation for the existing authored village routes."""
from pathlib import Path
import json
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()


def world_and_nav():
    editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():raise RuntimeError('Stop PIE before editing navigation')
    world=editor.get_editor_world()
    nav=next((n for n in unreal.ObjectIterator(unreal.NavigationSystemV1) if n.get_outer()==world),None)
    if not nav:raise RuntimeError('Existing navigation system missing; do not rebuild the world')
    return world,nav


def prepare():
    world,nav=world_and_nav()
    volumes=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.NavMeshBoundsVolume)
    if len(volumes)!=1:raise RuntimeError('Expected the existing single navigation bounds volume')
    volume=volumes[0];before=volume.get_actor_bounds(False)
    volume.set_actor_location(unreal.Vector(5000,1800,250),False,False)
    volume.set_actor_scale3d(unreal.Vector(65,60,10))
    nav.on_navigation_bounds_updated(volume)
    unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():raise RuntimeError('Level not saved')
    return {'before':str(before),'after':str(volume.get_actor_bounds(False)),'rebuild_requested':True,'validated':False}


def validate():
    world,nav=world_and_nav();source=json.loads((ROOT/'Content/Data/world.json').read_text(encoding='utf-8'))
    def project(p):
        requested=unreal.Vector(p[0]*100,p[2]*100,p[1]*100+50)
        result=nav.project_point_to_navigation(world,requested,None,None,unreal.Vector(160,160,180))
        # This API returns Vector; a zero result is failure for these authored routes.
        if result is None or result.is_nearly_zero():return None
        return result
    def xyz(p):return [p.x,p.y,p.z]
    routes=[];issues=[]
    for index,points in enumerate(source['paths']):
        projected=[project(p) for p in points];segments=[]
        if any(p is None for p in projected):
            issues.append({'route':index,'unprojected_points':[points[i] for i,p in enumerate(projected) if p is None]});continue
        for start,end in zip(projected,projected[1:]):
            path=nav.find_path_to_location_synchronously(world,start,end)
            valid=bool(path and path.is_valid() and not path.is_partial());segments.append(valid)
        if not all(segments):issues.append({'route':index,'segments':segments})
        else:routes.append({'source_index':index,'points':[xyz(p) for p in projected]})
    residents=[]
    for r in source['residents']:
        point=project(r['position'])
        if point is None:issues.append({'resident':r['name'],'unprojected_position':r['position']});continue
        residents.append({'name':r['name'],'position':xyz(point),'yaw':90-r['rotation'][1]*180/3.141592653589793})
    report={'routes':routes,'residents':residents,'excluded_routes':issues,'source_routes':len(source['paths'])}
    # Partial routes are explicitly omitted, never used to teleport pedestrians.
    if len(routes)<6:raise RuntimeError('Insufficient complete routes: '+str(report))
    (ROOT/'Content/Data/village_routes.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return report

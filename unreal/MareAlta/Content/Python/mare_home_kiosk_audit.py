"""Read actual imported bounds and glass slots; no guessed pivots or global rescaling."""
import json,itertools
from pathlib import Path
import unreal
from mare_world_builder import transform
ROOT=Path(unreal.Paths.project_dir()).resolve()

def xyz(v):return [round(v.x,3),round(v.y,3),round(v.z,3)]
def run(action):
 if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():raise RuntimeError('QA profile required')
 data=ROOT/'Content/Data';w=json.loads((data/'world.json').read_text(encoding='utf-8-sig'));mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'));aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'))
 result=[]
 if action=='supports':
  world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
  actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
  for i,r in enumerate(w['instances']):
   x,y,z=r['transform']['position'];key=f"World_{r['mesh_index']:04d}";name=r['name']
   if not (35<x<40.5 and -15.5<z<-10.5 and name in ('cup_plastic','coconut_open','glass_juice','cocktail','table_plate','carved_wooden_plate','pineapple','lemon','orange','food_apple_01','food_lime_01','ceramic_vase_02','wooden_bowl_01','lambis_shell','wicker_basket_02_base')):continue
   path=mapping[aliases.get(key,key)];mesh=unreal.load_asset(path);b=mesh.get_bounds();t=transform(r['transform']);corners=[t.transform_location(b.origin+unreal.Vector(dx*b.box_extent.x,dy*b.box_extent.y,dz*b.box_extent.z)) for dx,dy,dz in itertools.product((-1,1),repeat=3)]
   base=min(v.z for v in corners);center=t.transform_location(b.origin)
   ignored=[a for a in actors if any(c.static_mesh==mesh for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent))]
   hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(center.x,center.y,base+.2),unreal.Vector(center.x,center.y,base-150),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,unreal.DrawDebugTrace.NONE)
   result.append({'row':i,'name':name,'base':base,'center':xyz(center),'support':xyz(hit.to_tuple()[5]) if hit else None,'support_actor':hit.to_tuple()[9].get_actor_label() if hit else None,'gap':round(base-hit.to_tuple()[5].z,3) if hit else None})
  Path('D:/CodexTemp/ue58-home-kiosk-fix/supports-before.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
 if action=='repair':
  from mare_materials import material,expression,MEL
  mat=material('M_ClearWindowGlass')
  mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
  mat.set_editor_property('two_sided',True);mat.set_editor_property('used_with_instanced_static_meshes',True)
  mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
  for prop,value in ((unreal.MaterialProperty.MP_BASE_COLOR,.92),(unreal.MaterialProperty.MP_ROUGHNESS,.065),(unreal.MaterialProperty.MP_SPECULAR,.5)):
   node=expression(mat,unreal.MaterialExpressionConstant,r=value);MEL.connect_material_property(node,'',prop)
  fresnel=expression(mat,unreal.MaterialExpressionFresnel,exponent=5.,base_reflect_fraction=.04)
  # Clear face-on, stronger at grazing angles: glass is legible without blue tint.
  from mare_materials import custom
  opacity=custom(mat,'return .10 + F*.48;',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'F':fresnel})
  MEL.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
  errors=list(MEL.recompile_material(mat))
  if errors:raise RuntimeError(str(errors))
  if not unreal.EditorAssetLibrary.save_loaded_asset(mat,False):raise RuntimeError('Glass not saved')
  actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
  panes=[]
  for a in actors:
   for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
    if not c.static_mesh:continue
    for j,slot in enumerate(c.static_mesh.static_materials):
     if slot.material_interface and 'a3573534a1ac032b2a83b215' in slot.material_interface.get_name():
      c.set_material(j,mat);c.set_editor_property('disallow_nanite',True);c.set_editor_property('cast_shadow',False)
      panes.append({'actor':a.get_actor_label(),'count':c.get_instance_count(),'slot':j,'mesh':c.static_mesh.get_path_name()})
  # Corrections refer to stable manifest rows, not actor labels stripped by cooking.
  fixes_path=data/'home_kiosk_layout.json'
  fixes=json.loads(fixes_path.read_text()) if fixes_path.exists() else {'changes':[]}
  if not fixes['changes']:
   for row_id,center in ((12902,(3590,-1410)),(12903,(3590,-1195)),(12904,(3995,-1260))):
    r=w['instances'][row_id];key=f"World_{r['mesh_index']:04d}";mesh=unreal.load_asset(mapping[aliases.get(key,key)]);b=mesh.get_bounds();t=transform(r['transform']);old=t.translation
    now=t.transform_location(b.origin);offset=unreal.Vector(center[0]-now.x,center[1]-now.y,0)
    ignored=[a for a in actors if any(c.static_mesh==mesh for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent))]
    hit=unreal.SystemLibrary.line_trace_single(actors[0],unreal.Vector(center[0],center[1],145),unreal.Vector(center[0],center[1],100),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,unreal.DrawDebugTrace.NONE)
    if not hit:raise RuntimeError('No counter support for '+r['name'])
    corners=[t.transform_location(b.origin+unreal.Vector(dx*b.box_extent.x,dy*b.box_extent.y,dz*b.box_extent.z)) for dx,dy,dz in itertools.product((-1,1),repeat=3)]
    offset.z=hit.to_tuple()[5].z+.10-min(v.z for v in corners)
    fixes['changes'].append({'row':row_id,'name':r['name'],'mesh':mesh.get_path_name(),'old':list(r['transform']['position']),'offset_cm':xyz(offset),'support_z':hit.to_tuple()[5].z})
  changed=[]
  for f in fixes['changes']:
   row=w['instances'][f['row']];old=list(f['old']);off=unreal.Vector(*f['offset_cm']);original=transform({**row['transform'],'position':old})
   row['transform']['position']=[old[0]+off.x/100,old[1]+off.z/100,old[2]+off.y/100]
   for a in actors:
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
     if not c.static_mesh or c.static_mesh.get_path_name()!=f['mesh']:continue
     for i in range(c.get_instance_count()):
      t=c.get_instance_transform(i,True)
      if (t.translation-original.translation).length()<.05:
       t.translation=t.translation+off;c.update_instance_transform(i,t,True,True,True);changed.append(f['row'])
  fixes['glass']=panes;fixes['material']=mat.get_path_name();fixes_path.write_text(json.dumps(fixes,indent=2),encoding='utf-8')
  (data/'world.json').write_text(json.dumps(w,ensure_ascii=False,indent='	'),encoding='utf-8')
  if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():raise RuntimeError('Map not saved')
  return {'glass_instances':sum(p['count'] for p in panes),'props_moved':changed,'details':fixes}
 if action=='trace-doc':
  return {'trace':unreal.SystemLibrary.line_trace_single.__doc__,'hit':dir(unreal.HitResult)}
 if action.startswith('view:'):
  world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  name=action.split(':')[1];capture=name.endswith('-capture');name=name.removesuffix('-capture')
  views={'kiosk-back':((3800,-1370,110),(-8,90,0)),'kiosk-left':((3800,-1300,110),(-10,175,0)),'home-window':((4550,2300,110),(0,120,0)),'bed':((4570,1990,110),(-20,-165,0))}
  if capture:
   path='D:/CodexTemp/ue58-home-kiosk-fix/'+name+'-before.png'
   unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename='+path);return {'capture':path}
  pos,rot=views[name];hero=unreal.GameplayStatics.get_player_pawn(world,0);pc=unreal.GameplayStatics.get_player_controller(world,0)
  hero.character_movement.set_movement_mode(unreal.MovementMode.MOVE_FLYING);hero.set_actor_location(unreal.Vector(*pos),False,False);pc.set_control_rotation(unreal.Rotator(pitch=rot[0],yaw=rot[1],roll=0));return {'view':name}
 if action=='inspect':
  for i,r in enumerate(w['instances']):
   x,y,z=r['transform']['position'];name=r['name'];key=f"World_{r['mesh_index']:04d}"
   if not ((34.8<x<40.5 and -15.5<z<-10.5 and name in ('cup_plastic','carved_wooden_plate','glass_juice','cocktail','pineapple','lemon','orange','food_apple_01','food_lime_01','wicker_basket_02_base','ceramic_vase_02','wooden_bowl_01','lambis_shell')) or (42<x<50 and 15<z<26 and ('Bed' in name or 'window' in name.lower() or 'vidro' in name.lower()))):continue
   mesh=unreal.load_asset(mapping[aliases.get(key,key)]);b=mesh.get_bounds();t=transform(r['transform']);corners=[t.transform_location(b.origin+unreal.Vector(dx*b.box_extent.x,dy*b.box_extent.y,dz*b.box_extent.z)) for dx,dy,dz in itertools.product((-1,1),repeat=3)]
   result.append({'row':i,'name':name,'key':key,'mesh':mesh.get_path_name(),'min':[round(min(getattr(v,k) for v in corners),3) for k in ('x','y','z')],'max':[round(max(getattr(v,k) for v in corners),3) for k in ('x','y','z')],'materials':[(mesh.get_material(j).get_path_name() if mesh.get_material(j) else None) for j in range(mesh.get_num_sections(0))]})
  # Material names, including anonymously named window panes from the source scene.
  glass=[]
  for key,path in mapping.items():
   if key!=aliases.get(key,key):continue
   mesh=unreal.load_asset(path)
   if not mesh:continue
   for slot in mesh.static_materials:
    m=slot.material_interface
    if m and any(s in m.get_name().lower() for s in ('glass','vidro')):glass.append({'key':key,'mesh':path,'material':m.get_path_name()})
  result={'props':result,'glass':glass}
  Path('D:/CodexTemp/ue58-home-kiosk-fix/geometry-before.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
  return result
 raise ValueError(action)

"""Measured, editor-only graphics pass. No economy or gameplay mutations."""
import json,math,random,re
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=Path('D:/CodexTemp/ue58-graphics');OUT.mkdir(exist_ok=True)

def inspect():
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();meshes={};instances=0
 for a in actors:
  for c in a.get_components_by_class(unreal.StaticMeshComponent):
   m=c.static_mesh
   if not m:continue
   instances+=c.get_instance_count() if isinstance(c,unreal.InstancedStaticMeshComponent) else 1
   if m.get_path_name() in meshes:continue
   mats=[];unsafe=False
   for slot in m.static_materials:
    mat=slot.material_interface
    instance_blend=None
    while isinstance(mat,unreal.MaterialInstanceConstant):
     overrides=mat.get_editor_property('base_property_overrides')
     if overrides.override_blend_mode and instance_blend is None:instance_blend=str(overrides.blend_mode)
     mat=mat.get_editor_property('parent')
    if not isinstance(mat,unreal.Material):unsafe=True;continue
    blend=instance_blend or str(mat.get_editor_property('blend_mode'));masked='MASKED' in blend
    wpo=unreal.MaterialEditingLibrary.get_material_property_input_node(mat,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is not None
    unsafe |= 'BLEND_OPAQUE' not in blend or wpo
    mats.append({'path':mat.get_path_name(),'blend':blend,'wpo':wpo})
   tris=m.get_num_triangles(0);nanite=m.get_editor_property('nanite_settings').enabled
   meshes[m.get_path_name()]={'triangles':tris,'nanite':nanite,'eligible':tris>=15000 and not unsafe and '/World/Models/' in m.get_path_name(),'materials':mats}
 report={'map':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),'instances':instances,'meshes':meshes,'cvars':{n:unreal.SystemLibrary.get_console_variable_int_value(n) for n in ['r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.Nanite','r.Shadow.Virtual.Enable','r.RayTracing','r.ScreenPercentage','sg.GlobalIlluminationQuality','sg.ReflectionQuality']}}
 (OUT/'inventory-before.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return {'meshes':len(meshes),'instances':instances,'nanite_enabled':sum(r['nanite'] for r in meshes.values()),'eligible':sum(r['eligible'] for r in meshes.values()),'cvars':report['cvars']}

def pilot():
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 path='/Game/Maps/GraphicsPilot'
 if not unreal.EditorAssetLibrary.does_asset_exist(path):unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),path)
 else:level.load_level(path)
 return path

def view(name):
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
 if not world:raise RuntimeError('PIE required')
 views={'kiosk':((3800,-1200,100),(-6,-90,0)),'grove':((2800,-750,100),(-4,145,0)),'home':((4520,2120,100),(-8,25,0)),'beach':((3800,-2600,100),(-3,-90,0)),'east':((6800,-750,100),(-4,145,0)),'hotel':((-2100,3500,450),(10,90,0)),'village':((3100,1500,100),(-8,70,0)),'inland':((1000,6500,100),(-8,10,0))}
 match=re.search(r'MareSaveRoot=([^\s]+)',unreal.SystemLibrary.get_command_line())
 if not match or not match[1].startswith('D:/CodexTemp/'):raise RuntimeError('Isolated QA profile required')
 p,r=views[name];pc=unreal.GameplayStatics.get_player_controller(world,0);hero=unreal.GameplayStatics.get_player_pawn(world,0);pc.close_phone();hero.character_movement.set_movement_mode(unreal.MovementMode.MOVE_FLYING);hero.set_actor_location(unreal.Vector(*p),False,False);pc.set_control_rotation(unreal.Rotator(pitch=r[0],yaw=r[1],roll=r[2]));sim=pc.get_simulation();sim.save();state=json.loads((Path(match[1])/"slot1.json").read_text(encoding="utf-8-sig"));sim.advance_minutes(720-state["minutes"]);unreal.GameplayStatics.get_game_mode(world).set_actor_tick_enabled(False)
 for cmd in ['sg.GlobalIlluminationQuality 2','sg.ReflectionQuality 2','sg.ShadowQuality 2','sg.ViewDistanceQuality 2','t.MaxFPS 0','r.VSync 0','r.ScreenPercentage 80','r.SetRes 1280x720w','r.ProfileGPU.ShowUI 0']:unreal.SystemLibrary.execute_console_command(world,cmd)
 return name

def profile(action,label):
 if not label.replace('-','').replace('_','').isalnum():raise ValueError(label)
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
 if action=='start':unreal.SystemLibrary.execute_console_command(world,'csvprofile start')
 elif action=='capture':unreal.SystemLibrary.execute_console_command(world,f'HighResShot 1280x720 filename={OUT/label}.png')
 elif action=='stop':
  unreal.SystemLibrary.execute_console_command(world,'csvprofile stop');unreal.SystemLibrary.execute_console_command(world,'profilegpu');unreal.SystemLibrary.execute_console_command(world,f'HighResShot 1280x720 filename={OUT/label}.png')
 else:raise ValueError(action)
 return {'action':action,'label':label}

def nanite_apply():
 data=json.loads((OUT/'inventory-before.json').read_text(encoding='utf-8'));editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);changed=[]
 for path,r in data['meshes'].items():
  if not r['eligible'] or r['nanite']:continue
  mesh=unreal.load_asset(path);settings=mesh.get_editor_property('nanite_settings');settings.enabled=True
  editor.set_nanite_settings(mesh,settings,True);unreal.EditorAssetLibrary.save_loaded_asset(mesh,False);changed.append(path)
 (OUT/'nanite-enabled.json').write_text(json.dumps(changed,indent=2));return {'enabled':len(changed),'paths':changed}

def pcg_build(zone="grove"):
 if zone not in ("grove","east"):raise ValueError(zone)
 xmin,xmax=(1500,2700) if zone=="grove" else (5500,6700)
 prefix="PCG_" if zone=="grove" else "PCG_East_"
 actor_prefix="PCG Pilot · " if zone=="grove" else "PCG East · "
 from editor_toolset.toolsets.actor import ActorTools
 world=json.loads((ROOT/'Content/Data/world.json').read_text(encoding='utf-8-sig'));mapping=json.loads((ROOT/'Content/Data/imported_meshes.json').read_text(encoding='utf-8-sig'));aliases=json.loads((ROOT/'Content/Data/model_aliases.json').read_text(encoding='utf-8-sig'))
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not any(x in unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name() for x in ('/GraphicsPilot.','/Coast.')):raise RuntimeError('Approved maps only')
 report=[]
 specs=[('Palms','__Palm',1,650),('TropicalTrees','tree_amendoeira_1',1,650),('Shrubs','Bush_Common',4,160),('GroundPlants','Fern_1',6,110),('Rocks','rock_07',4,180),('OrnamentalGarden','periwinkle_plant_04_LOD0',8,85),('NaturalDetails','sand_rocks_small_01_LOD0',6,110)]
 occupied=[]
 for category,name,count,radius in specs:
  path='/Game/Graphics/PCG/'+prefix+category
  if category=='Palms':native=json.loads((ROOT/'Content/Data/foliage_visual.json').read_text(encoding='utf-8'))['palms'][0]
  else:
   template=next(r for r in world['instances'] if r['name']==name);key=f"World_{template['mesh_index']:04d}";native=mapping[aliases.get(key,key)]
  source_scale=1. if category=='Palms' else math.sqrt(sum(v*v for v in template['transform']['basis'][0]))
  mesh=unreal.load_asset(native);bounds=mesh.get_bounds()
  graph=unreal.load_asset(path)
  if graph:
   for old in list(graph.get_editor_property('nodes')):graph.remove_node(old)
  else:graph=unreal.AssetToolsHelpers.get_asset_tools().create_asset(prefix+category,'/Game/Graphics/PCG',unreal.PCGGraph,unreal.PCGGraphFactory())
  node,settings=graph.add_node_of_type(unreal.PCGCreatePointsSettings)
  occupied=[]
  rng=random.Random(18100+len(report));points=[]
  for attempt in range(1500):
   if len(points)>=count:break
   x=rng.uniform(xmin,xmax);y=rng.uniform(-700,400)
   if any(abs(x-b[0]*100)<b[2]*50+radius+100 and abs(y-b[1]*100)<b[3]*50+radius+100 for b in world['blocks']):continue
   def distseg(a,b):
    ax,ay=a[0]*100,a[2]*100;bx,by=b[0]*100,b[2]*100;dx,dy=bx-ax,by-ay;t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/max(1,dx*dx+dy*dy)));return math.hypot(x-ax-t*dx,y-ay-t*dy)
   routes=world['paths']+[world['points']['kiosk_approach']]
   if any(distseg(a,b)<radius+160 for route in routes for a,b in zip(route,route[1:])):continue
   if any(math.hypot(x-p[0],y-p[1])<max(radius,p[2]) for p in occupied):continue
   scale=source_scale*rng.uniform(.8,1.05);z=-(bounds.origin.z-bounds.box_extent.z)*scale
   point=unreal.PCGPoint();point.transform=unreal.Transform(unreal.Vector(x,y,z),unreal.Rotator(yaw=rng.uniform(-180,180)),unreal.Vector(scale,scale,scale));point.density=1;point.seed=18100+attempt;points.append(point);occupied.append((x,y,radius))
  settings.set_editor_property('points_to_create',points)
  spawn,spawnsettings=graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
  selector=spawnsettings.get_editor_property('mesh_selector_parameters')
  entry=unreal.PCGMeshSelectorWeightedEntry();descriptor=entry.get_editor_property('descriptor');descriptor.set_editor_property('static_mesh',mesh);entry.set_editor_property('descriptor',descriptor);selector.set_editor_property('mesh_entries',[entry])
  graph.add_edge(node,'Out',spawn,'In');graph.add_edge(spawn,'Out',graph.get_output_node(),'Out')
  unreal.EditorAssetLibrary.save_loaded_asset(graph)
  actor=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==actor_prefix+category),None)
  if actor:component=actor.get_component_by_class(unreal.PCGComponent)
  else:
   actor=actors.spawn_actor_from_class(unreal.Actor,unreal.Vector());actor.set_actor_label(actor_prefix+category);actor.tags=['MareGraphicsPCG','GraphicsPilot'];component=ActorTools.add_component(actor,unreal.PCGComponent.static_class(),'PCG')
  box=actor.get_component_by_class(unreal.BoxComponent)
  if not box:box=ActorTools.add_component(actor,unreal.BoxComponent.static_class(),'GenerationBounds')
  box.set_box_extent(unreal.Vector(600,550,800),False);box.set_world_location(unreal.Vector((xmin+xmax)*.5,-150,400),False,False);box.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);box.set_hidden_in_game(True)
  component.set_editor_property('generation_trigger',unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
  component.set_graph(graph);component.generate_local(True)
  report.append({'category':category,'graph':path,'mesh':native,'points':len(points),'min_spacing_cm':radius,'seed':18100+len(report),'region':zone,'slope_deg':0,'collision':'NoCollision default PCG','exclusions':'building blocks + routes + kiosk access; flat terrain'})
 (OUT/('pcg-build.json' if zone=='grove' else 'pcg-east.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');return report

def pcg_status():
 result=[]
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if 'MareGraphicsPCG' not in [str(t) for t in a.tags]:continue
  cs=a.get_components_by_class(unreal.InstancedStaticMeshComponent)
  result.append({'actor':a.get_actor_label(),'instances':sum(c.get_instance_count() for c in cs),'collision':[str(c.get_collision_enabled()) for c in cs]})
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 (OUT/'pcg-validated.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 return result

def pcg_visibility(enabled):
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
 for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
  if 'MareGraphicsPCG' in [str(t) for t in a.tags]:a.set_actor_hidden_in_game(not enabled)
 return enabled

def lumen_apply():
 result=[]
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if not isinstance(a,unreal.PostProcessVolume):continue
  settings=a.settings
  changes={'auto_exposure_min_brightness':5.,'auto_exposure_max_brightness':14.,'lumen_scene_lighting_quality':1.,'lumen_final_gather_quality':1.,'lumen_reflection_quality':.75}
  for k,v in changes.items():settings.set_editor_property('override_'+k,True);settings.set_editor_property(k,v)
  a.settings=settings;result.append(changes)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();return result

def runtime_info():
 w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();pc=unreal.GameplayStatics.get_player_controller(w,0)
 return {'viewport':list(pc.get_viewport_size()),'screen_percentage':unreal.SystemLibrary.get_console_variable_float_value('r.ScreenPercentage'),'GI':unreal.SystemLibrary.get_console_variable_int_value('r.DynamicGlobalIlluminationMethod'),'reflections':unreal.SystemLibrary.get_console_variable_int_value('r.ReflectionMethod'),'GI_quality':unreal.SystemLibrary.get_console_variable_int_value('sg.GlobalIlluminationQuality'),'Nanite':unreal.SystemLibrary.get_console_variable_int_value('r.Nanite')}

def integrate_grove():
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/Coast')
 return {'PCG':pcg_build(),'Lumen':lumen_apply()}

def nanite_repair():
 editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);out=[]
 for path in json.loads((OUT/'nanite-enabled.json').read_text(encoding='utf-8')):
  mesh=unreal.load_asset(path);settings=mesh.get_editor_property('nanite_settings');settings.enabled=False;editor.set_nanite_settings(mesh,settings,True);unreal.EditorAssetLibrary.save_loaded_asset(mesh,False);out.append(path)
 return out

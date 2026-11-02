"""MetaHuman people for Maré Alta (UE 5.8 MetaHumanCharacter plugin, engine presets).

Run through the editor MCP: hotel_lobby action "mh_<name>" -> run(<name>, arg).
"""
import unreal

PRESETS = '/MetaHumanCharacter/Optional/Presets'
FOLDER = '/Game/People/MetaHumans'


def _subsystem():
    return unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)


def probe(name='Lani'):
    """State of an engine preset: rig, textures and what the build would need."""
    preset = unreal.load_asset(f'{PRESETS}/{name}.{name}')
    if not preset:
        return {'error': 'preset not found'}
    sub = _subsystem()
    out = {'class': preset.get_class().get_name()}
    for attr in ('has_high_resolution_textures', 'has_face_dna', 'has_body_dna'):
        v = getattr(preset, attr, None)
        out[attr] = v() if callable(v) else v
    out['props'] = [p for p in dir(preset) if not p.startswith('_')][:200]
    if sub.try_add_object_to_edit(preset):
        try:
            out['sub'] = [p for p in dir(sub) if not p.startswith('_')]
            out['can_build'] = sub.can_build_meta_human(preset, True)
        finally:
            sub.remove_object_to_edit(preset)
    return out


def copy(name):
    """Project copy of an engine preset (the presets live in read-only engine content)."""
    dest = f'{FOLDER}/MH_{name}'
    if not unreal.EditorAssetLibrary.does_asset_exist(dest) and not name.endswith('_Swim'):
        unreal.EditorAssetLibrary.duplicate_asset(f'{PRESETS}/{name}', dest)
    return unreal.load_asset(dest)


def cloud(name, what):
    """Blocking cloud request: 'rig' (face auto-rig, joints only) or 'tex' (high-resolution texture sources)."""
    character = copy(name)
    sub = _subsystem()
    if not sub.try_add_object_to_edit(character):
        raise RuntimeError('character already open for edit')
    try:
        if what == 'rig':
            req = unreal.MetaHumanCharacterAutoRiggingRequestParams()
            req.blocking = True
            req.report_progress = False
            req.rig_type = unreal.MetaHumanRigType.JOINTS_ONLY
            sub.request_auto_rigging(character, req)
        else:
            req = unreal.MetaHumanCharacterTextureRequestParams()
            req.blocking = True
            req.report_progress = False
            sub.request_texture_sources(character, req)
        unreal.EditorAssetLibrary.save_loaded_asset(character, False)
        return {'high_res': character.has_high_resolution_textures, 'can_build': sub.can_build_meta_human(character, True)}
    finally:
        sub.remove_object_to_edit(character)


def cloud_all(names):
    """Face rig + texture sources for several presets in one Epic login (the first request opens it)."""
    out = {}
    for name in names:
        try:
            cloud(name, 'rig')
            out[name] = cloud(name, 'tex')
        except Exception as e:
            out[name] = {'error': str(e)[:300]}
    return out


def build_all(names):
    """Build each ready character and save its folder; Control Rig link errors logged by the build raise
    in Python even when the assembly succeeds, so success is judged by the blueprint on disk."""
    out = {}
    for name in names:
        bp = f'{FOLDER}/{name}/MH_{name}/BP_MH_{name}'
        if unreal.EditorAssetLibrary.does_asset_exist(bp):
            out[name] = 'exists'
            continue
        try:
            build(name)
        except Exception as e:
            out[name] = str(e)[:160]
        unreal.EditorAssetLibrary.save_directory(FOLDER, True, True)
        out[name] = 'built' if unreal.EditorAssetLibrary.does_asset_exist(bp) else f'FAILED {out.get(name, "")}'
        # Each assembly keeps ~10 GB alive in the editor; release what the saved build no longer needs.
        unreal.SystemLibrary.collect_garbage()
    return out


def swim_variant(name):
    """MH_<name>_Swim: the rigged/textured character without the outfit, so the build keeps the whole body
    (a clothed build deletes the skin under the garment) for the bikini/trunks garments made in Blender."""
    swim = f'{FOLDER}/MH_{name}_Swim'
    if not unreal.EditorAssetLibrary.does_asset_exist(swim):
        unreal.EditorAssetLibrary.duplicate_asset(f'{FOLDER}/MH_{name}', swim)
    character = unreal.load_asset(swim)
    character.internal_collection.default_instance.set_single_slot_selection('Outfits', unreal.MetaHumanPaletteItemKey())
    skin = character.get_editor_property('skin_settings')
    props = skin.get_editor_property('skin')
    props.set_editor_property('show_top_underwear', False)
    skin.set_editor_property('skin', props)
    sub = _subsystem()
    if sub.try_add_object_to_edit(character):
        try:
            sub.commit_skin_settings(character, skin)
        finally:
            sub.remove_object_to_edit(character)
    unreal.EditorAssetLibrary.save_loaded_asset(character, False)
    return f'{name}_Swim'


def export(name, out_dir):
    """Body textures (TGA) and body skeletal mesh (FBX) of a built character for the Blender garment tools."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    base = f'{FOLDER}/{name}/MH_{name}/Body'
    done = []
    for asset, ext in ((f'{base}/Baked/T_Body_BC', 'tga'), (f'{base}/Baked/T_Body_N', 'tga'),
                       (f'{base}/Baked/T_Body_SRMF', 'tga'), (f'{base}/SKM_MH_{name}_BodyMesh', 'fbx')):
        task = unreal.AssetExportTask()
        task.object = unreal.load_asset(asset)
        task.filename = f'{out_dir}/{asset.split("/")[-1]}.{ext}'
        task.automated = True
        task.replace_identical = True
        task.prompt = False
        if ext == 'fbx':
            opts = unreal.FbxExportOption()
            opts.export_morph_targets = False
            opts.level_of_detail = False
            task.options = opts
        done.append([task.filename, unreal.Exporter.run_asset_export_task(task)])
    return done


SWIM = '/Game/People/Swimwear'


def _skeletal_pipeline(skeleton):
    """Interchange stack importing one skinned mesh onto an existing skeleton, without materials/physics/animation."""
    p = unreal.InterchangeGenericAssetsPipeline()
    p.common_skeletal_meshes_and_animations_properties.set_editor_property('skeleton', skeleton)
    p.common_meshes_properties.set_editor_property('force_all_mesh_as_type', unreal.InterchangeForceMeshType.IFMT_SKELETAL_MESH)
    p.mesh_pipeline.set_editor_property('create_physics_asset', False)
    p.animation_pipeline.set_editor_property('import_animations', False)
    p.material_pipeline.set_editor_property('import_materials', False)
    stack = unreal.InterchangePipelineStackOverride()
    stack.set_editor_property('override_pipelines', [unreal.SoftObjectPath(p.get_path_name())])
    return stack


def _swim_material():
    """M_MH_Swim: tintable swimwear fabric (Tint, Roughness) shared by every bikini/trunks."""
    path = f'{SWIM}/M_MH_Swim'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    mel = unreal.MaterialEditingLibrary
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_MH_Swim', SWIM, unreal.Material, unreal.MaterialFactoryNew())
    tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', unreal.LinearColor(.75, .08, .14, 1))
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 200)
    rough.set_editor_property('parameter_name', 'Roughness')
    rough.set_editor_property('default_value', .55)
    mel.connect_material_property(tint, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return mat


def _bind_swim_material(mesh):
    """Every slot of a swim garment uses M_MH_Swim (Tint is set per person at runtime). Struct copies from
    get_editor_property do not write back, so the slot array is rebuilt with new SkeletalMaterial entries."""
    mat = _swim_material()
    slots = []
    for old in mesh.get_editor_property('materials'):
        new = unreal.SkeletalMaterial()
        new.set_editor_property('material_interface', mat)
        new.set_editor_property('material_slot_name', old.get_editor_property('material_slot_name'))
        slots.append(new)
    mesh.set_editor_property('materials', slots)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return [str(m.get_editor_property('material_interface').get_path_name()) for m in mesh.get_editor_property('materials')]


def import_garment(name, fbx, kind):
    """Blender swim garment for <name>_Swim -> /Game/People/Swimwear/SKM_<Kind>_<name> on that body's skeleton."""
    body = unreal.load_asset(f'{FOLDER}/{name}_Swim/MH_{name}_Swim/Body/SKM_MH_{name}_Swim_BodyMesh')
    asset = f'SKM_{kind.capitalize()}_{name}'
    task = unreal.AssetImportTask()
    task.filename = fbx
    task.destination_path = SWIM
    task.destination_name = asset
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.options = _skeletal_pipeline(body.skeleton)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(f'{SWIM}/{asset}')
    if not isinstance(mesh, unreal.SkeletalMesh):
        raise RuntimeError(f'{asset}: import gave {mesh}; imported {list(task.imported_object_paths)}')
    _bind_swim_material(mesh)
    return {'mesh': mesh.get_path_name(), 'skeleton': mesh.skeleton.get_path_name(), 'body_skeleton': body.skeleton.get_path_name(),
            'imported': [str(p) for p in task.imported_object_paths]}


def replace_skin(name, folder):
    """Swap the swim build's baked body colour/normal for the underwear-free versions (tools/ue58/mh_skin_underwear.py)."""
    baked = f'{FOLDER}/{name}_Swim/MH_{name}_Swim/Body/Baked'
    out = {}
    for tex, normal in (('T_Body_BC', False), ('T_Body_N', True)):
        task = unreal.AssetImportTask()
        task.filename = f'{folder}/{tex}_Skin.tga'
        task.destination_path = baked
        task.destination_name = tex
        task.automated = True
        task.replace_existing = True
        task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        t = unreal.load_asset(f'{baked}/{tex}')
        t.set_editor_property('srgb', not normal)
        t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP if normal else unreal.TextureCompressionSettings.TC_DEFAULT)
        unreal.EditorAssetLibrary.save_loaded_asset(t, False)
        out[tex] = [t.blueprint_get_size_x(), str(t.get_editor_property('compression_settings'))]
    return out


def build_info():
    """Build parameter fields and the pipeline enums this engine exposes."""
    params = unreal.MetaHumanCharacterEditorBuildParameters()
    fields = {p: str(getattr(params, p)) for p in dir(params) if not p.startswith('_') and not callable(getattr(params, p, None))}
    enums = {}
    for n in dir(unreal):
        if n.startswith('MetaHuman') and ('Pipeline' in n or 'Quality' in n):
            cls = getattr(unreal, n)
            if isinstance(cls, type) and issubclass(cls, unreal.EnumBase):
                enums[n] = [k for k in dir(cls) if k.isupper()]
    return {'fields': fields, 'enums': enums}


def build(name, folder=None):
    """Optimized/Medium build of a rigged, textured character into /Game/People/MetaHumans/<name>."""
    character = copy(name)
    sub = _subsystem()
    if not sub.try_add_object_to_edit(character):
        raise RuntimeError('character already open for edit')
    try:
        if not sub.can_build_meta_human(character, True):
            raise RuntimeError('character cannot be built yet (rig/textures)')
        params = unreal.MetaHumanCharacterEditorBuildParameters()
        params.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
        params.pipeline_quality = unreal.MetaHumanQualityLevel.MEDIUM
        params.absolute_build_path = folder or f'{FOLDER}/{name}'
        params.common_folder_path = f'{FOLDER}/Common'
        sub.build_meta_human(character, params)
        unreal.EditorAssetLibrary.save_loaded_asset(character, False)
    finally:
        sub.remove_object_to_edit(character)
    built = unreal.EditorAssetLibrary.list_assets(folder or f'{FOLDER}/{name}', True, False)
    return {'assets': len(built), 'sample': built[:40]}


def preview(name, loc, clip='', at=.5, keep=False):
    """Spawn the assembled blueprint at "x,y,z" (yaw 0) for a viewport check, optionally frozen in a
    retargeted clip at fraction `at`; replaces earlier previews unless keep."""
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not keep:
        for a in sub.get_all_level_actors():
            if a.actor_has_tag('MareMHPreview'):
                sub.destroy_actor(a)
    bp = unreal.load_asset(f'{FOLDER}/{name}/MH_{name}/BP_MH_{name}')
    x, y, z = (float(v) for v in loc.split(','))
    actor = sub.spawn_actor_from_object(bp, unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=0))
    actor.tags = [unreal.Name('MareMHPreview')]
    if name.endswith('_Swim'):
        # Reference-pose check of the garment: a skeletal mesh actor at the same transform as the body.
        base = name[:-5]
        for kind in ('Bikini', 'Trunks'):
            path = f'{SWIM}/SKM_{kind}_{base}'
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                g = sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=0))
                g.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset(path))
                g.tags = [unreal.Name('MareMHPreview')]
                break
    if clip == 'bare':
        # Body check without the garment (does the build cut skin under the clothes?).
        for c in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() not in ('Body', 'Face'):
                c.set_visibility(False)
    elif clip:
        anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
        for c in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() == 'Body':
                c.override_animation_data(anim, True, False, anim.get_play_length() * at, 1.0)
    comps = [f'{c.get_name()}:{c.get_class().get_name()}' for c in actor.get_components_by_class(unreal.SceneComponent)]
    return {'actor': actor.get_path_name(), 'components': comps}


RETARGET = f'{FOLDER}/../Retarget'.replace('/MetaHumans/..', '')
CLIPS = ('Idle', 'Idle_Talking', 'Walk', 'Sitting_Idle', 'Interact')


def _catalog():
    import json
    path = unreal.Paths.project_content_dir() + 'Data/actors.json'
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _new_asset(name, cls, factory):
    path = f'{RETARGET}/{name}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, RETARGET, cls, factory)


def _ik_rig(name, mesh):
    """IK rig with the engine's auto-generated retarget chains and full-body IK for a skeletal mesh."""
    rig = _new_asset(name, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    ctrl = unreal.IKRigController.get_controller(rig)
    ctrl.set_skeletal_mesh(mesh)
    ctrl.apply_auto_generated_retarget_definition()
    ctrl.apply_auto_fbik()
    return rig, [str(c.get_editor_property('chain_name')) if hasattr(c, 'get_editor_property') else str(c) for c in ctrl.get_retarget_chains()]


def retarget_setup(name='Lani'):
    """IK rigs (UAL Human_0 source, built MetaHuman body target) and the retargeter between them."""
    row = _catalog()['Human_0']
    src_mesh = unreal.load_asset(row['skeletal_meshes'][0])
    tgt_mesh = unreal.load_asset(f'{FOLDER}/{name}/MH_{name}/Body/SKM_MH_{name}_BodyMesh')
    src, src_chains = _ik_rig('IK_UAL', src_mesh)
    tgt, tgt_chains = _ik_rig('IK_MH_Body', tgt_mesh)
    rtg = _new_asset('RTG_UAL_to_MH', unreal.IKRetargeter, unreal.IKRetargetFactory())
    ctrl = unreal.IKRetargeterController.get_controller(rtg)
    S, T = unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET
    ctrl.set_ik_rig(S, src)
    ctrl.set_ik_rig(T, tgt)
    ctrl.set_preview_mesh(S, src_mesh)
    ctrl.set_preview_mesh(T, tgt_mesh)
    ctrl.add_default_ops()
    ctrl.assign_ik_rig_to_all_ops(S, src)
    ctrl.assign_ik_rig_to_all_ops(T, tgt)
    ctrl.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    # UAL rests in a T-pose and MetaHumans in an A-pose: align the target limbs to the source pose.
    ctrl.create_retarget_pose('MareAligned', T)
    ctrl.auto_align_all_bones(T)
    for asset in (src, tgt, rtg):
        unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    return {'src_chains': src_chains, 'tgt_chains': tgt_chains,
            'ops': [ctrl.get_op_name(i) for i in range(ctrl.get_num_retarget_ops())],
            'batch_doc': unreal.IKRetargetBatchOperation.duplicate_and_retarget.__doc__}


ANIMS = '/Game/People/Animations'


def retarget_clips(name='Lani'):
    """Retarget the UAL clips the people use onto the MetaHuman body skeleton (/Game/People/Animations/MH_<clip>)."""
    row = _catalog()['Human_0']
    src_mesh = unreal.load_asset(row['skeletal_meshes'][0])
    tgt_mesh = unreal.load_asset(f'{FOLDER}/{name}/MH_{name}/Body/SKM_MH_{name}_BodyMesh')
    rtg = unreal.load_asset(f'{RETARGET}/RTG_UAL_to_MH')
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = [registry.get_asset_by_object_path(row['animations'][f'Human_0{c}']) for c in CLIPS]
    out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(
        assets, src_mesh, tgt_mesh, rtg, 'Human_0', 'MH_', '', '', ANIMS, False, False, True)
    paths = [str(a.package_name) for a in out]
    for p in paths:
        unreal.EditorAssetLibrary.save_asset(p, False)
    return paths


HAND_PREFIXES = ('hand_', 'thumb_', 'index_', 'middle_', 'ring_', 'pinky_')


def fix_hands(clips=CLIPS):
    """UAL and MetaHuman wrists roll about different axes, so the retargeted wrists bent outward and the fingers
    clawed. The clips here have no wrist/finger acting worth keeping: hold hands and fingers at the MetaHuman
    reference pose (straight, relaxed) on every frame. Arm IK for carried products still runs at runtime."""
    out = {}
    for clip in clips:
        anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
        skeleton = anim.get_editor_property('skeleton')
        ref = unreal.AnimPoseExtensions.get_reference_pose(skeleton)
        frames = unreal.AnimationLibrary.get_num_frames(anim)
        ctrl = anim.get_editor_property('controller')
        bones = [b for b in unreal.AnimPoseExtensions.get_bone_names(ref) if str(b).startswith(HAND_PREFIXES)]
        ctrl.open_bracket('Mare hands', False)
        for bone in bones:
            t = unreal.AnimPoseExtensions.get_bone_pose(ref, bone, unreal.AnimPoseSpaces.LOCAL)
            n = frames + 1
            ctrl.set_bone_track_keys(bone, [t.translation] * n, [t.rotation] * n, [t.scale3d] * n, False)
        ctrl.close_bracket(False)
        unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
        out[clip] = len(bones)
    return out


def _pie_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def run(action, arg=''):
    if action == 'clear':
        # Remove viewport previews from the level and save it.
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        gone = [a.get_name() for a in sub.get_all_level_actors() if a.actor_has_tag('MareMHPreview')]
        for a in sub.get_all_level_actors():
            if a.actor_has_tag('MareMHPreview'):
                sub.destroy_actor(a)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return gone
    if action == 'cvar':
        # "Lani,1" -> mare.MetaHuman / mare.MetaHumanCount in the PIE world.
        name, _, count = arg.partition(',')
        world = _pie_world()
        unreal.SystemLibrary.execute_console_command(world, f'mare.MetaHuman {name}')
        unreal.SystemLibrary.execute_console_command(world, f'mare.MetaHumanCount {count or 1}')
        return {'pie': bool(world)}
    if action == 'trace':
        # "Action": line from the player's eye to that service target, as FindFocused does.
        world = _pie_world()
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        loc, rot = pc.get_player_view_point()
        t = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget) if str(a.action) == arg)
        hit = unreal.SystemLibrary.line_trace_single(world, loc, t.get_actor_location(), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [unreal.GameplayStatics.get_player_pawn(world, 0), t], unreal.DrawDebugTrace.NONE, True)
        tup = hit.to_tuple() if hit else None
        return {'eye': [loc.x, loc.y, loc.z], 'rot': [rot.pitch, rot.yaw], 'target': [t.get_actor_location().x, t.get_actor_location().y, t.get_actor_location().z],
                'hidden': t.is_hidden_ed() if hasattr(t, 'is_hidden_ed') else None, 'hit': [str(tup[9].get_name()) if tup and tup[9] else None, str(tup[9].static_mesh_component.static_mesh.get_path_name()) if tup and tup[9] and hasattr(tup[9], 'static_mesh_component') else None, str(tup[9].get_actor_location()) if tup and tup[9] else None, tup[1] if tup else None] if tup else None}
    if action == 'fixmats':
        return {p: _bind_swim_material(unreal.load_asset(p)) for p in unreal.EditorAssetLibrary.list_assets(SWIM, False, False) if '/SKM_' in p}
    if action == 'mats':
        m = unreal.load_asset(arg)
        return [str(x.get_editor_property('material_interface').get_path_name()) if x.get_editor_property('material_interface') else None for x in m.get_editor_property('materials')]
    if action == 'delasset':
        return unreal.EditorAssetLibrary.delete_asset(arg)
    if action == 'closephone':
        pc = unreal.GameplayStatics.get_player_controller(_pie_world(), 0)
        pc.close_phone()
        return True
    if action == 'people':
        world = _pie_world()
        out = []
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            v = p.get_actor_location()
            out.append({'name': p.get_name(), 'mh': p.get_editor_property('meta_human'), 'stage': str(p.get_editor_property('stage')),
                        'employee': p.get_editor_property('employee'), 'table': p.get_editor_property('table_index'),
                        'yaw': p.get_actor_rotation().yaw, 'pos': [round(v.x), round(v.y), round(v.z)]})
        return [o for o in out if arg != 'mh' or o['mh']]
    if action == 'rtsetup':
        return retarget_setup(arg or 'Lani')
    if action == 'rtclips':
        return retarget_clips(arg or 'Lani')
    if action == 'fixhands':
        return fix_hands()
    if action == 'cloudall':
        return cloud_all(arg.split(','))
    if action == 'buildall':
        return build_all(arg.split(','))
    if action == 'export':
        name, _, out = arg.partition('@')
        return export(name, out or f'D:/CodexTemp/mh/{name}')
    if action == 'garment':
        # "Ada@D:/.../SKM_Bikini_Ada.fbx@bikini"
        name, fbx, kind = arg.split('@')
        return import_garment(name, fbx, kind)
    if action == 'noskin':
        name, _, folder = arg.partition('@')
        return replace_skin(name, folder or f'D:/CodexTemp/mh/{name}_Swim')
    if action == 'rebuild':
        # Delete a built folder so build_all assembles it again.
        unreal.EditorAssetLibrary.delete_directory(f'{FOLDER}/{arg}')
        return arg
    if action == 'swimall':
        return build_all([swim_variant(n) for n in arg.split(',')])
    if action == 'skin':
        ch = unreal.load_asset(f'{FOLDER}/MH_{arg or "Lani"}')
        out = {}
        for prop in ('skin_settings', 'makeup_settings', 'body_textures'):
            v = ch.get_editor_property(prop)
            out[prop] = str(v)[:1500]
            if hasattr(v, '__class__') and not isinstance(v, (str, int, float)):
                out[prop + '_fields'] = [f for f in dir(v) if not f.startswith('_') and not callable(getattr(v, f, None))][:80]
        return out
    if action == 'coll':
        ch = unreal.load_asset(f'{FOLDER}/MH_{arg or "Lani"}')
        col = ch.internal_collection
        inst = col.default_instance
        pub = lambda o: [m for m in dir(o) if not m.startswith('_')]
        out = {'slots': [str(n) for n in col.get_slot_names()], 'keys': [str(k) for k in col.get_all_item_keys()],
               'selection': str(inst.get_slot_selection_data())[:2500], 'param_items': str(inst.get_instance_parameter_item_paths())[:1500]}
        try:
            paths = inst.get_instance_parameter_item_paths()
            out['params'] = {str(pth): str(inst.get_instance_parameters(pth))[:1200] for pth in list(paths)[:6]}
        except Exception as e:
            out['params'] = str(e)[:300]
        for doc in ('set_single_slot_selection', 'get_instance_parameters', 'try_get_instance_parameter'):
            out[doc] = getattr(type(inst), doc).__doc__[:400]
        return out
    if action == 'bodies':
        # Fixed body type of every engine preset (to pick women/men for the beach roles).
        import os
        folder = unreal.Paths.engine_plugins_dir() + 'MetaHuman/MetaHumanCharacter/Content/Optional/Presets'
        names = sorted(f[:-7] for f in os.listdir(folder) if f.endswith('.uasset'))
        return {n: str(unreal.load_asset(f'{PRESETS}/{n}.{n}').get_editor_property('fixed_body_type')).split('.')[-1].split(':')[0] for n in names}
    if action == 'rtinfo':
        names = ('IKRigController', 'IKRetargeterController', 'IKRetargetBatchOperation', 'RetargetSourceOrTarget', 'AutoMapChainType')
        return {n: [m for m in dir(getattr(unreal, n, None)) if not m.startswith('_')] for n in names}
    if action == 'preview':
        # "Lani@x,y,z[@clip[@fraction]]"; a leading '+' keeps earlier previews.
        keep = arg.startswith('+')
        name, loc, *rest = arg.lstrip('+').split('@') + ['']
        return preview(name or 'Lani', loc or '0,0,60000', rest[0] if rest else '',
                       float(rest[1]) if len(rest) > 1 and rest[1] else .5, keep)
    if action == 'probe':
        return probe(arg or 'Lani')
    if action == 'buildinfo':
        return build_info()
    if action == 'build':
        return build(arg or 'Lani')
    if action == 'save':
        # The build leaves its assets in memory; persist everything under the people folder.
        unreal.EditorAssetLibrary.save_directory(FOLDER, True, True)
        return unreal.EditorAssetLibrary.list_assets(f'{FOLDER}/{arg}' if arg else FOLDER, True, False)
    if action in ('rig', 'tex'):
        return cloud(arg or 'Lani', action)
    raise ValueError(action)

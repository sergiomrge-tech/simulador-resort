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


def dress_variant(name, suffix, items):
    """MH_<name>_<suffix>: the character wearing real Fab outfits (parametric wardrobe items, e.g.
    /Game/Outfits/Shorts/WI_OA_Shorts) instead of the default Epic garment; every item goes in the Outfits slot
    (several pieces: top, bottom, shoes). Build it with build('<name>_<suffix>')."""
    # An empty suffix dresses the character itself (its normal build then wears the outfit).
    variant = f'{FOLDER}/MH_{name}_{suffix}' if suffix else f'{FOLDER}/MH_{name}'
    if suffix and not unreal.EditorAssetLibrary.does_asset_exist(variant):
        unreal.EditorAssetLibrary.duplicate_asset(f'{FOLDER}/MH_{name}', variant)
    character = unreal.load_asset(variant)
    col = character.internal_collection
    inst = col.default_instance
    keys, out = [], {}
    for path in items:
        wi = unreal.load_asset(path)
        if not isinstance(wi, unreal.MetaHumanWardrobeItem):
            out[path] = 'not a wardrobe item'
            continue
        found = list(col.get_item_keys_for_wardrobe_item(wi)) if hasattr(col, 'get_item_keys_for_wardrobe_item') else []
        key, slot = (found[0], 'Outfits') if found else (None, '')
        for slot in ([] if key else ('Outfits', 'Top Garment', 'Bottom Garment')):
            key = col.try_add_item_from_wardrobe_item(slot, wi)
            if key:
                break
        out[path] = f'ok {slot}' if key else f'refused (principal {wi.get_editor_property("principal_asset") if hasattr(wi, "get_editor_property") else "?"})'
        if key:
            keys.append(key)
    if keys:
        inst.set_single_slot_selection('Outfits', keys[0])
        for key in keys[1:]:
            sel = unreal.MetaHumanPipelineSlotSelection()
            sel.set_editor_property('slot_name', 'Outfits')
            sel.set_editor_property('selected_item', key)
            out[f'select {len(out)}'] = inst.try_add_slot_selection(sel)
    unreal.EditorAssetLibrary.save_loaded_asset(character, False)
    out['selection'] = str(inst.get_slot_selection_data())[:600]
    return out


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
    """Swap the swim build's baked body colour/normal/specular-roughness for the underwear-free versions
    (tools/ue58/mh_skin_underwear.py)."""
    import os
    baked = f'{FOLDER}/{name}_Swim/MH_{name}_Swim/Body/Baked'
    out = {}
    for tex, normal in (('T_Body_BC', False), ('T_Body_N', True), ('T_Body_SRMF', None)):
        if not os.path.exists(f'{folder}/{tex}_Skin.tga'):
            continue
        before = unreal.load_asset(f'{baked}/{tex}')
        keep = {p: before.get_editor_property(p) for p in ('srgb', 'compression_settings')} if before else {}
        task = unreal.AssetImportTask()
        task.filename = f'{folder}/{tex}_Skin.tga'
        task.destination_path = baked
        task.destination_name = tex
        task.automated = True
        task.replace_existing = True
        task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        t = unreal.load_asset(f'{baked}/{tex}')
        if normal is None:   # data map: keep the baked texture's own settings (linear, masks)
            for p, v in keep.items():
                t.set_editor_property(p, v)
        else:
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


def wear(name, loc, kinds):
    """Preview: extra garments (Tank, Boardshorts, Coverup...) of <name> at "x,y,z", next to an existing preview."""
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    x, y, z = (float(v) for v in loc.split(','))
    out = []
    for kind in kinds.split(','):
        path = f'{SWIM}/SKM_{kind}_{name}'
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            out.append(f'missing {path}')
            continue
        g = sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=0))
        g.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset(path))
        g.tags = [unreal.Name('MareMHPreview')]
        out.append(path)
    return out


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
        comps = actor.get_components_by_class(unreal.SkeletalMeshComponent)
        body = next(c for c in comps if c.get_name() == 'Body')
        body.override_animation_data(anim, True, False, anim.get_play_length() * at, 1.0)
        for c in comps:
            if c is not body:     # face and clothes follow the body (otherwise the head floats in the rest pose)
                c.set_leader_pose_component(body, True)
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


MOCAP = '/Game/People/AnimSource/Mocap'


def import_mocap(folder='D:/CodexTemp/fab/anim'):
    """Free Fab mocap clips (Animation Shopee, FBX on Mixamo-style rigs with a body mesh). The rigs differ a little
    (some have extra thumb bones), so every clip gets its own mesh and skeleton: one pass imports the mesh (no
    animation) into <clip>/Mesh, a second pass imports only the animation onto that skeleton into <clip>/Anim (one
    pass gave the mesh and the clip the same name and one replaced the other). Returns {clip: [mesh, anim]}."""
    import os
    if unreal.EditorAssetLibrary.does_directory_exist(MOCAP):
        unreal.EditorAssetLibrary.delete_directory(MOCAP)
    out = {}

    def run(fbx, dest, skeleton=None):
        p = unreal.InterchangeGenericAssetsPipeline()
        p.material_pipeline.set_editor_property('import_materials', False)
        p.mesh_pipeline.set_editor_property('create_physics_asset', False)
        props = p.common_skeletal_meshes_and_animations_properties
        if skeleton:
            props.set_editor_property('skeleton', skeleton)
            props.set_editor_property('import_only_animations', True)
            # Mocap lengths that are not whole frames at 30 fps (12.596 s) are refused unless snapped.
            p.animation_pipeline.set_editor_property('frame_alignment', unreal.InterchangeFrameAlignment.SNAP_TO_CLOSEST)
        else:
            p.animation_pipeline.set_editor_property('import_animations', False)
        stack = unreal.InterchangePipelineStackOverride()
        stack.set_editor_property('override_pipelines', [unreal.SoftObjectPath(p.get_path_name())])
        task = unreal.AssetImportTask()
        task.filename = fbx
        task.destination_path = dest
        task.automated = True
        task.replace_existing = True
        task.save = True
        task.options = stack
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        return [unreal.load_asset(str(x)) for x in task.imported_object_paths]

    for f in sorted(x for x in os.listdir(folder) if x.lower().endswith('.fbx')):
        clip = os.path.splitext(f)[0]
        try:
            mesh = next(a for a in run(f'{folder}/{f}', f'{MOCAP}/{clip}/Mesh') if isinstance(a, unreal.SkeletalMesh))
            anim = next((a for a in run(f'{folder}/{f}', f'{MOCAP}/{clip}/Anim', mesh.skeleton) if isinstance(a, unreal.AnimSequence)), None)
            out[clip] = [mesh.get_path_name(), anim.get_path_name() if anim else None]
        except Exception as e:
            out[clip] = f'error {str(e)[:160]}'
    return out


def ground_mocap(clips=('LieDown', 'SitDrink', 'SitTalk', 'TalkGesture', 'Dance', 'DanceHip', 'Cheer')):
    """Retargeted mocap carries the capture stage offset in the root (tens of metres): move every root key so the
    pelvis starts over the origin and the lowest body point during the clip touches the floor (z = 0)."""
    out = {}
    probe = ('foot_l', 'foot_r', 'ball_l', 'ball_r', 'hand_l', 'hand_r', 'pelvis', 'head', 'spine_03', 'calf_l', 'calf_r')
    for clip in clips:
        anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
        if not anim:
            continue
        frames = unreal.AnimationLibrary.get_num_frames(anim)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        opts = unreal.AnimPoseEvaluationOptions()
        low, first = 1e9, None
        for f in range(0, frames + 1, max(1, frames // 60)):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * f / max(frames, 1), opts)
            for bone in probe:
                t = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD).translation
                low = min(low, t.z)
            if first is None:
                first = unreal.AnimPoseExtensions.get_bone_pose(pose, 'pelvis', unreal.AnimPoseSpaces.WORLD).translation
        offset = unreal.Vector(first.x, first.y, low - 3.0)      # bones sit ~3 cm inside the skin surface
        pos, rot, scl = [], [], []
        for f in range(frames + 1):
            t = unreal.AnimationLibrary.get_bone_pose_for_frame(anim, 'root', f, False)
            pos.append(t.translation - offset)
            rot.append(t.rotation)
            scl.append(t.scale3d)
        ctrl = anim.get_editor_property('controller')
        ctrl.open_bracket('Mare ground mocap', False)
        ctrl.set_bone_track_keys('root', pos, rot, scl, False)
        ctrl.close_bracket(False)
        unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
        out[clip] = [round(offset.x), round(offset.y), round(offset.z)]
    return out


def rescale_mocap_root(clips=('LieDown', 'SitDrink', 'SitTalk', 'TalkGesture', 'Dance', 'DanceHip', 'Cheer'), factor=.01):
    """The mocap rig moves its hips in metres while the pose is in centimetres: after retargeting, the root travels
    100x too far (a talking man walked 68 m). Scale the root motion relative to the first frame and set the height so
    the lowest body point over the clip sits on the floor."""
    out = {}
    probe = ('foot_l', 'foot_r', 'ball_l', 'ball_r', 'hand_l', 'hand_r', 'pelvis', 'head', 'spine_03', 'calf_l', 'calf_r')
    for clip in clips:
        anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
        if not anim:
            continue
        frames = unreal.AnimationLibrary.get_num_frames(anim)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        roots = [unreal.AnimationLibrary.get_bone_pose_for_frame(anim, 'root', f, False) for f in range(frames + 1)]
        r0 = roots[0].translation
        moved = [(t.translation - r0) * factor for t in roots]
        opts = unreal.AnimPoseEvaluationOptions()
        lowest = 1e9
        for f in range(0, frames + 1, max(1, frames // 80)):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * f / max(frames, 1), opts)
            low = min(unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation.z for b in probe)
            lowest = min(lowest, low - roots[f].translation.z + moved[f].z)
        base = 3.0 - lowest
        pos = [unreal.Vector(m.x, m.y, m.z + base) for m in moved]
        ctrl = anim.get_editor_property('controller')
        ctrl.open_bracket('Mare mocap root scale', False)
        ctrl.set_bone_track_keys('root', pos, [t.rotation for t in roots], [t.scale3d for t in roots], False)
        ctrl.close_bracket(False)
        unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
        span = max(abs(m.x) + abs(m.y) for m in moved)
        out[clip] = {'base': round(base), 'max_travel_cm': round(span)}
    return out


def orient_mocap(clips=('LieDown', 'SitDrink', 'SitTalk', 'TalkGesture', 'Dance', 'DanceHip', 'Cheer'), seated=('SitDrink', 'SitTalk')):
    """Every capture faced its own way: turn each clip's root so the body faces +Y like the game clips, and seat the
    sitting clips like Sitting_Idle (pelvis 30 cm behind the root, so AMarePerson's seat placement fits).
    Facing = perpendicular to the hip line (thigh_l -> thigh_r) averaged over the clip (knees/feet move with crossed
    legs and gestures). Check with mh_twist: shoulders, hips and knees must agree, as in the capture."""
    import math
    opts = unreal.AnimPoseEvaluationOptions()
    out = {}
    for clip in clips:
        anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
        frames = unreal.AnimationLibrary.get_num_frames(anim)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        fx = fy = 0.0
        for k in range(1, 10):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * k / 10, opts)
            g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
            r = g('thigh_r') - g('thigh_l')
            fx += r.y          # forward = hip line x up: facing +Y has the right hip at -X
            fy -= r.x
        yaw = math.degrees(math.atan2(1, 0) - math.atan2(fy, fx))       # rotate the forward vector onto +Y
        turn = unreal.Rotator(roll=0, pitch=0, yaw=yaw).quaternion()
        roots = [unreal.AnimationLibrary.get_bone_pose_for_frame(anim, 'root', f, False) for f in range(frames + 1)]
        back = -30.0 if clip in seated else 0.0
        pos = [unreal.Vector(0, back, t.translation.z) for t in roots]
        rot = [turn * t.rotation for t in roots]
        ctrl = anim.get_editor_property('controller')
        ctrl.open_bracket('Mare mocap facing', False)
        ctrl.set_bone_track_keys('root', pos, rot, [t.scale3d for t in roots], False)
        ctrl.close_bracket(False)
        unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
        out[clip] = round(yaw)
    return out


def retarget_mocap(name='Lani', version='3'):
    """Per clip: IK rig on its own mocap mesh, retargeter to the MetaHuman body rig, and /Game/People/Animations/MH_<clip>."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    tgt_mesh = unreal.load_asset(f'{FOLDER}/{name}/MH_{name}/Body/SKM_MH_{name}_BodyMesh')
    tgt = unreal.load_asset(f'{RETARGET}/IK_MH_Body')
    S, T = unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET
    out = {}
    folders = sorted({'/'.join(str(a.package_path).split('/')[:6]) for a in registry.get_assets_by_path(MOCAP, True)})
    for folder in folders:
        clip = folder.split('/')[-1]
        items = registry.get_assets_by_path(folder, True)
        meshes = [a.get_asset() for a in items if str(a.asset_class_path.asset_name) == 'SkeletalMesh']
        anims = [a for a in items if str(a.asset_class_path.asset_name) == 'AnimSequence']
        if not meshes or not anims:
            continue
        # Versioned names: retargeters used in this editor session stay loaded and refuse deletion; remove old
        # versions with the editor closed (Content/People/Retarget/*_Mocap*).
        old = f'{RETARGET}/RTG_Mocap{version}_{clip}'   # the retargeter references the IK rig: delete it first
        if unreal.EditorAssetLibrary.does_asset_exist(old):
            unreal.EditorAssetLibrary.delete_asset(old)
        src, _ = _ik_rig(f'IK_Mocap{version}_{clip}', meshes[0])
        rtg = _new_asset(f'RTG_Mocap{version}_{clip}', unreal.IKRetargeter, unreal.IKRetargetFactory())
        ctrl = unreal.IKRetargeterController.get_controller(rtg)
        ctrl.set_ik_rig(S, src)
        ctrl.set_ik_rig(T, tgt)
        ctrl.set_preview_mesh(S, meshes[0])
        ctrl.set_preview_mesh(T, tgt_mesh)
        ctrl.add_default_ops()
        ctrl.assign_ik_rig_to_all_ops(S, src)
        ctrl.assign_ik_rig_to_all_ops(T, tgt)
        ctrl.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
        # The capture rigs face -Y and the MetaHuman faces +Y (mh_reffacing): the retargeter needs both facing the same
        # way, otherwise the pelvis and the FK chains disagree by 180 degrees and the body comes out twisted. Turn the
        # source BEFORE aligning the target to it: aligned to the unturned T-pose, the arms (horizontal) pointed the
        # other way and every hand came out mirrored (mh_arms), while the vertical legs and spine looked right.
        ctrl.create_retarget_pose('MareFacing', S)
        ctrl.set_rotation_offset_for_retarget_pose_bone('Hips', unreal.Rotator(roll=0, pitch=0, yaw=180).quaternion(), S)
        ctrl.create_retarget_pose('MareAligned', T)
        ctrl.auto_align_all_bones(T)
        # The mocap hips translation is in metres (x100): IK goals built from it bend the legs and torso. Rotations
        # only (FK chains) carry the captured pose exactly; the root is rescaled afterwards (rescale_mocap_root).
        for i in range(ctrl.get_num_retarget_ops()):
            if 'IK' in str(ctrl.get_op_name(i)) and 'FK' not in str(ctrl.get_op_name(i)):
                ctrl.set_retarget_op_enabled(i, False)
        for asset in (src, rtg):
            unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
        res = unreal.IKRetargetBatchOperation.duplicate_and_retarget(anims, meshes[0], tgt_mesh, rtg, '', f'MH_{clip}_', '', '', ANIMS, False, False, True)
        for a in res:
            unreal.EditorAssetLibrary.save_asset(str(a.package_name), False)
        out[clip] = [str(a.package_name) for a in res]
    return out


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
    if action == 'mparams':
        mi = unreal.load_asset(arg)
        out = {'parent': str(mi.get_editor_property('parent').get_path_name()) if hasattr(mi, 'parent') and mi.get_editor_property('parent') else None}
        mel = unreal.MaterialEditingLibrary
        base = mi
        while isinstance(base, unreal.MaterialInstance):
            base = base.get_editor_property('parent')
        out['vectors'] = [str(n) for n in mel.get_vector_parameter_names(base)]
        out['scalars'] = [str(n) for n in mel.get_scalar_parameter_names(base)][:40]
        out['textures'] = [str(n) for n in mel.get_texture_parameter_names(base)]
        return out
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
    if action == 'wear':
        # "Ada@x,y,z@Tank,Boardshorts"
        name, loc, kinds = arg.split('@')
        return wear(name, loc, kinds)
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
    if action == 'api':
        # Method names of the collection, its default instance, a palette item key and a wardrobe item asset.
        ch = unreal.load_asset(f'{FOLDER}/MH_{arg or "Ada"}')
        col = ch.internal_collection
        pub = lambda o: [m for m in dir(o) if not m.startswith('_')]
        wi = unreal.load_asset('/Game/Outfits/Shorts/WI_OA_Shorts')
        out = {'collection': pub(col), 'key': pub(unreal.MetaHumanPaletteItemKey()), 'wi': str(wi), 'wi_api': pub(wi) if wi else None,
               'unreal': [n for n in dir(unreal) if 'Wardrobe' in n or 'Palette' in n or 'MetaHumanCollection' in n][:60]}
        out['instance'] = pub(col.default_instance)
        for doc in ('try_add_item_from_wardrobe_item',):
            out[doc] = getattr(type(col), doc).__doc__[:500]
        for doc in [m for m in pub(col.default_instance) if 'select' in m]:
            out[doc] = getattr(type(col.default_instance), doc).__doc__[:300]
        try:
            out['items'] = [str(i) for i in col.get_items()][:8]
        except Exception as e:
            out['items'] = str(e)[:200]
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
    if action == 'outfitmats':
        # Materials of a built character's outfit meshes and their vector/scalar parameters (runtime tint names).
        out = {}
        for path in unreal.EditorAssetLibrary.list_assets(f'{FOLDER}/{arg}', True, False):
            if '/Clothing/' not in path:
                continue
            a = unreal.load_asset(path)
            if not isinstance(a, unreal.SkeletalMesh):
                continue
            for i, m in enumerate(a.get_editor_property('materials')):
                mi = m.get_editor_property('material_interface')
                if not mi:
                    continue
                vec = [str(n) for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(mi)]
                out[f'{a.get_name()}[{i}] {mi.get_path_name()}'] = vec[:20]
        return out
    if action == 'texcap':
        # Fab outfit textures ship at 4K: cap them (default 1024) so a crowd of dressed people fits in video memory.
        size = int(arg or 1024)
        out = {'capped': 0, 'kept': 0}
        for root in ('/Game/Outfits', '/Game/OutFits', '/Game/MetaOutfits'):
            for path in unreal.EditorAssetLibrary.list_assets(root, True, False):
                data = unreal.EditorAssetLibrary.find_asset_data(path)
                if str(data.asset_class_path.asset_name) != 'Texture2D':
                    continue
                tex = unreal.load_asset(path)
                if tex.get_editor_property('max_texture_size') == size:
                    out['kept'] += 1
                    continue
                tex.set_editor_property('max_texture_size', size)
                unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
                out['capped'] += 1
        return out
    if action == 'rmfab':
        # Remove one folder of models imported from Fab (re-import with new materials needs a clean folder).
        if not arg.startswith('/Game/Custom/Fab') and arg != '/Game/Custom/Festival/festa_campfire_scan':
            return 'refused: only /Game/Custom/Fab* folders'
        return unreal.EditorAssetLibrary.delete_directory(arg)
    if action == 'pipeprops':
        ap = unreal.InterchangeGenericAssetsPipeline().animation_pipeline
        fa = ap.get_editor_property('frame_alignment')
        return {'frame_alignment': str(fa), 'type': type(fa).__name__, 'members': [m for m in dir(type(fa)) if m.isupper()][:20],
                'sample_rate': str(ap.get_editor_property('custom_bone_animation_sample_rate'))}
    if action == 'mvanims':
        # Game names for the retargeted mocap clips (AMarePerson loads /Game/People/Animations/MH_<Clip>).
        names = {'lying_on_the_floor': 'LieDown', 'sits_on_stool_drinks': 'SitDrink', 'conversation_while_sit': 'SitTalk',
                 'serious_conversation': 'TalkGesture', 'dancing': 'Dance', 'shaking_hip': 'DanceHip', 'celebrating_victory': 'Cheer'}
        out = {}
        for src, dst in names.items():
            a, b = f'{ANIMS}/{src}', f'{ANIMS}/MH_{dst}'
            if not unreal.EditorAssetLibrary.does_asset_exist(a):
                out[dst] = 'missing'
                continue
            if unreal.EditorAssetLibrary.does_asset_exist(b):
                unreal.EditorAssetLibrary.delete_asset(b)
            out[dst] = unreal.EditorAssetLibrary.rename_asset(a, b) if unreal.EditorAssetLibrary.does_asset_exist(a) else 'missing'
        return out
    if action == 'animprobe':
        # Pelvis/root/head positions (component space) at a time fraction of each clip: retarget sanity check.
        out = {}
        for clip in (arg or 'Idle,LieDown,Dance').split(','):
            anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
            if not anim:
                out[clip] = 'missing'
                continue
            length = unreal.AnimationLibrary.get_sequence_length(anim)
            opts = unreal.AnimPoseEvaluationOptions()
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * .4, opts)
            row = {'len': round(length, 2)}
            for bone in ('root', 'pelvis', 'head'):
                t = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)
                row[bone] = [round(t.translation.x), round(t.translation.y), round(t.translation.z)]
            out[clip] = row
        return out
    if action == 'rootmocap':
        return rescale_mocap_root()
    if action == 'inplacemocap':
        # Loops stay in place: no horizontal root travel (the pelvis keeps its own sway relative to the root).
        out = {}
        for clip in ('LieDown', 'SitDrink', 'SitTalk', 'TalkGesture', 'Dance', 'DanceHip', 'Cheer'):
            anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
            frames = unreal.AnimationLibrary.get_num_frames(anim)
            roots = [unreal.AnimationLibrary.get_bone_pose_for_frame(anim, 'root', f, False) for f in range(frames + 1)]
            ctrl = anim.get_editor_property('controller')
            ctrl.open_bracket('Mare mocap in place', False)
            ctrl.set_bone_track_keys('root', [unreal.Vector(0, 0, t.translation.z) for t in roots], [t.rotation for t in roots], [t.scale3d for t in roots], False)
            ctrl.close_bracket(False)
            unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
            out[clip] = frames
        return out
    if action == 'lean':
        # "anim_path@hips@head@shoulder_l@shoulder_r": torso lean (head minus hips, cm) and shoulder line height
        # difference at 0.2/0.5/0.8 of the clip, to compare a source capture with its retarget.
        path, hips, head, sl, sr = arg.split('@')
        anim = unreal.load_asset(path)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        rows = []
        for f in (.2, .5, .8):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * f, unreal.AnimPoseEvaluationOptions())
            g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
            d = g(head) - g(hips)
            rows.append({'lean': [round(d.x), round(d.y), round(d.z)], 'shoulders_dz': round(g(sl).z - g(sr).z)})
        return rows
    if action == 'bodyframe':
        # "anim@hips@head@thigh_l@thigh_r@knee_l@knee_r": in the body's own frame (forward = hip line x up), how far
        # the head leans forward and the knees sit forward of the hips; a retarget that mirrors front/back flips signs.
        path, hips, head, tl, tr, kl, kr = arg.split('@')
        anim = unreal.load_asset(path)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        rows = []
        for f in (.2, .5, .8):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * f, unreal.AnimPoseEvaluationOptions())
            g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
            r = g(tr) - g(tl)
            fx, fy = r.y, -r.x
            n = max((fx * fx + fy * fy) ** .5, 1e-3)
            fwd = lambda v: round((v.x * fx + v.y * fy) / n)
            rows.append({'head_fwd': fwd(g(head) - g(hips)), 'knee_l_fwd': fwd(g(kl) - g(hips)), 'knee_r_fwd': fwd(g(kr) - g(hips))})
        return rows
    if action == 'twist':
        # "anim@hips@shoulder_l@shoulder_r@thigh_l@thigh_r@knee_l@knee_r": world yaw (deg) of the shoulder-line forward,
        # the hip-line forward and the hips->knees direction at mid clip; all three agree on an untwisted body.
        import math
        path, hips, sl, sr, tl, tr, kl, kr = arg.split('@')
        anim = unreal.load_asset(path)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * .5, unreal.AnimPoseEvaluationOptions())
        g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
        yaw_of_line = lambda l, r: round(math.degrees(math.atan2(-(g(r) - g(l)).x, (g(r) - g(l)).y)))
        k = (g(kl) + g(kr)) * .5 - g(hips)
        return {'shoulders': yaw_of_line(sl, sr), 'hips': yaw_of_line(tl, tr), 'knees': round(math.degrees(math.atan2(k.y, k.x)))}
    if action == 'reffacing':
        # "skeleton@thigh_l@thigh_r@foot_l@toe_l@head": reference pose facing two ways - hip line (assumes a left-handed
        # body) and foot->toe (anatomy). Disagreement by 180 means the rig is mirrored front/back.
        import math
        path, tl, tr, fl, tt, hd = arg.split('@')
        asset = unreal.load_asset(path)
        skel = asset if isinstance(asset, unreal.Skeleton) else asset.get_editor_property('skeleton')
        ref = unreal.AnimPoseExtensions.get_reference_pose(skel)
        g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(ref, b, unreal.AnimPoseSpaces.WORLD).translation
        r = g(tr) - g(tl)
        f = g(tt) - g(fl)
        return {'hips': round(math.degrees(math.atan2(-r.x, r.y))), 'toes': round(math.degrees(math.atan2(f.y, f.x))),
                'thigh_l': [round(v) for v in (g(tl).x, g(tl).y, g(tl).z)], 'head': [round(v) for v in (g(hd).x, g(hd).y, g(hd).z)]}
    if action == 'arms':
        # "anim@thigh_l@thigh_r@shoulder_l@elbow_l@hand_l@shoulder_r@elbow_r@hand_r": elbows and hands relative to their
        # shoulder in the body frame [forward, left, up], as a fraction of the arm length, at 0.2/0.5/0.8 of the clip:
        # compares a capture with its retarget regardless of body size.
        path, tl, tr, sl, el, hl, sr, er, hr = arg.split('@')
        anim = unreal.load_asset(path)
        length = unreal.AnimationLibrary.get_sequence_length(anim)
        rows = []
        for f in (.2, .5, .8):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * f, unreal.AnimPoseEvaluationOptions())
            g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
            r = g(tr) - g(tl)
            n = max((r.x * r.x + r.y * r.y) ** .5, 1e-3)
            fx, fy = r.y / n, -r.x / n            # forward
            lx, ly = -r.x / n, -r.y / n           # left
            row = {}
            for side, (s0, e, h) in (('L', (sl, el, hl)), ('R', (sr, er, hr))):
                arm = (g(e) - g(s0)).length() + (g(h) - g(e)).length()
                rel = lambda b: [round((g(b) - g(s0)).x * fx + (g(b) - g(s0)).y * fy, 1) / arm,
                                 round((g(b) - g(s0)).x * lx + (g(b) - g(s0)).y * ly, 1) / arm, (g(b) - g(s0)).z / arm]
                row[side] = {'elbow': [round(v, 2) for v in rel(e)], 'hand': [round(v, 2) for v in rel(h)]}
            rows.append(row)
        return rows
    if action == 'bones':
        anim = unreal.load_asset(arg)
        ref = unreal.AnimPoseExtensions.get_reference_pose(anim.get_editor_property('skeleton'))
        return [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(ref)][:40]
    if action == 'orientmocap':
        return orient_mocap()
    if action == 'groundmocap':
        return ground_mocap()
    if action == 'rtgprobe':
        # Chains of a mocap IK rig, the retargeter's chain mapping and the IK rigs' retarget roots.
        clip = arg or 'dancing'
        src = unreal.load_asset(f'{RETARGET}/IK_Mocap_{clip}')
        tgt = unreal.load_asset(f'{RETARGET}/IK_MH_Body')
        rtg = unreal.load_asset(f'{RETARGET}/RTG_Mocap_{clip}')
        out = {}
        for tag, rig in (('src', src), ('tgt', tgt)):
            c = unreal.IKRigController.get_controller(rig)
            out[tag + '_root'] = str(c.get_retarget_root())
            out[tag + '_chains'] = [[str(ch.get_editor_property('chain_name')), str(ch.get_editor_property('start_bone').get_editor_property('bone_name')), str(ch.get_editor_property('end_bone').get_editor_property('bone_name'))] for ch in c.get_retarget_chains()]
        rc = unreal.IKRetargeterController.get_controller(rtg)
        try:
            out['mapping'] = {str(t): str(rc.get_source_chain(t)) for t in [ch[0] for ch in out['tgt_chains']]}
        except Exception as e:
            out['mapping'] = str(e)[:200]
        out['rc_methods'] = [m for m in dir(rc) if not m.startswith('_')][:120]
        return out
    if action == 'meshsize':
        m = unreal.load_asset(arg)
        b = m.get_bounds()
        return [round(b.box_extent.x * 2, 2), round(b.box_extent.y * 2, 2), round(b.box_extent.z * 2, 2)]
    if action == 'rtgops':
        rc = unreal.IKRetargeterController.get_controller(unreal.load_asset(f'{RETARGET}/RTG_Mocap_{arg or "dancing"}'))
        return [[i, str(rc.get_op_name(i)), rc.get_retarget_op_enabled(i)] for i in range(rc.get_num_retarget_ops())]
    if action == 'animcurve':
        # Pelvis and head height every 10% of each clip (does it sit down, stand up, lie down within the clip?).
        out = {}
        for clip in (arg or 'SitDrink,SitTalk,TalkGesture,LieDown,Dance,DanceHip,Cheer').split(','):
            anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
            length = unreal.AnimationLibrary.get_sequence_length(anim)
            opts = unreal.AnimPoseEvaluationOptions()
            row = []
            for k in range(11):
                pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * k / 10, opts)
                pz = unreal.AnimPoseExtensions.get_bone_pose(pose, 'pelvis', unreal.AnimPoseSpaces.WORLD).translation.z
                hz = unreal.AnimPoseExtensions.get_bone_pose(pose, 'head', unreal.AnimPoseSpaces.WORLD).translation.z
                row.append(f'{round(pz)}/{round(hz)}')
            out[clip] = [round(length, 1)] + row
        return out
    if action == 'facing':
        # Knees and toes relative to the pelvis (which way the clip faces) at 60% of each clip.
        out = {}
        for clip in (arg or 'Sitting_Idle,SitTalk,SitDrink,Idle,TalkGesture').split(','):
            anim = unreal.load_asset(f'{ANIMS}/MH_{clip}')
            length = unreal.AnimationLibrary.get_sequence_length(anim)
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, length * .6, unreal.AnimPoseEvaluationOptions())
            g = lambda b: unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
            pv, root = g('pelvis'), g('root')
            out[clip] = {'pelvis_from_root': [round(pv.x - root.x), round(pv.y - root.y), round(pv.z - root.z)],
                         'pelvis': [round(pv.x), round(pv.y), round(pv.z)],
                         'knee_l': [round(g('calf_l').x - pv.x), round(g('calf_l').y - pv.y)],
                         'knee_r': [round(g('calf_r').x - pv.x), round(g('calf_r').y - pv.y)],
                         'head': [round(g('head').x - pv.x), round(g('head').y - pv.y), round(g('head').z - pv.z)],
                         'toe_l': [round(g('ball_l').x - pv.x), round(g('ball_l').y - pv.y)]}
        return out
    if action == 'ls':
        return [str(x) for x in unreal.EditorAssetLibrary.list_assets(arg, True, False)][:80]
    if action == 'mocap':
        return import_mocap(arg or 'D:/CodexTemp/fab/anim')
    if action == 'remocap':
        return retarget_mocap('Lani', arg or '3')
    if action == 'show':
        # Preview static meshes side by side: "x,y,z@/Game/a/a,/Game/b/b" (tagged as previews, removed by mh_clear).
        loc, paths = arg.split('@')
        x, y, z = (float(v) for v in loc.split(','))
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        out = []
        for i, path in enumerate(paths.split(',')):
            mesh = unreal.load_asset(path)
            if not mesh:
                out.append(f'missing {path}')
                continue
            a = sub.spawn_actor_from_object(mesh, unreal.Vector(x + i * 40, y, z), unreal.Rotator(roll=0, pitch=0, yaw=0))
            a.tags = [unreal.Name('MareMHPreview')]
            out.append(path)
        return out
    if action == 'dress':
        # "Mateo@Beach@/Game/Outfits/Shorts/WI_OA_Shorts,/Game/..."
        name, suffix, items = arg.split('@')
        return dress_variant(name, suffix, items.split(','))
    if action == 'build':
        return build(arg or 'Lani')
    if action == 'save':
        # The build leaves its assets in memory; persist everything under the people folder.
        unreal.EditorAssetLibrary.save_directory(FOLDER, True, True)
        return unreal.EditorAssetLibrary.list_assets(f'{FOLDER}/{arg}' if arg else FOLDER, True, False)
    if action in ('rig', 'tex'):
        return cloud(arg or 'Lani', action)
    raise ValueError(action)

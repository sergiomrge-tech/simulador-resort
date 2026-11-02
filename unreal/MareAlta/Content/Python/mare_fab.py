"""Fab packs (Standard License) imported as separate furniture meshes for decorating the resort.
Wabi Sabi Boutique Guesthouse Interior Scene (Mint Studio): FBX + maps in D:/Assets/Fab/wabi_sabi."""
import json
from pathlib import Path
import unreal

PACKS = {'wabi': ('D:/Assets/Fab/wabi_sabi/wabi_sabi.fbx', '/Game/Fab/WabiSabi_m2')}
REPORT = Path('D:/CodexTemp/claude-mcp/fab_meshes.json')


def _pipeline():
    p = unreal.InterchangeGenericAssetsPipeline()
    p.mesh_pipeline.combine_static_meshes_behavior = unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE
    p.mesh_pipeline.build_nanite = True
    p.mesh_pipeline.fallback_collision_type = unreal.InterchangeMeshCollision.NONE
    p.common_meshes_properties.bake_meshes = False
    p.material_pipeline.search_location = unreal.InterchangeMaterialSearchLocation.LOCAL
    stack = unreal.InterchangePipelineStackOverride()
    stack.set_editor_property('override_pipelines', [unreal.SoftObjectPath(p.get_path_name())])
    return stack


def import_pack(key):
    source, folder = PACKS[key]
    task = unreal.AssetImportTask()
    task.filename = source
    task.destination_path = folder
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.options = _pipeline()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return inspect(key)


def inspect(key):
    folder = PACKS[key][1]
    rows = []
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        asset = unreal.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        box = asset.get_bounding_box()
        size = box.max - box.min
        rows.append({'path': path.split('.')[0], 'size_cm': [round(size.x), round(size.y), round(size.z)],
                     'tris': asset.get_num_triangles(0), 'mats': len(asset.static_materials)})
    rows.sort(key=lambda r: r['path'])
    REPORT.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding='utf-8')
    return {'meshes': len(rows), 'report': str(REPORT)}


GALLERY = unreal.Vector(0, 0, 60000)


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def gallery(ids, cols=4, step=260.0):
    """Temporary contact sheet high above the level: each candidate at 1/10 scale (pack is in mm) with its id."""
    clear_gallery()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    folder = PACKS['wabi'][1]
    rows = (len(ids) + cols - 1) // cols
    floor = actors.spawn_actor_from_object(unreal.load_asset('/Engine/BasicShapes/Plane'), GALLERY + unreal.Vector(cols * step / 2, rows * step / 2, 0))
    floor.set_actor_scale3d(unreal.Vector(cols * step / 100 + 4, rows * step / 100 + 4, 1))
    floor.tags = ['FabGallery']
    for i, mid in enumerate(ids):
        mesh = unreal.load_asset(f'{folder}/Mesh_ncl_{mid}')
        if not mesh:
            continue
        box = mesh.get_bounding_box()
        centre = (box.min + box.max) * 0.05
        base = GALLERY + unreal.Vector((i % cols + .5) * step, (i // cols + .5) * step, 0)
        a = actors.spawn_actor_from_object(mesh, base - unreal.Vector(centre.x, centre.y, box.min.z * .1))
        a.set_actor_scale3d(unreal.Vector(.1, .1, .1))
        a.tags = ['FabGallery']
    return {'placed': len(ids), 'origin': [GALLERY.x, GALLERY.y, GALLERY.z], 'rows': rows}


def clear_gallery():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone = [a for a in actors.get_all_level_actors() if 'FabGallery' in [str(t) for t in a.tags]]
    for a in gone:
        actors.destroy_actor(a)
    return {'removed': len(gone)}


def run(action, arg=''):
    if action == 'prune':
        return prune()
    if action == 'purge':
        return purge_old()
    if action == 'corona':
        return corona()
    if action == 'materials':
        return materials([int(v) for v in arg.split(',')])
    if action == 'gallery':
        return gallery([int(v) for v in arg.split(',')])
    if action == 'cleargallery':
        return clear_gallery()
    if action == 'import':
        return import_pack(arg or 'wabi')
    if action == 'decor':
        return decor()
    if action == 'clearbox':
        return clear_box(arg.replace('!', ''), arg.endswith('!'))
    if action == 'clearrooms':
        return clear_rooms(arg == 'apply')
    if action == 'probe':
        return probe(arg)
    if action == 'inspect':
        return inspect(arg or 'wabi')
    raise ValueError(action)


def materials(ids):
    folder = PACKS['wabi'][1]
    out = {}
    for mid in ids:
        mesh = unreal.load_asset(f'{folder}/Mesh_ncl_{mid}')
        rows = []
        for sm in mesh.static_materials:
            m = sm.material_interface
            if not m:
                rows.append(None)
                continue
            info = {'name': m.get_name(), 'class': m.get_class().get_name()}
            if isinstance(m, unreal.MaterialInstance):
                info['parent'] = m.parent.get_name() if m.parent else None
                info['tex'] = [(str(p.parameter_info.name), p.parameter_value.get_name() if p.parameter_value else None) for p in m.texture_parameter_values]
                info['vec'] = [(str(p.parameter_info.name), [round(p.parameter_value.r, 2), round(p.parameter_value.g, 2), round(p.parameter_value.b, 2)]) for p in m.vector_parameter_values]
                info['scal'] = [(str(p.parameter_info.name), round(p.parameter_value, 2)) for p in m.scalar_parameter_values]
            rows.append(info)
        out[mid] = rows
    return out


LINKS = Path('D:/CodexTemp/claude-mcp/wabi_links.json')
MASTER = '/Game/Fab/Materials/M_FabCorona'
MASTER_MASKED = '/Game/Fab/Materials/M_FabCoronaMasked'


def _master(path, masked):
    lib = unreal.MaterialEditingLibrary
    name = path.split('/')[-1]
    folder = path.rsplit('/', 1)[0]
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if masked:
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
        m.set_editor_property('two_sided', True)
    tex = lib.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0)
    tex.set_editor_property('parameter_name', 'Diffuse')
    tex.set_editor_property('texture', unreal.load_asset('/Engine/EngineResources/WhiteSquareTexture'))
    tint = lib.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, 300)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    mul = lib.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    lib.connect_material_expressions(tex, 'RGB', mul, 'A')
    lib.connect_material_expressions(tint, '', mul, 'B')
    lib.connect_material_property(mul, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = lib.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -250, 400)
    rough.set_editor_property('parameter_name', 'Roughness')
    rough.set_editor_property('default_value', 0.6)
    lib.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    if masked:
        op = lib.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -600, 600)
        op.set_editor_property('parameter_name', 'Opacity')
        op.set_editor_property('texture', unreal.load_asset('/Engine/EngineResources/WhiteSquareTexture'))
        lib.connect_material_property(op, 'R', unreal.MaterialProperty.MP_OPACITY_MASK)
    m.set_editor_property('used_with_nanite', True)
    m.set_editor_property('used_with_instanced_static_meshes', True)
    lib.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    return m


def corona():
    """Corona/V-Ray maps are lost by the FBX import; relink diffuse/opacity textures parsed from the FBX."""
    links = json.loads(LINKS.read_text(encoding='utf-8'))
    folder = PACKS['wabi'][1]
    solid, masked = _master(MASTER, False), _master(MASTER_MASKED, True)
    lib = unreal.MaterialEditingLibrary
    textures = {}
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        a = unreal.load_asset(path)
        if isinstance(a, unreal.Texture2D):
            textures[a.get_name().lower()] = a
    done, missing = 0, []
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        mi = unreal.load_asset(path)
        if not isinstance(mi, unreal.MaterialInstanceConstant):
            continue
        name = mi.get_name()
        key = name if name in links else (name[:-1] if name.endswith('1') and name[:-1] in links else None)
        slots = links.get(key, {}) if key else {}
        diffuse = next((f for p, f in slots.items() if f and ('baseTexmap' in p or 'texmapDiffuse' in p or 'mixmaps[0]' in p or 'texmapSkinColor' in p or p.endswith('LightMtlPb|texmap'))), '')
        opacity = next((f for p, f in slots.items() if f and 'opacityTexmap' in p), '')
        colour = next((v.parameter_value for v in mi.vector_parameter_values if str(v.parameter_info.name) == 'DiffuseColor'), unreal.LinearColor(.8, .8, .8, 1))
        shine = next((v.parameter_value for v in mi.scalar_parameter_values if str(v.parameter_info.name) == 'Shininess'), 32.0)
        lib.set_material_instance_parent(mi, masked if opacity else solid)
        tex = textures.get(Path(diffuse).stem.lower()) if diffuse else None
        if diffuse and not tex:
            missing.append(diffuse)
        if tex:
            lib.set_material_instance_texture_parameter_value(mi, 'Diffuse', tex)
            lib.set_material_instance_vector_parameter_value(mi, 'Tint', unreal.LinearColor(1, 1, 1, 1))
        else:
            lib.set_material_instance_vector_parameter_value(mi, 'Tint', colour)
        if opacity and textures.get(Path(opacity).stem.lower()):
            lib.set_material_instance_texture_parameter_value(mi, 'Opacity', textures[Path(opacity).stem.lower()])
        lib.set_material_instance_scalar_parameter_value(mi, 'Roughness', max(.25, min(.9, 1.0 - (shine / 256.0) ** .5)))
        unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
        done += 1
    return {'instances': done, 'textures': len(textures), 'missing': sorted(set(missing))[:20]}


def mesh(slug):
    """'fab:145' -> Wabi Sabi mesh 145 (authored in mm, placed at 1/10 scale)."""
    return unreal.load_asset(f"{PACKS['wabi'][1]}/Mesh_ncl_{slug.split(':')[1]}")


def place(actors, slug, x, y, floor_z, yaw, scale=1.0):
    """Spawn a pack mesh with its footprint centred on (x, y) and its base on floor_z (pivots are scene-space)."""
    import math
    m = mesh(slug)
    s = scale * .1
    b = m.get_bounds()
    ox, oy = b.origin.x * s, b.origin.y * s
    r = math.radians(yaw)
    dx, dy = ox * math.cos(r) - oy * math.sin(r), ox * math.sin(r) + oy * math.cos(r)
    z = floor_z - (b.origin.z - b.box_extent.z) * s
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x - dx, y - dy, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    actor.static_mesh_component.set_static_mesh(m)
    actor.set_actor_scale3d(unreal.Vector(s, s, s))
    return actor, (b.box_extent.z * 2) * s


def purge_old():
    """Remove the first, texture-less import (nothing references it)."""
    old = '/Game/Fab/WabiSabi'
    ok = unreal.EditorAssetLibrary.delete_directory(old) if unreal.EditorAssetLibrary.does_directory_exist(old) else None
    return {'deleted': ok}


KEEP = [145, 143, 144, 148, 151, 147, 150, 146, 153, 242, 240, 247, 84, 301, 216, 114, 17, 79, 127, 65, 315]


def prune(keep=KEEP):
    """Keep only the furniture/plants used for decoration (plus their materials and textures)."""
    folder = PACKS['wabi'][1]
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
    keep_pkgs, stack = set(), [f'{folder}/Mesh_ncl_{i}' for i in keep]
    while stack:
        pkg = stack.pop()
        if pkg in keep_pkgs:
            continue
        keep_pkgs.add(pkg)
        for dep in reg.get_dependencies(pkg, opts) or []:
            dep = str(dep)
            if dep.startswith(folder):
                stack.append(dep)
    # Deleting ~700 assets inside the editor crashed it (GPU page fault): write the list, delete files with it closed.
    drop = sorted({p.split('.')[0] for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True)} - keep_pkgs)
    Path('D:/CodexTemp/claude-mcp/fab_drop.json').write_text(json.dumps(drop), encoding='utf-8')
    return {'kept': len(keep_pkgs), 'drop': len(drop)}


def probe(arg):
    """Actors and instances inside a world rectangle 'x0,x1,y0,y1' (placement checks)."""
    x0, x1, y0, y1 = [float(v) for v in arg.split(',')]
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        p = a.get_actor_location()
        if x0 < p.x < x1 and y0 < p.y < y1:
            origin, ext = a.get_actor_bounds(True)
            out.append([a.get_actor_label(), [round(p.x), round(p.y), round(p.z)], [round(ext.x), round(ext.y), round(ext.z)]])
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh:
                continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                q = t.translation
                if x0 < q.x < x1 and y0 < q.y < y1 and t.scale3d.x > .01:
                    out.append([a.get_actor_label() + '/' + c.static_mesh.get_name(), [round(q.x), round(q.y), round(q.z)]])
    return out[:120]


# Bungalow interiors, in Blender room metres (x right, y to the back wall; tools/ue58/gen_rooms.py):
# reading chair under the right window, a low plant in the right-front corner, a stump side table.
BUNGALOW_DECOR = [
    [('fab:17', 1.82, -.45, (-1, 0)), ('fab:151', 1.86, -1.42, (-1, 0)), ('fab:240', 1.98, .22, (-1, 0))],
    [('fab:79', 1.82, -.45, (-1, 0)), ('fab:147', 1.82, -1.4, (-1, 0)), ('fab:247', 1.95, .25, (-1, 0))],
    [('fab:127', 1.82, -.45, (-1, 0)), ('fab:146', 1.8, -1.42, (-1, 0)), ('fab:240', 1.98, .22, (-1, 0))],
]
# Hotel restaurant pavilion (world cm): low potted plants along the front edge between the columns.
RESTAURANT_DECOR = [('fab:148', -1330, 3790, 0), ('fab:150', -1330, 4620, 0), ('fab:147', -1330, 4060, 0), ('fab:151', -1330, 4470, 0)]


def _floor(world, x, y, top):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, top), unreal.Vector(x, y, -500), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else None


def decor():
    """Place the remaining Wabi Sabi pieces in the pousada bungalows and the hotel restaurant."""
    import math, mare_beach
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in actors.get_all_level_actors():
        if 'MareFabDecor' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    rooms = {round(a.get_actor_location().x): a for a in actors.get_all_level_actors() if 'MareBungalow' in [str(t) for t in a.tags]}
    out = []
    for i, (bx, by, region) in enumerate(mare_beach.BUNGALOWS):
        room = rooms.get(bx)
        floor = room.get_actor_location().z + 49 if room else None
        for slug, lx, ly, face in BUNGALOW_DECOR[i]:
            # Bungalow yaw 180 and the Blender->UE Y flip: room (lx, ly) m -> world (bx - lx, by + ly).
            yaw = math.degrees(math.atan2(-face[1], -face[0]))
            actor, h = place(actors, slug, bx - lx * 100, by + ly * 100, floor, yaw)
            actor.set_actor_label(f'Bangalô {i + 1} · {slug}')
            actor.tags = [unreal.Name('MareGenerated'), unreal.Name(region), unreal.Name('MareFabDecor')]
            actor.set_folder_path('Interiors/Bungalows')
            out.append([slug, i + 1, round(h)])
    for slug, x, y, yaw in RESTAURANT_DECOR:
        z = _floor(world, x, y, 300)
        actor, h = place(actors, slug, x, y, z, yaw)
        actor.set_actor_label('Hotel restaurante · ' + slug)
        actor.tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name('MareFabDecor')]
        actor.set_folder_path('Hotel/Restaurant')
        out.append([slug, 'restaurant', round(z), round(h)])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out


def clear_box(arg, apply=False):
    """Lawn/flower instances poking through a building floor: "x0,x1,y0,y1,label_part" shrinks every instance of
    actors whose label contains label_part inside the box (Grand Hotel lobby: the 'lote grand_hotel' lawn dressing)."""
    x0, x1, y0, y1, part = arg.split(',')
    x0, x1, y0, y1 = float(x0), float(x1), float(y0), float(y1)
    hits = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if part not in a.get_actor_label():
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                tr = c.get_instance_transform(i, True)
                p = tr.translation
                if tr.scale3d.x > .01 and x0 < p.x < x1 and y0 < p.y < y1:
                    hits += 1
                    if apply:
                        tr.scale3d = unreal.Vector(.001, .001, .001)
                        c.update_instance_transform(i, tr, True, True, True)
    if apply and hits:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return hits


def clear_rooms(apply=False):
    """Instances (trees exported with generic names such as @MeshInstance3D@1068) standing inside a bungalow room or deck."""
    import mare_beach
    hits = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            name = c.static_mesh.get_name().lower() if c.static_mesh else ''
            if not name or a.get_actor_label().startswith('PCG') or any(k in name for k in ('grass', 'flower', 'fern', 'clover')):
                continue
            for i in range(c.get_instance_count()):
                tr = c.get_instance_transform(i, True)
                p = tr.translation
                if tr.scale3d.x > .01 and any(abs(p.x - bx) < 300 and by - 400 < p.y < by + 260 for bx, by, _ in mare_beach.BUNGALOWS):
                    hits.append([a.get_actor_label(), name, [round(p.x), round(p.y), round(p.z)]])
                    if apply:
                        tr.scale3d = unreal.Vector(.001, .001, .001)
                        c.update_instance_transform(i, tr, True, True, True)
    if apply:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return hits

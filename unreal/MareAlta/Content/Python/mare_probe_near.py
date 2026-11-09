"""Editor probe: static mesh components near a point (QA helper, 09/11). arg "x,y,z,radius" (cm)."""
import json
import unreal


def near(arg=''):
    x, y, z, r = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                n = c.get_instance_count()
                for i in range(min(n, 4000)):
                    l = c.get_instance_transform(i, True).translation
                    if (l.x - x) ** 2 + (l.y - y) ** 2 + (l.z - z) ** 2 < r * r:
                        out.append({'actor': actor.get_actor_label(), 'mesh': m.get_path_name(), 'inst': i, 'at': [round(l.x), round(l.y), round(l.z)],
                                    'mats': [c.get_material(k).get_path_name() if c.get_material(k) else None for k in range(c.get_num_materials())]})
                        break
            else:
                l = c.get_world_location()
                if (l.x - x) ** 2 + (l.y - y) ** 2 + (l.z - z) ** 2 < r * r:
                    out.append({'actor': actor.get_actor_label(), 'mesh': m.get_path_name(), 'at': [round(l.x), round(l.y), round(l.z)],
                                'mats': [c.get_material(k).get_path_name() if c.get_material(k) else None for k in range(c.get_num_materials())]})
    open("D:/CodexTemp/probe_near.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=0))
    return len(out)


def mat_info(arg=''):
    """Textures and scalar/vector values a material (or instance) uses. arg: asset path or name fragment under /Game."""
    path = arg
    if not path.startswith('/'):
        hits = [a for a in unreal.EditorAssetLibrary.list_assets('/Game', recursive=True) if arg in a]
        path = hits[0] if hits else ''
    m = unreal.load_asset(path)
    out = {'path': path, 'class': m.get_class().get_name() if m else None}
    if isinstance(m, unreal.MaterialInstance):
        out['parent'] = m.get_editor_property('parent').get_path_name()
        out['tex'] = [[str(p.parameter_info.name), p.parameter_value.get_path_name() if p.parameter_value else None] for p in m.get_editor_property('texture_parameter_values')]
        out['scal'] = [[str(p.parameter_info.name), p.parameter_value] for p in m.get_editor_property('scalar_parameter_values')]
    if isinstance(m, unreal.Material):
        out['used_tex'] = [t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(m)]
    return json.dumps(out, default=str)


def mesh_uv(arg=''):
    """UV0 extent and triangle count of a static mesh (LOD0 section 0) via the mesh description. arg: asset path."""
    m = unreal.load_asset(arg)
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    bb = m.get_bounding_box()
    return json.dumps({'tris': m.get_num_triangles(0), 'box': [str(bb.min), str(bb.max)], 'uv_channels': sub.get_num_uv_channels(m, 0),
                       'nanite': m.get_editor_property('nanite_settings').enabled})


def tex_info(arg=''):
    t = unreal.load_asset(arg)
    return json.dumps({'size': [t.blueprint_get_size_x(), t.blueprint_get_size_y()], 'srgb': t.get_editor_property('srgb'),
                       'source': t.get_editor_property('asset_import_data').get_first_filename() if t.get_editor_property('asset_import_data') else None})


def forest_meshes(arg=''):
    """Nanite settings, LODs and material blend modes of the island forest trees (far trees losing leaves, 09/11)."""
    import mare_mountains as mm
    out = {}
    for slug in (arg or 'World_0507,tree_small_02,World_0505,jacaranda_tree,World_0504,World_1206').split(','):
        m = mm._mesh(slug)
        ns = m.get_editor_property('nanite_settings')
        mats = []
        for sm in m.get_editor_property('static_materials'):
            mi = sm.material_interface
            base = mi.get_base_material() if mi else None
            mats.append([mi.get_name() if mi else None, str(base.get_editor_property('blend_mode')).split('.')[-1] if base else None,
                         base.get_editor_property('two_sided') if base else None])
        props = {}
        for p in ('enabled', 'preserve_area', 'explicit_tangents', 'fallback_percent_triangles', 'keep_percent_triangles', 'position_precision', 'shape_preservation'):
            try:
                v = ns.get_editor_property(p)
                props[p] = str(v)
            except Exception:
                pass
        out[slug] = {'path': m.get_path_name(), 'tris': m.get_num_triangles(0), 'lods': m.get_num_lods(), 'nanite': props, 'mats': mats}
    return json.dumps(out)


def forest_preserve_area(arg=''):
    """Far trees lost their leaves (09/11): Nanite simplified the leaf cards away at ~1 km. Shape preservation
    'Preserve Area' (made for foliage) keeps the leaf area as it simplifies. PIE stopped; saves the meshes."""
    import mare_mountains as mm
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    done = []
    for slug in (arg or 'World_0507,tree_small_02,World_0505,jacaranda_tree,World_0504,World_1206').split(','):
        m = mm._mesh(slug)
        ns = m.get_editor_property('nanite_settings')
        ns.set_editor_property('shape_preservation', unreal.NaniteShapePreservation.PRESERVE_AREA)
        sub.set_nanite_settings(m, ns, True)
        unreal.EditorAssetLibrary.save_loaded_asset(m, False)
        done.append([slug, str(m.get_editor_property('nanite_settings').get_editor_property('shape_preservation'))])
    return json.dumps(done)


def texts(arg=''):
    """TextRender components in the editor world whose text contains arg (case-insensitive)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.TextRenderComponent):
            t = str(c.get_editor_property('text'))
            if arg.lower() in t.lower():
                l = c.get_world_location()
                out.append({'actor': actor.get_actor_label(), 'comp': c.get_name(), 'text': t, 'at': [round(l.x), round(l.y), round(l.z)]})
    return json.dumps(out, ensure_ascii=False)


def pool_sign(_=''):
    """09/11: the pool sign read 'duche' (European Portuguese) in the Brazilian game: 'ducha'. PIE stopped; saves the level."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.TextRenderComponent):
            if str(c.get_editor_property('text')) == 'PISCINA<br>duche antes de entrar':
                c.set_editor_property('text', 'PISCINA<br>ducha antes de entrar')
                n += 1
    if n:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return n

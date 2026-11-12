"""Forest lighting (10/11, Sergio on the trail photo: "muito claras", "sem sombras"). probe() reports the sun, sky light
and the forest HISM settings that decide how dark the woods are."""
import json
import unreal

FOREST_LABEL = 'Ilha · floresta e coqueiros'
COVER_LABEL = 'Ilha · capim e plantas rasteiras'
MOUNTAIN_LABEL = 'Mountain vegetation'


def _props(obj, names):
    out = {}
    for n in names:
        try:
            v = obj.get_editor_property(n)
            out[n] = v if isinstance(v, (int, float, bool, str)) else str(v)
        except Exception as e:
            out[n] = 'ERR ' + str(e)[:60]
    return out


def probe(arg=''):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    rep = {'lights': [], 'sky': [], 'forest': {}}
    for a in actors:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            rep['lights'].append({'actor': a.get_actor_label(), **_props(c, [
                'intensity', 'cast_shadows', 'dynamic_shadow_distance_movable_light', 'dynamic_shadow_distance_stationary_light',
                'far_shadow_cascade_count', 'far_shadow_distance', 'shadow_amount', 'cast_ray_traced_shadows',
                'contact_shadow_length', 'atmosphere_sun_light', 'mobility', 'indirect_lighting_intensity',
                'shadow_source_angle_factor', 'light_source_angle'])})
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            rep['sky'].append({'actor': a.get_actor_label(), **_props(c, [
                'intensity', 'cast_shadows', 'real_time_capture', 'indirect_lighting_intensity', 'lower_hemisphere_is_black',
                'occlusion_max_distance', 'occlusion_contrast', 'occlusion_exponent', 'min_occlusion', 'mobility'])})
        lab = a.get_actor_label()
        if lab in (FOREST_LABEL, COVER_LABEL) or 'Mountain' in lab or 'Montanha' in lab or 'mata' in lab.lower():
            comps = {}
            for c in a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
                m = c.get_editor_property('static_mesh')
                comps[c.get_name()] = {'mesh': m.get_name() if m else None, 'n': c.get_instance_count(), **_props(c, [
                    'cast_shadow', 'cast_dynamic_shadow', 'cast_contact_shadow', 'cast_far_shadow', 'affect_dynamic_indirect_lighting',
                    'affect_distance_field_lighting', 'instance_start_cull_distance', 'instance_end_cull_distance',
                    'shadow_cache_invalidation_behavior', 'cast_shadow_as_two_sided'])}
                if m:
                    try:
                        comps[c.get_name()]['nanite'] = m.get_editor_property('nanite_settings').get_editor_property('enabled')
                    except Exception:
                        pass
            rep['forest'][lab] = comps
    lines = []
    for l in rep['lights']:
        lines.append('SUN ' + json.dumps(l, ensure_ascii=False, default=str))
    for l in rep['sky']:
        lines.append('SKY ' + json.dumps(l, ensure_ascii=False, default=str))
    for lab, comps in rep['forest'].items():
        lines.append('== %s (%d)' % (lab, len(comps)))
        for n, c in comps.items():
            lines.append('  %s n=%s sh=%s far=%s ind=%s df=%s cull=%s-%s nan=%s two=%s' % (c['mesh'], c['n'], c['cast_shadow'], c['cast_far_shadow'],
                         c['affect_dynamic_indirect_lighting'], c['affect_distance_field_lighting'], c['instance_start_cull_distance'],
                         c['instance_end_cull_distance'], c.get('nanite'), c['cast_shadow_as_two_sided']))
    return chr(10).join(lines)


WOODS = (FOREST_LABEL, 'Ilha · galhos, troncos e folhas do chão da mata', 'Mare · Vegetação das montanhas')


def canopy_df(arg='1'):
    """10/11: the woods' shadow casters (trees, palms, rocks, trunks) back in the distance field, still out of the Lumen
    card scene. On 08/11 the forest left Lumen altogether (`mare_island.forest_lumen 0`) because its cards kept daylight
    into the night; that also let the sky light through every canopy: leaves lit evenly and the forest floor as bright
    as a clearing. In the distance field (no cards) the trees block sky and bounce light again with nothing cached to go
    stale. arg '1' on, '0' back to 08/11. PIE stopped; saves the level."""
    on = arg.strip() != '0'
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() in WOODS:
            for c in a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
                if c.get_editor_property('cast_shadow'):
                    c.set_editor_property('affect_distance_field_lighting', on)
                    c.set_editor_property('affect_dynamic_indirect_lighting', False)
                    n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'components': n, 'distance_field': on})


def pp_probe(arg=''):
    """Post-process volumes: bounds, priority and the exposure settings they override."""
    lines = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            s = a.get_editor_property('settings')
            ov = {}
            for n in ('auto_exposure_method', 'auto_exposure_min_brightness', 'auto_exposure_max_brightness', 'auto_exposure_bias',
                      'auto_exposure_speed_up', 'auto_exposure_speed_down', 'auto_exposure_apply_physical_camera_exposure'):
                if s.get_editor_property('override_' + n):
                    ov[n] = s.get_editor_property(n)
            o, e = a.get_actor_bounds(False)
            lines.append('%s unbound=%s prio=%s blend=%s at=(%d,%d,%d) ext=(%d,%d,%d) tags=%s %s' % (
                a.get_actor_label(), a.get_editor_property('unbound'), a.get_editor_property('priority'), a.get_editor_property('blend_radius'),
                o.x, o.y, o.z, e.x, e.y, e.z, [str(t) for t in a.tags], ov))
    return chr(10).join(lines)

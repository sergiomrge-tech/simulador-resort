"""Full moon, stars and aurora in the night sky (09/11, Sergio: "coloque uma lua cheia nas noites", "lua que gera luz
noturna", "coloque nuvens de estrela no céu a noite, tipo aurora boreal").

The moon light (tag MareMoon) already lit the night faintly from a fixed direction. Now UMareVisualWorld turns it to rise
opposite the sun and keeps a disc in the sky along it: a camera-facing plane far away (tag MareMoonDisc) with an unlit
additive material that draws the real lunar surface. The colour map is NASA's CGI Moon Kit (LRO LROC colour mosaic,
public domain, SourceArt/Sky/T_MoonColor.jpg): the custom node turns the disc into a sphere's near side and reads the
equirectangular map by longitude/latitude, with a slight limb darkening and a soft halo.

The night sky dome (tag MareStarDome) is an inside-out sphere around the camera with an additive procedural material:
twinkling stars, the Milky Way band and an aurora's curtains low over the sea (green foot, violet top). Both materials
are fogged with the cloud contribution, so passing clouds cover them.

Editor, PIE stopped: mare_hud module "mare_moon.run|". Reexecutable (rebuilds the materials, replaces the actors)."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MEL = unreal.MaterialEditingLibrary
FOLDER = '/Game/World/Sky'

MOON_CODE = r'''
float2 p = (UV * 2.0 - 1.0) * 1.7;   // the disc fills 1/1.7 of the plane, the rest is halo
p.y = -p.y;
float r2 = dot(p, p);
float r = sqrt(r2);
float halo = exp(-max(r - 1.0, 0.0) * 5.0) * 0.06 * saturate(2.0 - r);
if (r2 >= 1.0) return float3(0.78, 0.85, 1.0) * halo * Bright;
float3 n = float3(p.x, p.y, sqrt(saturate(1.0 - r2)));
float lon = atan2(n.x, n.z);
float lat = asin(clamp(n.y, -1.0, 1.0));
float2 tuv = float2(0.5 + lon / 6.2831853, 0.5 - lat / 3.1415927);
float3 c = Texture2DSampleLevel(Tex, TexSampler, tuv, 0).rgb;
c = pow(saturate(c * 1.25), 1.7) * 1.6;   // more contrast for the maria (the raw map is pale)
float limb = 0.62 + 0.38 * n.z;
float edge = 1.0 - smoothstep(0.985, 1.0, r);
return (c * 1.35 * limb * edge + float3(0.78, 0.85, 1.0) * halo) * Bright;
'''

SKY_CODE = r'''
float3 d = normalize(Dir);
if (d.z < -0.03 || Night <= 0.001) return 0;
float up = smoothstep(-0.03, 0.12, d.z);
float3 col = 0;
// Milky Way: a band along a tilted great circle, broken by soft noise
float3 bn = normalize(float3(0.35, 0.78, 0.52));
float bd = dot(d, bn);
float band = exp(-bd * bd / 0.035);
float3 q = d * 6.0;
float nz = 0.0;
float amp = 0.5;
for (int i = 0; i < 5; i++) { nz += amp * (sin(q.x) * sin(q.y * 1.31) * sin(q.z * 0.77) * 0.5 + 0.5); q = q * 2.07 + float3(1.7, 9.2, 3.1); amp *= 0.5; }
float dust = smoothstep(0.35, 0.75, nz);
col += float3(0.55, 0.6, 0.8) * band * (0.25 + 0.75 * dust) * 0.10;
// stars: one random point per cell of a fine 3D grid on the sphere, denser in the band
float3 g = d * 520.0;
float3 cell = floor(g);
float h = frac(sin(dot(cell, float3(12.9898, 78.233, 37.719))) * 43758.5453);
float keep = 0.988 - 0.012 * band;
if (h > keep)
{
  float3 off = float3(frac(h * 13.1), frac(h * 71.7), frac(h * 31.3)) - 0.5;
  float dd = length(frac(g) - 0.5 - off * 0.5);
  float b = pow(frac(h * 997.0), 4.0);
  float tw = 0.7 + 0.3 * sin(Time * (1.3 + 3.0 * frac(h * 7.0)) + h * 50.0);
  float3 tint = lerp(float3(0.75, 0.85, 1.0), float3(1.0, 0.85, 0.7), frac(h * 41.0));
  col += tint * smoothstep(0.32, 0.0, dd) * (0.35 + 4.0 * b) * tw;
}
// aurora: curtains low over the sea (azimuth 0 = world -Y), green at the foot, violet on top, slowly waving
float az = atan2(d.x, -d.y);
float el = asin(clamp(d.z, -1.0, 1.0));
float win = exp(-az * az / 0.55);
float base = 0.06 + 0.06 * sin(az * 2.3 + Time * 0.04) + 0.025 * sin(az * 6.1 - Time * 0.07);
float hh = el - base;
float warp = az * 31.0 + 3.0 * sin(az * 4.7 + Time * 0.18) + 1.5 * sin(az * 13.0 - Time * 0.11);
float rays = 0.3 + 0.7 * pow(0.5 + 0.5 * sin(warp), 3.0) * (0.55 + 0.45 * sin(az * 8.3 - Time * 0.13));
float sheet = smoothstep(0.0, 0.02, hh) * exp(-max(hh, 0.0) * 9.0) * rays;
float pulse = 0.65 + 0.35 * sin(az * 1.7 - Time * 0.09);
float3 aur = lerp(float3(0.12, 1.0, 0.45), float3(0.65, 0.25, 1.0), saturate(hh * 4.0));
col += aur * sheet * win * pulse * 0.9 * Aurora;
return col * Night * up;
'''


def _connect(src, out, dst, name):
    if not MEL.connect_material_expressions(src, out, dst, name):
        raise RuntimeError('connect failed ' + name)


def _new_material(name):
    path = FOLDER + '/' + name
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    # fogged with the cloud contribution, so a cloud passing in front covers the moon and the stars
    mat.set_editor_property('use_translucency_vertex_fog', True)
    mat.set_editor_property('apply_cloud_fogging', True)
    mat.set_editor_property('compute_fog_per_pixel', True)
    return mat


def _custom(mat, code, desc, inputs):
    node = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -350, 100)
    node.set_editor_property('code', code)
    node.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    node.set_editor_property('description', desc)
    values = []
    for name in inputs:
        ci = unreal.CustomInput()
        ci.set_editor_property('input_name', name)
        values.append(ci)
    node.set_editor_property('inputs', values)
    for name, src in inputs.items():
        _connect(src, '', node, name)
    MEL.connect_material_property(node, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = MEL.recompile_material(mat) if hasattr(MEL, 'recompile_material') else None
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return errors


def _scalar(mat, name, y):
    node = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, y)
    node.set_editor_property('parameter_name', name)
    node.set_editor_property('default_value', 1.0)
    return node


def _mesh(source, name):
    path = FOLDER + '/' + name
    mesh = unreal.load_asset(path)
    if not mesh:
        unreal.EditorAssetLibrary.duplicate_asset(source, path)
        mesh = unreal.load_asset(path)
    nanite = mesh.get_editor_property('nanite_settings')
    nanite.set_editor_property('enabled', False)
    mesh.set_editor_property('nanite_settings', nanite)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return mesh


def texture():
    path = FOLDER + '/T_MoonColor'
    tex = unreal.load_asset(path)
    if not tex:
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'SourceArt/Sky/T_MoonColor.jpg')
        task.destination_path = FOLDER
        task.destination_name = 'T_MoonColor'
        task.automated = True
        task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(path)
    tex.set_editor_property('srgb', True)
    tex.set_editor_property('address_x', unreal.TextureAddress.TA_WRAP)
    tex.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
    return tex


def moon_material(tex):
    mat = _new_material('M_MoonDisc')
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    obj = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureObject, -700, 150)
    obj.set_editor_property('texture', tex)
    errors = _custom(mat, MOON_CODE, 'MareMoon', {'UV': uv, 'Tex': obj, 'Bright': _scalar(mat, 'Bright', 300)})
    return mat, errors


def sky_material():
    mat = _new_material('M_NightSky')
    wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -900, 0)
    cam = MEL.create_material_expression(mat, unreal.MaterialExpressionCameraPositionWS, -900, 120)
    sub = MEL.create_material_expression(mat, unreal.MaterialExpressionSubtract, -700, 50)
    _connect(wp, '', sub, 'A')
    _connect(cam, '', sub, 'B')
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -700, 200)
    errors = _custom(mat, SKY_CODE, 'MareNightSky', {'Dir': sub, 'Time': t, 'Night': _scalar(mat, 'Night', 300), 'Aurora': _scalar(mat, 'Aurora', 400)})
    return mat, errors


def _place(label, tag, mesh, mat):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in unreal.GameplayStatics.get_all_actors_with_tag(world, tag):
        sub.destroy_actor(a)
    actor = sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 300000), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    actor.tags = [tag]
    comp = actor.static_mesh_component
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    comp.set_material(0, mat)
    comp.set_cast_shadow(False)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_editor_property('affect_distance_field_lighting', False)
    comp.set_editor_property('affect_dynamic_indirect_lighting', False)
    return actor


def run(_=''):
    moon, moon_errors = moon_material(texture())
    _place('Céu · lua cheia', 'MareMoonDisc', _mesh('/Engine/BasicShapes/Plane', 'SM_MoonPlane'), moon)
    sky, sky_errors = sky_material()
    _place('Céu · estrelas e aurora', 'MareStarDome', _mesh('/Engine/BasicShapes/Sphere', 'SM_SkyDome'), sky)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'moon_errors': [str(e) for e in moon_errors or []], 'sky_errors': [str(e) for e in sky_errors or []]}, ensure_ascii=False)

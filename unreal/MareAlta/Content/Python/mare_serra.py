"""Mountain range across the sea (07/11, Sergio: "montanhas ao fundo, coloque isso no nosso jogo"): two ridges from
tools/ue58/gen_mountains.py (SourceArt/Models/Mountains), forest on the lower slopes, rock on the crests (UV1.u), and an
aerial haze toward the sky colour by distance from the camera (darkens at night through MPC_MareTime.Night).
Entry (mare_hud module): "mare_serra.build|" (editor, PIE stopped), "mare_serra.probe|"."""
import json
from pathlib import Path
import unreal
import mare_materials as mm
from mare_hotel_lobby import _import

ROOT = Path(unreal.Paths.project_dir()).resolve()
MEL = unreal.MaterialEditingLibrary
FOLDER = '/Game/World/Mountains'
# The beach looks toward -Y; the volcano sits 1.3 km out. The ridges stand far behind it, foot just below the sea.
PLACES = [('Serra ao fundo · perto', 'Mountains_Near', (2000.0, -520000.0, -40.0)),
          ('Serra ao fundo · longe', 'Mountains_Far', (-9000.0, -820000.0, -40.0))]


def _material():
    path = FOLDER + '/M_Mountains'
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Mountains', FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_nanite', True)
    uvm = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate, coordinate_index=1)
    pos = mm.expression(mat, unreal.MaterialExpressionWorldPosition)
    cam = mm.expression(mat, unreal.MaterialExpressionCameraPositionWS)
    nrm = mm.expression(mat, unreal.MaterialExpressionVertexNormalWS)
    night = mm._mpc(mat, 'Night')
    code = (
        'float2 q=P.xy/100; float n=frac(sin(dot(floor(q/180),float2(12.99,78.23)))*43758.55);'
        'float n2=frac(sin(dot(floor(q/47),float2(39.3,11.7)))*24634.6);'
        'float ridge=saturate(M.x); float hn=saturate(1-M.y);'   # glTF stores v flipped
        'float slope=1-saturate(N.z);'
        'float rock=saturate(ridge*.9+smoothstep(.62,.95,hn+.12*(n-.5))+smoothstep(.55,.8,slope));'
        'float3 forest=lerp(float3(.035,.07,.03),float3(.07,.11,.045),n2);'
        'float3 stone=lerp(float3(.16,.15,.14),float3(.23,.22,.2),n);'
        'float3 c=lerp(forest,stone,rock);'
        'float d=length(P-C)/100;'                                   # metres to the camera
        'float haze=saturate(1-exp(-d/11000))*.8;'
        'float3 sky=lerp(float3(.42,.52,.72),float3(.012,.016,.03),saturate(Nt));'
        'return lerp(c,sky,haze);')
    color = mm.custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'M': uvm, 'P': pos, 'C': cam, 'N': nrm, 'Nt': night})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(mm.expression(mat, unreal.MaterialExpressionConstant, r=1.0), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mm.expression(mat, unreal.MaterialExpressionConstant, r=0.1), '', unreal.MaterialProperty.MP_SPECULAR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError('M_Mountains ' + str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build(arg=''):
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    models = ROOT / 'SourceArt/Models/Mountains'
    mat = _material()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    have = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)}
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = {}
    for label, name, at in PLACES:
        mesh = _import(models / (name + '.glb'), FOLDER + '/' + name, name, True, search=False)
        a = have.get(label) or sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*at))
        a.set_actor_label(label)
        a.set_actor_location(unreal.Vector(*at), False, False)
        comp = a.static_mesh_component
        comp.set_static_mesh(mesh)
        comp.set_material(0, mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_collision_profile_name('NoCollision')
        comp.set_editor_property('can_ever_affect_navigation', False)
        comp.set_editor_property('cast_shadow', False)                      # 5 km away: shadows cost, add nothing
        comp.set_editor_property('affect_dynamic_indirect_lighting', False)
        comp.set_editor_property('affect_distance_field_lighting', False)
        o, e = a.get_actor_bounds(False)
        out[label] = {'origin': [round(o.x), round(o.y), round(o.z)], 'extent': [round(e.x), round(e.y), round(e.z)]}
    unreal.EditorLevelLibrary.save_current_level()
    return json.dumps(out)

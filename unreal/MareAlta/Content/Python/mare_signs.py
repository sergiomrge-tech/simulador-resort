"""Restore exported Label3D signs as native, correctly oriented TextRender actors."""
import unreal,json
from pathlib import Path
def text_material():
    """One-sided copy of the engine's opaque text material: the default renders both faces, so a sign seen from
    behind showed its text mirrored. Signs readable from both sides get a second text facing the other way."""
    path='/Game/World/Materials/M_TextOneSided'
    mat=unreal.load_asset(path)
    if not mat:
        mat=unreal.EditorAssetLibrary.duplicate_asset('/Engine/EngineMaterials/DefaultTextMaterialOpaque',path)
    mat.set_editor_property('two_sided',False)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
    return mat
def build():
    root=Path(unreal.Paths.project_dir()).resolve()
    rows=json.loads((root/'Content/Data/world.json').read_text(encoding='utf-8-sig'))['texts']
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if 'MareText' in [str(t) for t in actor.tags]:actors.destroy_actor(actor)
    stock={103:'coco_gelado',104:'suco',105:'caipirinha',106:'petiscos',107:'sorvete_morango',108:'sorvete_chocolate',109:'batata_frita',110:'porcao_peixe'}
    expanded=list(enumerate(rows))
    for source_index,new_index,z,height,text,size in [(32,111,-16.30,2.45,'MARÉ ALTA',18.),(33,112,-16.30,2.23,'QUIOSQUE • SABORES DA PRAIA',4.),(37,113,-15.465,2.32,'FECHADO',8.)]:
        row=json.loads(json.dumps(rows[source_index]));row['transform']['basis'][0]=[-v for v in row['transform']['basis'][0]];row['transform']['basis'][2]=[-v for v in row['transform']['basis'][2]]
        row['transform']['position'][1]=height;row['transform']['position'][2]=z;row['text']=text;row['size']=size;row['pixel_size']=.01
        expanded.append((new_index,row))
    # The food truck name floated over the middle of the roof as a double-sided label (mirrored from one side):
    # painted on both sides of the box instead, each facing out (box measured with traces: x 2440-2820, y 2975-3195; the north side is the serving hatch with an awning).
    for i,row in list(expanded):
        if row['text']=='Food truck do Pastel':
            expanded.remove((i,row))
            for k,(y,z,size,flip) in enumerate(((31.97,.86,24,False),(29.73,2.25,44,True))):   # north (serving side): under the counter
                side=json.loads(json.dumps(row));side['transform']['position']=[26.3,z,y];side['size']=size
                if flip:side['transform']['basis'][0]=[-v for v in side['transform']['basis'][0]];side['transform']['basis'][2]=[-v for v in side['transform']['basis'][2]]
                expanded.append((i if k==0 else 200,side))
    # Business signs float on their own (no wall behind): a second, back-to-back text so both sides read right.
    for i,row in list(expanded):
        if row.get('region','').startswith('Biz_') and row['text']!='Food truck do Pastel':
            back=json.loads(json.dumps(row));b=back['transform']['basis']
            back['transform']['position']=[back['transform']['position'][k]-b[2][k]*.02 for k in range(3)]
            b[0]=[-v for v in b[0]];b[2]=[-v for v in b[2]]
            expanded.append((300+i,back))
    material=text_material()
    for i,row in expanded:
        data=row['transform'];bx,by,bz=data['basis'];p=data['position']
        cv=lambda v:unreal.Vector(v[0],v[2],v[1])
        rotation=unreal.MathLibrary.make_rotation_from_axes(cv(bz),-cv(bx),cv(by))
        actor=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(p[0]*100,p[2]*100,p[1]*100),rotation)
        actor.set_actor_label('Letreiro · '+row['text'].split('\n')[0]);actor.tags=['MareGenerated','MareText','Region_'+row.get('region','')]
        comp=actor.get_component_by_class(unreal.TextRenderComponent)
        comp.set_text(row['text'].replace('\n','<br>'))
        comp.set_text_material(material)
        comp.set_world_size(row['size']*row['pixel_size']*100)
        comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        comp.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        comp.set_text_render_color(unreal.Color(36,31,24,255) if i in (36,37,100,101) else unreal.Color(239,235,222,255))
        comp.set_editor_property('cast_shadow',False)
        if i in (32,111):actor.tags=list(actor.tags)+['MareCompanySign']
        if i in (37,113):actor.tags=list(actor.tags)+['MareStatusSign'];comp.set_world_size(8.)
        if i in (100,101):actor.tags=list(actor.tags)+['MarePromoSign']
        if i==35:actor.tags=list(actor.tags)+['MareMenuSign']
        if i in stock:actor.tags=list(actor.tags)+['MareStock_'+stock[i]];comp.set_world_size(2.3)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'native_texts':len(expanded)}

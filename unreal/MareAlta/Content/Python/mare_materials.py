"""Native physically based coast materials, built with Unreal material expressions."""
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
MEL=unreal.MaterialEditingLibrary

def connect(source,output,destination,input_name):
    if not MEL.connect_material_expressions(source,output,destination,input_name):
        names=list(MEL.get_material_expression_input_names(destination))
        raise RuntimeError(f'Connection failed {type(destination).__name__}.{input_name}; inputs={names}')


def material(name):
    path='/Game/World/Materials/'+name
    mat=unreal.load_asset(path)
    if not mat:mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,'/Game/World/Materials',unreal.Material,unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat,old)
    if MEL.get_num_material_expressions(mat)!=0:raise RuntimeError('Old material graph not cleared')
    return mat

def expression(mat,cls,**values):
    node=MEL.create_material_expression(mat,cls)
    for key,value in values.items():node.set_editor_property(key,value)
    return node

def custom(mat,code,output,inputs):
    node=expression(mat,unreal.MaterialExpressionCustom,code=code,output_type=output)
    values=[]
    for name in inputs:
        value=unreal.CustomInput();value.set_editor_property('input_name',name);values.append(value)
    node.set_editor_property('inputs',values)
    for name,source in inputs.items():connect(source,'',node,name)
    return node

def texture(name,normal=False):
    path='/Game/World/Terrain/'+name
    tex=unreal.load_asset(path)
    if not tex:
        task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt'/'Terrain'/(name+'.jpg'));task.destination_path='/Game/World/Terrain';task.destination_name=name;task.automated=True;task.save=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=unreal.load_asset(path)
    if normal:
        tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('flip_green_channel',True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex

def build_ground(seabed=False,island=False):
    # 09/11 (C19, reference: strong caustics in the shallows): caustic lines sharper (pow 4) and twice as bright (x1.05).
    # 08/11 (the full island): seabed=True builds M_IslandSeabed_PBR, the same sand all wet (no grass, no dry band):
    # the old wet/inland bands follow the straight beach along y and painted the new sea floor green.
    # island=True builds M_IslandGround_PBR for the new land of the full island (gen_island_terrain.py, step 4): the
    # wet sand, dry sand and grass bands follow the distance to the coast (T_IslandSDF) instead of the straight y.
    mat=material('M_IslandSeabed_PBR' if seabed else 'M_IslandGround_PBR' if island else 'M_CoastGround_PBR')
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    uv=custom(mat,'return Position.xy * 0.0022;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    inputs={'Position':pos}
    for key,name in [('Sand','coast_sand_01'),('Wet','damp_beach_sand'),('Grass','leafy_grass')]:
        for normal in (False,True):
            tex=texture(name+('_nor' if normal else '_diff'),normal)
            node=expression(mat,unreal.MaterialExpressionTextureSample,texture=tex,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            connect(uv,'',node,'UVs')
            inputs[key+('Normal' if normal else '')]=node
    # Second, rotated and larger sampling of the dry sand hides the 4.5 m tile grid on pale sand.
    uv_b=custom(mat,'return float2(Position.x*.8-Position.y*.6,Position.x*.6+Position.y*.8)*0.00083;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    for normal in (False,True):
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=texture('coast_sand_01'+('_nor' if normal else '_diff'),normal),sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        connect(uv_b,'',node,'UVs')
        inputs['SandB'+('Normal' if normal else '')]=node
    # Copacabana-style dry sand (03/11, Sergio: "areia tipo Copacabana, volumosa e mais clara"): Poly Haven
    # aerial_sand (trampled beach, 15 m per tile; a second rotated sampling hides the repeat) for the volume, its AO
    # darkening the hollows, and dense_sand (1.8 m) for the fine grain up close.
    uv_t=custom(mat,'return Position.xy/1500.0;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    uv_t2=custom(mat,'return float2(Position.x*.6-Position.y*.8,Position.x*.8+Position.y*.6)/1150.0+.37;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    uv_f=custom(mat,'return Position.xy/180.0;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    for key,name,uvn in [('Tr','aerial_sand',uv_t),('Tr2','aerial_sand',uv_t2),('Fine','dense_sand',uv_f)]:
        for kind in ('diff','nor','ao'):
            tex=texture(f'{name}_{kind}',kind=='nor')
            if kind=='ao':
                tex.set_editor_property('srgb',False);unreal.EditorAssetLibrary.save_loaded_asset(tex)
            node=expression(mat,unreal.MaterialExpressionTextureSample,texture=tex,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if kind=='nor' else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR if kind=='ao' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            connect(uvn,'',node,'UVs')
            inputs[key+{'diff':'','nor':'Normal','ao':'AO'}[kind]]=node
    # 10/11 (checklist: the summit's bare face read as a pale beige cone above the forest from the sea): the steep-slope
    # rock is darker and big patches of it are covered in dark green growth, so from afar it sits with the forest.
    blend='float edge=sin(Position.x*.0017)*90+sin(Position.x*.0041)*35; float wet=1-smoothstep(-3400,-2400,Position.y+edge); float inland=smoothstep(-1200,-500,Position.y+edge*.6); '
    if seabed:
        # 09/11 (checklist: dark bands with straight edges in the west cove): 'sea' still followed the old bay's straight
        # beach (y < -43 m), so all round the rest of the island the floor was dark wet sand without the caustics, next to
        # the bright island floor. The sea floor is the lit bed everywhere.
        blend='float edge=-1000000; float wet=1; float inland=0; '
    if island:
        coast=custom(mat,'float2 uv=(Position.xy-float2(-160000,-110000))/320000.0; return -2950-(Texture2DSampleLevel(Tex,TexSampler,uv,0).r-.5)*80000.0;',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'Position':pos,'Tex':expression(mat,unreal.MaterialExpressionTextureObject,texture=island_sdf_texture())})
        inputs['Coast']=coast
        blend=blend.replace('Position.y+edge','Coast+edge')
        # 08/11 (Sergio: "galhos e folhas no chão da mata"): dry leaf litter (Poly Haven leaves_forest_ground, CC0, 3 m
        # tiles) on the forest floor, from ~35 m inland (where the trees start), in patches that leave grassy clearings.
        uv_l=custom(mat,'return Position.xy/300.0;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
        for normal in (False,True):
            node=expression(mat,unreal.MaterialExpressionTextureSample,texture=texture('leaves_forest_ground'+('_nor' if normal else '_diff'),normal),sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            connect(uv_l,'',node,'UVs')
            inputs['Leaf'+('Normal' if normal else '')]=node
        blend+='float pn=.5+.5*sin(Position.x*.0009+sin(Position.y*.0013)*2.3)*sin(Position.y*.0008+sin(Position.x*.0011)*1.7); float forest=smoothstep(500,2500,Coast)*(.3+.7*smoothstep(.3,.7,pn)); '
    color=custom(mat,blend+'float l=dot(Grass.rgb,float3(.2126,.7152,.0722)); float macro=.88+.12*sin(Position.x*.0013)*sin(Position.y*.0011); float detail=clamp(l*2.4,.65,1.25); float3 turf=lerp(Grass.rgb,float3(.115,.215,.06)*detail,.7)*macro; float mixb=.5+.35*sin(Position.x*.00031+sin(Position.y*.00047)*2.1)*sin(Position.y*.00027); float3 sand=lerp(Sand.rgb,SandB.rgb,mixb); float sl=dot(sand,float3(.2126,.7152,.0722)); float mt=.5+.4*sin(Position.x*.00021+sin(Position.y*.00033)*1.7); float lt=dot(lerp(Tr.rgb,Tr2.rgb,mt),float3(.2126,.7152,.0722)); float lf=dot(Fine.rgb,float3(.2126,.7152,.0722)); float ao=lerp(TrAO.r,Tr2AO.r,mt)*lerp(.82,1.0,FineAO.r); float shade=clamp(lt/.42,.78,1.12)*clamp(lf/.45,.9,1.08); float3 dry=float3(.95,.88,.74)*shade*lerp(.58,1.0,ao); float wl=dot(Wet.rgb,float3(.2126,.7152,.0722)); float3 damp=min(lerp(Wet.rgb,float3(wl,wl,wl),.3)*float3(1.35,1.3,1.2),float3(.66,.61,.53)); float sea=1-smoothstep(-4900,-4300,Position.y+edge); float2 cwarp=float2(sin(Position.y*.0023+Time*.05)+sin(Position.x*.0017-1.3),sin(Position.x*.0021-Time*.04)+sin(Position.y*.0013+2.1))*1.7; float2 c=(Position.xy*.011)+cwarp; float cw=sin(c.x+sin(c.y*1.3+Time*.7)*1.6)+sin(c.y*1.1+sin(c.x*1.2-Time*.6)*1.6); float2 cr=float2(c.x*.8-c.y*.6,c.x*.6+c.y*.8)*1.37+3.1; float cw2=sin(cr.x+sin(cr.y*1.2-Time*.55)*1.5)+sin(cr.y*1.15+sin(cr.x*1.1+Time*.65)*1.5); float cpatch=.35+.65*smoothstep(-.6,.9,sin(Position.x*.0009+sin(Position.y*.0011)*2.0)*sin(Position.y*.0008-1.0+sin(Position.x*.0007)*1.5)+.3); float caustic=(pow(saturate(1-abs(cw)*.6),4)*.65+pow(saturate(1-abs(cw2)*.6),4)*.5)*cpatch; float3 bed=dry*float3(.9,.93,.92)*(1+caustic*1.05); '+('float3 g=lerp(lerp(lerp(dry,damp,wet),bed,sea),turf,inland); g=lerp(g,Leaf.rgb*float3(.95,.92,.86),forest); float under=1-smoothstep(-80.0,-15.0,Position.z); g=lerp(g,bed,under); float steep=1-smoothstep(.55,.8,abs(N.z)); float2 suv=(abs(N.x)>abs(N.y)?Position.yz:Position.xz)/260.0; float rl=0.0; float amp=.5; float2 pp=suv*1.7; for(int o=0;o<5;o++){float2 ci=floor(pp); float2 cf=frac(pp); cf=cf*cf*(3.0-2.0*cf); float ha=frac(sin(dot(ci,float2(127.1,311.7)))*43758.5453); float hb=frac(sin(dot(ci+float2(1,0),float2(127.1,311.7)))*43758.5453); float hc=frac(sin(dot(ci+float2(0,1),float2(127.1,311.7)))*43758.5453); float hd=frac(sin(dot(ci+float2(1,1),float2(127.1,311.7)))*43758.5453); rl+=amp*lerp(lerp(ha,hb,cf.x),lerp(hc,hd,cf.x),cf.y); pp=pp*2.07+float2(5.2,1.3); amp*=.5;} float crack=smoothstep(.36,.30,rl); float moss=smoothstep(.42,.58,rl)*.85; float big=.5+.5*sin(Position.x*.0011+sin(Position.y*.0013)*2.0)*sin(Position.z*.0017+sin(Position.x*.0009)*1.5); moss=saturate(moss+smoothstep(.3,.7,big)*.75); float3 stone=lerp(float3(.085,.08,.065),float3(.20,.185,.15),saturate((rl-.25)*2.2))*(1.0-.35*crack); float3 rock=lerp(stone,float3(.065,.115,.04)*(.75+.5*rl),moss); return lerp(g,rock,steep);' if island else 'return lerp(lerp(lerp(dry,damp,wet),bed,sea),turf,inland);'),unreal.CustomMaterialOutputType.CMOT_FLOAT3,dict({k:v for k,v in inputs.items() if 'Normal' not in k},Time=expression(mat,unreal.MaterialExpressionTime),**({'N':expression(mat,unreal.MaterialExpressionVertexNormalWS)} if island else {})))
    for key in ('TrAO','Tr2AO','FineAO'):MEL.connect_material_expressions(inputs[key],'R',color,key)
    normal=custom(mat,blend+'float mixb=.5+.35*sin(Position.x*.00031+sin(Position.y*.00047)*2.1)*sin(Position.y*.00027); float mt=.5+.4*sin(Position.x*.00021+sin(Position.y*.00033)*1.7); float3 tn=lerp(TrNormal.xyz,Tr2Normal.xyz,mt); float3 sn=normalize(float3(tn.xy*1.7+FineNormal.xy*.6,tn.z)); '+('return normalize(lerp(lerp(lerp(sn,WetNormal.xyz,wet),GrassNormal.xyz,inland),LeafNormal.xyz,forest));' if island else 'return normalize(lerp(lerp(sn,WetNormal.xyz,wet),GrassNormal.xyz,inland));'),unreal.CustomMaterialOutputType.CMOT_FLOAT3,{k:v for k,v in inputs.items() if k in ('Position','Coast') or 'Normal' in k})
    rough=custom(mat,blend+('return lerp(lerp(lerp(.9,.45,wet),.96,inland),.92,forest);' if island else 'return lerp(lerp(.9,.45,wet),.96,inland);'),unreal.CustomMaterialOutputType.CMOT_FLOAT1,{k:v for k,v in inputs.items() if k in ('Position','Coast')})
    for node,prop in [(color,unreal.MaterialProperty.MP_BASE_COLOR),(normal,unreal.MaterialProperty.MP_NORMAL),(rough,unreal.MaterialProperty.MP_ROUGHNESS)]:MEL.connect_material_property(node,'',prop)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def island_sdf_texture():
    """T_IslandSDF (tools/ue58/gen_island.py): 16-bit coast distance, imported linear as half float, no mips."""
    path='/Game/World/Island/T_IslandSDF'
    task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt'/'Island'/'T_IslandSDF.png');task.destination_path='/Game/World/Island'
    task.destination_name='T_IslandSDF';task.automated=True;task.save=True;task.replace_existing=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex=unreal.load_asset(path)
    tex.set_editor_property('srgb',False)
    tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_HALF_FLOAT)
    tex.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('never_stream',True)
    tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex

def build_water():
    mat=material('M_CoastalWater_PBR')
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('used_with_nanite',False)
    mat.set_editor_property('automatically_set_usage_in_editor',False)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    time=expression(mat,unreal.MaterialExpressionTime)
    storm=_mpc(mat,'Storm')
    # 08/11 (the full island, ILHA_PLANO step 3): what used to follow the straight beach along y follows the distance to
    # the nearest coast: T_IslandSDF (gen_island.py, 0.5 = coast, +-400 m) gives Yc = the old bay y at the same distance
    # (bay waterline -2950 minus the distance), so the shore break, the swell rolling in, the shallow colours and the
    # clear shallows go all round the island. Coast.yz = gradient of Yc (towards the coast), for the swell's push.
    sdf_tex=island_sdf_texture()
    sdf_obj=expression(mat,unreal.MaterialExpressionTextureObject,texture=sdf_tex)
    coast_node=custom(mat,'float2 uv=(Position.xy-float2(-160000,-110000))/320000.0; float e=1.0/1024.0; float s=Texture2DSampleLevel(Tex,TexSampler,uv,0).r; float sx=Texture2DSampleLevel(Tex,TexSampler,uv+float2(e,0),0).r; float sy=Texture2DSampleLevel(Tex,TexSampler,uv+float2(0,e),0).r; float k=2*40000.0; float yc=-2950-(s-.5)*k; return float3(yc,-(sx-s)*k/312.5,-(sy-s)*k/312.5);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Tex':sdf_obj})
    # 09/11 (B14): the grid now carries on to the horizon as a ring of large flat quads (tools/ue58/gen_ocean.py); 'rim'
    # brings the waves down to flat over the last 150 m of the detailed grid (x -1300..1350 m, y -2432..2050 m) so the
    # T-junctions where the two meet stay shut. AMarePerson::SeaHeight has the same factor.
    # 05/11: inside the tour boat's hull (MPC Boat*) the surface goes flat at BoatH, under the deck.
    # 08/11 (Sergio: "quando tem tsunami, a água recua um pouco, aí depois vem"): MPC Drawback (cm) lowers the sea
    # within ~150 m of every coast, fading out by ~400 m (AMarePerson::SeaHeight has the same term).
    # 04/11 (Sergio again: 'mar muito calmo'): long ~60 m swell ~1.7 m crest to trough, mid waves x1.7, sharp Gerstner-like
    # crests and waves kept out to ~300 m. Before: baseline swell ~75 cm offshore / 37 cm at the shore (03/11, three times: 'mais ondas', 'parece lago', 'mais agitado'); Storm (rough-sea
    # days) scales it 2.4x, adds a short choppy wave and whitecaps.
    wpo=custom(mat,'float Yc=Coast.x; float2 Gc=Coast.yz; float a=Position.x*.003+Position.y*.0017-Time*(.55+Storm*.35); float b=Position.y*.004-Position.x*.0012-Time*(.38+Storm*.3); float c=Position.x*.011+Position.y*.007-Time*1.9; float shore=smoothstep(-6500,-4300,Yc)*(1-smoothstep(-3000,-2300,Yc)); float swell=sin(Yc*.009+sin(Position.x*.0025)*.7-Time*(.8+Storm*.4)); float2 outside=max(float2(0,-30000-Yc),0); float fade=1-smoothstep(4000,20000,length(outside))*.6; float offshoreWaves=smoothstep(-2600,-6500,Yc); float d=Position.x*.0069-Position.y*.0052-Time*1.15; float sw=Yc*.00105+Position.x*.00028-Time*.42; float swell2=(sin(sw)*.75+.25*sin(sw*2+1.1))*85;float h=swell2*(1+Storm*.7)+(sin(a)*60+sin(b)*40+sin(d)*22)*(1+Storm*1.1)+sin(c)*(12+Storm*10)+sin(Position.x*.019-Position.y*.013-Time*2.6)*6; float coast=lerp(.35,1,smoothstep(-5500,-11000,Yc)); float2 pq=abs(Position.xy-float2(6780,-4300))-float2(450,1100); float pier=lerp(.2,1,smoothstep(0,900,length(max(pq,0)))); float2 rq=(Position.xy-float2(4200,-13100))*float2(1,1.8); float calm=lerp(.08,1,smoothstep(2200,5200,length(rq))); float k=fade*offshoreWaves*coast*pier*calm; float2 dir=length(Gc)>.01?normalize(Gc+float2(.28,0)):normalize(float2(.28,1.05)); float2 xy=-dir*cos(sw)*55*(1+Storm*.6)*k-normalize(float2(.003,.0017))*cos(a)*22*k; float3 wv=float3(xy,h*k+shore*(swell*15*(1+Storm*.8)+7+Storm*5)*pier-DB*(1-smoothstep(-17950,-42950,Yc))); float cy=cos(BYaw*.0174533); float sy=sin(BYaw*.0174533); float2 rel=Position.xy-float2(BX,BY); float al=rel.x*cy+rel.y*sy; float ac=-rel.x*sy+rel.y*cy; float e=al*al/(530.0*530.0)+ac*ac/(170.0*170.0); float m=(1-smoothstep(.75,1.0,e))*BOn; float rim=smoothstep(0,15000,min(min(Position.x+130000,135000-Position.x),min(Position.y+243200,205000-Position.y))); wv*=rim; return float3(wv.xy*(1-m),lerp(wv.z,BH,m));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Time':time,'Storm':storm,'BX':_mpc(mat,'BoatX'),'BY':_mpc(mat,'BoatY'),'BYaw':_mpc(mat,'BoatYaw'),'BH':_mpc(mat,'BoatH'),'BOn':_mpc(mat,'BoatOn'),'DB':_mpc(mat,'Drawback'),'Coast':coast_node})
    uv1=custom(mat,'return Position.xy*.0015 + Time*float2(.017,.011);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    uv2=custom(mat,'return float2(Position.x-Position.y*.37,Position.y+Position.x*.29)*.0021 + Time*float2(-.013,.008);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    water_normal=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    samples=[]
    uv3=custom(mat,'return float2(Position.x+Position.y*.21,Position.y-Position.x*.33)*.0043 + Time*float2(.031,-.022);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    for uv in (uv1,uv2,uv3):
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=water_normal,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(uv,'',node,'UVs');samples.append(node)
    # 08/11 (Sergio: 'diminua as ondas, ondas fortes só quando estiver chovendo'): Storm goes below zero on fair days
    # (mare.SeaCalm, MareVisualWorld), which shrinks the heights; colour and foam only follow its positive part.
    # 05/11 (snorkel, CHECKLIST_EXPANSOES 2.3): the offshore reef (~42 x 13 m core around 4200,-13100) is a sheltered spot
    # where the swell drops to 8% ('calm', in the WPO, its slope and AMarePerson::SeaHeight): swimmers there have a
    # flat swimming volume and the ~2 m open-sea waves rolled over their heads.
    # Three scales of ripples (swell, wind waves, fine chop) so the sea never looks like a lake (03/11).
    # Large WPO waves do not bend the vertex normals: their analytic slope is added so the swells catch the light (04/11).
    slope=custom(mat,'float Yc=Coast.x; float2 Gc=Coast.yz; float2 rq=(Position.xy-float2(4200,-13100))*float2(1,1.8); float off=smoothstep(-2600,-6500,Yc)*lerp(.35,1,smoothstep(-5500,-11000,Yc))*lerp(.08,1,smoothstep(2200,5200,length(rq))); float a=Position.x*.003+Position.y*.0017-Time*(.55+Storm*.35); float b=Position.y*.004-Position.x*.0012-Time*(.38+Storm*.3); float sw=Yc*.00105+Position.x*.00028-Time*.42; float d=Position.x*.0069-Position.y*.0052-Time*1.15; float m=1+Storm*1.1; float2 g=(float2(.00028,0)+.00105*Gc)*(cos(sw)*.75+.5*cos(sw*2+1.1))*85*(1+Storm*.7)+(float2(.003,.0017)*cos(a)*60+float2(-.0012,.004)*cos(b)*40+float2(.0069,-.0052)*cos(d)*22)*m; return g*off;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time,'Storm':storm,'Coast':coast_node})
    normal=custom(mat,'return normalize(float3((A.xy+B.xy+C.xy*.8)*(.6+Storm*.4)-S*.7,max(.4,A.z*B.z)));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'A':samples[0],'B':samples[1],'C':samples[2],'Storm':storm,'S':slope})
    color=custom(mat,'float Yc=Coast.x; float offshore=1-smoothstep(-17000,-4000,Yc); float near=1-smoothstep(-9000,-4200,Yc); float3 sea=lerp(lerp(float3(.05,.40,.31),float3(.018,.21,.22),near),float3(.006,.055,.12),offshore); float shore=smoothstep(-6500,-4300,Yc)*(1-smoothstep(-3000,-2300,Yc)); float phase=Yc*.009+sin(Position.x*.0025)*.7-Time*.8; float crest=smoothstep(.80,.985,sin(phase)); float n1=sin(Position.x*.0023+sin(Position.y*.004)*.8+Time*.1)*.5+.5; float n2=sin(Position.x*.0061-Time*.17+sin(Position.x*.0013)*2.0)*.5+.5; float breaks=smoothstep(.3,.75,n1)*(.55+.45*smoothstep(.2,.8,n2)); sea=lerp(sea,float3(.035,.06,.065),saturate(Storm)*.6); float crest2=smoothstep(.74-saturate(Storm)*.2,.985,sin(phase)); float wx=Position.x+sin(Position.y*.0011+Time*.05)*900+sin(Position.x*.0007+Position.y*.0005)*1400; float wy=Position.y+sin(Position.x*.0009-Time*.04)*1100+sin(Position.x*.00031-Position.y*.00027)*1700; float patch=smoothstep(.45,.85,sin(Position.x*.00041+Position.y*.00023+Time*.03)*.35+sin(Position.y*.00057-Position.x*.00019-Time*.02)*.35+sin(wx*.0013-wy*.0009)*.3+.5); float caps=saturate(Storm)*smoothstep(.86,.99,sin(wx*.0031+wy*.0019-Time*.9)*sin(wy*.0043+wx*.0007-Time*.6))*(1-shore)*(.25+.75*patch); float crest1=smoothstep(.74,.985,sin(phase)); float whitecap=smoothstep(.93,.995,sin(wx*.003+wy*.0017-Time*.55)*.5+sin(wy*.004-wx*.0012-Time*.38)*.5)*(1-shore)*.35*patch; return lerp(sea,float3(.84,.89,.88),saturate(shore*lerp(crest1,crest2,saturate(Storm))*breaks*(.22+saturate(Storm)*.5)+caps*.7+whitecap*saturate(Storm)));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Time':time,'Storm':storm,'Coast':coast_node})
    # Shore foam (03/11, Sergio: espuma na transição da água para a areia): water depth from the scene behind the
    # water (SceneDepthWithoutWater) minus the surface depth; a solid white band where it is very shallow, broken up
    # by noise, plus foam lines running in towards the beach in the shallows; stronger in a storm.
    behind=expression(mat,unreal.MaterialExpressionSceneDepthWithoutWater)
    surface=expression(mat,unreal.MaterialExpressionPixelDepth)
    foam=custom(mat,'float d=max(Behind-Surface,0); float n=(A.x*.5+.5)*.55+(sin(Position.x*.013+sin(Position.y*.017)*2.0-Time*.6)*.5+.5)*.45; float edge=1-smoothstep(4,38+Storm*30,d+n*14); float wash=smoothstep(.62,.93,sin(d*.09-Time*2.1+n*4.0)*.5+.5)*(1-smoothstep(25,160+Storm*120,d)); return saturate(edge*(.55+.45*n)+wash*(.35+Storm*.3));',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'Behind':behind,'Surface':surface,'Position':pos,'Time':time,'Storm':storm,'A':samples[0]})
    final=custom(mat,'return lerp(Sea,float3(.9,.93,.92),F);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Sea':color,'F':foam})
    rough=custom(mat,'return lerp(.24,.75,F);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'F':foam})
    specular=expression(mat,unreal.MaterialExpressionConstant,r=.25)
    MEL.connect_material_property(specular,'',unreal.MaterialProperty.MP_SPECULAR)
    # Crystal-clear shallows (03/11, Sergio's photo: green, transparent, sand visible): nearly see-through where the
    # bottom is close, denser over deep water; foam stays opaque.
    depth=custom(mat,'return max(Behind-Surface,0);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'Behind':behind,'Surface':surface})
    # Density grows smoothly with the distance from the beach (the modelled sea floor ends abruptly offshore, so a
    # depth-only fade drew a hard line there); depth only clears the very shallow water at the sand.
    opacity=custom(mat,'float far=lerp(.10,.62,smoothstep(-4600,-14000,Coast.x)); return lerp(lerp(.06,far,smoothstep(20,260,D)),1.0,F);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'F':foam,'D':depth,'Coast':coast_node})
    for node,prop in [(wpo,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET),(normal,unreal.MaterialProperty.MP_NORMAL),(final,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(opacity,unreal.MaterialProperty.MP_OPACITY)]:MEL.connect_material_property(node,'',prop)
    output=expression(mat,unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    # Clear tropical water: red absorbed first, blue a little more than green, so shallow water reads green-turquoise.
    # 09/11 (B6, 'mar verde ao pôr do sol'): with green scattering above blue, the yellow light of the late afternoon
    # (16h30-17h30) turned the whole sea emerald, near and far. Blue now scatters a little more than green: still
    # turquoise by day (the shallows keep their own green base colour), no longer green under a low sun. Green is also
    # absorbed a little more (.0019 -> .0026): deep water seen at a grazing angle (the horizon at 17h) was lime green.
    # At a grazing angle (the horizon seen from the beach) real water shows almost only the reflection; here the
    # scattered light stayed and, added to the yellow sky in the reflection, drew a lime band along the horizon at
    # 17h. The scattering fades to a quarter as the view gets flat.
    scatter_base=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.0004,.0020,.0034,1))
    camera=expression(mat,unreal.MaterialExpressionCameraVectorWS)
    scattering=custom(mat,'float g=pow(1-saturate(abs(V.z)),6); return S*lerp(1,.25,g);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'S':scatter_base,'V':camera})
    absorption=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.013,.0026,.0032,1))
    connect(scattering,'',output,'ScatteringCoefficients')
    connect(absorption,'',output,'AbsorptionCoefficients')
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_pool_water():
    """Clear swimming-pool water (Single Layer Water): the exported Godot pool shader fell back to
    an opaque dark green; this replaces it with bright, transparent pool-blue water."""
    mat=material('M_PoolWater_PBR')
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('used_with_nanite',False)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    time=expression(mat,unreal.MaterialExpressionTime)
    water_normal=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    samples=[]
    for code in ('return Position.xy*.004 + Time*float2(.03,.02);','return float2(Position.x-Position.y*.4,Position.y+Position.x*.3)*.006 + Time*float2(-.02,.025);'):
        uv=custom(mat,code,unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=water_normal,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(uv,'',node,'UVs');samples.append(node)
    normal=custom(mat,'return normalize(float3((A.xy+B.xy)*.07,1));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'A':samples[0],'B':samples[1]})
    # Clear, chlorinated water: little colour of its own; the tint comes from depth (absorption below).
    color=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.02,.11,.12,1))
    rough=expression(mat,unreal.MaterialExpressionConstant,r=.02)
    MEL.connect_material_property(expression(mat,unreal.MaterialExpressionConstant,r=.5),'',unreal.MaterialProperty.MP_SPECULAR)
    opacity=expression(mat,unreal.MaterialExpressionConstant,r=.5)
    for node,prop in [(normal,unreal.MaterialProperty.MP_NORMAL),(color,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(opacity,unreal.MaterialProperty.MP_OPACITY)]:MEL.connect_material_property(node,'',prop)
    output=expression(mat,unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    # Per cm, like the sea (M_CoastalWater_PBR) but ~4x clearer: 1.5 m keeps ~70% green/blue and ~15% red,
    # so the tiled floor stays visible with the natural cyan of a real pool.
    connect(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.0003,.0016,.0018,1)),'',output,'ScatteringCoefficients')
    connect(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.013,.0026,.002,1)),'',output,'AbsorptionCoefficients')
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_pool_tiles():
    """Pool floor and walls: 5 cm glass mosaic (aqua tiles, light grout, per-tile shade) with sunlit
    caustics, so the bottom reads through the clear M_PoolWater_PBR like in a real pool."""
    mat=material('M_PoolTiles_PBR')
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mat.set_editor_property('used_with_nanite',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    nrm=expression(mat,unreal.MaterialExpressionVertexNormalWS)
    time=expression(mat,unreal.MaterialExpressionTime)
    night=expression(mat,unreal.MaterialExpressionCollectionParameter,collection=time_collection(),parameter_name='Night')
    plane='float3 an=abs(N); float2 uv=an.z>.5?P.xy:(an.x>an.y?P.yz:P.xz);'
    color=custom(mat,plane+'float2 cell=floor(uv/5.0); float2 g=frac(uv/5.0); float grout=smoothstep(.0,.07,min(g.x,g.y))*smoothstep(1.0,.93,max(g.x,g.y)); float h=frac(sin(dot(cell,float2(12.9898,78.233)))*43758.5453); float3 tile=lerp(float3(.30,.60,.74),float3(.38,.68,.80),h); tile*=.94+.06*frac(h*7.31); return lerp(float3(.80,.83,.80),tile,grout);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'P':pos,'N':nrm})
    rough=custom(mat,plane+'float2 g=frac(uv/5.0); float grout=smoothstep(.0,.07,min(g.x,g.y))*smoothstep(1.0,.93,max(g.x,g.y)); return lerp(.75,.18,grout);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'P':pos,'N':nrm})
    # Caustics: three warped sine fields; bright thin lines where their sum crosses zero, drifting slowly.
    caustic=custom(mat,plane+'float2 q=uv*.02; float t=T*.55; float a=sin(q.x*1.7+sin(q.y*1.3+t)*1.6+t*.7); float b=sin(q.y*1.9+sin(q.x*1.1-t*.8)*1.7-t*.5); float c=sin((q.x+q.y)*1.3+sin(q.x*.7-q.y*.9+t*.9)*1.4+t*.4); float v=abs(a+b+c)/3.0; float lines=pow(saturate(1.0-v),6.0); float floorOnly=saturate(abs(N.z)*1.5-.3); return float3(1.0,.98,.9)*lines*floorOnly*(1.0-Night)*1.1;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'P':pos,'N':nrm,'T':time,'Night':night})
    # Orca mural on each pool floor (Canva mosaic, one texel per 5 cm tile, tools/ue58/orca_mural.py):
    # 6 x 3 m in the resort pool, 9 x 4.5 m in the Grand Hotel pool, aligned to the tile grid.
    mural=_custom_texture('orca_mural.png')
    mural.set_editor_property('filter',unreal.TextureFilter.TF_NEAREST)
    mural.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    mural.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    mural.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP);mural.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(mural)
    place='bool hotel=abs(P.x+2600)<1300 && abs(P.y-3600)<800; float2 c=hotel?float2(-2600,3600):float2(0,400); float2 size=hotel?float2(900,450):float2(600,300);'
    mural_uv=custom(mat,place+'float2 cell=floor((P.xy-c+size*.5)/5.0); float2 uv=(cell+.5)/(size/5.0); return float2(uv.x,1.0-uv.y);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'P':pos})
    sample=expression(mat,unreal.MaterialExpressionTextureSample,texture=mural)
    connect(mural_uv,'',sample,'UVs')
    final=custom(mat,plane+place+'float2 m=(P.xy-c)/size+.5; float inside=(all(m>0) && all(m<1))?1.0:0.0; float floorOnly=step(.7,an.z); float2 g=frac(uv/5.0); float grout=smoothstep(.0,.07,min(g.x,g.y))*smoothstep(1.0,.93,max(g.x,g.y)); float k=MuralA*inside*floorOnly*grout; return lerp(Tiles,MuralRGB,k);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'P':pos,'N':nrm,'Tiles':color,'MuralRGB':sample,'MuralA':sample})
    MEL.connect_material_expressions(sample,'A',final,'MuralA');MEL.connect_material_expressions(sample,'RGB',final,'MuralRGB')
    for node,prop in [(final,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(caustic,unreal.MaterialProperty.MP_EMISSIVE_COLOR)]:MEL.connect_material_property(node,'',prop)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_suite_daylight():
    """Suite windows (gen_suite 'DaylightPanel'): bright sky by day behind the sheers, deep blue at night."""
    mat=material('M_SuiteDaylight')
    night=expression(mat,unreal.MaterialExpressionCollectionParameter,collection=time_collection(),parameter_name='Night')
    glow=custom(mat,'return lerp(float3(.75,.86,.96)*3.2,float3(.03,.05,.10),saturate(N));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'N':night})
    MEL.connect_material_property(glow,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.8,.88,.95,1)),'',unreal.MaterialProperty.MP_BASE_COLOR)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def time_collection():
    """MPC_MareTime, written by UMareVisualWorld every tick: Night (0 day .. 1 night) and the weather, eased:
    Rain (0..1, curtain and puddles), Wind (0 calm .. 1 storm, palms) and Storm (0..1, rough sea)."""
    path='/Game/World/Materials/MPC_MareTime'
    mpc=unreal.load_asset(path)
    if not mpc:
        mpc=unreal.AssetToolsHelpers.get_asset_tools().create_asset('MPC_MareTime','/Game/World/Materials',unreal.MaterialParameterCollection,unreal.MaterialParameterCollectionFactoryNew())
    params=list(mpc.get_editor_property('scalar_parameters'))
    names=[str(p.get_editor_property('parameter_name')) for p in params]
    added=False
    # Volcano: 0..1 eruption glow on the volcanic island (UMareMarineWorld, random nights).
    # Boat*: the tour boat's hull (UMareBoatTourWorld): the sea is flattened under it so no wave shows inside the boat.
    # Drawback: the tsunami's draw-back in cm (UMareSummitWorld, 08/11): the sea sinks by it near every coast.
    for name,default in (('Night',0.0),('Rain',0.0),('Wind',.2),('Storm',0.0),('Volcano',0.0),('BoatX',0.0),('BoatY',0.0),('BoatYaw',0.0),('BoatH',0.0),('BoatOn',0.0),('Drawback',0.0)):
        if name not in names:
            p=unreal.CollectionScalarParameter();p.set_editor_property('parameter_name',name);p.set_editor_property('default_value',default)
            params.append(p);added=True
    if added:
        mpc.set_editor_property('scalar_parameters',params)
        unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    return mpc


def _mpc(mat,name):
    return expression(mat,unreal.MaterialExpressionCollectionParameter,collection=time_collection(),parameter_name=name)


def build_window_pane():
    """Facade window glass seen from the street: the panes sit on the wall, so a transparent
    material showed plaster. Dark, polished glass reflects the sky like a real window by day,
    with a soft lighter band suggesting a curtain behind it."""
    mat=material('M_WindowPane_PBR')
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mat.set_editor_property('used_with_nanite',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    color=custom(mat,'float band=smoothstep(.15,.35,frac(Position.z/280.0))*(1-smoothstep(.75,.95,frac(Position.z/280.0))); float folds=.85+.15*sin(Position.x*.21+Position.y*.21); return lerp(float3(.018,.026,.03),float3(.11,.10,.085)*folds,band*.35);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos})
    for node,prop in [(color,unreal.MaterialProperty.MP_BASE_COLOR),(expression(mat,unreal.MaterialExpressionConstant,r=.035),unreal.MaterialProperty.MP_ROUGHNESS),(expression(mat,unreal.MaterialExpressionConstant,r=.9),unreal.MaterialProperty.MP_SPECULAR)]:MEL.connect_material_property(node,'',prop)
    # Night: about 55% of the windows glow warm behind the curtain (per-instance random), like Godot.
    night=expression(mat,unreal.MaterialExpressionCollectionParameter,collection=time_collection(),parameter_name='Night')
    rnd=expression(mat,unreal.MaterialExpressionPerInstanceRandom)
    glow=custom(mat,'float lit=step(.45,R); float band=.6+.4*sin(Position.z*.02); return float3(1.0,.62,.30)*N*lit*band*3.0;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'R':rnd,'N':night,'Position':pos})
    MEL.connect_material_property(glow,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_palm_frond():
    """Modelled palm leaflets: two-sided foliage with back-lighting and gentle colour variation."""
    mat=material('M_PalmFrond_PBR')
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    mat.set_editor_property('used_with_nanite',True)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    uv=expression(mat,unreal.MaterialExpressionTextureCoordinate)
    color=custom(mat,'float v=.5+.5*sin(Position.x*.013+Position.y*.017); float tip=UV.y; float3 a=float3(.055,.17,.03); float3 b=float3(.12,.26,.045); return lerp(lerp(a,b,v),float3(.16,.24,.06),tip*.35);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'UV':uv})
    sss=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.18,.32,.04,1))
    for node,prop in [(color,unreal.MaterialProperty.MP_BASE_COLOR),(expression(mat,unreal.MaterialExpressionConstant,r=.55),unreal.MaterialProperty.MP_ROUGHNESS),(sss,unreal.MaterialProperty.MP_SUBSURFACE_COLOR)]:MEL.connect_material_property(node,'',prop)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def _model_texture(file, folder, normal=False):
    """Texture shipped next to a re-exported model glTF (SourceArt/Models)."""
    name = Path(file).stem
    path = folder + '/' + name
    tex = unreal.load_asset(path)
    if not tex:
        task = unreal.AssetImportTask(); task.filename = str(ROOT / 'SourceArt' / 'Models' / file); task.destination_path = folder
        task.destination_name = name; task.automated = True; task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); tex = unreal.load_asset(path)
    if normal:
        tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex


def palm_fab(arg=''):
    """hud module entry: rebuild M_PalmFab_PBR (PIE stopped)."""
    return build_palm_fab().get_path_name()


def build_palm_fab():
    """Fab "Coconut Tree" (CC BY 4.0): one atlas for trunk, fronds and nuts; fronds cut out by the
    alpha channel, lit from both sides like foliage."""
    folder = '/Game/Nature/Palms'
    color_tex = _model_texture('palm_fab_basecolor.png', folder)
    normal_tex = _model_texture('palm_fab_normal.jpg', folder, True)
    mat = material('M_PalmFab_PBR')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    color = expression(mat, unreal.MaterialExpressionTextureSample, texture=color_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    normal = expression(mat, unreal.MaterialExpressionTextureSample, texture=normal_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    # leaf transmission fades at night (the fronds glowed bright green against the night sky)
    # 05/11 (Sergio: 'tronco e folhas muito claras das palmeiras'): the earlier darkening never applied (it was wired to
    # an undefined node, the function stopped there). Deeper, more saturated green on the fronds and a darker trunk
    # (the brownish/grey texels of the shared atlas), little sky reflection, and much less light through the leaves:
    # backlit by a low sun the fronds glowed almost white.
    sss = custom(mat, 'return Base.rgb * float3(.22,.32,.12) * (1 - .75*Night);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': color, 'Night': _mpc(mat, 'Night')})
    MEL.connect_material_property(custom(mat, 'float3 c=Base.rgb; float green=saturate((c.g-max(c.r,c.b))*6); float3 leafc=c*float3(.5,.6,.42); float3 trunk=c*float3(.56,.52,.48); return lerp(trunk,leafc,green);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': color}), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.12), '', unreal.MaterialProperty.MP_SPECULAR)
    MEL.connect_material_property(color, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.connect_material_property(normal, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(sss, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.7), '', unreal.MaterialProperty.MP_ROUGHNESS)
    # Wind (MPC Wind, 0 calm .. 1 storm): the trunk bends more with height and leans downwind, fronds flutter
    # with their distance from the trunk axis. ObjectPositionWS is the instance base (palms are instanced).
    pos = expression(mat, unreal.MaterialExpressionWorldPosition)
    origin = expression(mat, unreal.MaterialExpressionObjectPositionWS)
    time = expression(mat, unreal.MaterialExpressionTime)
    wind = custom(mat, 'float h=saturate((P.z-O.z)/750); float bend=h*h; float ph=T*(.55+W*.9)+O.x*.003+O.y*.002; float2 dir=normalize(float2(1,.35)); float sway=(sin(ph)*.65+sin(ph*2.3+1.7)*.25)*(5+W*26)*bend+W*W*22*bend; float r=saturate((length(P.xy-O.xy)-70)/320)*h; float flutter=sin(T*(2.6+W*5)+P.x*.05+P.y*.04)*(1.2+W*7)*r; return float3(dir*(sway+flutter*.4),flutter);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'P': pos, 'O': origin, 'T': time, 'W': _mpc(mat, 'Wind')})
    MEL.connect_material_property(wind, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mat.set_editor_property('max_world_position_offset_displacement', 70.0)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_rain():
    """M_RainCurtain: two layers of falling streaks (T_RainStreaks, drawn by tools/ue58/gen_weather_textures.py) on
    an open cylinder that UMareVisualWorld keeps around the player while it rains outdoors. Unlit translucent,
    faded at the top/bottom and where it meets geometry; Rain scales the opacity, darker at night."""
    tex = _custom_texture('T_RainStreaks.png')
    mat = material('M_RainCurtain')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    uv = expression(mat, unreal.MaterialExpressionTextureCoordinate)
    time = expression(mat, unreal.MaterialExpressionTime)
    samples = []
    for tiling, speed in (((5, 2.2), 1.5), ((9, 4), 2.3)):
        u = custom(mat, f'return UV*float2({tiling[0]},{tiling[1]})+float2(T*.03,-T*{speed});', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': uv, 'T': time})
        node = expression(mat, unreal.MaterialExpressionTextureSample, texture=tex)
        connect(u, '', node, 'UVs')
        samples.append(node)
    fade = expression(mat, unreal.MaterialExpressionDepthFade, fade_distance_default=120.0)
    rain = _mpc(mat, 'Rain')
    alpha = custom(mat, 'float v=UV.y; float ends=smoothstep(0,.15,v)*smoothstep(1,.8,v); return saturate(A*.8+B*.55)*ends*Rain*.28*Fade;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'UV': uv, 'Rain': rain, 'Fade': fade, 'A': samples[0], 'B': samples[1]})
    MEL.connect_material_expressions(samples[0], 'A', alpha, 'A')
    MEL.connect_material_expressions(samples[1], 'A', alpha, 'B')
    color = custom(mat, 'return float3(.62,.68,.74)*lerp(1.0,.12,Night);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Night': _mpc(mat, 'Night')})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(alpha, '', unreal.MaterialProperty.MP_OPACITY)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_puddle():
    """M_Puddle: rain puddles on streets and the square (mare_hud puddles). One of four shapes of T_PuddleMask
    per instance; they grow from the middle as Rain rises (opacity mask = shape * Rain) and vanish when dry.
    Dark, almost mirror water with rain ripples."""
    tex = _custom_texture('T_PuddleMask.png')
    mat = material('M_Puddle')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('opacity_mask_clip_value', .5)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    uv = expression(mat, unreal.MaterialExpressionTextureCoordinate)
    rnd = expression(mat, unreal.MaterialExpressionPerInstanceRandom)
    cell = custom(mat, 'float k=floor(R*3.999); return UV*.5+float2(fmod(k,2),floor(k/2))*.5;', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': uv, 'R': rnd})
    shape = expression(mat, unreal.MaterialExpressionTextureSample, texture=tex)
    connect(cell, '', shape, 'UVs')
    rain = _mpc(mat, 'Rain')
    mask = custom(mat, 'return A*smoothstep(.05,.9,Rain)*1.6;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'Rain': rain, 'A': shape})
    MEL.connect_material_expressions(shape, 'A', mask, 'A')
    pos = expression(mat, unreal.MaterialExpressionWorldPosition)
    time = expression(mat, unreal.MaterialExpressionTime)
    water_normal = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    ripples = []
    for code in ('return Position.xy*.012 + Time*float2(.05,.03);', 'return Position.yx*.017 - Time*float2(.04,.06);'):
        u = custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'Position': pos, 'Time': time})
        node = expression(mat, unreal.MaterialExpressionTextureSample, texture=water_normal, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(u, '', node, 'UVs')
        ripples.append(node)
    normal = custom(mat, 'return normalize(float3((A.xy+B.xy)*(.04+Rain*.08),1));', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': ripples[0], 'B': ripples[1], 'Rain': rain})
    MEL.connect_material_property(mask, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.connect_material_property(normal, '', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.018, .02, .022, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.03), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.6), '', unreal.MaterialProperty.MP_SPECULAR)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_sand_footprint():
    """M_SandFootprint: the imprints the player leaves in the sand (UMareVisualWorld footprints). The foot mask of
    tools/ue58/gen_footprints.py as a soft shaded dent: a little darker than dry sand, with its normal map, fading
    out with PerInstanceCustomData 0 (age 0..1)."""
    folder = '/Game/Custom/Beach/beach_footprint'
    mask = unreal.load_asset(f'{folder}/beach_footprint_color')
    dent = unreal.load_asset(f'{folder}/beach_footprint_normal')
    mat = material('M_SandFootprint')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    a = expression(mat, unreal.MaterialExpressionTextureSample, texture=mask)
    n = expression(mat, unreal.MaterialExpressionTextureSample, texture=dent, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    age = expression(mat, unreal.MaterialExpressionPerInstanceCustomData, data_index=0)
    opacity = custom(mat, 'float a=saturate(Age); return saturate(M*1.4)*.9*(1-a*a*a);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'M': a, 'Age': age})
    MEL.connect_material_expressions(a, 'A', opacity, 'M')
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.33, .28, .21, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.95), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(opacity, '', unreal.MaterialProperty.MP_OPACITY)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_weather():
    """MPC weather params + rough sea + palm wind + rain curtain + puddles (03/11/2026)."""
    time_collection()
    return {m.get_name(): m.get_path_name() for m in (build_water(), build_palm_fab(), build_rain(), build_puddle())}


def build_hp_tree():
    """Fab "HighPoly Tree Model" (Next Spring, CC BY 4.0): alpha-cut two-sided leaves + bark with normal."""
    folder = '/Game/Nature/Trees'
    leaf_tex = _model_texture('hp_tree_leaf.png', folder)
    bark_tex = _model_texture('hp_tree_trunk.png', folder)
    bark_nrm = _model_texture('hp_tree_trunk_normal.png', folder, True)
    leaf = material('M_HPTreeLeaf_PBR')
    leaf.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    leaf.set_editor_property('two_sided', True)
    leaf.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    for m in (leaf,):
        m.set_editor_property('used_with_nanite', True)
        m.set_editor_property('used_with_instanced_static_meshes', True)
    color = expression(leaf, unreal.MaterialExpressionTextureSample, texture=leaf_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    # The texture is a pale spring green that read as frosted next to the tropical bush: deeper and more saturated.
    MEL.connect_material_property(custom(leaf, 'float l=dot(Base.rgb,float3(.2126,.7152,.0722)); return max(lerp(l.xxx,Base.rgb,1.4),0) * float3(.55,.66,.42);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': color}), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(color, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    # Light through the leaves: a third of the old (.6,.8,.4) and fading at night. At full strength the shaded crowns
    # under the big jacaranda glowed almost white against the sun behind them (03/11 simulation, CHECKLIST_SIMULACAO).
    night = _mpc(leaf, 'Night')
    MEL.connect_material_property(custom(leaf, 'return Base.rgb * float3(.2,.27,.12) * (1 - .75 * N);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': color, 'N': night}), '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    MEL.connect_material_property(expression(leaf, unreal.MaterialExpressionConstant, r=.65), '', unreal.MaterialProperty.MP_ROUGHNESS)
    # Sky light reaches under the big jacaranda crown almost unoccluded (masked foliage barely blocks Lumen's sky
    # light): shaded leaves and bark washed out pale. A material AO darkens only that indirect light, not the sun.
    for m in (leaf,):
        MEL.connect_material_property(expression(m, unreal.MaterialExpressionConstant, r=.45), '', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    bark = material('M_HPTreeTrunk_PBR')
    bark.set_editor_property('used_with_nanite', True)
    bark.set_editor_property('used_with_instanced_static_meshes', True)
    c = expression(bark, unreal.MaterialExpressionTextureSample, texture=bark_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    n = expression(bark, unreal.MaterialExpressionTextureSample, texture=bark_nrm, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    # Near-white bark looked like a birch in snow: a warm grey-brown keeps the texture's grain.
    MEL.connect_material_property(custom(bark, 'return Base.rgb * float3(.52,.46,.38);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': c}), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(expression(bark, unreal.MaterialExpressionConstant, r=.85), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(expression(bark, unreal.MaterialExpressionConstant, r=.5), '', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    for m in (leaf, bark):
        errors = list(MEL.recompile_material(m))
        if errors: raise RuntimeError(str(errors))
        unreal.EditorAssetLibrary.save_loaded_asset(m)
    return {'leaf': leaf, 'trunk': bark}


def build_coconut():
    """Dry coconut (Fab, Rabeya Akter): husk with the CC0 Poly Haven palm_bark maps, fibre strands."""
    folder = '/Game/Nature/Coconut'
    diff = _model_texture('coconut_husk_diff.jpg', folder)
    nor = _model_texture('coconut_husk_nor_gl.jpg', folder, True)
    nor.set_editor_property('flip_green_channel', True)
    rough = _model_texture('coconut_husk_rough.jpg', folder)
    rough.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(nor); unreal.EditorAssetLibrary.save_loaded_asset(rough)
    husk = material('M_CoconutHusk_PBR')
    fibre = material('M_CoconutFiber_PBR')
    fibre.set_editor_property('two_sided', True)
    for m in (husk, fibre):
        m.set_editor_property('used_with_nanite', True)
        m.set_editor_property('used_with_instanced_static_meshes', True)
    uv = custom(husk, 'return UV * 2.0;', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': expression(husk, unreal.MaterialExpressionTextureCoordinate)})
    nodes = {}
    for key, tex, kind in (('c', diff, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR), ('n', nor, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                           ('r', rough, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)):
        nodes[key] = expression(husk, unreal.MaterialExpressionTextureSample, texture=tex, sampler_type=kind)
        connect(uv, '', nodes[key], 'UVs')
    # Palm bark is grey-brown; a dry husk is warmer and darker.
    color = custom(husk, 'float l=dot(Base.rgb,float3(.2126,.7152,.0722)); return float3(.50,.27,.11)*clamp(l*2.3,.45,1.45);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': nodes['c']})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nodes['n'], 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(nodes['r'], 'R', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(expression(fibre, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.22, .13, .06, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(fibre, unreal.MaterialExpressionConstant, r=.9), '', unreal.MaterialProperty.MP_ROUGHNESS)
    for m in (husk, fibre):
        errors = list(MEL.recompile_material(m))
        if errors: raise RuntimeError(str(errors))
        unreal.EditorAssetLibrary.save_loaded_asset(m)
    return {'husk': husk, 'fiber': fibre}


def build_hill_ground():
    """Low-poly Godot hill tiles: CC0 Poly Haven aerial_grass_rock projected tri-planar in world space
    (no stretching on the steep faces), tinted toward the lawn green, with a second larger sample
    and macro variation so the tile repeat and the facets read as terrain."""
    folder = '/Game/World/Terrain'
    diff = _model_texture('hill_grass_rock_diff.jpg', folder)
    nor = _model_texture('hill_grass_rock_nor_gl.jpg', folder, True)
    nor.set_editor_property('flip_green_channel', True)
    unreal.EditorAssetLibrary.save_loaded_asset(nor)
    mat = material('M_HillGround_PBR')
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    # 09/11: the tiles end in a flat skirt 2.2 m under the sea; through the shallow water it showed as pale stair-step
    # rectangles. Under the water the hill turns to the island floor's sand (with its caustics) and is lifted (below).
    # (Cutting the skirt out was tried: the sea floor 2.5 m down then showed as a dark band through the water.)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    fn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture')
    def projected(tex, size):
        obj = expression(mat, unreal.MaterialExpressionTextureObject, texture=tex)
        call = expression(mat, unreal.MaterialExpressionMaterialFunctionCall)
        call.set_editor_property('material_function', fn)
        connect(obj, '', call, 'TextureObject')
        connect(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(size, size, size, 1)), '', call, 'TextureSize')
        return call
    near, far, nrm = projected(diff, 900.0), projected(diff, 4100.0), projected(nor, 900.0)
    # 10/11 (checklist: the forest floor on the hills was a smooth pale green): dry leaf litter in patches, the same
    # Poly Haven leaves_forest_ground (3 m tiles) as the island's new land, so the two grounds match under the trees.
    # Only in the forest (more than ~35 m from the coast, T_IslandSDF: the open slopes by the sea stay grass) and only near
    # the camera (30-70 m): all over, the hills turned brown seen from the sea and from the air.
    leaf = expression(mat, unreal.MaterialExpressionTextureSample, texture=texture('leaves_forest_ground_diff', False),
                      sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    connect(custom(mat, 'return P.xy/300.0;', unreal.CustomMaterialOutputType.CMOT_FLOAT2,
                   {'P': expression(mat, unreal.MaterialExpressionWorldPosition)}), '', leaf, 'UVs')
    # Colour, cut and lift all read the tile's own height (without the lift below).
    pos = expression(mat, unreal.MaterialExpressionWorldPosition,
                     world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    color = custom(mat, 'float m=.5+.5*sin(P.x*.00021+sin(P.y*.00017)*2.0); float3 c=lerp(A.rgb,B.rgb,.45*m); float l=dot(c,float3(.2126,.7152,.0722)); float3 turf=float3(.11,.22,.05)*clamp(l*2.6,.55,1.35); float3 o=lerp(c,turf,.55)*(.9+.12*sin(P.x*.0009)*sin(P.y*.0007)); float pn=.5+.5*sin(P.x*.0009+sin(P.y*.0013)*2.3)*sin(P.y*.0008+sin(P.x*.0011)*1.7); float2 suv=(P.xy-float2(-160000,-110000))/320000.0; float inl=-(Texture2DSampleLevel(Sdf,SdfSampler,suv,0).r-.5)*80000.0; float litter=(.25+.75*smoothstep(.3,.7,pn))*smoothstep(3400.0,5400.0,inl)*(1-smoothstep(3000.0,7000.0,length(P-Cam))); o=lerp(o,L.rgb*float3(.95,.92,.86),litter*.7); float2 qwarp=float2(sin(P.y*.0023+T*.05)+sin(P.x*.0017-1.3),sin(P.x*.0021-T*.04)+sin(P.y*.0013+2.1))*1.7; float2 q=(P.xy*.011)+qwarp; float cw=sin(q.x+sin(q.y*1.3+T*.7)*1.6)+sin(q.y*1.1+sin(q.x*1.2-T*.6)*1.6); float2 qr=float2(q.x*.8-q.y*.6,q.x*.6+q.y*.8)*1.37+3.1; float cw2=sin(qr.x+sin(qr.y*1.2-T*.55)*1.5)+sin(qr.y*1.15+sin(qr.x*1.1+T*.65)*1.5); float cpatch=.35+.65*smoothstep(-.6,.9,sin(P.x*.0009+sin(P.y*.0011)*2.0)*sin(P.y*.0008-1.0+sin(P.x*.0007)*1.5)+.3); float caustic=(pow(saturate(1-abs(cw)*.6),4)*.65+pow(saturate(1-abs(cw2)*.6),4)*.5)*cpatch; float3 bed=float3(.95,.88,.74)*.88*float3(.9,.93,.92)*(.95+.1*m)*(1+caustic*1.05); return lerp(o,bed,1-smoothstep(-80.0,-15.0,P.z));',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': near, 'B': far, 'P': pos, 'T': expression(mat, unreal.MaterialExpressionTime), 'L': leaf,
                    'Sdf': expression(mat, unreal.MaterialExpressionTextureObject, texture=island_sdf_texture()),
                    'Cam': expression(mat, unreal.MaterialExpressionCameraPositionWS)})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nrm, 'XYZ Texture', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.92), '', unreal.MaterialProperty.MP_ROUGHNESS)
    # The underwater slope and skirt of a hill tile drop to -2.2 m within a few metres while the island floor beside it
    # stays at -0.8..-1.2 m: through the water the deeper hill read as a dark band with the floor's straight edge next to
    # it. Below the waterline the hill is lifted, its depth squeezed to 45% (-2.2 m -> -1.15 m), so the floors meet.
    lift = custom(mat, 'return float3(0, 0, P.z < -30.0 ? (-30.0 - P.z) * .55 : 0.0);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'P': pos})
    MEL.connect_material_property(lift, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    try:
        mat.set_editor_property('max_world_position_offset_displacement', 130.0)   # Nanite bounds for the lift
    except Exception:
        pass
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_lamp_glow():
    """Lamp globes and bulbs: frosted warm glass, softly lit by day, glowing at night (MPC_MareTime.Night).
    The Godot 'glow' materials were lost in the glTF export (they came in as the default grey)."""
    mat = material('M_LampGlow_PBR')
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    night = expression(mat, unreal.MaterialExpressionCollectionParameter, collection=time_collection(), parameter_name='Night')
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.92, .86, .72, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.25), '', unreal.MaterialProperty.MP_ROUGHNESS)
    glow = custom(mat, 'return float3(1.0,.70,.38)*(.05+N*N*60.0);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'N': night})
    MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_person_outfit():
    """Tintable clothing for the UBC people: the outfit atlas is desaturated (keeps folds, seams and
    stitching) and recoloured by 'Tint', so beach / social / casual outfits differ per person."""
    path = '/Game/Actors/Combined/Shared/M_PersonOutfit'
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PersonOutfit', '/Game/Actors/Combined/Shared', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    atlas = expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Atlas',
                       texture=unreal.load_asset('/Game/Actors/Combined/Human_0/Human_0_texture_6'))
    tint = expression(mat, unreal.MaterialExpressionVectorParameter, parameter_name='Tint', default_value=unreal.LinearColor(.8, .8, .8, 1))
    color = custom(mat, 'float l=dot(A.rgb,float3(.2126,.7152,.0722)); float detail=clamp(l*2.8,.45,1.25); return T.rgb*detail;',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': atlas, 'T': tint})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.82), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_person_body():
    """UBC body with swimwear: the dark-grey underwear painted on the body atlas (bra/briefs) becomes a
    bikini or swim trunks in 'SwimTint'; skin is untouched. M_PersonHidden removes garment pieces."""
    path = '/Game/Actors/Combined/Shared/M_PersonBody'
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PersonBody', '/Game/Actors/Combined/Shared', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    atlas = expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Atlas',
                       texture=unreal.load_asset('/Game/Actors/Combined/Human_2/Human_2_texture_2'))
    tint = expression(mat, unreal.MaterialExpressionVectorParameter, parameter_name='SwimTint', default_value=unreal.LinearColor(.85, .2, .3, 1))
    code = ('float mx=max(A.r,max(A.g,A.b)); float mn=min(A.r,min(A.g,A.b)); float sat=(mx-mn)/max(mx,.001); float l=dot(A.rgb,float3(.2126,.7152,.0722));'
            ' float cloth=(1-smoothstep(.16,.30,sat))*(1-smoothstep(.22,.40,l)); float detail=clamp(l*4.0,.55,1.2);'
            ' return lerp(A.rgb,T.rgb*detail,cloth);')
    color = custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': atlas, 'T': tint})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.62), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    hidden = unreal.load_asset('/Game/Actors/Combined/Shared/M_PersonHidden')
    if not hidden:
        hidden = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PersonHidden', '/Game/Actors/Combined/Shared', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(hidden)):
        MEL.delete_material_expression(hidden, old)
    hidden.set_editor_property('used_with_skeletal_mesh', True)
    hidden.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    MEL.connect_material_property(expression(hidden, unreal.MaterialExpressionConstant, r=0), '', unreal.MaterialProperty.MP_OPACITY_MASK)
    errors = list(MEL.recompile_material(hidden))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(hidden)
    return mat



def _custom_texture(file, normal=False, linear=False):
    """CC0 Poly Haven maps copied to SourceArt/Textures/Custom, imported into /Game/Custom/Textures."""
    name = Path(file).stem
    path = '/Game/Custom/Textures/' + name
    tex = unreal.load_asset(path)
    if not tex:
        task = unreal.AssetImportTask(); task.filename = str(ROOT / 'SourceArt/Textures/Custom' / file); task.destination_path = '/Game/Custom/Textures'
        task.destination_name = name; task.automated = True; task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); tex = unreal.load_asset(path)
    if normal:
        tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property('flip_green_channel', True)
    elif linear:
        tex.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex


def _custom_pbr(name, slug, size_cm, color_code='return A.rgb;', emissive_code=None, two_sided=False, rough_const=None):
    """World-aligned (tri-planar) PBR so any exported mesh UV works; color_code may recolour A (diffuse)."""
    path = '/Game/Custom/Materials/' + name
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Custom/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    mat.set_editor_property('two_sided', two_sided)
    fn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture')

    def projected(tex):
        obj = expression(mat, unreal.MaterialExpressionTextureObject, texture=tex)
        call = expression(mat, unreal.MaterialExpressionMaterialFunctionCall)
        call.set_editor_property('material_function', fn)
        connect(obj, '', call, 'TextureObject')
        connect(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(size_cm, size_cm, size_cm, 1)), '', call, 'TextureSize')
        return call
    diff = projected(_custom_texture(slug + '_diff_1k.jpg'))
    nor = projected(_custom_texture(slug + '_nor_1k.jpg', normal=True))
    inputs = {'A': diff, 'P': expression(mat, unreal.MaterialExpressionWorldPosition), 'O': expression(mat, unreal.MaterialExpressionObjectPositionWS)}
    color = custom(mat, color_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, inputs)
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nor, 'XYZ Texture', unreal.MaterialProperty.MP_NORMAL)
    rough_file = ROOT / 'SourceArt/Textures/Custom' / (slug + '_rough_1k.jpg')
    if rough_const is None and rough_file.exists():
        MEL.connect_material_property(projected(_custom_texture(slug + '_rough_1k.jpg', linear=True)), 'XYZ Texture', unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=rough_const or .6), '', unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive_code:
        night = expression(mat, unreal.MaterialExpressionCollectionParameter, collection=time_collection(), parameter_name='Night')
        t = expression(mat, unreal.MaterialExpressionTime)
        glow = custom(mat, emissive_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'N': night, 'T': t, 'P': inputs['P']})
        MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(name + str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat.get_path_name()


def build_custom_materials():
    """Material tiers of Data/customization.json from CC0 Poly Haven photo-scanned PBR sets."""
    lum = 'float l=dot(A.rgb,float3(.2126,.7152,.0722));'
    # Radial stripes around the umbrella centre (object position), over the linen weave detail.
    stripes = lum + 'float2 d=P.xy-O.xy; float a=atan2(d.y,d.x)/6.2831853+.5; float s=step(.5,frac(a*12.0)); float detail=clamp(l*2.2,.7,1.25); return lerp(%s,%s,s)*detail;'
    out = {}
    out['M_Custom_Counter_2'] = _custom_pbr('M_Custom_Counter_2', 'oak_wood_planks', 120)
    out['M_Custom_Counter_3'] = _custom_pbr('M_Custom_Counter_3', 'blue_painted_planks', 120, lum + 'return lerp(A.rgb,float3(.10,.52,.55)*clamp(l*2.6,.5,1.4),.65);')
    out['M_Custom_Counter_4'] = _custom_pbr('M_Custom_Counter_4', 'blue_floor_tiles_01', 90, 'return A.rgb*1.45;')
    out['M_Custom_Counter_5'] = _custom_pbr('M_Custom_Counter_5', 'teak_veneer', 140, 'return A.rgb*1.05;', rough_const=.32)
    out['M_Custom_Umbrella_1'] = _custom_pbr('M_Custom_Umbrella_1', 'rough_linen', 60, lum + 'return float3(.86,.80,.68)*clamp(l*2.0,.7,1.2);', two_sided=True)
    out['M_Custom_Umbrella_2'] = _custom_pbr('M_Custom_Umbrella_2', 'rough_linen', 60, stripes % ('float3(.08,.32,.62)', 'float3(.92,.92,.88)'), two_sided=True)
    out['M_Custom_Umbrella_3'] = _custom_pbr('M_Custom_Umbrella_3', 'rough_linen', 60, stripes % ('float3(.90,.38,.30)', 'float3(.93,.86,.70)'), two_sided=True)
    out['M_Custom_Umbrella_4'] = _custom_pbr('M_Custom_Umbrella_4', 'thatch_roof_angled', 140, lum + 'return lerp(A.rgb,float3(.66,.50,.28)*clamp(l*2.4,.5,1.4),.6);', two_sided=True)
    out['M_Custom_Umbrella_5'] = _custom_pbr('M_Custom_Umbrella_5', 'denim_fabric', 50, lum + 'return float3(.05,.09,.22)*clamp(l*3.0,.6,1.5);', two_sided=True)
    neon = 'return %s*(.8+N*N*40.0);'
    out['M_Custom_Sign_1'] = _custom_pbr('M_Custom_Sign_1', 'oak_wood_planks', 80)
    out['M_Custom_Sign_2'] = _custom_pbr('M_Custom_Sign_2', 'rough_linen', 40, 'return float3(.9,.9,.9);', emissive_code=neon % 'float3(1.0,.97,.92)', rough_const=.2)
    out['M_Custom_Sign_3'] = _custom_pbr('M_Custom_Sign_3', 'rough_linen', 40, 'return float3(.4,.9,.9);', emissive_code=neon % 'float3(.10,.95,.90)', rough_const=.2)
    out['M_Custom_Sign_4'] = _custom_pbr('M_Custom_Sign_4', 'rough_linen', 40, 'return float3(.95,.5,.8);', emissive_code=neon % 'float3(1.0,.18,.62)', rough_const=.2)
    rainbow = 'float h=frac(T*.08+P.x*.0015); float3 c=saturate(abs(frac(h+float3(0,.333,.667))*6-3)-1); return c*(.8+N*N*40.0);'
    out['M_Custom_Sign_5'] = _custom_pbr('M_Custom_Sign_5', 'rough_linen', 40, 'return float3(.9,.9,.9);', emissive_code=rainbow, rough_const=.2)
    # Water slide fibreglass: glossy colour over a faint weave so it does not read as flat plastic.
    glass = lum + 'return %s*clamp(l*1.6,.85,1.12);'
    out['M_Custom_Slide_2'] = _custom_pbr('M_Custom_Slide_2', 'rough_linen', 200, glass % 'float3(.05,.45,.75)', rough_const=.18)
    out['M_Custom_Slide_3'] = _custom_pbr('M_Custom_Slide_3', 'rough_linen', 200, glass % 'float3(.95,.72,.08)', rough_const=.18)
    out['M_Custom_Slide_4'] = _custom_pbr('M_Custom_Slide_4', 'rough_linen', 200, glass % 'float3(.93,.38,.30)', rough_const=.18)
    out['M_Custom_Slide_5'] = _custom_pbr('M_Custom_Slide_5', 'rough_linen', 200, 'return float3(.85,.85,.9);', emissive_code='float h=frac(T*.05+P.z*.002); float3 c=saturate(abs(frac(h+float3(0,.333,.667))*6-3)-1); return c*N*N*12.0;', rough_const=.18)
    return out


PLASTER_NOR = '/Game/Custom/mare_suite_m5/mare_suite_painted_plaster_wall_nor_1k'
PLASTER_STONE_NOR = '/Game/Custom/mare_suite_m5/mare_suite_plaster_stone_wall_01_nor_1k'


def plaster_finish(path):
    """Fine painted-plaster finish on an imported flat-colour facade material (Grand Hotel tower, 03/11: the walls
    were one flat beige). World-aligned so it needs no UVs and the grain keeps the same size on every wall: the
    painted-plaster normal (fine trowel marks) over the stone-plaster normal (broad undulation), a faint large-scale
    tone variation and a little grime in the first half metre above the ground. The original colour is kept."""
    mel = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(path)
    src = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(src, unreal.MaterialExpressionCustom) and src.get_editor_property('desc') == 'MarePlaster':
        return 'already'
    out_name = mel.get_material_property_input_node_output_name(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(src, unreal.MaterialExpressionMultiply) and src.get_editor_property('desc') == 'MareTint':
        for e in mel.get_material_expressions(mat) if hasattr(mel, 'get_material_expressions') else []:
            if isinstance(e, unreal.MaterialExpressionConstant3Vector) and e.get_editor_property('desc') == 'MareTint':
                e.set_editor_property('constant', unreal.LinearColor(1, 1, 1, 1))
    fine = expression(mat, unreal.MaterialExpressionTextureObject, texture=unreal.load_asset(PLASTER_NOR))
    broad = expression(mat, unreal.MaterialExpressionTextureObject, texture=unreal.load_asset(PLASTER_STONE_NOR))
    wpos = expression(mat, unreal.MaterialExpressionWorldPosition)
    wnrm = expression(mat, unreal.MaterialExpressionVertexNormalWS)
    uv_code = ('float3 a=abs(N); float2 uv = a.z>max(a.x,a.y) ? P.xy : (a.x>a.y ? P.yz : P.xz); ')
    color = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -300, 0)
    color.set_editor_property('desc', 'MarePlaster')
    color.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    color.set_editor_property('code', uv_code +
        'float3 h = Texture2DSample(Tex, TexSampler, uv/180).rgb; '
        'float n = sin(uv.x*.0021+sin(uv.y*.0017)*2.3)*sin(uv.y*.0013+uv.x*.0007); '
        'float tone = 1 + .035*n + (h.r-.5)*.05; '
        'float grime = lerp(.82, 1, saturate(P.z/60)); '
        'return Base.rgb * tone * grime;')
    ins = []
    for n in ('Base', 'P', 'N', 'Tex'):
        v = unreal.CustomInput(); v.set_editor_property('input_name', n); ins.append(v)
    color.set_editor_property('inputs', ins)
    mel.connect_material_expressions(src, out_name or '', color, 'Base')
    mel.connect_material_expressions(wpos, '', color, 'P')
    mel.connect_material_expressions(wnrm, '', color, 'N')
    mel.connect_material_expressions(broad, '', color, 'Tex')
    mel.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    normal = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -300, 300)
    normal.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    normal.set_editor_property('code', uv_code +
        'float3 f = Texture2DSample(Fine, FineSampler, uv/90).rgb*2-1; '
        'float3 b = Texture2DSample(Broad, BroadSampler, uv/320).rgb*2-1; '
        'float3 n = float3(f.xy*.55 + b.xy*.35, 1); return normalize(n);')
    ins = []
    for n in ('P', 'N', 'Fine', 'Broad'):
        v = unreal.CustomInput(); v.set_editor_property('input_name', n); ins.append(v)
    normal.set_editor_property('inputs', ins)
    for n, s in (('P', wpos), ('N', wnrm), ('Fine', fine), ('Broad', broad)):
        mel.connect_material_expressions(s, '', normal, n)
    mel.connect_material_property(normal, '', unreal.MaterialProperty.MP_NORMAL)
    errors = list(mel.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return 'ok'


def grass_hue(path):
    """Poly Haven grass_medium clumps read as dark, dry wisps next to the inland PCG turf (03/11, "gramas mais
    realistas"): route their atlas through the same natural green the PCG grass uses (mare_grass.grass_material),
    keeping the texture's light/dark blades as variation. In place, once (desc MareGrassHue)."""
    mel = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(path)
    src = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(src, unreal.MaterialExpressionCustom) and src.get_editor_property('desc') == 'MareGrassHue':
        return 'already'
    out_name = mel.get_material_property_input_node_output_name(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(src, unreal.MaterialExpressionMultiply) and src.get_editor_property('desc') == 'MareTint':
        for e in mel.get_material_expressions(mat) if hasattr(mel, 'get_material_expressions') else []:
            if isinstance(e, unreal.MaterialExpressionConstant3Vector) and e.get_editor_property('desc') == 'MareTint':
                e.set_editor_property('constant', unreal.LinearColor(1, 1, 1, 1))
    node = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -300, 0)
    node.set_editor_property('desc', 'MareGrassHue')
    node.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    node.set_editor_property('code', 'float l=dot(Base.rgb,float3(.2126,.7152,.0722)); '
                                     'return float3(.06,.21,.028)*clamp(l*3,.7,1.55);')
    v = unreal.CustomInput(); v.set_editor_property('input_name', 'Base')
    node.set_editor_property('inputs', [v])
    mel.connect_material_expressions(src, out_name or '', node, 'Base')
    mel.connect_material_property(node, '', unreal.MaterialProperty.MP_BASE_COLOR)
    errors = list(mel.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return 'ok'


GRASS_TONE = ('float v = saturate((Prev.g/.2 - .65)/.85); '
              'float3 c = lerp(float3(.026,.08,.015), float3(.072,.16,.032), v); '
              'float m = .5 + .5*sin(P.x*.0009 + sin(P.y*.0013)*2.0)*sin(P.y*.0011 + P.x*.0004); '
              'float d = .5 + .5*sin(P.x*.0071 + sin(P.y*.0053)*1.7)*sin(P.y*.0067); '
              'c *= lerp(.82, 1.08, m) * lerp(.9, 1.05, d); '
              'return lerp(c, c*float3(1.25,1.02,.7), (1-m)*.35);')


def grass_tone(path):
    """Deeper, textured green for the lawn grass (03/11: the PCG turf read as a flat, artificial light green).
    Chained after the existing recolour node (its output still carries the blade brightness in .g), so the
    atlas variation stays: darker blade bases, lighter tips, broad patches a little drier or lusher across
    the ground and a finer mottling. Once per material (desc MareGrassTone)."""
    mel = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(path)
    src = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(src, unreal.MaterialExpressionCustom) and src.get_editor_property('desc') == 'MareGrassTone':
        src.set_editor_property('code', GRASS_TONE)
    else:
        out_name = mel.get_material_property_input_node_output_name(mat, unreal.MaterialProperty.MP_BASE_COLOR)
        node = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -150, 0)
        node.set_editor_property('desc', 'MareGrassTone')
        node.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        node.set_editor_property('code', GRASS_TONE)
        ins = []
        for n in ('Prev', 'P'):
            v = unreal.CustomInput(); v.set_editor_property('input_name', n); ins.append(v)
        node.set_editor_property('inputs', ins)
        mel.connect_material_expressions(src, out_name or '', node, 'Prev')
        mel.connect_material_expressions(mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -400, 200), '', node, 'P')
        mel.connect_material_property(node, '', unreal.MaterialProperty.MP_BASE_COLOR)
    errors = list(mel.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return 'ok'


def build_underwater_fog():
    """Post-process for the diving camera (UMareGame Eyes, blend weight 1 under water). Real water, not a tint:
    distance fog towards a water colour that is light looking up at the surface and deep blue-green looking down,
    and red absorbed first with distance. The open sea past the reef fades into that colour instead of the old
    flat blue void (03/11, PENDENCIAS "horizonte subaquático azul e vazio")."""
    mat = material('M_UnderwaterFog')
    mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_POST_PROCESS)
    mat.set_editor_property('blendable_location', unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    scene = expression(mat, unreal.MaterialExpressionSceneTexture)
    scene.set_editor_property('scene_texture_id', unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    depth = expression(mat, unreal.MaterialExpressionSceneDepth)
    cam = expression(mat, unreal.MaterialExpressionCameraVectorWS)
    pos = expression(mat, unreal.MaterialExpressionCameraPositionWS)
    node = custom(mat,
        'float3 v = -normalize(C); float up = saturate(v.z*.5 + .5); '
        'float deep = saturate(-P.z/900); '
        'float3 water = lerp(float3(.015,.085,.11), float3(.09,.36,.40), pow(up, 1.6)) * lerp(1, .7, deep); '
        'float f = 1 - exp(-D/2000); '
        'float3 lit = S.rgb * lerp(float3(1,1,1), float3(.6,.86,.9), saturate(D/1400)); '
        'return lerp(lit, water, saturate(f*.94));',
        unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'S': scene, 'D': depth, 'C': cam, 'P': pos})
    MEL.connect_material_property(node, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return mat.get_path_name()


def wood_floor(path):
    """Honey wood vinyl planks on the hotel floor (03/11, Sergio: "chão da mesma cor das paredes, coloque pisos como na
    referência"): CC0 Poly Haven laminate_floor, world-aligned from above (2 m per tile) so it needs no UVs, with its
    normal and roughness (a satin varnish). Replaces the flat colour of the imported floor material, in place."""
    mel = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(path)
    diff = texture('laminate_floor_diff')
    nor = texture('laminate_floor_nor', True)
    rough = texture('laminate_floor_rough')
    rough.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(rough)
    pos = expression(mat, unreal.MaterialExpressionWorldPosition)
    uv = custom(mat, 'return P.xy/200.0;', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'P': pos})
    nodes = {}
    for key, tex, kind in (('c', diff, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR), ('n', nor, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                           ('r', rough, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)):
        nodes[key] = expression(mat, unreal.MaterialExpressionTextureSample, texture=tex, sampler_type=kind)
        connect(uv, '', nodes[key], 'UVs')
    MEL.connect_material_property(custom(mat, 'return C.rgb*.92;', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'C': nodes['c']}), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nodes['n'], 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(custom(mat, 'return R.r*.55+.18;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'R': nodes['r']}), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(mel.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return 'ok'


BEACH_CANOPIES = ['/Game/World/Models/World_2029/World_2029/StaticMeshes/World_2029', '/Game/World/Models/World_2030/World_2030/StaticMeshes/World_2030',
                  '/Game/World/Models/World_2035/World_2035/StaticMeshes/World_2035', '/Game/World/Models/World_2036/World_2036/StaticMeshes/World_2036',
                  '/Game/World/Models/World_2040/World_2040', '/Game/World/Models/World_2041/World_2041', '/Game/World/Models/World_2045/World_2045',
                  '/Game/World/Models/World_2050/World_2050']
BEACH_TOWELS = ['/Game/World/Models/World_2031/World_2031/StaticMeshes/World_2031', '/Game/World/Models/World_2032/World_2032/StaticMeshes/World_2032',
                '/Game/World/Models/World_2037/World_2037/StaticMeshes/World_2037', '/Game/World/Models/World_2038/World_2038/StaticMeshes/World_2038',
                '/Game/World/Models/World_2042/World_2042', '/Game/World/Models/World_2043/World_2043', '/Game/World/Models/World_2047/World_2047',
                '/Game/World/Models/World_2051/World_2051']


def _flat_colour(mat):
    """Base colour of an imported flat material: the glTF factor of a material instance, or the constant wired to a
    material's base colour; None when it is textured (left alone)."""
    if isinstance(mat, unreal.MaterialInstanceConstant):
        for p in mat.get_editor_property('texture_parameter_values'):
            if p.parameter_value and 'color' in str(p.parameter_info.name).lower():
                return None
        for p in mat.get_editor_property('vector_parameter_values'):
            name = str(p.parameter_info.name).lower()
            if 'color' in name or 'colour' in name:
                return p.parameter_value
        return None
    node = MEL.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(node, unreal.MaterialExpressionMaterialFunctionCall):
        # Re-made materials pass the colour through a function: its first constant colour input.
        node = next((n for n in MEL.get_inputs_for_material_expression(mat, node) if isinstance(n, unreal.MaterialExpressionConstant3Vector)), None)
    if isinstance(node, unreal.MaterialExpressionConstant3Vector):
        return node.get_editor_property('constant')
    if isinstance(node, unreal.MaterialExpressionVectorParameter):
        return node.get_editor_property('default_value')
    return None


def beach_fabric_master():
    """M_BeachFabric (03/11, Sergio: "guarda-sol e as toalhas no chão não têm texturas"): the beach towels and umbrella
    canopies were flat colours. Keeps each piece's colour (Tint) and adds the cloth: Kind 0 = terry towel (CC0 waffle
    piqué cotton normal, 12 cm tile, soft matte, hemmed with white end bands), Kind 1 = umbrella canvas (CC0 Poly Haven
    denim weave normal, 9 cm tile; the painting-canvas maps showed stains and frame edges as tiles), light sheen, 8 sewn panels. Projected in world space by the face's dominant axis (the generated meshes have no usable UVs)
    plus a faint large-scale tone variation so a towel is not one flat colour."""
    mat = material('M_BeachFabric')
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    mat.set_editor_property('used_with_nanite', True)
    tint = expression(mat, unreal.MaterialExpressionVectorParameter, parameter_name='Tint', default_value=unreal.LinearColor(.8, .8, .8, 1))
    kind = expression(mat, unreal.MaterialExpressionScalarParameter, parameter_name='Kind', default_value=0.)
    pos = expression(mat, unreal.MaterialExpressionWorldPosition)
    nrm = expression(mat, unreal.MaterialExpressionVertexNormalWS)
    uv = custom(mat, 'float3 a=abs(N); float2 p=a.z>.6?P.xy:(a.x>a.y?P.yz:P.xz); return p/lerp(12.0,9.0,K);',
                unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'P': pos, 'N': nrm, 'K': kind})
    terry = expression(mat, unreal.MaterialExpressionTextureSample, texture=unreal.load_asset('/Game/Custom/mare_suite_m5/mare_suite_waffle_pique_cotton_nor_1k'),
                       sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    canvas_n = expression(mat, unreal.MaterialExpressionTextureSample, texture=unreal.load_asset('/Game/Custom/Textures/denim_fabric_nor_1k'),
                          sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    for node in (terry, canvas_n):
        connect(uv, '', node, 'UVs')
    # Towel (mesh space: 95 x 194 cm, long side along local Y): hemmed edges and white bands near both ends with a
    # thin stripe of a deeper shade between them. Canopy: 8 sewn panels around the pole, seams a shade darker and each
    # panel catching the light slightly differently.
    loc = expression(mat, unreal.MaterialExpressionLocalPosition)
    color = custom(mat, 'float n=sin(P.x*.013+sin(P.y*.017)*2.0)*.5+.5; float3 c=T.rgb*lerp(.9,1.04,n); '
                   'float y=abs(L.y), x=abs(L.x); float pile=1.0-saturate(length(Tn.xy)*2.2); '
                   'float band=(step(60.0,y)*step(y,67.0))+(step(73.0,y)*step(y,77.0)); float deep=step(68.5,y)*step(y,71.5); '
                   'float hem=step(43.5,x)+step(92.0,y); '
                   'float3 towel=lerp(c,float3(.86,.85,.80),saturate(band)); towel=lerp(towel,c*.62,deep); towel*=lerp(.72,1.06,pile)*(1.0-.14*saturate(hem)); '
                   'float weave=1.0-saturate(length(Cn.xy)*1.8); float a=atan2(L.y,L.x); float seam=smoothstep(.94,1.0,cos(a*8.0)); '
                   'float panel=.93+.07*step(0.0,sin(a*8.0)); float3 canvas=c*lerp(.86,1.03,weave)*panel*(1.0-.3*seam); '
                   'return lerp(towel,canvas,K);',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'P': pos, 'L': loc, 'T': tint, 'Cn': canvas_n, 'Tn': terry, 'K': kind})
    normal = custom(mat, 'float3 t=float3(A.xy*2.2,A.z); float3 c=float3(B.xy*.9,B.z); return normalize(lerp(t,c,K));',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': terry, 'B': canvas_n, 'K': kind})
    rough = custom(mat, 'return lerp(.92,.7,K);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'K': kind})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(normal, '', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return mat


def beach_fabrics(dry=False):
    """Each towel/canopy slot gets an instance of M_BeachFabric with the colour it had (MI_BeachFabric_<mesh>_<slot>);
    the original flat material is kept as the instance's source colour, so running it again is harmless."""
    master = None if dry else beach_fabric_master()
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    out = []
    for kind, paths in ((0, BEACH_TOWELS), (1, BEACH_CANOPIES)):
        for path in paths:
            mesh = unreal.load_asset(path)
            if not mesh:
                out.append([path, 'missing'])
                continue
            b = mesh.get_bounding_box()
            slots = list(mesh.static_materials)
            for j, slot in enumerate(slots):
                old = slot.material_interface
                if old and old.get_name().startswith('MI_BeachFabric'):
                    out.append([mesh.get_name(), j, 'done'])
                    continue
                c = _flat_colour(old) if old else None
                out.append([mesh.get_name(), j, old.get_name() if old else None, [round(v, 3) for v in (c.r, c.g, c.b)] if c else None,
                            [round(b.max.x - b.min.x), round(b.max.y - b.min.y), round(b.max.z - b.min.z)]])
                if dry or not c:
                    continue
                name = f'MI_BeachFabric_{mesh.get_name()}_{j}'
                mi = unreal.load_asset(f'/Game/World/Materials/BeachFabric/{name}') or tools.create_asset(
                    name, '/Game/World/Materials/BeachFabric', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                MEL.set_material_instance_parent(mi, master)
                MEL.set_material_instance_vector_parameter_value(mi, 'Tint', unreal.LinearColor(c.r, c.g, c.b, 1))
                MEL.set_material_instance_scalar_parameter_value(mi, 'Kind', float(kind))
                unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
                slot.material_interface = mi
                slots[j] = slot
            if not dry:
                mesh.set_editor_property('static_materials', slots)
                unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return out

"""Verificação estática dos JSON do Maré Alta, sem Unreal ou dependências externas.

Uso: python tools/ue58/qa/data_lint.py
     python tools/ue58/qa/data_lint.py --asset-index tools/ue58/balance/package_index.json --json
     python tools/ue58/qa/data_lint.py --self-test

Regras de referência seguem os consumidores C++ indicados em RULE_SOURCES.
/Game válido exige sintaxe de package/object path e pacote .uasset no checkout,
no índice Git opcional ou em catálogo de importação. Não testa LoadObject,
material, licença, conteúdo binário nem qualidade visual. O índice opcional é
metadado de um snapshot, nunca cria um .uasset ou um modelo fictício.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DEFAULT_DATA=ROOT/'unreal/MareAlta/Content/Data'
RULE_SOURCES={
 'expansoes_capitulos_missoes':'MareSimulation.cpp:277,297,330,348,803',
 'receitas_insumos':'MareSimulation.cpp:148,168; MareBar.cpp:43,353; MareBarWorld.cpp:241; MarePerson.cpp:247',
 'personalizacao':'MareCustomWorld.cpp:19,34,92; MareSimulation.cpp:534,650',
 'equipe':'MareStaff.cpp:59,92; MareStaffWorld.cpp:147; MareSimulation.cpp:737,787',
 'horarios':'MareBusiness.cpp:17; MarePool.cpp:77; MareBar.cpp:70; MareTours.cpp:284; MareRestaurant.cpp:40,135; MareHotelEvents.cpp:110',
 'sorteios':'MareEvents.cpp:19,68; MareHotelRooms.cpp:215; MareComicEvents.cpp:102; MareIceCream.cpp:69; MarePastel.cpp:67; MareRental.cpp:79; MareRestaurant.cpp:170,192; MareHotelEvents.cpp:32,92',
 'modelos':'Content/Python/mare_fab.py::mesh (fab:N), mare_hotel_lobby.py::_lib_mesh; MareCustomWorld.cpp:19; MareBoatTourWorld.cpp:27; MareSnorkelWorld.cpp:81; MareReefWorld.cpp:111; MarePerson.cpp:247',
}
# Valores monetários: não confundir businesses.<id>.hour (renda) com hora do relógio.
MONEY={'price','cost','hire','wage','base_price','fee','prize','runner_up','price30',
       'price_per_scoop','topping_price','tip_perfect','wrap_fee','card_cost','card_price',
       'subject_bonus','cana_price','popsicle_cost','popsicle_price','fine','rescue_reward',
       'rate_base','star_bonus','spend','income','buy_cost','star_price'}
PROB={'chance','odds','regular_chance','vip_chance','dolphin_chance','chance_per_hour',
      'chance_per_room_hour','rain_odds','kid_chance','cana_chance','dent_chance',
      'adrift_chance','buy_chance','gift_chance','card_chance','clerk_share','bartender_share',
      'crew_share','photo_share','reschedule_keep','min_score'}
RANGES={'bite_wait','cm','arrivals','scoops','right','dirt_per_hour','night_players','spectators','every_days'}
HOURS={'open','hours','happy_hour','token_hours','sunset'}
HOUR_SCALARS={'event_hour','guest_final_hour','full_moon_from','night_from','offer_hour','setup_from'}
MODELS={'model','mesh','slug','kayak_mesh','pole_mesh'}
MODEL_LISTS={'models','meshes','static_meshes','skeletal_meshes'}
BROKEN=re.compile('\ufffd|Ã(?:©|£|§|¡|­|³|º|µ|¢|ª|´|‰|“|š|‡)|Â(?:°|º|ª| )|â(?:€|„|œ|™|˜)')
PACKAGE=re.compile(r'^/Game/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)?$')


class JSONObject(dict):
    def __init__(self,pairs):
        self.duplicates=[]
        for key,value in pairs:
            if key in self:self.duplicates.append(key)
            self[key]=value


def pointer(parts):
    return '/'+'/'.join(str(p).replace('~','~0').replace('/','~1') for p in parts) if parts else '/'


def number(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool)


def walk(value,parts=()):
    yield parts,value
    if isinstance(value,dict):
        for key,child in value.items():yield from walk(child,parts+(key,))
    elif isinstance(value,list):
        for i,child in enumerate(value):yield from walk(child,parts+(i,))


def package_path(value):
    if not isinstance(value,str):return None
    # Aceita object paths exportados e package paths; não inventa nomes de pacote.
    if "'" in value:
        m=re.fullmatch(r"(?:StaticMesh|SkeletalMesh|Blueprint|Texture2D)'([^']+)'",value)
        if not m:return None
        value=m[1]
    if not PACKAGE.fullmatch(value):return None
    path,_,obj=value.partition('.')
    if obj and obj!=path.rsplit('/',1)[-1]:return None
    return path


class Linter:
    def __init__(self,data_dir,asset_index=None):
        self.data_dir=Path(data_dir)
        self.content=self.data_dir.parent
        self.docs={};self.problems=[];self.packages=set();self.asset_checks=0
        self.index=asset_index

    def error(self,file,parts,problem):
        row={'arquivo':file,'campo':pointer(parts),'problema':problem}
        if row not in self.problems:self.problems.append(row)

    def load(self):
        if not self.data_dir.is_dir():
            self.error(str(self.data_dir),(),'diretório de dados inexistente');return
        paths=sorted(self.data_dir.rglob('*.json'))
        if not paths:self.error(str(self.data_dir),(),'nenhum JSON encontrado')
        for p in paths:
            try:
                def invalid(token):raise ValueError('número não JSON: '+token)
                d=json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=JSONObject,parse_constant=invalid)
                self.docs[p.relative_to(self.data_dir).as_posix()]=d
            except (OSError,UnicodeError,ValueError) as exc:
                self.error(p.name,(),'JSON inválido: '+str(exc))
        # Apenas nomes e caminhos; não abre nem modifica conteúdo binário.
        for p in self.content.rglob('*.uasset'):
            self.packages.add('/Game/'+p.relative_to(self.content).with_suffix('').as_posix())
        if self.index:
            try:
                index=json.loads(Path(self.index).read_text(encoding='utf-8'))
                if not isinstance(index.get('packages'),list) or not index.get('revision'):
                    raise ValueError('índice precisa de revision e packages')
                # Evita aplicar uma lista de packages de outro snapshot aos JSON atuais.
                if index.get('data_sha256') and set(index['data_sha256'])!=set(self.docs):raise ValueError('índice obsoleto: lista de JSON mudou')
                for file,expected in index.get('data_sha256',{}).items():
                    actual=hashlib.sha256((self.data_dir/file).read_bytes()).hexdigest()
                    if actual!=expected:raise ValueError('índice obsoleto para '+file)
                for value in index['packages']:
                    p=package_path(value)
                    if p:self.packages.add(p)
                    else:raise ValueError('package inválido no índice: '+str(value))
            except (OSError,ValueError,KeyError,TypeError) as exc:
                self.error(str(self.index),(),'índice de assets inválido: '+str(exc))
        # Catálogos produzidos pelo importador (não qualquer referência arbitrária em Data).
        for file in ['custom_assets.json','imported_meshes.json','actors.json','home_assets.json','marine_assets.json']:
            for parts,value in walk(self.docs.get(file,{})):
                p=package_path(value)
                if p:self.packages.add(p)

    def reference(self,file,parts,value,ids,kind,empty=True):
        if empty and value in ('',None):return
        if not isinstance(value,str) or value not in ids:
            self.error(file,parts,f'referência de {kind} inexistente: {value!r}')

    def expansion_spec(self,file,parts,spec):
        # MareVisualWorld::UnlockMatches: vírgulas = AND, ! = negação.
        if not isinstance(spec,str):
            self.error(file,parts,'expressão de expansão deve ser texto');return
        for term in spec.split(','):
            term=term.strip().removeprefix('!')
            if term:self.reference(file,parts,term,self.expansions,'expansão')

    def resolve_model(self,file,parts,value):
        self.asset_checks+=1
        if not isinstance(value,str) or not value:
            self.error(file,parts,'referência de modelo vazia ou não textual');return
        if value.startswith('/Game/') or "'" in value:
            p=package_path(value)
            if not p:self.error(file,parts,'caminho Unreal inválido: '+value)
            elif p not in self.packages:self.error(file,parts,'pacote /Game não encontrado no checkout, índice ou catálogo de importação: '+value)
            return
        custom=self.docs.get('custom_assets.json',{})
        if value in custom:
            self.resolve_model(file,parts,custom[value]);return
        # Produtos carregados por AMarePerson::ProductMesh: o campo mesh do bar é o id do produto.
        if file=='bar.json' and len(parts)>=3 and parts[0]=='recipes' and parts[-1]=='mesh':
            actor=self.docs.get('actors.json',{}).get('Dish_'+value)
            if actor and actor.get('static_meshes'):
                for mesh in actor['static_meshes']:self.resolve_model(file,parts,mesh)
            else:self.error(file,parts,'produto sem modelo Dish_ no catálogo actors.json: '+value)
            return
        # TourMesh realmente monta este caminho no C++, não é um slug de custom_assets.
        if file=='tours.json' and parts in [('boat_tour','mesh'),('snorkel_tour','mesh')]:
            p='/Game/Custom/TourBoat/'+value+'/'+value
            if p not in self.packages:self.error(file,parts,'modelo do barco sem package registrado: '+p)
            return
        imported=self.docs.get('imported_meshes.json',{})
        aliases=self.docs.get('model_aliases.json',{})
        seen=set();key=value
        while key not in seen:
            if key in imported:
                self.resolve_model(file,parts,imported[key]);return
            seen.add(key)
            if not isinstance(aliases.get(key),str):break
            key=aliases[key]
        # hotel_lobby é um inventário de colocação: slugs Fab não são paths e ficam
        # sem resolução se nenhum catálogo ou package real os comprovar.
        if file=='hotel_lobby.json':
            if re.fullmatch(r'fab:\d+',value):
                path='/Game/Fab/WabiSabi_m2/Mesh_ncl_'+value.split(':')[1]
                if path in self.packages:return
            if any(p.startswith('/Game/Hotel/Lobby/'+value+'/') for p in self.packages):return
        self.error(file,parts,'modelo/slug não resolvido pelos catálogos ou packages: '+value)

    def generic(self,file,doc):
        for parts,value in walk(doc):
            key=str(parts[-1]) if parts else ''
            if isinstance(value,JSONObject):
                for duplicate in value.duplicates:self.error(file,parts+(duplicate,),'chave JSON duplicada')
            if isinstance(value,str) and BROKEN.search(value):
                self.error(file,parts,'texto com caractere de substituição ou indício de dupla codificação')
            if isinstance(value,list):
                ids={}
                for i,row in enumerate(value):
                    if isinstance(row,dict) and isinstance(row.get('id'),str):
                        id_=row['id']
                        if id_ in ids:self.error(file,parts+(i,'id'),f'id duplicado {id_!r}; primeira ocorrência em {pointer(parts+(ids[id_],'id'))}')
                        else:ids[id_]=i
            if number(value):
                if not math.isfinite(value):self.error(file,parts,'número não finito')
                if key in MONEY and value<0:self.error(file,parts,'preço/custo/valor monetário negativo')
                if key in PROB and not 0<=value<=1:self.error(file,parts,'chance/fração fora de [0, 1]')
                if key in HOUR_SCALARS and not 0<=value<=24:self.error(file,parts,'horário fora de 0–24')
                if file=='hotel_events.json' and key=='hour' and parts[0]=='kinds' and not 0<=value<=24:self.error(file,parts,'horário de evento fora de 0–24')
                if file=='customization.json' and len(parts)==4 and parts[:2]==('operations','tours') and key=='hour' and not 0<=value<=24:self.error(file,parts,'horário de saída fora de 0–24')
                if file=='definitions.json' and len(parts)==3 and parts[0]=='businesses' and key=='hour' and value<0:self.error(file,parts,'renda horária negativa')
            if isinstance(value,list) and key in MONEY|{'prices','price_mult','cost_mult','photo_price'}:
                for i,x in enumerate(value):
                    if number(x) and x<0:self.error(file,parts+(i,),'preço/custo/multiplicador monetário negativo')
            is_hour=key in HOURS and not any(p in ('lines','reviews','highlight') for p in parts)
            if is_hour:self.hour_range(file,parts,value)
            if isinstance(value,list) and (key in RANGES or is_hour) and len(value)==2 and all(number(x) for x in value):
                if value[0]>value[1]:self.error(file,parts,'faixa [min, max] invertida')
                if is_hour and any(not 0<=x<=24 for x in value):self.error(file,parts,'horário fora de 0–24')
            if isinstance(value,dict):
                if number(value.get('min')) and number(value.get('max')) and value['min']>value['max']:self.error(file,parts,'min maior que max')
                for k,x in value.items():
                    if k.endswith('_min') and number(x) and number(value.get(k[:-4]+'_max')) and x>value[k[:-4]+'_max']:self.error(file,parts+(k,),'limite mínimo maior que máximo')
            if key=='barman_error' and isinstance(value,list):
                for i,chance in enumerate(value):
                    if not number(chance) or not 0<=chance<=1:self.error(file,parts+(i,),'chance de erro fora de [0, 1]')
            if isinstance(value,list) and key=='services':
                for i,range_ in enumerate(value):self.hour_range(file,parts+(i,),range_)
            if file=='events.json' and parts==('odds',) and isinstance(value,list):
                for i,row in enumerate(value):
                    if not isinstance(row,list) or len(row)!=2:self.error(file,parts+(i,),'sorteio deve conter [evento, chance]');continue
                    self.reference(file,parts+(i,0),row[0],self.day_events,'evento do dia',False)
                    if not number(row[1]) or not 0<=row[1]<=1:self.error(file,parts+(i,1),'chance fora de [0, 1]')
                if all(isinstance(x,list) and len(x)==2 and number(x[1]) for x in value) and sum(x[1] for x in value)>1+1e-9:self.error(file,parts,'soma das chances maior que 1')
            if key in MODELS and not any(str(x).startswith('_') for x in parts):self.resolve_model(file,parts,value)
            if key in MODEL_LISTS and isinstance(value,list):
                for i,model in enumerate(value):
                    if isinstance(model,str):self.resolve_model(file,parts+(i,),model)

    def hour_range(self,file,parts,value):
        if not isinstance(value,list) or len(value)!=2 or not all(number(x) for x in value):
            self.error(file,parts,'horário deve ser [início, fim] numérico');return
        if value[0]>value[1]:self.error(file,parts,'faixa de horário invertida')
        if any(not 0<=x<=24 for x in value):self.error(file,parts,'horário fora de 0–24')

    def references(self):
        d=self.docs.get('definitions.json',{});file='definitions.json'
        for id_,e in d.get('expansions',{}).items():
            for i,r in enumerate(e.get('req',[])):self.reference(file,('expansions',id_,'req',i),r,self.expansions,'expansão',False)
            self.reference(file,('expansions',id_,'chapter'),e.get('chapter'),self.chapters,'capítulo')
        # Detecta também pré-requisitos cíclicos: nenhum jogador conseguiria comprar a cadeia.
        def visit(id_,stack):
            if id_ in stack:self.error(file,('expansions',id_,'req'),'ciclo de pré-requisitos: '+' → '.join(stack+[id_]));return
            for parent in d.get('expansions',{}).get(id_,{}).get('req',[]):
                if parent in self.expansions:visit(parent,stack+[id_])
        for id_ in self.expansions:visit(id_,[])
        for i,id_ in enumerate(d.get('expansion_order',[])):self.reference(file,('expansion_order',i),id_,self.expansions,'expansão',False)
        for id_,e in d.get('dishes',{}).items():
            self.reference(file,('dishes',id_,'requires'),e.get('requires'),self.expansions,'expansão')
            for supply in e.get('uses',{}):self.reference(file,('dishes',id_,'uses',supply),supply,self.supplies,'insumo',False)
        for i,id_ in enumerate(d.get('kiosk_menu',[])):self.reference(file,('kiosk_menu',i),id_,self.dishes,'prato',False)
        for id_,e in d.get('staff',{}).items():self.reference(file,('staff',id_,'req'),e.get('req'),self.expansions,'expansão')
        for i,role in enumerate(d.get('staff_rules',{}).get('exempt',[])):self.reference(file,('staff_rules','exempt',i),role,self.staff,'cargo',False)
        for id_,e in d.get('businesses',{}).items():self.reference(file,('businesses',id_,'chapter'),e.get('chapter'),self.chapters,'capítulo')
        for group in ['campaign','side_missions']:
            for i,m in enumerate(d.get(group,[])):self.mission(file,(group,i),m)
        for i,c in enumerate(d.get('chapters',[])):
            for j,m in enumerate(c.get('steps',[])):self.mission(file,('chapters',i,'steps',j),m)
        for id_,q in d.get('quests',{}).items():
            self.reference(file,('quests',id_,'need'),q.get('need'),self.supplies,'insumo',False)
            self.reference(file,('quests',id_,'req'),q.get('req'),self.expansions,'expansão')
        custom=self.docs.get('customization.json',{})
        for parts,o in walk(custom):
            if not isinstance(o,dict):continue
            if 'unlock' in o:self.expansion_spec('customization.json',parts+('unlock',),o['unlock'])
            if 'business' in o:self.reference('customization.json',parts+('business',),o['business'],self.businesses,'negócio')
        op=custom.get('operations',{})
        for id_,o in op.get('hourly',{}).items():self.reference('customization.json',('operations','hourly',id_,'staff'),o.get('staff'),self.staff,'cargo')
        for k in ['maid','receptionist']:self.reference('customization.json',('operations','pousada',k),op.get('pousada',{}).get(k),self.staff,'cargo')
        self.reference('customization.json',('operations','tour_guide'),op.get('tour_guide'),self.staff,'cargo')
        for i,t in enumerate(op.get('tours',[])):
            req=t.get('requires',{})
            if isinstance(req,dict) and req:
                place=req.get('place');self.reference('customization.json',('operations','tours',i,'requires','place'),place,custom.get('places',{}),'lugar',False)
                slots={s.get('id') for s in custom.get('places',{}).get(place,{}).get('slots',[])}
                self.reference('customization.json',('operations','tours',i,'requires','slot'),req.get('slot'),slots,'slot',False)
        bar=self.docs.get('bar.json',{});ingredients={x.get('id') for x in bar.get('ingredients',[])}
        for i,r in enumerate(bar.get('recipes',[])):
            for j,ing in enumerate(r.get('needs',[])):self.reference('bar.json',('recipes',i,'needs',j),ing,ingredients,'ingrediente',False)
        for group in ['ingredients','recipes']:
            for i,row in enumerate(bar.get(group,[])):self.reference('bar.json',(group,i,'requires'),row.get('requires'),bar.get('upgrades',{}),'melhoria do bar')
        for bid,b in self.docs.get('business_games.json',{}).get('businesses',{}).items():
            self.reference('business_games.json',('businesses',bid,'requires'),b.get('requires'),self.expansions,'expansão')
            for i,c in enumerate(b.get('shop',{}).get('crafts',[])):self.reference('business_games.json',('businesses',bid,'shop','crafts',i,'chapter'),c.get('chapter'),self.chapters,'capítulo')
        for role,o in self.docs.get('staff_world.json',{}).get('roles',{}).items():
            self.reference('staff_world.json',('roles',role),role,self.staff,'cargo',False)
            self.reference('staff_world.json',('roles',role,'requires'),o.get('requires'),self.expansions,'expansão')
        for filename,root,listkey in [('map_markers.json','markers','markers'),('audio_zones.json','zones','zones')]:
            for i,o in enumerate(self.docs.get(filename,{}).get(listkey,[])):
                self.reference(filename,(root,i,'requires'),o.get('requires'),self.expansions,'expansão')
                if 'biz' in o:self.reference(filename,(root,i,'biz'),o['biz'],self.businesses,'negócio',False)
        for i,o in enumerate(self.docs.get('lighting.json',{}).get('fixtures',[])):
            if o.get('unlock'):self.expansion_spec('lighting.json',('fixtures',i,'unlock'),o['unlock'])
        for i,o in enumerate(self.docs.get('comic_events.json',{}).get('events',[])):
            if o.get('role'):self.reference('comic_events.json',('events',i,'role'),o['role'],self.staff,'cargo')
            for j,dish in enumerate(o.get('foods',[])):self.reference('comic_events.json',('events',i,'foods',j),dish,self.dishes,'prato',False)
        for weekday,event in self.docs.get('events.json',{}).get('party_calendar',{}).items():self.reference('events.json',('party_calendar',weekday),event,self.day_events,'evento do dia',False)
        chapter=self.docs.get('events.json',{}).get('carnaval_chapter')
        self.reference('events.json',('carnaval_chapter',),chapter,self.chapters,'capítulo')
        hotel=self.docs.get('hotel_rooms.json',{});kinds={x.get('id') for x in hotel.get('kinds',[])}
        for profile,kind in hotel.get('profile_kind',{}).items():self.reference('hotel_rooms.json',('profile_kind',profile),kind,kinds,'tipo de quarto',False)
        for i,kind in enumerate(hotel.get('visitable',[])):self.reference('hotel_rooms.json',('visitable',i),kind,kinds,'tipo de quarto',False)
        # As duas janelas from/to em hotel_rooms são horas (não coordenadas ou minutos).
        for key in ['crew','complaints']:
            obj=hotel.get(key,{})
            for field in ['from','to']:
                if field in obj and (not number(obj[field]) or not 0<=obj[field]<=24):self.error('hotel_rooms.json',(key,field),'horário fora de 0–24')
            if number(obj.get('from')) and number(obj.get('to')) and obj['from']>obj['to']:self.error('hotel_rooms.json',(key,),'faixa de horário invertida')

    def mission(self,file,parts,m):
        kind=m.get('kind');item=m.get('item')
        domains={'expansion':(self.expansions,'expansão'),'chapter':(self.chapters,'capítulo'),
                 'sell':(self.dishes,'prato'),'deliver':(self.supplies,'insumo'),
                 'photo':(self.photo_ids,'assunto de foto')}
        if kind in domains:
            ids,label=domains[kind];self.reference(file,parts+('item',),item,ids,label,False)

    def run(self):
        self.load()
        d=self.docs.get('definitions.json',{})
        self.expansions=set(d.get('expansions',{}));self.staff=set(d.get('staff',{}));self.businesses=set(d.get('businesses',{}))
        self.dishes=set(d.get('dishes',{}));self.supplies=set(d.get('supplies',{}));self.chapters={x.get('id') for x in d.get('chapters',[])}
        self.day_events=set(self.docs.get('events.json',{}).get('events',{}));self.photo_ids={x.get('id') for x in self.docs.get('leisure.json',{}).get('photo_subjects',[])}
        for file,doc in self.docs.items():
            self.generic(file,doc)
            if file in ['custom_assets.json','imported_meshes.json'] and isinstance(doc,dict):
                for key,value in doc.items():
                    if not key.startswith('_') and not package_path(value):self.error(file,(key,),'caminho inválido no catálogo de importação')
        self.references()
        self.problems.sort(key=lambda x:(x['arquivo'],x['campo'],x['problema']))
        return self.problems


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);data=root/'Content/Data';data.mkdir(parents=True)
        baseline={'definitions.json':{'expansions':{'bar':{'req':[]}},'dishes':{'coco':{'uses':{'coco':1}}},'supplies':{'coco':{'cost':3}},'staff':{'guia':{}},'businesses':{'surfe':{'hour':32}},'chapters':[{'id':'pier','steps':[]}], 'campaign':[]},'customization.json':{},'events.json':{'events':{'sol':{}},'odds':[['sol',.5]]},'leisure.json':{'species':[{'id':'sardinha','weight':40,'cm':[10,20]}]},'pool.json':{'water_z':-8,'open':[9,18]},'custom_assets.json':{'mesa':'/Game/Custom/Mesa.Mesa'}}
        def check(docs):
            for p in data.glob('*.json'):p.unlink()
            for name,value in docs.items():(data/name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
            return Linter(data).run()
        assert check(baseline)==[]
        cases=[]
        def case(file,path,value):
            d=copy.deepcopy(baseline);node=d[file]
            for key in path[:-1]:node=node[key]
            node[path[-1]]=value;cases.append(d)
        case('definitions.json',['supplies','coco','cost'],-1)
        case('definitions.json',['expansions','bar','req'],['fantasma'])
        case('definitions.json',['campaign'],[{'id':'x','kind':'sell','item':'fantasma'}])
        case('definitions.json',['expansions','bar','chapter'],'fantasma')
        case('customization.json',['operations'],{'tour_guide':'fantasma'})
        case('leisure.json',['species'],[{'id':'a'},{'id':'a'}])
        case('pool.json',['open'],[18,9])
        case('pool.json',['hours'],[0,25])
        case('pool.json',['odds'],1.1)
        case('pool.json',['model'],'fantasma')
        case('pool.json',['mesh'],'/Game/Inexistente.Inexistente')
        case('pool.json',['name'],'cafÃ©')
        case('pool.json',['name'],'caf\ufffd')
        for i,d in enumerate(cases):assert check(d),i
        d=copy.deepcopy(baseline);d['pool.json']['mesh']='/Game/Custom/Mesa.Mesa';assert not check(d)
        d=copy.deepcopy(baseline);d['pool.json']['name']='Pão, ação e café';assert not check(d)
        d=copy.deepcopy(baseline);d['pool.json']['at']=[-100,20,-8];assert not check(d)
        d=copy.deepcopy(baseline);d['pool.json']['model']='mesa';assert not check(d)
        check(baseline);(data/'quebrado.json').write_text('{');assert any('JSON inválido' in x['problema'] for x in Linter(data).run())
        (data/'quebrado.json').write_text('{"id":"a","id":"b"}');assert any('duplicada' in x['problema'] for x in Linter(data).run())
        print('PASS: JSON inválido/chave duplicada, ids, referências, valores, chances, faixas, horários, modelos e mojibake; aceita posições negativas, renda horária 32 e português válido')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=DEFAULT_DATA)
    parser.add_argument('--asset-index',type=Path,help='Índice de packages obtido da árvore Git, opcional para checkout sem binários')
    parser.add_argument('--json',action='store_true',help='Saída estruturada para relatório/CI')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:self_test();return 0
    # Checkout textual: usar apenas índice de packages comprovados da árvore Git.
    # Em checkout completo os .uasset presentes continuam sendo a fonte primária.
    asset_index=args.asset_index
    if asset_index is None and args.data_dir.resolve()==DEFAULT_DATA.resolve() and not any(args.data_dir.parent.rglob('*.uasset')):
        candidate=ROOT/'tools/ue58/balance/package_index.json'
        if candidate.exists():asset_index=candidate
    linter=Linter(args.data_dir,asset_index);problems=linter.run()
    if args.data_dir.resolve()==DEFAULT_DATA.resolve():
        from glossary_check import check
        problems.extend(check())
        from achievements_check import check as check_achievements
        problems.extend(check_achievements())
        from demo_walkthrough import check as check_demo
        problems.extend(check_demo())
        from number_text_check import check as check_numbers
        problems.extend(check_numbers())
    result={'arquivos_lidos':len(linter.docs),'referencias_modelos_verificadas':linter.asset_checks,'packages_conhecidos':len(linter.packages),'erros':len(problems),'problemas':problems,'fontes_das_regras':RULE_SOURCES}
    if args.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        for row in problems:print(f"{row['arquivo']} → {row['campo']} → {row['problema']}")
        print(f"{'FAIL' if problems else 'PASS'}: {len(linter.docs)} JSON lidos, {len(problems)} problema(s), {linter.asset_checks} referências de modelos verificadas")
    return 1 if problems else 0


if __name__=='__main__':sys.exit(main())

"""Vincula números escritos de instruções a seus dados, sem confundir IDs/ficção com regras.
Não infere economia pelo número encontrado em qualquer lugar: cada vínculo é contextual.
"""
import importlib.util
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'unreal/MareAlta/Content/Data'
NUMBER=re.compile(r'(?<!\w)\d+(?:[.,]\d+)*(?!\w)')


def nums(text):
    text=re.sub(r'%(?:[-+#0]*\d*(?:\.\d+)?)?[sdifgu](?![A-Za-zÀ-ú])|\{\d+\}','',text)
    out=[]
    for m in NUMBER.finditer(text):
        s=m[0]
        if re.fullmatch(r'\d{1,3}(?:\.\d{3})+',s):s=s.replace('.','')
        else:s=s.replace(',','.')
        out.append(float(s))
    return out


def check(docs=None):
    d={p.stem:json.loads(p.read_text(encoding='utf-8-sig')) for p in DATA.glob('*.json')} if docs is None else docs;errors=[]
    def error(file,ptr,msg):errors.append({'arquivo':file+'.json','campo':ptr,'problema':msg})
    def equal(file,ptr,text,expected):
        actual=nums(text)
        if actual!=[float(x) for x in expected]:error(file,ptr,f'números no texto {actual} diferem dos dados {expected}')
    defs=d['definitions'];custom=d['customization'];biz=d['business_games']['businesses']
    for i,m in enumerate(defs['campaign']):
        title_value={'Sete mil vendas':7000,'Quatro mil fregueses':4000}.get(m['title'])
        if title_value is not None and title_value!=m['qty']:error('definitions',f'/campaign/{i}/title','quantidade no título diverge da meta')
        if m['kind'] in ['sales','offerings','recipes','custom','fame']:equal('definitions',f'/campaign/{i}/task',m['task'],[m['qty']])
    for i,c in enumerate(defs['chapters']):
        for j,s in enumerate(c['steps']):
            if s['kind'] in ['deliver','serve','sell','pay','recipes','biz']:equal('definitions',f'/chapters/{i}/steps/{j}/text',s['text'],[s.get('qty',1)])
    for id,q in defs.get('quests',{}).items():
        if nums(q.get('desc','')):equal('definitions','/quests/'+id+'/desc',q['desc'],[q.get('qty',0)])
    for id,b in biz.items():
        for i,level in enumerate(b.get('levels',[])):
            text=level.get('blurb','');s=level.get('set',{});expected=None
            if id=='sorveteria':expected=[s['scoops'][1]] if i==0 else [*s['scoops'],s['show_seconds']]
            elif id=='aluguel':expected=[s['wax_turns']]
            elif id=='food_truck':expected=[s['golden_from'],s['golden_to']]
            elif id=='souvenir':expected=[s['memo_s'],s['fast_s']]
            if expected is not None:equal('business_games',f'/businesses/{id}/levels/{i}/blurb',text,expected)
    # Preços impressos são os preços-base, não o preço personalizado de um save.
    names={v['name']:v['price'] for v in defs['dishes'].values()}
    price_lines=0
    for i,row in enumerate(d['world']['texts']):
        text=row['text'];last=''
        for line in text.splitlines():
            for name in sorted(names,key=len,reverse=True):
                if name.casefold() in line.casefold():last=name;break
            prices=re.findall(r'R\$\s*(\d+(?:[.,]\d+)?)',line)
            if prices:
                if not last:error('world',f'/texts/{i}/text','preço sem produto identificável');continue
                if float(prices[0].replace(',','.'))!=names[last]:error('world',f'/texts/{i}/text','preço impresso diverge de dishes.'+last)
                price_lines+=1
    if not price_lines:error('world','/texts','nenhum preço impresso verificado')
    slots=custom['places']['kiosk']['slots']
    counter=next(s for s in slots if s['id']=='balcao')
    for i,t in enumerate(counter['tiers']):
        if i and 'rápido' in t.get('desc',''):equal('customization',f'/places/kiosk/balcao/{i}',t['desc'],[round(custom['effects']['speed_per_counter_tier']*i*100)])
    boat=next(s for s in custom['places']['passeios']['slots'] if s['id']=='barco')
    for i,t in enumerate(boat['tiers']):
        if i:equal('customization',f'/places/passeios/barco/{i}',t['desc'],[boat['seats']*i])
    # Os parâmetros fixos nativos ficam identificados no relatório; aqui os lados data-driven.
    share=d['business_games']['clerk_share']*100
    equal('tutorial','/tips/BusinessCounter/text',d['tutorial']['tips']['BusinessCounter']['text'],[share])
    bartender=defs['staff']['bartender']['blurb']
    equal('definitions','/staff/bartender/blurb',bartender,[d['bar']['bartender_share']*100,custom['operations']['hourly']['bar']['staff_bonus']*100])
    if d['hotel_events']['min_score']!=.5:error('hotel_events','/min_score','textos “metade das peças” precisam ser revistos')
    trail=d['tours']['trail_tour']
    times=[int(h)*60+round((h-int(h))*60) for h in trail['sunset']]
    written=[int(h)*60+int(m) for h,m in re.findall(r'(\d+)h(\d+)',trail['lines']['go_lighthouse'])]
    if written!=times:error('tours','/trail_tour/lines/go_lighthouse',f'horário escrito {written} difere de sunset {times}')
    return errors


def inventory():
    spec=importlib.util.spec_from_file_location('extract',ROOT/'tools/ue58/i18n_extract.py');extract=importlib.util.module_from_spec(spec);spec.loader.exec_module(extract)
    loc,code=extract.scan_code();data=extract.scan_data();alltext=set(code)|set(data)|set(loc.values());rows=[]
    words=r'\b(?:dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|vinte|trinta|cem|mil|milhão|metade|dobro)\b'
    from collections import defaultdict
    data_index=defaultdict(list);code_index=defaultdict(list)
    def index_data(x,file,path=''):
        if isinstance(x,dict):
            for k,v in x.items():
                if not k.startswith('_'):index_data(v,file,path+'/'+k)
        elif isinstance(x,list):
            for i,v in enumerate(x):index_data(v,file,path+'/'+str(i))
        elif isinstance(x,str):data_index[x].append(file+':'+path)
    for p in DATA.glob('*.json'):index_data(json.loads(p.read_text(encoding='utf-8-sig')),p.name)
    for p in (ROOT/'unreal/MareAlta/Source/MareAlta').glob('*'):
        if p.suffix not in ['.cpp','.h'] or p.name.endswith('Tests.cpp') or any(x in p.stem for x in ['QA','Bench','MareLoc']):continue
        for n,line in enumerate(p.read_text().splitlines(),1):
            for raw in extract.LIT.findall(line):
                text=extract.unescape(raw);code_index[text].append(p.name+':'+str(n));code_index[extract.template(text)].append(p.name+':'+str(n))
            for _,raw in extract.LOCTEXT.findall(line):code_index[extract.unescape(raw)].append(p.name+':'+str(n))
    for text in sorted(alltext):
        cleaned=re.sub(r'\{\d+\}|%(?:[-+#0]*\d*(?:\.\d+)?)?[sdifgu](?![A-Za-zÀ-ú])','',text)
        if not re.search(r'\d|%|'+words,cleaned,re.I):continue
        datarefs=data_index[text];coderefs=code_index[text]
        if re.match(r'QA|Starts|Daily offering|Draw distance|Everyday sea|Local lights|MetaHuman|Night EV|People |Stops of exposure|Use the free|Volcano |start:',text):kind='interno_console_debug';basis='Não é promessa ao jogador; parâmetros de console/câmera/QA, lidos na linha indicada.'
        elif re.search(r'fios|TV |TV\b|chocolate 70|vasos|vasinhos|Aniversário|Caiaques para dois|Sete tempos|Três sabores|Baião|BANGALÔ|Bangalô [12]|Suíte · teto|Hotel quartos ·|Unreal Engine',text):kind='atributo_nome_identificador';basis='Nome, numeração espacial, atributo do objeto/comida ou versão do motor; não é preço nem contador de progressão.'
        elif re.search(r'garoupa|robalo|bigode|trinta anos|Trinta anos|Cem|cem metros|três semanas|dois vasos|sete minutos|dez minutos|Nota 10|Metade do barco',text):kind='narrativo_hipérbole';basis='Fala/humor ou elogio informal, sem regra numérica de economia. Não converter exageros em parâmetros.'
        elif '{' in text or re.search(r'%\.?\d*[df]',text):kind='formato_dinâmico';basis='Os argumentos vêm do estado/dados pelo consumidor referenciado. Denominadores literais de etapas/jogos seguem suas regras nativas.'
        elif any(x in text.lower() for x in ['dívida','pagos','milhão','metade da maré']):kind='contrato_dívida';basis='debt.json principal=1000000, marcos .25/.5/.75 e demo_payment_cap=250000; conteúdo ainda aguarda integração nativa.'
        elif any(x in text.lower() for x in ['r$','vender','vendas','entregar 15','levar','pagar','doar','melhorar receitas','personaliza','fama máxima','ter 2','parafina','ponto dourado','fita','bolas','picolé','atendente','60%','85%','90%','nível','vaga','lugares','hora','21:00','18h','22h','20h','17h','5 estrelas','5★','estrelas','fotos','32 quartos','oferenda','pratos','6h','14h','24h','clientes','servir','ganhe','três dias']):kind='regra_mecânica';basis='Conferência contextual: missões/metas, atributos do mesmo JSON, business_games.levels.set, operações/customization, debt/achievements; constantes nativas em arquivo:linha.'
        else:kind='regra_nativa_ou_enum';basis='Regra de minijogo/numeração/tecla ou atributo contextual da UI; ver consumidor nativo. Sem associação artificial a um preço de outro JSON.'
        rows.append({'text':text,'classification':kind,'basis':basis,'data':datarefs,'cpp':sorted(set(coderefs))})
    defs=json.loads((DATA/'definitions.json').read_text(encoding='utf-8-sig'))
    return {'base':'09dcc3837a91e3428c29b9fb8d91c38dc3c05ec9','scope':'Inventário de números/percentuais e números por extenso nos textos extraídos; não inclui metadados _doc, caminhos pulados nem promete provar o visual dos objetos. check() valida vínculos mecânicos explícitos. Classificações do inventário são triagem contextual, não validação automática de cada afirmação nativa.','facts':{'expansion_costs':{k:v['cost'] for k,v in defs['expansions'].items()},'last_sales_goal':next(m['qty'] for m in defs['campaign'] if m['id']=='fregueses'),'principal':json.loads((DATA/'debt.json').read_text(encoding='utf-8-sig'))['principal'],'businesses':len(defs['businesses']),'hotel_room_kinds':len(json.loads((DATA/'hotel_rooms.json').read_text(encoding='utf-8-sig'))['kinds'])},'entries':rows}


def main():
    import argparse,copy
    p=argparse.ArgumentParser();p.add_argument('--inventory',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.inventory:print(json.dumps(inventory(),ensure_ascii=False,indent=1));return 0
    if a.self_test:
        d={p.stem:json.loads(p.read_text(encoding='utf-8-sig')) for p in DATA.glob('*.json')};assert not check(d)
        for fn in [lambda x:x['definitions']['campaign'][2].update(qty=999),lambda x:x['business_games']['businesses']['aluguel']['levels'][0]['set'].update(wax_turns=99),lambda x:x['definitions']['dishes']['coco_gelado'].update(price=99),lambda x:x['business_games'].update(clerk_share=.1),lambda x:x['definitions']['campaign'][19].update(title='Quatro mil fregueses')]:
            changed=copy.deepcopy(d);fn(changed);assert check(changed)
        print('PASS: quantidade, título, voltas, preço impresso e percentual divergentes são reprovados');return 0
    errors=check()
    for e in errors:print(e)
    print(f'{"FAIL" if errors else "PASS"}: vínculos de números dos textos, {len(errors)} erro(s)')
    return bool(errors)
if __name__=='__main__':raise SystemExit(main())

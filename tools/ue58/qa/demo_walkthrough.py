"""Percurso de alcançabilidade da demo em dados, sem Unreal.

Espelha os predicados lidos em MareSimulation.cpp (BuyExpansion, MissionAmount,
ChapterStepProgress, AdvanceChapter, ClaimMission, IsCampaignAtFullGame) e
MareEvents.cpp::IsEndOfContentDue na base 09dcc383. Não executa C++, navegação,
cronômetros ou UI; não é playtest nem prova de duração de 2 h. Vendas repetíveis
com margem positiva financiam o percurso; não se injeta dinheiro nem se paga dívida.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
LANGS=['de','en','es','fr','it','ja','ko','nl','pl','pt-PT','ru','zh-Hans']
# MareSimulation.cpp:381, :252, :364. Contrato nativo explícito, sem inventar campos no save.
FAME_XP=[0,100,250,450,700,1000,1400,1900,2500,3200]


class InvalidDemo(ValueError):pass


def require(test,message):
    if not test:raise InvalidDemo(message)


def load(root):
    base=Path(root)/'unreal/MareAlta/Content'
    docs={p.stem:json.loads(p.read_text()) for p in (base/'Data').glob('*.json')}
    loc={lang:json.loads((base/'Localization/Mare'/f'{lang}.json').read_text()) for lang in LANGS}
    return docs,loc


class Walk:
    def __init__(self,docs,loc):
        self.docs=docs;self.loc=loc;self.d=docs['definitions'];self.exp=self.d['expansions']
        initial=docs['default_save'];self.cash=float(initial.get('money',0));self.xp=initial.get('prog',{}).get('fame_xp',0)
        self.owned={k for k,v in initial.get('unlocked',{}).items() if v is True}
        self.chapters={};self.business=set();self.trace=[];self.sales=0;self.days=1;self.discoveries=set()
        self.company=False;self.open=False;self.staff=False;self.met=False;self.offerings=0;self.last_offering_day=None
        self.visiting=set();self.costs=0.;self.income=0.

    def note(self,action,**values):self.trace.append(dict(action=action,**values,cash=round(self.cash,2)))

    def translated(self,text,where):
        require(isinstance(text,str) and text,where+': texto vazio')
        for lang in LANGS:require(bool(self.loc[lang]['strings'].get(text)),where+': sem tradução '+lang+' '+repr(text))

    def validate(self):
        require(self.d.get('demo') is True,'definitions.demo precisa estar ativo')
        require(self.cash>=0,'caixa inicial inválido')
        require(not self.docs['default_save'].get('prog',{}).get('ea_end_shown',False),'save inicial já marcou a tela final como vista')
        order=self.d['expansion_order'];require(len(set(order))==len(order),'expansion_order duplicada')
        require(set(order)==set(self.exp),'expansion_order deve listar todas as expansões')
        seen=set()
        for id in order:
            e=self.exp[id]
            require(set(e.get('req',[]))<=seen,'pré-requisito inexistente ou fora de ordem: '+id)
            require(e.get('cost',0)>=0,'preço negativo: '+id)
            if not e.get('full_game'):
                require(not any(self.exp[r].get('full_game') for r in e.get('req',[])),'expansão full_game exigida na demo: '+id)
            if e.get('chapter'):require(any(c['id']==e['chapter'] for c in self.d['chapters']),'capítulo ausente: '+id)
            seen.add(id)
        for chapter in self.d['chapters']:
            for n,s in enumerate(chapter['steps']):
                kind=s['kind'];item=s.get('item');q=s.get('qty',1)
                require(type(q) in (int,float) and math.isfinite(q) and q>=1 and int(q)==q,'meta inválida: '+chapter['id'])
                if kind=='deliver':require(item in self.d['supplies'],'insumo ausente: '+str(item))
                if kind=='sell':require(item in self.d['dishes'] and item in self.d['kiosk_menu'],'produto fora do cardápio: '+str(item))
                if kind=='photo':require(item in {s['id'] for s in self.docs['leisure']['photo_subjects']},'foto ausente: '+str(item))
                self.translated(s['text'],f'chapter/{chapter["id"]}/{n}')
            for k in ['title','story','unlock']:self.translated(chapter[k],'chapter/'+chapter['id']+'/'+k)
        for m in self.d['campaign']:
            for k in ['title','task','story']:self.translated(m[k],'campaign/'+m['id']+'/'+k)
        tips=self.docs['tutorial']['tips']
        # Chaves realmente chamadas por ShowTip(Action), StartBusinessGame ou OpenPhone/RecordPhoto.
        required=['phone','KioskSign','Customer','Fridge','Cupboard','Clean','Bed','Resident','Elder',
                  'Fishing','photo','BarCounter','BarIngredient','BarGlass','PousadaReception','RoomTask',
                  'PoolLeaves','PoolTowel','PoolCooler','TourBooth','TourVest','TourStory','TourSpecies',
                  'TrailWater','TrailStory','RentalTow','Comic','Door','IntroLetter']
        required+=['biz:'+k for k in self.d['businesses']]
        for key in required:require(key in tips,'sistema demo sem dica: '+key)
        for key,t in tips.items():
            for field in ['title','text']:self.translated(t[field],'tutorial/'+key+'/'+field)
        end=self.docs['events']['end_of_content']
        for k in ['title','text','next_title','review_text']:self.translated(end[k],'end/'+k)
        for text in end['next']:self.translated(text,'end/next')
        require('Grand Hotel' in end['text'] and 'Dona Dilce' in end['text'],'final da demo sem gancho do hotel/dívida')

    @property
    def fame(self):return sum(self.xp>=t for t in FAME_XP)

    def sell(self,n,dish='coco_gelado'):
        require(self.company and self.open,'venda com quiosque fechado')
        require(dish in self.d['kiosk_menu'],'produto não vendável: '+dish)
        recipe=self.d['dishes'][dish];req=recipe.get('requires')
        if req and req not in self.owned:self.buy_to(req)
        require(not recipe.get('secret'),'produto exige descoberta não modelada: '+dish)
        cost=sum(self.d['supplies'][k]['cost']*q for k,q in recipe['uses'].items())
        price=recipe['price'];require(price>cost and self.cash>=cost,'sem fonte repetível de caixa: '+dish)
        self.cash+=n*(price-cost);self.income+=n*price;self.costs+=n*cost;self.sales+=n;self.xp+=2*n
        self.note('vender produtos',dish=dish,quantity=n,unit_price=price,unit_supplies=cost)

    def fund(self,cost):
        require(type(cost) in (int,float) and math.isfinite(cost) and cost>=0,'custo inválido')
        r=self.d['dishes']['coco_gelado'];unit=sum(self.d['supplies'][k]['cost']*q for k,q in r['uses'].items())
        # Escolha do jogador: guardar insumos/caixa para financiar pelo menos a próxima venda.
        if self.cash<cost+unit:
            require(r['price']>unit,'vendas de coco sem margem positiva')
            self.sell(math.ceil((cost+unit-self.cash)/(r['price']-unit)))
        require(self.cash>=cost,'caixa insuficiente')
        self.cash-=cost;self.costs+=cost

    def buy_to(self,target):
        require(target in self.exp,'expansão inexistente: '+target)
        require(not self.exp[target].get('full_game'),'expansão full_game exigida na demo: '+target)
        for id in self.d['expansion_order']:
            if not self.exp[id].get('full_game') and id not in self.owned:self.buy(id)
            if id==target:return
        raise InvalidDemo('expansão full_game exigida na demo: '+target)

    def buy(self,id):
        require(id not in self.visiting,'dependência circular em '+id)
        if id in self.owned:return
        self.visiting.add(id);e=self.exp[id]
        require(not e.get('full_game'),'compra de conteúdo completo na demo: '+id)
        for req in e.get('req',[]):
            require(req in self.owned,'compra fora de ordem: '+id+' requer '+req)
        if e.get('chapter'):self.chapter(e['chapter'])
        self.ensure_fame(e.get('fame',1));self.fund(e['cost']);self.owned.add(id);self.visiting.remove(id)
        self.note('comprar expansão',id=id,cost=e['cost'])

    def ensure_fame(self,level):
        require(level<=len(FAME_XP),'fama acima do nível alcançável')
        if level>0 and self.fame<level:self.sell(math.ceil((FAME_XP[level-1]-self.xp)/2))

    def chapter(self,id):
        if id in self.chapters:return
        chapters=self.d['chapters'];index=next((i for i,c in enumerate(chapters) if c['id']==id),-1)
        require(index>=0,'capítulo inexistente: '+id)
        if index:self.chapter(chapters[index-1]['id'])
        c=chapters[index]
        for i,s in enumerate(c['steps']):
            kind=s['kind'];q=int(s.get('qty',1));item=s.get('item')
            if kind=='deliver':
                if item=='peixe':require(any(v['weight']>0 for v in self.docs['leisure']['species']),'pesca impossível: nenhuma espécie disponível')
                else:self.fund(self.d['supplies'][item]['cost']*q)
            elif kind=='pay':self.fund(q)
            elif kind=='serve':self.sell(q) # Deliver incrementa por PRODUTO durante esta etapa.
            elif kind=='sell':self.sell(q,item)
            elif kind=='fame':self.ensure_fame(q)
            elif kind=='photo':require(q<=1,'meta de foto booleana maior que 1')
            elif kind=='recipes':
                self.buy_to('bar');bar=self.docs['bar'];ings={v['id']:v for v in bar['ingredients']}
                available=[r for r in bar['recipes'] if not r.get('known') and not r.get('secret') and not r.get('requires') and all(n in ings and not ings[n].get('requires') for n in r['needs'])]
                require(q<=len(available),'descobertas maiores que receitas acessíveis na demo')
                for r in available[:q]:
                    self.fund(sum(ings[n]['cost'] for n in r['needs']));self.discoveries.add(r['id'])
            elif kind=='biz':
                available=[(v['cost'],k) for k,v in self.d['businesses'].items() if (not v.get('chapter') or v['chapter'] in self.chapters) and v.get('fame',1)<=len(FAME_XP)]
                require(q<=len(available),'negócios exigem capítulo ainda trancado')
                for cost,k in sorted(available):
                    if len(self.business)>=q:break
                    if k not in self.business:self.ensure_fame(self.d['businesses'][k].get('fame',1));self.fund(cost);self.business.add(k);self.note('comprar negócio',id=k,cost=cost)
            else:raise InvalidDemo('tipo de etapa sem consumidor modelado: '+kind)
            self.note('concluir etapa',chapter=id,index=i,kind=kind,quantity=q)
        self.chapters[id]=len(c['steps']);self.cash+=c['reward'];self.income+=c['reward'];self.xp+=80
        self.note('concluir capítulo',id=id)

    def run(self):
        self.validate();gate=None;claimed=[]
        for m in self.d['campaign']:
            kind=m['kind'];item=m.get('item');q=m.get('qty',1)
            require(type(q) in (int,float) and math.isfinite(q) and q>=1 and int(q)==q,'meta inválida: '+m['id'])
            if kind=='expansion':
                require(item in self.exp,'item de campanha inexistente: '+str(item))
                if self.exp[item].get('full_game'):
                    require(m['id']=='marealta' and item=='grand_hotel','expansão full_game exigida antes do limite da demo')
                    gate=m['id'];self.note('campanha trancada',id=gate);break
            if kind in ['company','open','staff','elder','chapter','expansion','finale','photo']:require(q<=1,'meta booleana maior que 1: '+m['id'])
            if kind=='company':self.company=True
            elif kind=='open':self.open=True
            elif kind=='sales':
                if self.sales<q:self.sell(q-self.sales)
            elif kind=='staff':self.fund(self.d['staff']['atendente']['hire']);self.staff=True
            elif kind=='elder':
                self.met=True;self.last_offering_day=self.days
                self.note('conhecer morador e oferta de cortesia',day=self.days,counted=False)
            elif kind=='offerings':
                require(self.met,'oferenda antes de conhecer Seu Tibúrcio')
                require(self.d['kiosk_menu'],'nenhum produto para oferenda')
                r=self.d['dishes']['coco_gelado'];cost=sum(self.d['supplies'][k]['cost']*n for k,n in r['uses'].items())
                # MareSummitWorld.cpp:156–157: a cortesia do encontro cobre o dia,
                # mas não incrementa summit.count. Uma entrega manual por dia seguinte.
                rules=self.d['staff_rules']
                wage_bound=self.d['staff']['atendente']['wage']*(1+rules['raise']*(len(rules['xp_levels'])-1)) if self.staff else 0
                for _ in range(int(q)):
                    if self.last_offering_day==self.days:
                        self.fund(wage_bound);self.days+=1
                    self.fund(cost);self.offerings+=1;self.last_offering_day=self.days
                    self.note('entregar oferenda',day=self.days)
            elif kind=='chapter':self.chapter(item)
            elif kind=='expansion':self.buy_to(item)
            else:raise InvalidDemo('missão inesperada antes do limite: '+kind)
            self.cash+=m['reward'];self.income+=m['reward'];claimed.append(m['id']);self.note('resgatar missão',id=m['id'],reward=m['reward'])
        require(gate=='marealta','demo não para em A Maré Alta da vila')
        for id in self.d['expansion_order']:
            if not self.exp[id].get('full_game') and id not in self.owned:self.buy(id)
        for c in self.d['chapters']:self.chapter(c['id'])
        require(all(id in self.owned for id,e in self.exp.items() if not e.get('full_game')),'tela final inacessível: expansão da demo pendente')
        require(not any(id in self.owned for id,e in self.exp.items() if e.get('full_game')),'hotel/salão liberado na demo')
        require(self.cash>=0,'caixa negativo')
        self.note('mostrar tela final',title=self.docs['events']['end_of_content']['title'])
        return {'scope':'Alcançabilidade de dados; não executa C++ nem mede 2 h. Dinheiro vem de vendas repetíveis, recompensas e custos explícitos; sem gorjetas/fama extra como atalhos. Salário nas noites usa teto conservador dos níveis, não reprodução de relógio/XP.','campaign_claimed':claimed,'gate':gate,'expansions':[id for id in self.d['expansion_order'] if id in self.owned],'chapters':self.chapters,'sales':self.sales,'fame':self.fame,'cash':round(self.cash,2),'trace':self.trace}


def check(root=ROOT):
    try:
        docs,loc=load(root);Walk(docs,loc).run();return []
    except (OSError,ValueError,KeyError,TypeError,OverflowError) as exc:
        return [{'arquivo':'demo_walkthrough','campo':'/','problema':str(exc)}]


def self_test():
    docs,loc=load(ROOT);assert not check();cases=[]
    def mutation(fn):
        d=copy.deepcopy(docs);l=copy.deepcopy(loc);fn(d,l);cases.append((d,l))
    mutation(lambda d,l:d['definitions']['expansions']['bar']['req'].append('fantasma'))
    mutation(lambda d,l:d['definitions']['expansions']['bar']['req'].append('grand_hotel'))
    mutation(lambda d,l:d['definitions']['campaign'][0].update(qty=2))
    mutation(lambda d,l:d['definitions']['chapters'][0]['steps'][0].update(item='peixe_fantasma'))
    mutation(lambda d,l:d['definitions']['chapters'][1]['steps'][0].update(qty=11))
    mutation(lambda d,l:d['definitions']['chapters'][2]['steps'][0].update(qty=999))
    mutation(lambda d,l:d['definitions']['expansions']['bar'].update(full_game=True))
    mutation(lambda d,l:d['definitions']['expansions']['grand_hotel'].update(full_game=False))
    mutation(lambda d,l:l['en']['strings'].update({d['tutorial']['tips']['Customer']['text']:''}))
    mutation(lambda d,l:d['tutorial']['tips'].pop('TourVest'))
    mutation(lambda d,l:d['definitions']['dishes']['coco_gelado'].update(price=0))
    mutation(lambda d,l:d['definitions']['chapters'][3]['steps'][1].update(qty=99))
    mutation(lambda d,l:d['default_save'].setdefault('prog',{}).update(ea_end_shown=True))
    for i,(d,l) in enumerate(cases):
        try:Walk(d,l).run()
        except InvalidDemo:pass
        else:raise AssertionError('mutação não detectada: '+str(i))
    print(f'PASS: percurso válido e {len(cases)} mutações impossíveis/incompletas reprovadas')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--json',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:self_test();return 0
    try:d,l=load(a.root);result=Walk(d,l).run()
    except (OSError,ValueError,KeyError,TypeError) as exc:print('FAIL:',exc);return 1
    if a.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:print('PASS: demo —',len(result['campaign_claimed']),'missões,',len(result['expansions']),'expansões,',len(result['chapters']),'capítulos; hotel trancado e tela final alcançável. Duração não medida.')
    return 0
if __name__=='__main__':raise SystemExit(main())

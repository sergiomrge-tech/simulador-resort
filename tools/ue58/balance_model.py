"""Modelo econômico auditável do Maré Alta Resort (06/11/2026).

Sem Unreal, dependências externas ou escrita em Content. Lê o snapshot do checkout.
As fórmulas monetárias vêm dos JSON/C++; comportamento e tempos de operação são
HIPÓTESES em balance/profiles.json. Não é uma reprodução da navegação/física UE.
Uso: python tools/ue58/balance_model.py --seeds 30 --days 360 --out tools/ue58/balance/results
     python tools/ue58/balance_model.py --self-test
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'unreal/MareAlta/Content/Data'
SOURCE = ROOT / 'unreal/MareAlta/Source/MareAlta'
HERE = Path(__file__).resolve().parent / 'balance'
FILES = ('definitions', 'default_save', 'customization', 'bar', 'events', 'pool',
         'restaurant', 'tours', 'leisure', 'business_games', 'game_room', 'hotel_rooms', 'tutorial')
SOURCES = ('MareSimulation', 'MareBusiness', 'MareBizCommon', 'MareHotelRooms',
           'MareStays', 'MarePoolCup', 'MareRental', 'MareArcade', 'MareIceCream',
           'MarePastel', 'MareSouvenir', 'MareBar', 'MarePool', 'MareTours',
           'MareRestaurant', 'MareStaff', 'MareEvents', 'MareLeisure', 'MareKioskWorld',
           'MareGame', 'MareSummitWorld', 'MareComicEvents', 'MareGameRoom',
           'MareFoosball', 'MareTableTennis')
FAME = ()
PROFILES = json.loads((HERE / 'profiles.json').read_text(encoding='utf-8'))


def rounded(x):
    """FMath::RoundToDouble para valores não negativos usados nas fórmulas."""
    return math.floor(x + .5) if x >= 0 else math.ceil(x - .5)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def read_data():
    global FAME
    code = (SOURCE / 'MareSimulation.cpp').read_text(encoding='utf-8-sig')
    match = re.search(r'FameThresholds\[\]\s*=\s*\{([^}]+)', code)
    if not match:
        raise ValueError('FameThresholds mudou: revisar o extrator')
    FAME = tuple(int(x.strip()) for x in match[1].split(','))
    return {n: json.loads((DATA / f'{n}.json').read_text(encoding='utf-8-sig')) for n in FILES}


def overlay(data, changes):
    """JSON Pointer RFC 6901; exige valor atual para impedir proposta obsoleta."""
    out = copy.deepcopy(data)
    for row in changes:
        node = out[Path(row['file']).stem]
        parts = [s.replace('~1', '/').replace('~0', '~') for s in row['pointer'].split('/')[1:]]
        if not parts:
            raise ValueError('Pointer vazio')
        for key in parts[:-1]:
            node = node[int(key)] if isinstance(node, list) else node[key]
        key = int(parts[-1]) if isinstance(node, list) else parts[-1]
        if node[key] != row['current']:
            raise ValueError(f"Proposta obsoleta: {row['file']} {row['pointer']}")
        node[key] = row['new']
    return out


class Model:
    def __init__(self, data, profile, seed):
        self.d = data
        self.defs = data['definitions']
        self.c = data['customization']
        self.p = PROFILES[profile]
        self.profile, self.seed = profile, seed
        self.r = random.Random(seed)
        self.money = data['default_save']['money']
        self.stock = Counter(data['default_save']['stock'])
        self.xp = data['default_save']['prog']['fame_xp']
        self.ratings = list(data['default_save']['ratings'])
        self.owned, self.staff = set(), {}
        self.biz, self.barup = Counter(), Counter()
        self.custom, self.recipes = defaultdict(lambda: 1), defaultdict(lambda: 1)
        self.custom_owned = set()
        self.ch = Counter()
        self.ch_count = Counter()
        self.stage, self.offerings, self.sales = 0, 0, 0
        self.fish, self.photos, self.ice_sales = 0, set(), 0
        self.known = {x['id'] for x in data['bar']['recipes'] if x.get('known')}
        self.barstock = None
        self.rooms, self.arrival_queue = [], []
        self.complaints = []
        self.queues = defaultdict(list)
        self.rent_out, self.rent_returns = [], []
        self.shelf, self.cards, self.maker_today = [], 0, Counter()
        self.pool_dirt, self.towels, self.popsicles, self.popsicle_stock = 0., 0, 0, 0
        self.restaurant_orders = []
        self.event_booking = None
        self.cup_round, self.cup_edition = None, -1
        self.bar_records = set()
        self.barman_known = set()
        self.barman_day = None
        self.buzz = Counter()
        self.milestones, self.rows = {}, []
        self.post_end_days = 0

    @property
    def fame(self):
        return sum(self.xp >= t for t in FAME)

    @property
    def stars(self):
        return sum(self.ratings) / len(self.ratings)

    def rate(self, x):
        self.ratings = (self.ratings + [clamp(x, 1, 5)])[-40:]

    def add_fame(self, x):
        # MareSimulation::AddFame ignora Xp<=0, inclusive penalidades (bug registrado).
        self.xp += max(0, int(x))

    def book(self, amount, source, expense='operacao'):
        self.money += amount
        (self.income if amount >= 0 else self.expenses)[source if amount >= 0 else expense] += abs(amount)

    def spend(self, amount, category):
        if self.money + 1e-8 < amount:
            return False
        self.book(-amount, '', category)
        return True

    def act(self, seconds):
        # HIPÓTESE: um jogador, orçamento compartilhado; a equipe age em paralelo.
        if self.budget < seconds:
            return False
        self.budget -= seconds
        return True

    def points(self, place, field):
        return sum(s.get(field, 0) * (self.custom[place, s['id']] - 1)
                   for s in self.c['places'].get(place, {}).get('slots', []))

    def effect(self, place, key):
        return self.c['places'].get(place, {}).get('effects', {}).get(key, 0)

    def factor(self, place):
        return 1 + self.effect(place, 'income_per_point') * (self.points(place, 'comfort') + self.points(place, 'beauty')) + self.points(place, 'income')

    def done(self, chapter):
        return self.ch[chapter] >= len(next(x for x in self.defs['chapters'] if x['id'] == chapter)['steps'])

    def available(self, place):
        p = self.c['places'][place]
        return (not p.get('unlock') or p['unlock'] in self.owned) and (not p.get('business') or self.biz[p['business']] > 0)

    def stamp(self, key):
        self.milestones.setdefault(key, self.day)

    def mark_buy(self, key, cost, category='investimentos'):
        if self.money - cost < self.reserve:
            return False
        if not self.spend(cost, category):
            return False
        self.bought.append(key)
        self.stamp(key)
        return True

    def bizdef(self, bid):
        key = {'sorveteria': 'icecream', 'food_truck': 'pastel', 'aluguel': 'rental', 'souvenir': 'shop'}.get(bid)
        g = self.d['business_games']['businesses'][bid]
        out = dict(g.get(key, {}))
        for l in g.get('levels', [])[:max(0, self.biz[bid] - 1)]:
            out.update(l.get('set', {}))
        return out

    def bizmult(self, bid):
        return self.d['business_games']['businesses'][bid]['levels'][self.biz[bid]-2]['price_mult'] if self.biz[bid] >= 2 else 1

    def on_duty(self, role, hour):
        w = self.staff.get(role)
        return bool(w) and (role == 'atendente' or (w['absent'] != self.day and w['off'] != (self.day-1) % 7))

    def staff_skill(self, role):
        w = self.staff[role]
        rules = self.defs['staff_rules']
        level = sum(w['xp'] >= x for x in rules['xp_levels'])
        return (1 + rules['level_bonus'] * (level-1)) * (1-rules['tired_penalty'] if w['fatigue'] >= rules['tired'] else 1)

    def restock_dish(self, dish):
        uses = self.defs['dishes'][dish]['uses']
        if all(self.stock[k] >= q for k, q in uses.items()):
            return True
        missing = {k: max(0, q*10-self.stock[k]) for k, q in uses.items()}
        cost = sum(q*self.defs['supplies'][k]['cost'] for k, q in missing.items())
        if not self.spend(cost, 'estoque_quiosque'):
            return False
        self.stock.update(missing)
        return True

    def kiosk_hour(self, h):
        start, end = self.d['default_save']['company']['sim']['start'], self.d['default_save']['company']['sim']['end']
        # Neon não altera sim.end no código atual: respeitar o horário efetivo, não o blurb.
        if not start <= h-1 < end:
            return
        menu = [k for k in self.defs['kiosk_menu'] if not self.defs['dishes'][k].get('requires') or self.defs['dishes'][k]['requires'] in self.owned]
        weights = [1 + self.c['recipes']['demand_per_level']*(self.recipes[k]-1) for k in menu]
        effects = self.c['effects']
        arrival = (1+effects['arrival_per_point']*(self.points('kiosk', 'comfort')+self.points('kiosk', 'beauty'))) * (1+.04*(self.fame-1)) * self.demand * clamp(1+(self.stars-3.5)*.17, .7, 1.25)
        rush = 1.6 if 12 <= h-1 < 14 or 17 <= h-1 < 18.5 else 1
        elapsed, customers = 0., 0
        while elapsed < 60:
            elapsed += self.r.uniform(18, 30)/(arrival*rush)
            if elapsed <= 60:
                customers += 1
        # HIPÓTESE: bloqueio dos dois balcões/mesas, limpeza e deslocamento resumidos na capacidade.
        cap = int(60 / self.p['attendant_seconds_per_item'] * (1+effects['speed_per_counter_tier']*(self.custom['kiosk','balcao']-1))) if 'atendente' in self.staff else 0
        for _ in range(customers):
            if self.r.random() > self.p['kiosk_share']:
                continue
            items = 1 + (self.r.randrange(4) == 0)  # 25%, não 1,5 itens do modelo antigo
            vip = self.fame >= self.defs['kiosk_vip']['min_fame'] and self.r.random() < self.defs['kiosk_vip']['odds']
            served = 0
            for _ in range(items):
                dish = self.r.choices(menu, weights)[0]
                auto = cap > 0
                if not auto and not self.act(self.p['manual_seconds_per_item']):
                    break
                if not self.restock_dish(dish):
                    break
                cap -= int(auto)
                self.stock.subtract(self.defs['dishes'][dish]['uses'])
                price = rounded(self.defs['dishes'][dish]['price'] * self.c['recipes']['price_mult'][self.recipes[dish]-1])
                tip = round(price*effects['tip_per_comfort']*self.points('kiosk','comfort'), 2)
                self.book(price+tip, 'quiosque')
                if vip:
                    self.book(price*self.defs['kiosk_vip']['tip'], 'vip_quiosque')
                self.add_fame(2+(self.recipes[dish] >= self.c['recipes']['fame_from_level'])+(self.points('kiosk','beauty') >= effects['fame_beauty_threshold']))
                self.sales += 1
                self.ice_sales += dish.startswith('sorvete_')
                for c in self.defs['chapters']:
                    if not self.done(c['id']):
                        step = c['steps'][self.ch[c['id']]]
                        if step['kind'] == 'serve' or step['kind'] == 'sell' and step['item'] == dish:
                            self.ch_count[c['id'], step['kind']] += 1
                served += 1
            if served == items:
                self.rate(5-2.5*(1-self.p['success'])*.4)  # HIPÓTESE: tempo de serviço, não medição
                if vip:
                    self.add_fame(self.defs['kiosk_vip']['fame'])
            else:
                self.rate(1)

    def bar_hour(self, h):
        if 'bar' not in self.owned:
            return
        d = self.d['bar']
        if self.barstock is None:
            self.barstock = Counter({i['id']: d['restock_qty']//2 for i in d['ingredients']})
        if not d['open'][0] <= h < d['open'][1]:
            return
        melt = d['melt_per_hour']*(d['melt_hot'] if self.event == 'calor' else 1)*max(0,1-self.barup['freezer']*d['upgrades']['freezer']['melt_cut'])
        self.barstock['gelo'] = max(0,self.barstock['gelo']-melt)
        rush = d['happy_hour'][0] <= h < d['happy_hour'][1] or self.event == 'lua' and h >= d['full_moon_from']
        seats = min(len(d['stools']), max(d['max_orders_rush'] if rush else d['max_orders'], d['max_orders']+(max(d['upgrades']['banquetas']['seats'][:self.barup['banquetas']], default=0))))
        arrivals = min(seats, self.r.randint(1,2+self.fame//4)*(d['rush_mult'] if rush else 1))
        if h >= d['upgrades']['neon']['night_from']:
            arrivals = min(seats, rounded(arrivals*(1+self.barup['neon']*d['upgrades']['neon']['night_bonus'])))
        recipes = [x for x in d['recipes'] if not x.get('requires') or self.barup[x['requires']]]
        auto_served=0
        if self.on_duty('bartender',h):
            self.barman_known.update(x['id'] for x in recipes if x.get('known'))
            if self.barman_day is None:self.barman_day=self.day
            if self.day-self.barman_day>=d['barman_learn_days']:
                self.barman_day=self.day
                extra=next((x['id'] for x in recipes if x['id'] in self.known and x['id'] not in self.barman_known),None)
                if extra:self.barman_known.add(extra)
        for _ in range(arrivals):
            manual = self.r.random() < .35 and self.act(22)
            if manual:
                unknown = [x for x in recipes if x['id'] not in self.known and not x.get('secret')]
                recipe = self.r.choice(unknown or recipes)
                if recipe.get('secret') and recipe['id'] not in self.known:
                    recipe = recipes[0]
                if self.fame >= d['vip_fame'] and self.r.random() < d['vip_chance']:
                    self.known.update(x['id'] for x in recipes if x.get('secret'))
                if recipe['id'] not in self.known:
                    self.add_fame(d['discovery_fame']); self.known.add(recipe['id'])
            elif self.on_duty('bartender',h) and auto_served<3:
                known = [x for x in recipes if x['id'] in self.barman_known]
                recipe = self.r.choice(known)
                auto_served+=1
            else:
                continue
            if any(self.barstock[k] < 1 for k in recipe['needs']):
                want = {i['id']: max(0,d['restock_qty']+(self.barup['freezer']*d['upgrades']['freezer']['ice_stock'] if i['id']=='gelo' else 0)-self.barstock[i['id']]) for i in d['ingredients'] if not i.get('requires') or self.barup[i['requires']]}
                cost = sum(want.get(i['id'],0)*i['cost'] for i in d['ingredients'])
                if not self.spend(rounded(cost),'estoque_bar'):
                    continue
                self.barstock.update(want)
            self.barstock.subtract(recipe['needs'])
            price = rounded(recipe['price'] * self.factor('bar') * (1+.03*(self.fame-1)) * (1+self.barup['chopeira']*d['upgrades']['chopeira']['chope_price'] if recipe['id']=='chope' else 1))
            if manual:
                self.book(rounded(price*1.05*(1+d['prep_tip']*(2*self.p['success']-1))), 'bar_drinks')
                self.add_fame(1)
            else:
                level = sum(self.staff['bartender']['xp'] >= x for x in self.defs['staff_rules']['xp_levels'])
                if self.r.random() >= d['barman_error'][level-1]:
                    self.book(rounded(price*d['bartender_share']), 'bar_drinks')
        if 'coqueiro' in self.known:
            self.stamp('bar_secreto')

    def lodging_hour(self, h):
        ops = self.c['operations']
        counts = {'pousada': ops['pousada']['rooms_base']+sum(self.defs['expansions'][e].get('rooms',0) for e in self.owned) if 'pousada' in self.owned else 0,
                  'hotel': 32 if 'grand_hotel' in self.owned else 0}
        for place, total in counts.items():
            have = sum(x['place']==place for x in self.rooms)
            for i in range(have,total):
                kind = 'standard'
                if place=='hotel':
                    kinds = list(self.d['hotel_rooms']['visitable'])
                    if i < len(kinds):
                        kind = kinds[i]
                    else:
                        left = i-len(kinds)
                        for k in self.d['hotel_rooms']['kinds']:
                            n = k['count']-kinds.count(k['id'])
                            if left < n: kind = k['id'];break
                            left -= n
                self.rooms.append({'place':place,'index':i,'kind':kind,'state':'free','tasks':[]})
            if not total:
                continue
            hotel = place=='hotel'
            op = ops['hotel_stays' if hotel else 'pousada']
            occ = clamp(.42+.12*(self.stars-4)+.03*(self.fame-7)+sum(self.effect(p,'hotel_per_point')*(self.points(p,'comfort')+self.points(p,'beauty')) for p in self.c['places'])+self.effect('pool','stay_per_point')*(self.points('pool','comfort')+self.points('pool','beauty')), .15,.98) if hotel else clamp(op['occupancy']+op['fame_occupancy']*(self.fame-1)+self.effect('pousada','occupancy_per_comfort')*self.points('pousada','comfort')+self.effect('pousada','occupancy_per_beauty')*self.points('pousada','beauty')+(op['maid_bonus'] if self.on_duty('camareira',h) else 0)+self.effect('pool','stay_per_point')*(self.points('pool','comfort')+self.points('pool','beauty')), .15,1)
            if 10 <= h < 20:
                chance = clamp(occ*op['arrivals_per_room_hour']*total,0,.95)
                count = math.floor(chance*3+self.r.random()) if hotel else int(self.r.random()<chance)
                for _ in range(count):
                    if sum(q['place']==place for q in self.arrival_queue) >= 3:break
                    profile = self.r.choice(op['profiles'])
                    kind = self.d['hotel_rooms']['profile_kind'].get(profile['id'],'standard') if hotel else ''
                    rate = rounded(220+self.points('hotel_suites','rate')+12*(self.stars-4)) if hotel else rounded(op['rate_base']+op['star_bonus']*self.stars+self.points('pousada','rate'))
                    mult = next(x['rate_mult'] for x in self.d['hotel_rooms']['kinds'] if x['id']==kind) if hotel else 1
                    limit = rounded(rate*mult*self.r.uniform(profile['min'],profile['max']))
                    self.arrival_queue.append({'place':place,'profile':profile['id'],'kind':kind,'limit':limit,'offer':rounded(limit*self.r.uniform(.75,.9)),'nights':self.r.randint(profile['nights_min'],profile['nights_max']),'since':h})
            for q in list(self.arrival_queue):
                if q['place'] != place:continue
                free = [x for x in self.rooms if x['place']==place and x['state']=='free']
                if not free:continue
                manual = self.r.random() < self.p['reception_share'] and self.act(10)
                if not manual and not (hotel and h-q['since']>=2 or not hotel and self.on_duty('recepcionista',h)):continue
                room = next((x for x in free if x['kind']==q['kind']),free[0])
                price = rounded((q['offer']+q['limit'])/2) if manual else q['offer']
                mood = .55+.45*clamp((q['limit']-price)/max(1,q['limit']*.25),0,1)
                room.update(state='occupied',guest=q,nights=q['nights'],mood=mood)
                self.book(price*q['nights'],'hotel_diarias' if hotel else 'pousada')
                self.arrival_queue.remove(q)
            budget = self.d['hotel_rooms']['crew']['tasks_per_hour'] if hotel and self.d['hotel_rooms']['crew']['from'] <= h < self.d['hotel_rooms']['crew']['to'] else (rounded(op.get('maid_tasks_per_hour',3)*self.staff_skill('camareira')) if not hotel and self.on_duty('camareira',h) else 0)
            for room in sorted((x for x in self.rooms if x['place']==place and x['state']=='dirty'),key=lambda x:x['index']<3):
                if hotel and room['index']<3 and h<self.d['hotel_rooms']['crew']['visitable_after']:continue
                while room['tasks'] and budget>0:
                    task = room['tasks'][0]
                    if task=='minibar' and not self.spend(room.get('refill',0),'estoque_frigobar'):break
                    room['tasks'].pop(0);budget-=1
                if not room['tasks']:room['state']='free'
        self.hotel_requests(h)

    def hotel_requests(self,h):
        if 'grand_hotel' not in self.owned:return
        rules = self.d['hotel_rooms']['complaints'];vip = rules.get('vip',{})
        kinds = rules['kinds']
        for c in list(self.complaints):
            room = c['room'];kind=c['kind']
            if self.r.random()<self.p['complaint_response']:
                manual = room['index']<len(self.d['hotel_rooms']['visitable']) and self.act(18)
                if not manual and not self.spend(kind['cost'],'reclamacoes'):continue
                room['mood']=clamp(room['mood']+rules['solved_mood'],0,1)
                if kind.get('vip'):
                    self.add_fame(kind['fame']*(vip['in_person_fame_mult'] if manual else 1))
                    if manual:self.book(kind['tip'],'vip_hotel')
                    self.stamp('vip_hotel_atendido')
                elif manual:self.add_fame(1)
                self.complaints.remove(c)
            elif h*60 >= c['due']:
                room['mood']=max(0,room['mood']-(vip['failed_mood'] if kind.get('vip') else rules['failed_mood']))
                # Perda não ocorre: AddFame rejeita negativos.
                self.complaints.remove(c)
        if not rules['from'] <= h < rules['to']:return
        for room in self.rooms:
            if room['place']!='hotel' or room['state']!='occupied' or room.get('vip_asked'):continue
            if room['guest']['profile'] in vip.get('profiles',[]) and self.r.random()<vip['chance_per_hour'] and not any(c['room'] is room for c in self.complaints):
                kind=self.r.choice([k for k in kinds if k.get('vip')]);room['vip_asked']=True
                self.complaints.append({'room':room,'kind':kind,'due':h*60+kind['minutes']});break
        if len(self.complaints)<rules['max_open']:
            for room in self.rooms:
                if room['place']=='hotel' and room['state']=='occupied' and self.r.random()<rules['chance_per_room_hour'] and not any(c['room'] is room for c in self.complaints):
                    kind=self.r.choice([k for k in kinds if not k.get('vip')]);self.complaints.append({'room':room,'kind':kind,'due':h*60+kind['minutes']});break

    def biz_hour(self,h):
        share = self.d['business_games']['clerk_share']
        for bid,level in sorted(self.biz.items()):
            if not level:continue
            definition=self.defs['businesses'][bid];d=self.bizdef(bid);mult=self.bizmult(bid)
            is_open=definition['open'][0]<=h<definition['open'][1]
            # RentalHour nega chuva por multiplicador, mas não fecha por rough_sea (incoerência).
            if bid=='souvenir':
                self.shop_hour(h,d,is_open,mult);continue
            if bid=='surfe':
                if definition['open'][0]<=h-1<definition['open'][1]:
                    rate=definition['hour']*mult*(1+self.c['operations']['business_fame']*(self.fame-1))*self.factor('biz_'+bid)*(self.c['operations']['business_rain'] if self.rain else 1)
                    self.book(rounded(rate*share*self.r.uniform(.85,1.15)),'surfe')
                    if self.act(16):
                        hits=sum(self.r.random()<self.p['success'] for _ in range(3))
                        self.book(rounded(rate*self.d['business_games']['rewards'][hits]),'surfe')
                        self.add_fame(hits*self.d['business_games']['fame_per_hit'])
                continue
            # Fila anterior é atendida pelo funcionário antes da expiração, como no C++.
            for order in self.queues[bid]:
                self.book(rounded(order['price']*share),bid)
                if bid=='aluguel':self.rent_out.append({'due':h+order['duration']/60,'item':order['item']})
            self.queues[bid]=[]
            if bid=='aluguel':
                for fine in self.rent_returns:self.book(rounded(fine*share),'aluguel')
                self.rent_returns=[]
                for rental in list(self.rent_out):
                    if rental['due']<=h or not is_open:
                        self.rent_returns.append(d['fine'] if self.r.random()<d['dent_chance'] else 0);self.rent_out.remove(rental)
                if self.rent_out and self.r.random()<d['adrift_chance'] and self.act(30):
                    self.book(d['rescue_reward'],'aluguel');self.add_fame(3)
            if not is_open:continue
            n=self.r.randint(*d['arrivals'])
            if self.rain:n*=d['rain_mult']
            if self.event=='calor' and 'hot_mult' in d:n*=d['hot_mult']
            if self.event in d.get('party_events',[]):n*=d['party_mult']
            n=min(d['queue_max'],math.floor(n)+(self.r.random()<n%1))
            for _ in range(n):
                order={}
                if bid=='sorveteria':
                    scoops=self.r.randint(*d['scoops']);price=(scoops*d['price_per_scoop']+(d['topping_price'] if self.r.randrange(len(d['toppings'])) else 0))*mult
                elif bid=='food_truck':
                    filling=self.r.choice(d['fillings']);juice=self.r.random()<d['cana_chance'];price=(filling['price']+juice*d['cana_price'])*mult;order.update(filling=filling['price']*mult,juice=juice)
                else:
                    item=self.r.choice(sorted(d['items']));duration=self.r.choice([30,60]);price=rounded(d['items'][item]['price30']*(duration//30)*mult);order.update(item=item,duration=duration)
                if self.act(18 if bid!='aluguel' else 14):
                    hits=sum(self.r.random()<self.p['success'] for _ in range(3))
                    if bid=='aluguel':
                        wax=hits>=2;paid=price+(rounded(price*d['wax_tip']) if wax else 0);self.add_fame(2 if wax else 1)
                        self.rent_out.append({'due':h+duration/60,'item':item})
                    else:
                        paid=rounded(price*d['pay'][hits])+(d['tip_perfect'] if hits==3 else 0)
                        if bid=='food_truck':paid=rounded(order['filling']*d['pay'][hits])+order['juice']*rounded(d['cana_price']*mult)+(d['tip_perfect'] if hits==3 else 0)
                        self.add_fame(hits*d['fame_per_hit'])
                    self.book(paid,bid)
                else:self.queues[bid].append(dict(order,price=price))
            if bid=='sorveteria':
                made=min(d['popsicle_supply'],max(0,d['popsicle_cap']-self.popsicle_stock))
                if self.spend(made*d['popsicle_cost'],'estoque_picoles'):self.popsicle_stock+=made

    def shop_hour(self,h,d,is_open,mult):
        for _ in self.queues['souvenir']:self.book(rounded(d['wrap_fee']*mult*self.d['business_games']['clerk_share']),'souvenir')
        self.queues['souvenir']=[]
        if not is_open:return
        if not self.shelf:
            self.shelf=[{'item':x[0],'qty':x[1]} for x in d['start_shelf']]
        # HIPÓTESE: visita diária para comprar dos artesãos e repor; sem compras mágicas por visitante.
        if h==10:
            crafts=[x for x in d['crafts'] if not x.get('chapter') or self.done(x['chapter'])]
            crafts.sort(key=lambda x:(x['price']*mult-x['cost'])*x['appeal'],reverse=True)
            for i,s in enumerate(self.shelf):
                craft=crafts[i % len(crafts)]
                if not s['item'] or s['qty']==0:s['item']=craft['id']
                c=next(x for x in crafts if x['id']==s['item'])
                n=min(d['slot_cap']-s['qty'],c['daily'])
                if self.spend(n*c['cost'],'estoque_artesanato'):s['qty']+=n
            n=min(d['card_batch'],d['card_max']-self.cards)
            if self.photos and self.spend(n*d['card_cost'],'estoque_postais'):self.cards+=n
        n=self.r.randint(*d['browsers'])*(1+d['fame_browsers']*(self.fame-1))*d['event_mult'].get(self.event,1)
        for _ in range(math.floor(n)+(self.r.random()<n%1)):
            for i,s in enumerate(self.shelf):
                if not s['qty']:continue
                craft=next(x for x in d['crafts'] if x['id']==s['item'])
                if self.r.random()>=d['buy_chance']*d['slots'][i]['mult']*craft['appeal']:continue
                s['qty']-=1;self.book(rounded(craft['price']*mult),'souvenir')
                if self.r.random()<d['gift_chance']:
                    if self.act(12):
                        hits=sum(self.r.random()<self.p['success'] for _ in range(3));self.book(rounded(d['wrap_fee']*mult*d['pay'][hits])+(d['tip_perfect'] if hits==3 else 0),'souvenir');self.add_fame(hits*d['fame_per_hit'])
                    elif len(self.queues['souvenir'])<d['queue_max']:self.queues['souvenir'].append(1)
                break
            if self.cards and self.r.random()<d['card_chance']:
                self.cards-=1;self.book(rounded((d['card_price']+d['subject_bonus']*min(2,len(self.photos)))*mult),'souvenir')

    def pool_hour(self,h):
        if 'pool' not in self.owned:return
        op=self.c['operations']['hourly']['pool'];d=self.d['pool']
        if not op['open'][0]<=h-1<op['open'][1]:return
        self.pool_dirt=min(100,self.pool_dirt+self.r.uniform(*d['dirt_per_hour'])+(d['rain_extra'] if self.rain else 0))
        if not self.rain:
            self.towels=min(len(d['loungers']),self.towels+(self.r.random()<.6));self.popsicles=min(d['max_popsicles'],self.popsicles+self.r.randint(0,2))
        if self.on_duty('piscineiro',h):self.pool_dirt=max(0,self.pool_dirt-30);self.towels=0
        elif self.pool_dirt>25 and self.act(8):self.pool_dirt=max(0,self.pool_dirt-d['scoop']);self.towels=0
        if self.popsicles and self.act(4):
            homemade=self.biz['sorveteria']>0;sold=min(self.popsicles,self.popsicle_stock) if homemade else self.popsicles
            self.book(rounded(sold*d['popsicle_price']*max(1,self.factor('pool'))*(self.bizdef('sorveteria')['homemade_mult'] if homemade else 1)),'picoles')
            self.popsicles-=sold
            if homemade:self.popsicle_stock-=sold
            if sold:self.add_fame(1)
        self.clean=clamp(1-self.pool_dirt/100*d['dirt_penalty']-self.towels*d['towel_penalty'],.3,1)
        if h-1==op['open'][1]-1:self.rate(rounded((2+3*self.clean)*2)/2);self.popsicles=0

    def hourly_passive(self,h):
        for place,op in self.c['operations']['hourly'].items():
            if op['unlock'] not in self.owned or not op['open'][0]<=h-1<op['open'][1]:continue
            staff=1+op.get('staff_bonus',0)*self.staff_skill(op['staff']) if op.get('staff') and self.on_duty(op['staff'],h) else 1
            income=op['guests']*op['spend']*self.factor(place)*(1+.04*(self.fame-1))*staff*(.6 if self.rain else 1)*(getattr(self,'clean',1) if place=='pool' else 1)
            self.book(rounded(income*self.r.uniform(.85,1.15)),place+'_passivo')

    def tours_day(self):
        if 'passeios' not in self.owned:return
        op=self.c['operations'];guide=self.on_duty('guia',14)
        for t in op['tours']:
            req=t.get('requires')
            if req and self.custom[req['place'],req['slot']]<req['tier']:continue
            if self.rough and t['id']!='farol':continue
            seats=t['seats']+rounded(self.points('passeios','seats'))+(2 if self.fame>=8 else 0)
            yesterday=getattr(self,'occupied_yesterday',0)
            wanted=clamp(rounded((1+self.stars*1.2+yesterday*1.5+.3*(self.fame-1)+.08*(self.points('passeios','comfort')+self.points('passeios','beauty')))*(.6 if self.rain else 1))+self.buzz[t['id']],1,seats)
            # Mesmo total de 3 janelas e grupos inteiros do C++, sem remarcação (política cancela mar bravo).
            sold=0
            for _ in range(3):
                people=max(0,min(math.ceil(wanted/3)+self.r.randint(-1,1),seats-sold+2))
                while people>0:
                    adults=self.r.randint(1,min(people,self.d['tours'].get('max_adults',3)));kids=min(people-adults,self.r.randint(1,self.d['tours'].get('max_kids',2))) if people>adults and self.r.random()<self.d['tours'].get('kid_chance',.4) else 0
                    group=adults+kids;people-=group
                    if sold+group<=seats:sold+=group
            manual=self.day % self.p['tour_every']==0 and not getattr(self,'guided_today',False) and self.act(120)
            if not guide and not manual or not sold:continue
            self.guided_today |= manual
            price=rounded(t['price']*self.factor('passeios'))
            good=sum(self.r.random()<self.p['success'] for _ in range(3)) if manual else 0
            rating=clamp(2+good+.5*(3-good),1,5) if manual else self.d['tours']['guide_rating']
            self.book(sold*price+rounded(sold*price*.1*good),'passeios');self.book(-t['cost'],'','custos_passeios')
            self.add_fame(sold//2+good*2);self.rate(rating)
            tier=self.custom['passeios','fotos']
            if tier>1:self.book(rounded(sold*self.d['tours']['photo_share']*rating/5)*self.d['tours']['photo_price'][tier-1],'fotos_passeios')
            buzz=self.d['tours']['buzz'];self.buzz[t['id']]=buzz['great_people'] if rating>=buzz['great'] else buzz['good_people'] if rating>=buzz['good'] else buzz['bad_people'] if rating<buzz['bad'] else 0
            self.stamp('passeio:'+t['id'])

    def restaurant_hour(self,h):
        if 'grand_hotel' not in self.owned:return
        d=self.d['restaurant'];factor=max(1,self.factor('hotel_restaurante'))
        for order in self.restaurant_orders:
            manual=self.act(14)
            share=(1+d['room_fee'] if order['room'] else 1.05) if manual else (.9 if self.on_duty('garcom_hotel',h) else d['crew_share'])
            self.book(rounded(order['price']*factor*share),'restaurante')
            if manual:self.add_fame(1)
        self.restaurant_orders=[]
        if any(a<=h<b for a,b in d['services']):
            n=sum(self.r.random()<.5 for _ in d['tables'])
            for _ in range(n):self.restaurant_orders.append({'price':self.r.choice(d['menu'])['price'],'room':False})
            if self.r.random()<.7:self.restaurant_orders.append({'price':self.r.choice(d['menu'])['price'],'room':True})
        if self.event_booking and self.event_booking['day']==self.day and h-1==d['event_hour']:
            e=self.event_booking['event'];self.book(rounded(e['income']*factor),'eventos_hotel');self.add_fame(e['fame']);self.stamp('evento:'+e['id']);self.event_booking=None

    def game_room_hour(self,h):
        if 'salao_jogos' not in self.owned:return
        d=self.d['business_games'];room=d['game_room'];cup=self.d['game_room']['cup']
        if room['token_hours'][0]<=h-1<room['token_hours'][1]:
            total=len(self.rooms);occupied=sum(x['state']=='occupied' for x in self.rooms)
            guests=rounded(room['night_players'][0]+(room['night_players'][1]-room['night_players'][0])*occupied/max(1,total))
            if self.cup_night:guests+=self.r.randint(*cup['spectators'])
            self.book(rounded(guests*room['token_price']*self.r.uniform(.8,1.2)),'fichas')
        if h==19 and self.day%self.p['tour_every']==0 and self.act(90):
            win=self.r.random()<self.p['win'];stake=self.d['game_room']['stakes'][0]
            self.book(stake if win else -stake,'sinuca_tenis','apostas')
            if win:self.add_fame(2)
        # Máquinas do mesmo id compartilham limite de uma recompensa por hora.
        if h in (20,22) and self.act(35):
            for bid in ['pebolim','fliperama']:
                hits=sum(self.r.random()<self.p['success'] for _ in range(3))
                self.book(rounded(d['businesses'][bid]['base']*d['rewards'][hits]),bid)
                self.add_fame(hits*d['fame_per_hit'])
            self.stamp('fliperamas_jogados')

    def cup_day(self):
        if 'salao_jogos' not in self.owned:return
        cup=self.d['game_room']['cup'];edition=(self.day-cup['first_day'])//cup['every_days'];into=(self.day-cup['first_day'])%cup['every_days']
        if 0<=into<cup['signup_days'] and edition!=self.cup_edition and self.cup_round is None and self.r.random()<self.p['cup_join'] and self.spend(cup['fee'],'campeonato'):
            self.cup_round=0;self.cup_edition=edition;self.stamp('campeonato_inscrito')
        if self.cup_round is not None and self.act(90):
            self.cup_night=True;win=self.r.random()<self.p['win']
            if self.cup_round==2:
                self.book(cup['prize'] if win else cup['runner_up'],'campeonato')
                if win:self.add_fame(cup['fame'])
                self.cup_round=None
            elif not win:self.cup_round=None
            else:self.cup_round+=1
        if into==cup['signup_days']-1 and edition!=self.cup_edition:self.cup_night=True

    def story(self):
        # HIPÓTESE: a visita ao morro cabe nos 960 segundos; todo perfil realiza o núcleo narrativo.
        if self.day>=2 and getattr(self,'offering_day',0)!=self.day:
            self.offering_day=self.day
            self.offerings+=1
            if self.restock_dish('coco_gelado'):self.stock.subtract(self.defs['dishes']['coco_gelado']['uses'])
        if self.day>=2 and not self.fish:
            self.fish=5;self.stock['peixe']+=5
            species=self.d['leisure']['species']
            for fish in self.r.choices(species,weights=[x['weight'] for x in species],k=5):self.add_fame(10 if fish['id']=='garoupa' else 2)
        if self.day>=2:
            new={'farol','por_do_sol'}-self.photos
            self.photos.update(new);self.add_fame(3*len(new))
        for idx,c in enumerate(self.defs['chapters']):
            cid=c['id']
            if idx and not self.done(self.defs['chapters'][idx-1]['id']):break
            while not self.done(cid):
                step=c['steps'][self.ch[cid]];kind=step['kind'];qty=step.get('qty',1)
                have={'serve':self.ch_count[cid,'serve'],'sell':self.ch_count[cid,'sell'],'fame':self.fame,'recipes':sum(x['id'] in self.known and not x.get('known') for x in self.d['bar']['recipes']),'biz':sum(v>0 for v in self.biz.values()),'photo':step.get('item') in self.photos,'pay':self.money}.get(kind,0)
                if kind=='deliver':
                    item=step['item'];cost=max(0,qty-self.stock[item])*self.defs['supplies'][item]['cost']
                    if self.money<cost+self.reserve:break
                    self.spend(cost,'estoque_historia');self.stock[item]=max(qty,self.stock[item]);have=qty
                if have<qty:break
                if kind=='pay' and not self.spend(qty,'historia'):break
                if kind=='deliver':self.stock[step['item']]-=qty
                self.ch[cid]+=1
                if self.done(cid):self.book(c['reward'],'recompensas');self.add_fame(80);self.stamp('capitulo:'+cid)
        self.claim_campaign()

    def claim_campaign(self):
        while self.stage<len(self.defs['campaign']):
            m=self.defs['campaign'][self.stage];k=m['kind'];item=m.get('item')
            have={'company':1,'open':1,'sales':self.sales,'staff':'atendente' in self.staff,'elder':self.day>=2,'offerings':self.offerings,'fame':self.fame,'recipes':sum(v-1 for v in self.recipes.values()),'custom':sum(v-1 for v in self.custom.values()),'finale':self.day>=self.milestones.get('festa_pronta',10**6)+1}.get(k,0)
            if k=='expansion':have=item in self.owned
            if k=='chapter':have=self.done(item)
            if have<m['qty']:break
            self.book(m['reward'],'recompensas');self.stamp('missao:'+m['id']);self.stage+=1
        if self.stage<len(self.defs['campaign']) and self.defs['campaign'][self.stage]['kind']=='finale':self.stamp('festa_pronta')
        if self.stage==len(self.defs['campaign']):self.stamp('campanha_completa')

    def purchases(self):
        # HIPÓTESE: compra diária no fechamento, reserva para operação; não exige pousada para comprar negócio.
        for role,d in self.defs['staff'].items():
            if d.get('company') or role in self.staff or d.get('req') and d['req'] not in self.owned:continue
            if self.mark_buy('equipe:'+role,d['hire']):
                self.staff[role]={'xp':0,'fatigue':0,'off':-1 if role=='atendente' else 6,'absent':-1}
        for eid in self.defs['expansion_order']:
            e=self.defs['expansions'][eid]
            if eid in self.owned or any(x not in self.owned for x in e['req']) or self.fame<e.get('fame',0) or e.get('chapter') and not self.done(e['chapter']):continue
            self.stamp('liberada:'+eid)
            if self.mark_buy(eid,e['cost']):self.owned.add(eid)
        for bid,b in sorted(self.defs['businesses'].items(),key=lambda p:p[1]['cost']):
            if self.biz[bid] or self.fame<b['fame'] or b.get('chapter') and not self.done(b['chapter']):continue
            if self.mark_buy('negocio:'+bid,b['cost']):self.biz[bid]=1
        # Melhorias úteis antes do hotel: pequenas compras deixam capital para expansões.
        limit=max(0,self.money-self.reserve)*(.3 if 'grand_hotel' not in self.owned else .65)
        candidates=[]
        for place,p in self.c['places'].items():
            if not self.available(place):continue
            for s in p['slots']:
                if s.get('unlock') and s['unlock'] not in self.owned:continue
                tier=self.custom[place,s['id']]
                if tier<5:
                    cost=rounded(s['base_price']*self.c['price_mult'][tier]);candidates.append((cost,'custom',(place,s['id'],tier+1)))
        for dish,d in self.defs['dishes'].items():
            if d.get('requires') and d['requires'] not in self.owned:continue
            level=self.recipes[dish]
            if level<5:candidates.append((rounded(d['price']*self.c['recipes']['cost_mult'][level]),'receita',(dish,level+1)))
        if 'bar' in self.owned:
            for bid,b in self.d['bar']['upgrades'].items():
                level=self.barup[bid]
                if level<len(b['prices']):candidates.append((b['prices'][level],'bar',(bid,level+1)))
        for bid,level in self.biz.items():
            if level<3:
                b=self.d['business_games']['businesses'][bid]['levels'][level-1]
                if self.fame>=b['fame']:candidates.append((b['cost'],'negocio_nivel',(bid,level+1)))
        for cost,kind,key in sorted(candidates):
            if cost>limit:continue
            name=kind+':'+':'.join(map(str,key))
            if not self.mark_buy(name,cost):continue
            limit-=cost
            if kind=='custom':self.custom[key[:2]]=key[2];self.custom_owned.add(key)
            elif kind=='receita':self.recipes[key[0]]=key[1]
            elif kind=='bar':self.barup[key[0]]=key[1]
            else:self.biz[key[0]]=key[1]
        self.claim_campaign()
        if len(self.owned)==len(self.defs['expansions']) and all(self.done(c['id']) for c in self.defs['chapters']):self.stamp('tela_fim_ea')
        all_custom=all((p,s['id'],t) in self.custom_owned for p,v in self.c['places'].items() for s in v['slots'] for t in range(2,6))
        all_recipes=all(self.recipes[k]==5 for k in self.defs['dishes'])
        if all_custom and all_recipes and all(self.biz[k]==3 for k in self.defs['businesses']) and all(self.barup[k]==len(v['prices']) for k,v in self.d['bar']['upgrades'].items()) and len(self.owned)==len(self.defs['expansions']):self.stamp('todas_compras')

    def night(self):
        rules=self.defs['staff_rules']
        for role,w in self.staff.items():
            level=sum(w['xp']>=x for x in rules['xp_levels'])
            self.book(-rounded(self.defs['staff'][role]['wage']*(1+rules['raise']*(level-1))),'','salarios')
            if role!='atendente':
                off=w['off']==(self.day-1)%7 or w['absent']==self.day
                w['fatigue']=clamp(w['fatigue']-rules['recover']+(-rules['rest'] if off else rules['shifts']['integral']['fatigue']),0,100)
                if w['fatigue']>=rules['absent']:w['absent']=self.day+1
        for bid in self.defs['businesses']:
            if self.biz[bid]:self.book(-self.defs['businesses'][bid]['wage'],'','salarios_negocios')
        self.book(-rounded(sum(self.defs['expansions'][e]['cost']*.005 for e in self.owned)),'','manutencao')
        occupied=sum(x['state']=='occupied' for x in self.rooms);self.occupied_yesterday=occupied
        for room in self.rooms:
            if room['state']!='occupied':continue
            room['nights']-=1
            if room['nights']>0:continue
            hotel=room['place']=='hotel';rating=(3.9 if hotel else 3.3+.025*self.points('pousada','comfort'))+1.2*(room['mood']-.5)+.3
            if hotel:rating+=sum(self.effect(p,'hotel_per_point')*(self.points(p,'comfort')+self.points(p,'beauty')) for p in self.c['places'])*4
            self.rate(rating);self.add_fame(2 if hotel else 1)
            room['state']='dirty';room['tasks']=['bed','towels','trash']
            if hotel:
                items=self.d['hotel_rooms']['minibar'];taken=[self.r.choice(items) for _ in range(self.r.randint(0,self.d['hotel_rooms']['minibar_take_max']))]
                self.book(sum(x['price'] for x in taken),'frigobar');room['refill']=sum(x['cost'] for x in taken)
                if taken:room['tasks'].append('minibar')
                self.complaints=[c for c in self.complaints if c['room'] is not room]
                # vip_asked não é limpo no checkout atual: reproduzido, não corrigido.
        self.arrival_queue=[]
        if 'grand_hotel' in self.owned:
            hotel_occ=sum(x['place']=='hotel' and x['state']=='occupied' for x in self.rooms)
            self.book(rounded(hotel_occ*1.7*35*self.factor('hotel_restaurante')*self.factor('hotel_piscina')),'hotel_refeicoes_noturnas')
            self.book(-900,'','equipe_hotel')
        self.add_fame(math.floor(self.points('home','beauty')*self.effect('home','fame_per_beauty_night')))

    def roll_event(self,day):
        d=self.d['events']
        if day>=d['party_from_day']:
            party=d['party_calendar'].get(str(day%7))
            if party and (party!='carnaval' or self.done(d['carnaval_chapter'])):return party
        roll=self.r.random()
        for event,odds in d['odds']:
            roll-=odds
            if roll<0:return event
        return ''

    def run(self,days):
        self.forecast=self.roll_event(1)
        self.prepared=False
        for self.day in range(1,days+1):
            self.income,self.expenses=Counter(),Counter();self.bought=[];start=self.money
            self.reserve=100 if 'bar' not in self.owned else (1200 if 'grand_hotel' in self.owned else 250)
            self.budget=max(0,self.p['active_seconds']-(180 if self.day>=2 else 40));self.guided_today=False;self.cup_night=False
            self.event=self.forecast;self.forecast=self.roll_event(self.day+1)
            seasons=self.d['events']['seasons'];pos=(self.day-1)%sum(x['days'] for x in seasons)
            for season in seasons:
                if pos<season['days']:break
                pos-=season['days']
            ed=self.d['events']['events'].get(self.event,{})
            self.rain=ed.get('rain',False) or self.r.random()<season['rain_odds'];self.rough=ed.get('rough_sea',False)
            self.demand=season['demand']*ed.get('deco_demand' if self.prepared and 'deco_demand' in ed else 'demand',1)
            if self.event=='tempestade' and not self.prepared:
                for k in self.stock:self.stock[k]-=math.floor(self.stock[k]*self.d['events']['storm_loss'])
            self.story()
            # Passeios e campeonato reservam tempo antes das tarefas opcionais; os bilhetes são agregados por dia.
            self.tours_day();self.cup_day()
            for h in range(9,25):
                for role,w in self.staff.items():
                    if self.on_duty(role,h):w['xp']+=rules_xp(self.defs)
                self.kiosk_hour(h);self.lodging_hour(h);self.bar_hour(h);self.biz_hour(h);self.pool_hour(h);self.restaurant_hour(h);self.game_room_hour(h);self.hourly_passive(h)
            self.night();self.story()
            affordable=[k for k,e in self.defs['expansions'].items() if k not in self.owned and all(r in self.owned for r in e['req']) and self.fame>=e.get('fame',0) and (not e.get('chapter') or self.done(e['chapter'])) and self.money>=e['cost']]
            self.purchases()
            if 'grand_hotel' in self.owned and not self.event_booking and self.day%self.p['event_every']==0:
                unseen=[e for e in self.d['restaurant']['events'] if 'evento:'+e['id'] not in self.milestones]
                event=max(unseen or self.d['restaurant']['events'],key=lambda e:e['income']*self.factor('hotel_restaurante')-e['cost'])
                if self.spend(event['cost'],'preparativos_hotel'):self.event_booking={'event':event,'day':self.day+1}
            prep=self.d['events']['events'].get(self.forecast,{}).get('prep')
            self.prepared=bool(prep and self.spend(self.d['events']['prep_cost'][prep],'preparativos_dia'))
            row={'dia':self.day,'caixa_inicial':round(start,2),'renda_total':round(sum(self.income.values()),2),'despesas_total':round(sum(self.expenses.values()),2),'caixa':round(self.money,2),'fama_xp':self.xp,'fama_nivel':self.fame,'estrelas':round(self.stars,2),'vendas_acumuladas':self.sales,'evento':self.event,'chuva':self.rain,'compras':'; '.join(self.bought),'expansoes_compraveis_antes_das_compras':'; '.join(affordable),'proxima_missao':self.defs['campaign'][self.stage]['id'] if self.stage<len(self.defs['campaign']) else 'concluida','segundos_ativos':self.p['active_seconds']-self.budget,'hotel_ocupados':sum(x['place']=='hotel' and x['state']=='occupied' for x in self.rooms)}
            row.update({'renda_'+k:round(v,2) for k,v in self.income.items()});row.update({'despesa_'+k:round(v,2) for k,v in self.expenses.items()})
            assert abs(row['caixa_inicial']+row['renda_total']-row['despesas_total']-row['caixa'])<.04
            assert all(v>=-1e-6 for v in self.stock.values())
            assert self.budget>=0
            assert sum(x['place']=='hotel' for x in self.rooms)<=32
            self.rows.append(row)
            if 'todas_compras' in self.milestones and 'campanha_completa' in self.milestones:
                self.post_end_days+=1
                if self.post_end_days>=7:break
        return self


def rules_xp(defs):
    return defs['staff_rules']['xp_per_hour']


def quantile(values,p):
    if not values:return None
    values=sorted(values);i=(len(values)-1)*p;lo=int(i);hi=math.ceil(i)
    return round(values[lo]+(values[hi]-values[lo])*(i-lo),2)


def summarize(models, days):
    milestones=sorted({k for m in models for k in m.milestones if not k.startswith(('custom:','receita:','bar:'))})
    results={k:{'concluidos':sum(k in m.milestones for m in models), 'p10':quantile([m.milestones[k] for m in models if k in m.milestones],.1),'p50':quantile([m.milestones[k] for m in models if k in m.milestones],.5),'p90':quantile([m.milestones[k] for m in models if k in m.milestones],.9)} for k in milestones}
    return {'sementes':len(models),'limite_dias':days,'marcos':results,'caixa_final_p50':quantile([m.money for m in models],.5),'censurados_compras':sum('todas_compras' not in m.milestones for m in models),'censurados_campanha':sum('campanha_completa' not in m.milestones for m in models)}


def write_csv(path, rows):
    fields=list(rows[0])+sorted(set().union(*(set(x) for x in rows))-set(rows[0]))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,restval=0);w.writeheader();w.writerows(rows)


def self_test(data):
    assert FAME == (0,100,250,450,700,1000,1400,1900,2500,3200)
    a=Model(data,'medio',17).run(8);b=Model(data,'medio',17).run(8)
    assert a.rows==b.rows, 'Mesma semente precisa reproduzir a trajetória'
    assert Model(data,'medio',18).run(8).rows!=a.rows, 'Sementes diferentes precisam afetar eventos'
    assert all(len(m['p10'].__str__())>0 for m in summarize([a],8)['marcos'].values())
    x=Model(data,'medio',0);x.xp=100;x.add_fame(-3);assert x.xp==100
    x.custom['hotel_restaurante','mesas']=2;assert x.factor('hotel_restaurante')==1.12
    changes=[{'file':'definitions.json','pointer':'/expansions/grand_hotel/cost','current':data['definitions']['expansions']['grand_hotel']['cost'],'new':1}]
    modified=overlay(data,changes);assert modified['definitions']['expansions']['grand_hotel']['cost']==1
    assert data['definitions']['expansions']['grand_hotel']['cost']!=1
    try:overlay(modified,changes)
    except ValueError:pass
    else:raise AssertionError('Deve rejeitar valor atual divergente')
    print('PASS: determinismo, aleatoriedade, caixa, estoque, fórmula de decoração, penalidade real, overlay sem mutação e rejeição de proposta obsoleta')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('legacy_days',type=int,nargs='?')
    parser.add_argument('--days',type=int,default=360)
    parser.add_argument('--seeds',type=int,default=30)
    parser.add_argument('--out',type=Path,default=HERE/'results')
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--service-scale',type=float,default=1,help='Sensibilidade: multiplicador do tempo por produto do atendente (hipótese)')
    args=parser.parse_args()
    if args.service_scale<=0:parser.error('service-scale deve ser positivo')
    for p in PROFILES.values():p['attendant_seconds_per_item']*=args.service_scale
    if args.seeds<1 or args.days<1:parser.error('days e seeds devem ser positivos')
    data=read_data()
    if args.self_test:self_test(data);return
    args.out.mkdir(parents=True,exist_ok=True)
    changes=json.loads((HERE/'proposed.json').read_text(encoding='utf-8'))
    summary={}
    (args.out/'configuracao.json').write_text(json.dumps({'dias':args.legacy_days or args.days,'sementes':list(range(args.seeds)),'perfis':PROFILES,'mudancas':changes,'service_scale':args.service_scale},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for scenario,d in [('atual',data),('proposto',overlay(data,changes))]:
        summary[scenario]={}
        for profile in PROFILES:
            models=[Model(d,profile,seed).run(args.legacy_days or args.days) for seed in range(args.seeds)]
            summary[scenario][profile]=summarize(models,args.legacy_days or args.days)
            write_csv(args.out/f'{scenario}_{profile}_diario_seed0.csv',models[0].rows)
            # Uma linha por execução, incluindo limites sem marco em vez de fingir conclusão.
            seed_rows=[{'semente':m.seed,**{k:m.milestones.get(k,'') for k in ['grand_hotel','salao_jogos','tela_fim_ea','campanha_completa','todas_compras']},'caixa_final':round(m.money,2)} for m in models]
            write_csv(args.out/f'{scenario}_{profile}_sementes.csv',seed_rows)
            print(scenario,profile,{k:v for k,v in summary[scenario][profile]['marcos'].items() if k in ['grand_hotel','tela_fim_ea','campanha_completa','todas_compras']})
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths=[DATA/f'{f}.json' for f in FILES]+[SOURCE/f'{f}.cpp' for f in SOURCES]
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (args.out/'inputs_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

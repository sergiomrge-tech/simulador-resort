"""Economy model of Maré Alta Resort (first balancing pass, 02/11/2026).

Reads the game data (definitions.json, customization.json, bar/pool/tours/restaurant/business_games/events.json) and
simulates an average player day by day: the kiosk always, every place bought as soon as the money (and the
prerequisites/fame) allow, in the order of expansion_order, the businesses when the fame allows. Prints the money curve,
the day of each unlock and the real playing time (1 game minute = 1 real second; a day = 08:00-24:00 played).

Assumptions are marked ASSUME and are the numbers to replace with measured play data.
    python tools/ue58/balance_model.py [days]
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/Content/Data'


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


defs, custom = load('definitions.json'), load('customization.json')
bar, pool, tours = load('bar.json'), load('pool.json'), load('tours.json')
restaurant, games, events = load('restaurant.json'), load('business_games.json'), load('events.json')
FAME = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200]

# ASSUME: how much of each system an average player actually does per day.
KIOSK_SERVED_SHARE = .8            # of the customers that arrive
KIOSK_ITEMS_PER_ORDER = 1.5
KIOSK_HOURS = 10                   # 08:00-18:00
BAR_ORDERS_SERVED_PER_HOUR = 2.0   # by hand, plus the passive hourly income
POUSADA_NIGHTS_PER_ROOM = .45
TOURS_GUIDED = 2                   # of 3 a day, about 5 passengers each
BUSINESS_TASKS_PER_DAY = 3         # counter tasks per owned business, 2/3 hits on average
RESTAURANT_DISHES_PER_DAY = 14
DAY_MINUTES_REAL = 16              # 08:00 to 24:00 at 1 game minute per second (MareGame clock, 04/11)
# Story time on top of the economy (04/11 campaign): the daily walk to Seu Tibúrcio's basket and back (421 m trail plus
# the village, about 3 real minutes) from the day he is met (day 2), and ~25 min of chapters, minigames and the party.
OFFERING_MIN_PER_DAY, STORY_MINUTES = 3.0, 25


def fame_level(xp):
    return max(i + 1 for i, t in enumerate(FAME) if xp >= t)


def kiosk_day(level, beauty_points):
    factor = (1 + .035 * beauty_points) * (1 + .04 * (level - 1))
    customers = KIOSK_HOURS * 3600 / 60 / (24 / factor)          # one every 18-30 real seconds / factor
    avg_price = sum(d['price'] for d in defs['dishes'].values()) / len(defs['dishes'])
    sales = customers * KIOSK_SERVED_SHARE * KIOSK_ITEMS_PER_ORDER
    return sales * avg_price, sales * 2                          # money, fame xp (2 per sale)


def run(days):
    owned, money, xp, beauty = set(), 0.0, 0, 0
    order = defs.get('expansion_order') or list(defs['expansions'])
    timeline = []
    for day in range(1, days + 1):
        level = fame_level(xp)
        income, gain = kiosk_day(level, beauty)
        hourly = custom['operations']['hourly']
        if 'bar' in owned:
            b = hourly['bar']
            drinks = sum(r['price'] for r in bar['recipes']) / len(bar['recipes'])
            income += b['guests'] * b['spend'] * (b['open'][1] - b['open'][0]) + BAR_ORDERS_SERVED_PER_HOUR * 12 * drinks
        if 'pool' in owned:
            p = hourly['pool']
            income += p['guests'] * p['spend'] * (p['open'][1] - p['open'][0]) * .9 + 4 * pool['popsicle_price']
        if 'pousada' in owned:
            income += custom['operations']['pousada']['rate_base'] * POUSADA_NIGHTS_PER_ROOM * 2
        if 'passeios' in owned:
            income += sum(t['price'] * 5 - t['cost'] for t in custom['operations']['tours'][:TOURS_GUIDED])
        if 'grand_hotel' in owned:
            income += 32 * .45 * 220 * .3 + RESTAURANT_DISHES_PER_DAY * 60      # ASSUME: hotel night net share
        if 'salao_jogos' in owned:
            income += 5 * 4 * 5 + 2 * 40
        for biz_id, b in defs['businesses'].items():
            if biz_id in owned:
                income += b['hour'] * (b['open'][1] - b['open'][0]) - b.get('wage', 0) + BUSINESS_TASKS_PER_DAY * b['hour'] * 1.4
        wages = sum(defs['staff'][r]['wage'] for r in ('atendente',) if day > 3)
        upkeep = .005 * sum(defs['expansions'][e]['cost'] for e in owned if e in defs['expansions'])   # 04/11 challenge
        money += income - wages - upkeep
        xp += gain
        bought = []
        for exp_id in order:
            e = defs['expansions'].get(exp_id)
            if not e or exp_id in owned or any(r not in owned for r in e.get('req', [])):
                continue
            if fame_level(xp) < (e.get('fame') or 0):   # the Grand Hotel waits for fame 9 (04/11)
                continue
            if money >= e['cost']:
                money -= e['cost']
                owned.add(exp_id)
                beauty += 3
                bought.append(exp_id)
        for biz_id, b in sorted(defs['businesses'].items(), key=lambda kv: kv[1]['cost']):
            if biz_id not in owned and fame_level(xp) >= b.get('fame', 1) and money >= b['cost'] and 'pousada' in owned:
                money -= b['cost']
                owned.add(biz_id)
                bought.append(biz_id)
        timeline.append((day, round(income), round(money), fame_level(xp), bought))
    return timeline


if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    print('dia | renda do dia | caixa | fama | comprou')
    hotel = None
    sales, sales_day, fame10 = 0.0, None, None
    expansions = 0
    for day, income, money, level, bought in run(days):
        expansions += len([b for b in bought if b in defs['expansions']])
        sales += kiosk_day(level, expansions * 3)[1] / 2
        if sales_day is None and sales >= 4000:
            sales_day = day
        if fame10 is None and level >= 10:
            fame10 = day
        print(f'{day:3d} | R$ {income:7d} | R$ {money:8d} | {level:2d} | {", ".join(bought)}  (~{day * DAY_MINUTES_REAL / 60:.1f} h)')
        if 'grand_hotel' in bought:
            hotel = day
    if hotel:
        # Act 5 gates the party: fame 10 and 3,400 kiosk sales (money for the game room, recipes and customization
        # piles up long before).
        end = max(hotel, sales_day or days, fame10 or days) + 1
        minutes = end * DAY_MINUTES_REAL + max(0, end - 1) * OFFERING_MIN_PER_DAY * 0 + STORY_MINUTES
        print(f'campanha: hotel no dia {hotel}, festa no dia {end}; ~{minutes / 60:.1f} h de jogo '
              f'(a oferenda diária cabe dentro dos 16 min do dia; capítulos/minijogos/festa ~{STORY_MINUTES} min)')

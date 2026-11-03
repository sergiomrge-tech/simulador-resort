"""PIE: physical kiosk cycle with the hired attendant. Logs every customer's stage changes, dirty tables and
money for ~6 real minutes, then saves, reloads (StopPIE/StartPIE) and checks orders/tables are not duplicated."""
import sys, time, json, collections
sys.argv = ['x']
exec(open('party_pie.py').read().split('def shot')[0])


def probe(phase='inspect'):
    return ret(call('mare_mcp.MareMigrationTools', 'gameplay_probe', {'phase': phase, 'dish': ''}))


if 'true' not in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower():
    call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
    time.sleep(45)
beach('clock', '540')
hud('cmd', 'mare.Weather 1')
probe('open_kiosk')
probe('hire')
hud('cmd', 'mare.Restock 30')
probe('position_kiosk')
history = collections.defaultdict(list)
dirty_seen, cash0 = set(), None
start = time.time()
while time.time() - start < 360:
    st = probe()
    if not isinstance(st, dict):
        time.sleep(3)
        continue
    cash0 = cash0 if cash0 is not None else st['cash']
    for p in st['people']:
        if p['employee'] or (p['counter'] < 0 and p['table'] < 0 and not p['order']):
            continue
        stage = p['stage'].split('.')[-1].split(':')[0]
        if not history[p['id']] or history[p['id']][-1] != stage:
            history[p['id']].append(stage)
    for d in st['used_dishes']:
        dirty_seen.add(tuple(d['table']))
    time.sleep(3)
st = probe()
print('customers', len(history))
flows = collections.Counter(' > '.join(v) for v in history.values())
for f, n in flows.most_common(10):
    print(f'{n:3d}  {f}')
print('dirty tables seen', len(dirty_seen), 'now dirty', len(st['used_dishes']), 'cash', cash0, '->', st['cash'])
before = {'orders': [p['order'] for p in st['people'] if p['order']], 'dishes': len(st['used_dishes']), 'cash': st['cash']}
probe('save')
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
time.sleep(8)
call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
time.sleep(45)
st = probe()
after = {'orders': [p['order'] for p in st['people'] if p['order']], 'dishes': len(st['used_dishes']), 'cash': st['cash']}
print('before reload', before)
print('after reload ', after)
dup = [o for o, n in collections.Counter(after['orders']).items() if n > 1]
print('duplicated orders after reload', dup)
json.dump({'flows': flows, 'before': before, 'after': after}, open('D:/CodexTemp/beach/kiosk_cycle.json', 'w'), indent=1, default=list)

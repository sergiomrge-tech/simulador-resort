"""Acceptance in the world (PENDENCIAS "100 ciclos sem travar NPC/fila"): the physical kiosk with the hired attendant
serves real NPC customers until 100 have been served, in PIE.

    python tools/ue58/qa/acceptance_world.py          (editor open with the MCP server, fresh -MareSaveRoot profile)

Every 3 s it reads every customer's stage (gameplay_probe inspect). A customer is served when it had an order and then
left the kiosk (stage history ends away from the counter and tables). Failures:
  - stuck: a customer in the same stage for more than STUCK seconds, except eating at a table (that lasts by design);
  - a queue that never moves: no customer changes stage for QUEUE seconds while some are waiting;
  - after each save/reload (every 25 served): an order present twice, or cash going down.
Every 4 real minutes the attendant's boss sleeps: a new day at 9:00 (each day has its own customer budget). Report in
D:/CodexTemp/qa/acceptance_world.json; exit 1 on any failure.
"""
import collections
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from mcp_client import UnrealClient  # noqa: E402

c = UnrealClient()
TARGET, STUCK, QUEUE, LIMIT = 100, 240, 180, 60 * 60
OUT = Path('D:/CodexTemp/qa/acceptance_world.json')


def call(ts, tool, args):
    r = c.rpc('tools/call', {'name': 'call_tool', 'arguments': {'toolset_name': ts, 'tool_name': tool, 'arguments': args}})
    return '\n'.join(e.get('text', '') for e in r.get('content', []))


def ret(text):
    try:
        v = json.loads(text)['returnValue']
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return text


def probe(phase='inspect'):
    return ret(call('mare_mcp.MareMigrationTools', 'gameplay_probe', {'phase': phase, 'dish': ''}))


def coast(action, arg):
    return call('mare_mcp.MareMigrationTools', 'caribbean_coast', {'action': action, 'arg': arg})


def hud(action, arg=''):
    return ret(call('mare_mcp.MareMigrationTools', 'hotel_lobby', {'action': 'hud_' + action, 'arg': arg}))


def pie(on):
    running = 'true' in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower()
    if on and not running:
        call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
        time.sleep(45)
    elif not on and running:
        call('EditorToolset.EditorAppToolset', 'StopPIE', {})
        time.sleep(8)


def new_day():
    # A day has a customer budget (the HUD's "N hoje"): going back to 9:00 the same day brings nobody, so sleep.
    probe('sleep')
    time.sleep(3)
    coast('clock', '540')


def setup():
    new_day()
    hud('cmd', 'mare.Weather 1')
    probe('open_kiosk')
    probe('hire')
    hud('cmd', 'mare.Restock 60')
    probe('position_kiosk')


def at_kiosk(p):
    return p['counter'] >= 0 or p['table'] >= 0 or bool(p['order'])


def main():
    pie(True)
    setup()
    history, changed, ordered, served = collections.defaultdict(list), {}, set(), set()
    stuck, frozen_queue, reloads = {}, [], []
    start = last_move = day_start = time.time()
    next_reload = 25
    prev = None
    while len(served) < TARGET and time.time() - start < LIMIT:
        st = probe()
        if not isinstance(st, dict):
            time.sleep(3)
            continue
        now = time.time()
        present = {}
        for p in st['people']:
            if p['employee']:
                continue
            present[p['id']] = p
            stage = p['stage'].split('.')[-1].split(':')[0]
            if p['order']:
                ordered.add(p['id'])
            if not history[p['id']] or history[p['id']][-1] != stage:
                history[p['id']].append(stage)
                changed[p['id']] = now
                last_move = now
            elif at_kiosk(p) and 'EATING' not in stage and now - changed[p['id']] > STUCK:
                stuck[p['id']] = {'stage': stage, 'seconds': round(now - changed[p['id']]), 'counter': p['counter'], 'table': p['table']}
        # Served: had an order and is now away from the counter and tables (or gone from the world).
        for pid in list(ordered - served):
            p = present.get(pid)
            if p is None or not at_kiosk(p):
                served.add(pid)
        waiting = [p for p in present.values() if at_kiosk(p) and 'EATING' not in p['stage']]
        if waiting and now - last_move > QUEUE:
            frozen_queue.append({'at': round(now - start), 'waiting': len(waiting)})
            last_move = now
        if len(served) >= next_reload:
            before = {'orders': sorted(p['order'] for p in st['people'] if p['order']), 'cash': st['cash']}
            probe('save')
            pie(False)
            pie(True)
            after_st = probe()
            after = {'orders': sorted(p['order'] for p in after_st['people'] if p['order']), 'cash': after_st['cash']}
            dup = [o for o, n in collections.Counter(after['orders']).items() if n > 1]
            reloads.append({'served': len(served), 'before': before, 'after': after, 'duplicated': dup,
                            'cash_lost': after['cash'] < before['cash'] - .01})
            print('reload at', len(served), 'served; duplicated', dup, 'cash', before['cash'], '->', after['cash'], flush=True)
            setup()
            day_start = time.time()
            next_reload += 25
            history.clear()
            changed.clear()
            last_move = time.time()
        if prev is None or len(served) // 10 != prev // 10:
            print(f'{round(time.time() - start)} s: {len(served)} served, {len(stuck)} stuck', flush=True)
            prev = len(served)
        # The kiosk closes at 18h: a new day every 4 real minutes (~1.6 game minutes per second: 9:00 -> 15:30).
        if time.time() - day_start > 240:
            new_day()
            probe('open_kiosk')
            day_start = time.time()
        time.sleep(3)
    report = {'served': len(served), 'seconds': round(time.time() - start), 'stuck': stuck, 'frozen_queue': frozen_queue,
              'reloads': reloads, 'flows': collections.Counter(' > '.join(v) for v in history.values()).most_common(12)}
    report['pass'] = (len(served) >= TARGET and not stuck and not frozen_queue
                      and not any(r['duplicated'] or r['cash_lost'] for r in reloads))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print('ACCEPTANCE', 'PASS' if report['pass'] else 'FAIL', json.dumps({k: report[k] for k in ('served', 'seconds', 'stuck', 'frozen_queue')}))
    pie(False)
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())

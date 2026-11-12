"""Full-game simulation in PIE on a fresh profile (editor launched with -MareSaveRoot=<new folder> -MareSkipMenu).

From the boat arrival to the Grand Hotel (in the demo: to the end screen, hotel locked) and the game room: every stage runs the real game (purchases, chapters
and businesses through the simulation, the world reacting), then records with data: new log errors, gliding
people, people inside furniture, badly seated people, kiosk flow, and a photo of the area. Output:
D:/CodexTemp/qa/sim/<stamp>/report.json and sheet_*.jpg, to be reviewed into docs/ue58/CHECKLIST_SIMULACAO.md.
Usage: MARE_SIM_ROOT=<the -MareSaveRoot folder> python tools/ue58/qa/simulate_game.py
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from mcp_client import UnrealClient  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # game messages carry ★ and accents
c = UnrealClient()
START = os.environ.get('SIM_FROM', '')   # resume from a stage group (e.g. 40) in the same PIE session
# 10/11 (Sergio: "acelerar o tempo da simulação"): the long game-time waits (the kiosk's first day, the night's sleep)
# run with the world SIM_SPEED times faster (slomo); the same game time in 1/SIM_SPEED of the real time. Audits and
# photos run at normal speed (gait compares two samples 0.6 s apart).
SPEED = max(1.0, float(os.environ.get('SIM_SPEED', '4')))


def fast(seconds):
    hud('cmd', f'slomo {SPEED}')
    time.sleep(seconds / SPEED)
    hud('cmd', 'slomo 1')
LOG = Path(r'D:\Projetos\MareAltaUE58\unreal\MareAlta\Saved\Logs\MareAlta.log')
SHOTS = Path(r'D:\CodexTemp\beach')
OUT = Path(r'D:\CodexTemp\qa\sim') / time.strftime('%Y%m%d-%H%M%S')
OUT.mkdir(parents=True, exist_ok=True)
BAD = re.compile(r'(Error:|: Error |Ensure condition failed|missing usage flag|Default Material will be used|REAL_MISSING|Fatal|gave up reaching)')


def call(ts, tool, args):
    r = c.rpc('tools/call', {'name': 'call_tool', 'arguments': {'toolset_name': ts, 'tool_name': tool, 'arguments': args}})
    return '\n'.join(e.get('text', '') for e in r.get('content', []))


def ret(text):
    try:
        v = json.loads(text)['returnValue']
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return text


def hud(action, arg=''):
    return ret(call('mare_mcp.MareMigrationTools', 'hotel_lobby', {'action': 'hud_' + action, 'arg': arg}))


def coast(action, arg):
    return call('mare_mcp.MareMigrationTools', 'caribbean_coast', {'action': action, 'arg': arg})


def probe(phase='inspect'):
    return ret(call('mare_mcp.MareMigrationTools', 'gameplay_probe', {'phase': phase, 'dish': ''}))


def cmd(text):
    hud('cmd', text)


def shot(name, spec):
    path = SHOTS / f'pie-sim_{name}.png'
    if path.exists():
        path.unlink()
    coast('pie', f'sim_{name},{spec}')
    time.sleep(6)   # exposure settles after the camera jump
    coast('pie', f'sim_{name}!,0,0,0,0,0')
    for _ in range(30):
        if path.exists():
            time.sleep(1)
            target = OUT / f'{name}.png'
            target.write_bytes(path.read_bytes())
            return str(target)
        time.sleep(1)
    return None


def gait():
    # 09/11: people nobody sees hold their pose on purpose (mare.OffscreenPose); sampling them like that reported
    # residents walking off screen as "gliding" (B4). Animate everyone while sampling, as the QA gate does.
    for c_ in ('mare.OffscreenPose 0', 'mare.PeopleHideOffscreen 0', 'mare.PeopleDrawDistance 0'):
        cmd(c_)
    time.sleep(1)
    a = hud('gait')
    time.sleep(.6)
    b = hud('gait')
    for c_ in ('mare.OffscreenPose 1', 'mare.PeopleHideOffscreen 1', 'mare.PeopleDrawDistance -1'):
        cmd(c_)
    pa = {x[0]: x for x in a}
    moving, gliding = 0, []
    for x in b:
        o = pa.get(x[0])
        if not o or x[5]:
            continue
        if ((x[2][0] - o[2][0]) ** 2 + (x[2][1] - o[2][1]) ** 2) ** .5 < 25:
            continue
        moving += 1
        if max(abs(u - v) for u, v in zip(x[3], o[3])) < 1.5:
            gliding.append([x[1], x[4], x[2]])
    return {'moving': moving, 'gliding': gliding}


report = {'stages': []}


def stage(name, actions, camera=None, wait=6, audits=True):
    offset = LOG.stat().st_size
    for a in actions:
        a() if callable(a) else cmd(a)
        time.sleep(1.5)
    time.sleep(wait)
    row = {'stage': name}
    if camera:
        row['shot'] = shot(name, camera)
    if audits:
        row['gait'] = gait()
        row['stand'] = hud('standaudit')
        seats = hud('seataudit')
        row['seat_fails'] = seats.get('fails') if isinstance(seats, dict) else seats
        cmd('mare.QA seats wake')
        time.sleep(3)
        cmd('mare.QA seats all')   # 10/11: pelvis against the seat point, benches and unseen people included
        time.sleep(1)
    text = LOG.read_bytes()[offset:].decode('utf-8', 'ignore')
    row['log_bad'] = sorted({re.sub(r'^\[[^\]]*\]\[[^\]]*\]', '', l.strip())[-200:] for l in text.splitlines() if BAD.search(l)})[:20]
    row['qa'] = [l.strip()[-160:] for l in text.splitlines() if 'mare.QA' in l or 'comic event' in l][-12:]
    row['seats'] = ([l.split('MARE_SEATS ')[-1].strip() for l in text.splitlines() if 'MARE_SEATS' in l] or [None])[-1]
    row['rests'] = ([l.split('MARE_RESTS ')[-1].strip() for l in text.splitlines() if 'MARE_RESTS' in l] or [None])[-1]
    row['talkers'] = ([l.split('MARE_TALKERS ')[-1].strip() for l in text.splitlines() if 'MARE_TALKERS' in l] or [None])[-1]
    st = probe()
    if isinstance(st, dict):
        row['cash'] = st.get('cash')
        row['open'] = st.get('open')
    report['stages'].append(row)
    (OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print(name, '| log', len(row['log_bad']), '| glide', len(row.get('gait', {}).get('gliding', [])), '| stand', len(row.get('stand') or []),
          '| seat', len(row.get('seat_fails') or []), '|', row['qa'][-2:] if row['qa'] else '')


if 'true' not in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower():
    call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
    time.sleep(40)
    cmd('mare.ShowUI play')   # the PIE opens the main menu (paused): continue like the QA gate
    time.sleep(5)

if not START or START < '40':
    # 1. Arrival by bus, grandma's letter, the company and the first day.
    stage('01_chegada', [], None, wait=8, audits=False)
    report['stages'][-1]['shot_ui'] = coast('pie', 'sim_chegada^,0,0,0,0,0')   # the player's own view of the bus arrival
    stage('02_carta', ['mare.ShowUI close', 'mare.ShowUI letter'], None, wait=3, audits=False)
    report['stages'][-1]['shot_ui'] = coast('pie', 'sim_carta^,0,0,0,0,0')
    # 10/11: with the starting R$ 150 the restock left nothing for the attendant (hire refused) and nobody served on day 1:
    # the service flow was never exercised. Cash for the hire here; the balance run is a separate task.
    stage('03_empresa', ['mare.ShowUI close', lambda: probe('open_kiosk'), 'mare.Restock 30', 'mare.QA money 1500', lambda: probe('hire')],
          '3750,-2600,200,-6,90', wait=10)
    stage('04_quiosque_dia1', [lambda: fast(150)], '3700,-1080,100,-12,-75', wait=2)
    kiosk = probe()
    report['kiosk_people'] = [[p['name'], p['stage'].split('.')[-1].split(':')[0], p['delivered']] for p in kiosk.get('people', []) if not p['employee'] and (p['counter'] >= 0 or p['table'] >= 0 or p['order'])] if isinstance(kiosk, dict) else kiosk
    stage('05_dormir', [lambda: probe('sleep'), lambda: fast(25)], '4600,2400,180,-5,-90', wait=4)
    # 2. Expansions in the game's order, each one photographed where it appears.
    cmd('mare.QA money 60000')
    areas = {
        'kiosk_tables': '3750,-2600,200,-6,90', 'drinks': '3700,-1080,100,-12,-75', 'neon': '3750,-2600,200,-6,90',
        'grill': '3700,-1080,100,-12,-75', 'bar': '450,-2150,110,-4,45', 'pousada': '-1080,330,550,-28,90',
        'pool': '-500,-300,300,-15,45', 'passeios': '6780,-2680,250,-12,-50',
    }
    for exp, cam in areas.items():
        # 07/11: the last demo purchase opens the end-of-demo screen, which pauses the game (every later photo froze).
        stage('10_' + exp, [f'mare.QA buy {exp}', 'mare.ShowUI close'], cam, wait=6, audits=exp in ('bar', 'pousada', 'pool'))
    # 3. The chapters (and the businesses the carnival asks for).
    for chapter in ('pier', 'prainha', 'sabores', 'carnaval'):
        # 10/11: the last chapter completes the demo (every expansion bought, every chapter done): the end screen opens
        # here. Photographed before the close (the close of this stage hid it and the later photo showed the plain HUD).
        last = chapter == 'carnaval'
        stage('20_' + chapter, [f'mare.QA step {chapter}'] * 3 + ([] if last else ['mare.ShowUI close']), None, wait=4 if last else 2, audits=False)
        if last:
            report['end_screen'] = coast('pie', 'sim_fim_demo^,0,0,0,0,0')
            time.sleep(3)
            cmd('mare.ShowUI close')
    for biz, cam in (('sorveteria', '4365,-2190,250,-12,45'), ('aluguel', '6310,-2300,250,-12,45'), ('food_truck', '2630,2600,100,4,90'),
                     ('souvenir', '7860,3630,300,-12,225'), ('surfe', '-4990,-2380,250,-12,45')):
        stage('30_' + biz, [], cam, wait=3, audits=False)
DEFS = json.loads(Path('D:/Projetos/MareAltaUE58/unreal/MareAlta/Content/Data/definitions.json').read_text(encoding='utf-8'))
DEMO = bool(DEFS.get('demo'))
report['demo'] = DEMO
cmd('mare.QA money 60000')
if DEMO:
    # 4. Demo (10/11): everything bought and every chapter done = the end screen "Obrigado por jogar a demo!" (it pauses
    # the game); the Grand Hotel and the game room stay locked even with money and fame.
    stage('39_fim_demo', ['mare.ShowUI close'], None, wait=2, audits=False)
    # "mare.QA buy" buys full-game expansions on purpose (QA of the full game); the player's purchase refusing the hotel
    # is the automation test "Hotel not for sale". Here: with fame and money the hotel lot stays as it is.
    stage('40_hotel_bloqueado', ['mare.QA fame 9', 'mare.ShowUI close'],
          '-1800,5000,250,-10,90', wait=6, audits=False)
    cmd('mare.QA dump qa-demo-lock')
    time.sleep(2)
else:
    # 4. Grand Hotel and the game room.
    stage('40_grand_hotel', ['mare.QA fame 9', 'mare.QA buy grand_hotel', 'mare.ShowUI close'], '-1800,5000,250,-10,90', wait=10)
    stage('41_restaurante', [], '-1420,3780,250,-12,45', wait=3, audits=False)
    stage('42_salao_jogos', ['mare.QA buy salao_jogos'], '-1800,5600,250,-12,90', wait=8)
# 5. Night, then save and reload.
# Lumen and the eye need ~25 s after the clock jumps to night (the 8 s wait photographed a white 'day' at 21h30).
stage('50_noite_quiosque', [lambda: coast('clock', '1290'), lambda: time.sleep(30)], '3750,-2600,200,-6,90', wait=8)
if DEMO:
    stage('51_noite_pousada', [], '-1080,330,550,-28,90', wait=3)
else:
    stage('51_noite_hotel', [], '-1800,5000,250,-10,90', wait=3)
stage('52_noite_vila', [], '4300,2900,100,-4,180', wait=3)
before = probe()
probe('save')
cmd('mare.QA dump qa-before-reload')
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
time.sleep(8)
call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
time.sleep(45)
cmd('mare.ShowUI play')
time.sleep(8)
after = probe()
cmd('mare.QA dump qa-after-reload')
time.sleep(2)
root = Path(os.environ.get('MARE_SIM_ROOT', ''))
if root.is_dir():
    def dump(n):   # UE writes UTF-16 with a BOM
        raw = (root / n).read_bytes()
        return json.loads(raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8-sig'))
    b, a2 = dump('qa-before-reload.json'), dump('qa-after-reload.json')
    # Businesses the game room registers on load arrive as empty entries: not owned, so not a difference.
    # Businesses keep serving between the two dumps (the clerk's queue and report move on): compare the rest.
    clean = lambda d: {**d, 'biz': {k: {kk: vv for kk, vv in v.items() if kk not in ('queue', 'report', 'next_customer')} for k, v in d.get('biz', {}).items() if v}}
    def diffs(x, y, path=''):
        if isinstance(x, dict) and isinstance(y, dict):
            return [d for k in sorted(set(x) | set(y)) for d in diffs(x.get(k), y.get(k), path + '.' + k)]
        return [] if x == y else [f'{path}: {str(x)[:80]} -> {str(y)[:80]}']
    report['reload'] = {'same': clean(b) == clean(a2), 'diffs': diffs(clean(b), clean(a2))[:40], 'before': b, 'after': a2}
    print('reload keeps the save:', clean(b) == clean(a2), report['reload']['diffs'][:8])
    if DEMO and (root / 'qa-demo-lock.json').exists():
        lock = dump('qa-demo-lock.json').get('unlocked', {})
        report['demo_lock'] = {k: bool(lock.get(k)) for k in ('grand_hotel', 'salao_jogos')}
        print('demo keeps the hotel locked:', report['demo_lock'])
if DEMO:
    stage('60_recarregado_pousada', [], '-1080,330,550,-28,90', wait=4)
else:
    stage('60_recarregado_hotel', [], '-1800,5000,250,-10,90', wait=4)
(OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')

# Contact sheets for review.
from PIL import Image, ImageDraw  # noqa: E402
rows = [(s['stage'], s['shot']) for s in report['stages'] if s.get('shot')]
for k in range(0, len(rows), 8):
    part = rows[k:k + 8]
    sheet = Image.new('RGB', (1280, 360 * ((len(part) + 1) // 2)))
    for i, (label, path) in enumerate(part):
        t = Image.open(path).convert('RGB').resize((640, 360))
        ImageDraw.Draw(t).text((10, 10), label, fill='yellow')
        sheet.paste(t, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(OUT / f'sheet_{k // 8 + 1}.jpg', quality=86)
print('report', OUT)

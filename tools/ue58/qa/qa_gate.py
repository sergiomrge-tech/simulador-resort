"""Quality gate run before every commit (Maré Alta, UE 5.8, editor open with the MCP server on 8000).

What it checks, with data (PASS only if all hard checks pass):
  0. JSON data         - data_lint.py checks the data before connecting to the editor; any error exits with code 1;
  1. automation tests  - every MareAlta.* test succeeds;
  2. floating props    - float_audit scan: no more floating instances than the accepted baseline;
     lights            - no room light shines at night without a lamp/fixture (mare_light_audit.bare_check);
     decor             - game room decoration defects stay fixed (mare_game_room.check);
     cameras           - minigame cameras turn off the 16:9 letterbox (HUD projections land on the balls);
     driver            - the bus driver of the intro is seated and dressed, not in swimwear (mare_intro_audit.driver);
  3. natural movement  - PIE gait audit by day and by night: nobody moving while feet/hands stay put; also on every
                         visible skeletal mesh (MetaHuman bodies): no glider, nobody frozen without idle motion;
  4. clean log         - no Error / Ensure / missing usage flag / default material lines during the PIE run
                         (patterns in baseline.json "log_allow" are known and accepted);
  5. untracked assets  - no new .uasset/.umap outside git (a material the level used was left out once, 03/11);
                         folders in baseline.json "untracked_allow" are the user's own pending files;
  6. reference shots   - fixed cameras captured and compared with the previous run: big differences are listed
                         for review (not a failure: people and clouds move), with a contact sheet.

Usage: python tools/ue58/qa/qa_gate.py [--no-shots] [--accept]
  --accept stores this run's counts as the new baseline (only after reviewing a real, intended change).
Report: D:/CodexTemp/qa/report.json and D:/CodexTemp/qa/shots/<stamp>/sheet.jpg
"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from mcp_client import UnrealClient  # noqa: E402

c = None  # Conectar somente depois da verificação estática dos JSON.
LOG = Path(r'D:\Projetos\MareAltaUE58\unreal\MareAlta\Saved\Logs\MareAlta.log')
OUT = Path(r'D:\CodexTemp\qa')
SHOTS = Path(r'D:\CodexTemp\beach')
BASELINE = HERE / 'baseline.json'
CAMERAS = [   # name, "x,y,z,pitch,yaw" (pawn position; noon, clear weather)
    ('praia', '3000,-3600,260,-8,90'),
    ('quiosque_dentro', '3700,-1080,100,-12,-75'),
    ('quiosque_fora', '3750,-2600,200,-6,90'),
    ('guarda_sois', '4700,-3150,240,-10,90'),
    ('vila_rua', '4300,2900,100,-4,180'),
    ('vila_praca', '2000,3300,260,-10,-20'),
]


def call(ts, tool, args, timeout=None):
    if timeout:
        os.environ['MARE_MCP_TIMEOUT'] = str(timeout)
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


DRIVER = {}


def pie(on):
    running = 'true' in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower()
    if on and not running:
        call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
        time.sleep(45)
        # A new PIE opens the main menu, which pauses the game (no village, no walkers): continue past it.
        hud('cmd', 'mare.ShowUI play')
        # 06/11 (CHECKLIST 0 A4): the fresh profile starts with the bus arrival; the driver must be a dressed villager
        # (with no role he took the beach roster and drove in a bikini). Checked while the bus is still on screen.
        time.sleep(3)
        got = ret(hud('module', 'mare_intro_audit.driver|'))
        DRIVER.update(json.loads(got) if isinstance(got, str) else got)
        time.sleep(12)
    if not on and running:
        call('EditorToolset.EditorAppToolset', 'StopPIE', {})
        time.sleep(6)


def tests():
    T = 'AutomationTestToolset.AutomationTestToolset'
    call(T, 'DiscoverTests', {}, 300)
    raw = call(T, 'RunTestsByFilter', {'filterExpression': 'MareAlta'}, 1500)
    rows = ret(raw)['tests']
    failed = [{'name': r['name'], 'errors': r['errors'][:4]} for r in rows if r['state'] != 'Success']
    return {'total': len(rows), 'failed': failed, 'pass': not failed and len(rows) > 0}


def floating(base):
    r = ret(call('mare_mcp.MareMigrationTools', 'float_audit', {'action': 'scan', 'arg': ''}, 900))
    n = r.get('floating', -1) if isinstance(r, dict) else -1
    return {'floating': n, 'baseline': base.get('floating'), 'worst': (r.get('worst') or [])[:5] if isinstance(r, dict) else r,
            'pass': n >= 0 and (base.get('floating') is None or n <= base['floating'])}


def gait(rounds=2):
    moving, gliding = {}, {}
    for _ in range(rounds):
        a = hud('gait')
        time.sleep(.6)
        b = hud('gait')
        pa = {x[0]: x for x in a}
        for x in b:
            o = pa.get(x[0])
            if not o or x[5]:
                continue
            moved = ((x[2][0] - o[2][0]) ** 2 + (x[2][1] - o[2][1]) ** 2) ** .5
            if moved < 25:
                continue
            limbs = max(abs(u - v) for u, v in zip(x[3], o[3]))
            moving[x[0]] = x[1]
            if limbs < 1.5:
                gliding[x[0]] = [x[1], x[4] or 'quaternius', x[2], round(moved)]
        time.sleep(2)
    return {'moving': len(moving), 'gliding': gliding}


def _limbs(a, b):
    """Largest change of any tracked bone coordinate (cm) between two allpeople rows of the same person."""
    return max((max(abs(u - v) for u, v in zip(r[1], s[1])) for r, s in zip(a[5], b[5]) if len(r[1]) == len(s[1])), default=0)


def visible(rounds=2):
    """The mesh the player sees (MetaHuman body follows the hidden rig by leader pose): three samples 0.35 s apart
    (1.2 s apart aliased with the walk cycle and showed false gliders). Gliding = moved, limbs still; frozen =
    standing with no idle motion at all."""
    glide, frozen, total = [], [], 0
    first = {}
    for k in range(rounds):
        samples = []
        for _ in range(3):
            got = hud('allpeople')
            samples.append({x[0]: x for x in got} if isinstance(got, list) else {})
            time.sleep(0.35)
        total = max(total, len(samples[-1]))
        for key, x in samples[0].items():
            first.setdefault(key, x)
        for key, x in samples[-1].items():
            seq = [s.get(key) for s in samples]
            if not all(seq):
                continue
            moved = ((x[3][0] - seq[0][3][0]) ** 2 + (x[3][1] - seq[0][3][1]) ** 2) ** .5
            limb = max(_limbs(seq[i], seq[j]) for i in range(3) for j in range(i + 1, 3))
            # 04/11: a person nobody sees holds the pose on purpose (mare.OffscreenPose): judge the walk only on
            # bodies drawn in the first sample (the gait audit, with the pose forced on, still covers everyone).
            drawn = any(len(r) > 2 and r[2] for r in seq[0][5])
            if moved > 15 and limb < 1.5 and drawn:
                glide.append([x[2], x[3]])
            # Frozen is judged over the whole check (both rounds, ~3 s), not 0.7 s: the calm Sitting_Idle only breathes
            # (head ~0.06 cm/s, 03/11), which a 0.7 s window took for a frozen pose. Off-screen MetaHuman bodies skip
            # their pose update on purpose (OnlyTickPoseWhenRendered): only a body the camera is drawing counts.
            if k == rounds - 1 and key in first:
                seen = any(len(r) > 2 and r[2] for r in x[5])
                drift = ((x[3][0] - first[key][3][0]) ** 2 + (x[3][1] - first[key][3][1]) ** 2) ** .5
                if drift < 2 and _limbs(first[key], x) < 0.05 and seen:
                    frozen.append([x[2], x[3]])
        if k < rounds - 1:
            time.sleep(1.5)
    return {'actors': total, 'gliding': glide, 'frozen': frozen, 'pass': not glide and not frozen and total > 0}


def log_since(offset, allow):
    whole = LOG.read_bytes().decode('utf-8', 'ignore')
    text = whole[len(whole.encode('utf-8', 'ignore')[:offset].decode('utf-8', 'ignore')):]
    # 04/11, seen only in the packaged game: a text-path load of a missing asset, VSM light overflow.
    bad = re.compile(r'(Error:|: Error |Ensure condition failed|missing usage flag|Default Material will be used|REAL_MISSING|Fatal'
                     r'|Failed to find object|max lights overflow)')
    lines = [l.strip()[-220:] for l in text.splitlines() if bad.search(l) and not any(a in l for a in allow)]
    # Logged when the mesh loads (editor start, before PIE): translucent glass on a Nanite mesh is not drawn.
    lines += [l.strip()[-220:] for l in whole.splitlines() if 'used on Nanite static mesh' in l and not any(a in l for a in allow)]
    seen, unique = set(), []
    for l in lines:
        key = re.sub(r'^\[[^\]]*\]\[[^\]]*\]', '', l)
        if key not in seen:
            seen.add(key)
            unique.append(l)
    return {'count': len(lines), 'unique': unique[:30], 'pass': not lines}


def shots(stamp):
    from PIL import Image, ImageChops, ImageDraw, ImageStat
    folder = OUT / 'shots' / stamp
    folder.mkdir(parents=True, exist_ok=True)
    last = OUT / 'shots' / 'last'
    tiles, review = [], []
    for name, spec in CAMERAS:
        src = SHOTS / f'pie-qa_{name}.png'
        if src.exists():
            src.unlink()
        coast('pie', f'qa_{name},{spec}')
        time.sleep(3)
        coast('pie', f'qa_{name}!,0,0,0,0,0')
        for _ in range(30):
            if src.exists():
                time.sleep(1)
                break
            time.sleep(1)
        if not src.exists():
            review.append({'shot': name, 'problem': 'no capture'})
            continue
        shutil.copy(src, folder / f'{name}.png')
        img = Image.open(folder / f'{name}.png').convert('RGB').resize((640, 360))
        prev = last / f'{name}.png'
        if prev.exists():
            diff = ImageStat.Stat(ImageChops.difference(img, Image.open(prev).convert('RGB').resize((640, 360)))).mean
            d = round(sum(diff) / 3, 1)
            if d > 12:
                review.append({'shot': name, 'mean_diff': d})
            ImageDraw.Draw(img).text((8, 8), f'{name}  diff {d}', fill='yellow')
        else:
            ImageDraw.Draw(img).text((8, 8), f'{name}  (primeira referencia)', fill='yellow')
        tiles.append(img)
    if not tiles:   # no capture at all (listed in review): nothing to lay out
        return {'folder': str(folder), 'review': review}
    sheet = Image.new('RGB', (1280, 360 * ((len(tiles) + 1) // 2)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(folder / 'sheet.jpg', quality=88)
    if last.exists():
        shutil.rmtree(last)
    shutil.copytree(folder, last)
    return {'folder': str(folder), 'review': review}


def untracked(base):
    import subprocess
    out = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'unreal/MareAlta/Content'],
                         cwd=str(HERE.parents[2]), capture_output=True, text=True, encoding='utf-8').stdout
    allow = base.get('untracked_allow', [])
    files = [l[3:].strip('"') for l in out.splitlines() if l.startswith('??') and l.rstrip('"').endswith(('.uasset', '.umap'))]
    files = [f for f in files if not any(f.startswith(a) for a in allow)]
    return {'files': files, 'pass': not files}


def cooking():
    """Everything the game loads by a text path is in the cooked build (cook_audit.py; 03/11 the MetaHumans were not)."""
    import cook_audit
    paths, patterns = cook_audit.collect()
    cook_audit.OUT.parent.mkdir(parents=True, exist_ok=True)
    cook_audit.OUT.write_text(json.dumps({'paths': paths, 'patterns': patterns}), encoding='utf-8')
    res = hud('cookaudit', str(cook_audit.OUT))
    res = json.loads(res) if isinstance(res, str) else res
    return {'missing': res['missing'], 'absent': res['absent'], 'cooked': res['cooked'],
            'pass': not res['missing'] and not res['absent']}


def lights():
    """No room light shines at night without a fixture (06/11: the Grand Hotel lobby had 6 bare 2500 cd lights, only 2 under
    a lamp; the bungalow ceilings had a light and no lamp). mare_light_audit.bare_check on the editor level."""
    res = ret(hud('module', 'mare_light_audit.bare_check|'))
    res = json.loads(res) if isinstance(res, str) else res
    return {'bare': res['bare'], 'pass': res['pass']}


def decor():
    """Game room decoration defects seen in photos stay fixed (06/11: lobby chair rail across the accent wall, potless plant
    leaves on the floor, opaque picture glass). mare_game_room.check on the editor level."""
    res = ret(hud('module', 'mare_game_room.check|'))
    res = json.loads(res) if isinstance(res, str) else res
    return res if isinstance(res, dict) else {'error': str(res), 'pass': False}


def cameras():
    """Minigame cameras never letterbox (06/11: the pool camera kept the CameraActor 16:9 constraint; black bars and the
    HUD aim line / called-pocket ring 20-40 px off the balls). Every SpawnActor<ACameraActor> outside the intro must turn
    SetConstraintAspectRatio(false) within the next lines."""
    src = Path(__file__).resolve().parents[3] / 'unreal' / 'MareAlta' / 'Source' / 'MareAlta'
    bad = []
    for f in sorted(src.glob('*.cpp')):
        if f.name == 'MareIntro.cpp':
            continue
        lines = f.read_text(encoding='utf-8-sig', errors='replace').splitlines()
        for i, line in enumerate(lines):
            if 'SpawnActor<ACameraActor>' in line and not any('SetConstraintAspectRatio(false)' in l for l in lines[i:i + 6]):
                bad.append(f'{f.name}:{i + 1}')
    return {'letterboxed': bad, 'pass': not bad}


def ui_shot():
    """A screenshot with the UI is written even with the editor minimized (06/11: 'shot showui' wrote nothing then;
    mare.Shot restores the window first). Minimizes the editor, asks for one and waits for the file."""
    import ctypes
    import subprocess
    out = OUT / 'ui_shot.png'
    if out.exists():
        out.unlink()
    pid = subprocess.run(['powershell', '-NoProfile', '-Command',
                          '(Get-Process UnrealEditor | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1).MainWindowHandle'],
                         capture_output=True, text=True).stdout.strip()
    hwnd = int(pid) if pid.isdigit() else 0
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 6)   # SW_MINIMIZE
        time.sleep(2)
    hud('cmd', 'mare.Shot ' + str(out).replace('\\', '/'))
    for _ in range(15):
        if out.exists():
            break
        time.sleep(1)
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 9)   # SW_RESTORE
    return {'file': str(out), 'minimized': bool(hwnd), 'pass': out.exists()}


def data_lint():
    """Etapa local de leitura dos JSON; não importa nem chama APIs da Unreal."""
    import subprocess
    try:
        run = subprocess.run([sys.executable, str(HERE / 'data_lint.py'), '--json'],
                             cwd=str(HERE.parents[2]), capture_output=True, text=True, encoding='utf-8')
        result = json.loads(run.stdout)
        if not isinstance(result, dict) or not isinstance(result.get('problemas'), list) or 'erros' not in result:
            raise ValueError('resposta incompleta do data_lint.py')
        return dict(result, **{'returncode': run.returncode, 'pass': run.returncode == 0 and result['erros'] == 0})
    except (OSError, ValueError) as exc:
        return {'pass': False, 'erros': 1, 'problemas': [], 'error': str(exc)}


def main():
    global c
    accept, with_shots = '--accept' in sys.argv, '--no-shots' not in sys.argv
    base = json.loads(BASELINE.read_text(encoding='utf-8')) if BASELINE.exists() else {}
    stamp = time.strftime('%Y%m%d-%H%M%S')
    report = {'stamp': stamp, 'data': data_lint()}
    if not report['data']['pass']:
        report['pass'] = False
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
        print('QA GATE FAIL')
        print(' data   ', report['data']['erros'], 'erro(s)', report['data'].get('error', ''))
        for row in report['data']['problemas']:
            print(f"  {row['arquivo']} → {row['campo']} → {row['problema']}")
        raise SystemExit(1)
    c = UnrealClient()
    pie(False)
    report['tests'] = tests()
    report['floating'] = floating(base)
    report['cook'] = cooking()
    report['lights'] = lights()
    report['decor'] = decor()
    report['cameras'] = cameras()
    offset = LOG.stat().st_size
    pie(True)
    coast('clock', '690')
    hud('cmd', 'mare.Weather 1')
    time.sleep(20)
    # The gait audit samples everyone, on screen or not: it checks the walk itself, so off-screen people animate here
    # (mare.OffscreenPose 0, and nobody hidden by distance or by being out of view, mare.PeopleHideOffscreen /
    # PeopleDrawDistance, 04/11); the visible-rig check below runs the game as shipped.
    hud('cmd', 'mare.OffscreenPose 0'); hud('cmd', 'mare.PeopleHideOffscreen 0'); hud('cmd', 'mare.PeopleDrawDistance 0')
    time.sleep(2)
    day = gait()
    hud('cmd', 'mare.OffscreenPose 1'); hud('cmd', 'mare.PeopleHideOffscreen 1'); hud('cmd', 'mare.PeopleDrawDistance -1')
    time.sleep(2)
    report['visible'] = visible()
    report['ui_shot'] = ui_shot()
    if with_shots:
        report['shots'] = shots(stamp)
    coast('clock', '1250')
    hud('cmd', 'mare.OffscreenPose 0'); hud('cmd', 'mare.PeopleHideOffscreen 0'); hud('cmd', 'mare.PeopleDrawDistance 0')
    time.sleep(20)
    night = gait()
    hud('cmd', 'mare.OffscreenPose 1'); hud('cmd', 'mare.PeopleHideOffscreen 1'); hud('cmd', 'mare.PeopleDrawDistance -1')
    report['gait'] = {'day': day, 'night': night, 'pass': not day['gliding'] and not night['gliding'] and day['moving'] > 0}
    report['log'] = log_since(offset, base.get('log_allow', []))
    pie(False)
    report['untracked'] = untracked(base)
    report['driver'] = dict(DRIVER, **{'pass': bool(DRIVER.get('driver')) and not DRIVER.get('swim')})
    report['pass'] = all(report[k]['pass'] for k in ('data', 'tests', 'floating', 'cook', 'lights', 'decor', 'cameras', 'gait', 'visible', 'log', 'untracked', 'driver', 'ui_shot'))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    if accept:
        base['floating'] = report['floating']['floating']
        BASELINE.write_text(json.dumps(base, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('QA GATE', 'PASS' if report['pass'] else 'FAIL')
    print(' data   ', report['data']['arquivos_lidos'], 'JSON,', report['data']['erros'], 'erro(s)')
    print(' tests  ', report['tests']['total'], 'run,', len(report['tests']['failed']), 'failed', [f['name'] for f in report['tests']['failed']])
    for f in report['tests']['failed']:
        print('         ', f['name'], f['errors'][:2])
    print(' cook   ', report['cook']['cooked'], 'packages,', len(report['cook']['missing']), 'loaded by path but not cooked',
          (report['cook']['missing'] + report['cook']['absent'])[:6])
    print(' float  ', report['floating']['floating'], '(baseline', report['floating']['baseline'], ')')
    print(' driver ', report['driver'].get('meshes'), 'swimwear' if report['driver'].get('swim') else '')
    print(' uishot ', 'ok' if report['ui_shot']['pass'] else 'NO FILE', '(editor minimized)' if report['ui_shot']['minimized'] else '')
    print(' lights ', len(report['lights']['bare']), 'room lights without a fixture', report['lights']['bare'][:6])
    print(' decor  ', 'ok' if report['decor']['pass'] else report['decor'])
    print(' camera ', 'ok' if report['cameras']['pass'] else report['cameras']['letterboxed'])
    print(' gait   day', day['moving'], 'moving', len(day['gliding']), 'gliding | night', night['moving'], 'moving', len(night['gliding']), 'gliding')
    v = report['visible']
    print(' visible', v['actors'], 'rigs seen |', len(v['gliding']), 'gliding', len(v['frozen']), 'frozen', (v['gliding'] + v['frozen'])[:6])
    print(' log    ', report['log']['count'], 'bad lines')
    for l in report['log']['unique'][:12]:
        print('   ', l)
    print(' git    ', len(report['untracked']['files']), 'untracked assets', report['untracked']['files'][:8])
    if with_shots:
        print(' shots  ', report['shots']['folder'], 'review:', report['shots']['review'])


if __name__ == '__main__':
    main()

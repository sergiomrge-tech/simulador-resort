"""Quality gate run before every commit (Maré Alta, UE 5.8, editor open with the MCP server on 8000).

What it checks, with data (PASS only if all hard checks pass):
  1. automation tests  - every MareAlta.* test succeeds;
  2. floating props    - float_audit scan: no more floating instances than the accepted baseline;
  3. natural movement  - PIE gait audit by day and by night: nobody moving while feet/hands stay put;
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

c = UnrealClient()
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


def pie(on):
    running = 'true' in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower()
    if on and not running:
        call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
        time.sleep(45)
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


def log_since(offset, allow):
    text = LOG.read_bytes()[offset:].decode('utf-8', 'ignore')
    bad = re.compile(r'(Error:|: Error |Ensure condition failed|missing usage flag|Default Material will be used|REAL_MISSING|Fatal)')
    lines = [l.strip()[-220:] for l in text.splitlines() if bad.search(l) and not any(a in l for a in allow)]
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


def main():
    accept, with_shots = '--accept' in sys.argv, '--no-shots' not in sys.argv
    base = json.loads(BASELINE.read_text(encoding='utf-8')) if BASELINE.exists() else {}
    stamp = time.strftime('%Y%m%d-%H%M%S')
    report = {'stamp': stamp}
    pie(False)
    report['tests'] = tests()
    report['floating'] = floating(base)
    offset = LOG.stat().st_size
    pie(True)
    coast('clock', '690')
    hud('cmd', 'mare.Weather 1')
    time.sleep(20)
    day = gait()
    if with_shots:
        report['shots'] = shots(stamp)
    coast('clock', '1250')
    time.sleep(20)
    night = gait()
    report['gait'] = {'day': day, 'night': night, 'pass': not day['gliding'] and not night['gliding'] and day['moving'] > 0}
    report['log'] = log_since(offset, base.get('log_allow', []))
    pie(False)
    report['untracked'] = untracked(base)
    report['pass'] = all(report[k]['pass'] for k in ('tests', 'floating', 'gait', 'log', 'untracked'))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    if accept:
        base['floating'] = report['floating']['floating']
        BASELINE.write_text(json.dumps(base, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('QA GATE', 'PASS' if report['pass'] else 'FAIL')
    print(' tests  ', report['tests']['total'], 'run,', len(report['tests']['failed']), 'failed', [f['name'] for f in report['tests']['failed']])
    print(' float  ', report['floating']['floating'], '(baseline', report['floating']['baseline'], ')')
    print(' gait   day', day['moving'], 'moving', len(day['gliding']), 'gliding | night', night['moving'], 'moving', len(night['gliding']), 'gliding')
    print(' log    ', report['log']['count'], 'bad lines')
    for l in report['log']['unique'][:12]:
        print('   ', l)
    print(' git    ', len(report['untracked']['files']), 'untracked assets', report['untracked']['files'][:8])
    if with_shots:
        print(' shots  ', report['shots']['folder'], 'review:', report['shots']['review'])


if __name__ == '__main__':
    main()

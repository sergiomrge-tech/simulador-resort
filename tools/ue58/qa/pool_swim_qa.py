"""Pool swimmers QA (UMarePoolSwimWorld, Content/Data/pool_swim.json): editor open with the MCP server, a NEW save
profile (restart_editor.ps1). Starts the PIE, buys the pool chain, sets 11h, forces swimmers and photographs them
from the deck and up close; writes the swimmer dump and a contact sheet to D:/CodexTemp/qa/pool_swim/<stamp>.
Usage: python tools/ue58/qa/pool_swim_qa.py [count=6] [wait_s=40]"""
import json
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import qa_gate  # noqa: E402
from mcp_client import UnrealClient  # noqa: E402

OUT = Path(r'D:\CodexTemp\qa\pool_swim')
CHAIN = ['kiosk_tables', 'drinks', 'neon', 'grill', 'bar', 'pousada', 'pool']


def dump():
    log = qa_gate.LOG
    start = log.stat().st_size
    qa_gate.hud('cmd', 'mare.PoolSwim dump')
    time.sleep(1.5)
    with open(log, encoding='utf-8', errors='replace') as f:
        f.seek(start)
        text = f.read()
    lines = [l for l in text.splitlines() if 'MARE_POOLSWIM' in l]
    rows = []
    if lines:
        for part in lines[-1].split('; '):
            m = re.search(r'(\d+) (\S*) (\w+) pos=\((-?\d+),(-?\d+),(-?\d+)\) yaw=(-?\d+)', part)
            if m:
                rows.append({'i': int(m[1]), 'mh': m[2], 'state': m[3], 'pos': [int(m[4]), int(m[5]), int(m[6])], 'yaw': int(m[7])})
    return rows


def shot(name, x, y, z, pitch, yaw, folder):
    src = qa_gate.SHOTS / f'pie-qa_{name}.png'
    if src.exists():
        src.unlink()
    qa_gate.coast('pie', f'qa_{name},{x:.0f},{y:.0f},{z:.0f},{pitch:.0f},{yaw:.0f}')
    time.sleep(2.5)
    qa_gate.coast('pie', f'qa_{name}!,0,0,0,0,0')
    for _ in range(30):
        if src.exists():
            time.sleep(1)
            shutil.copy(src, folder / f'{name}.png')
            return folder / f'{name}.png'
        time.sleep(1)
    return None


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    qa_gate.c = UnrealClient()
    stamp = time.strftime('%Y%m%d-%H%M%S')
    folder = OUT / stamp
    folder.mkdir(parents=True, exist_ok=True)
    qa_gate.pie(True)
    qa_gate.hud('cmd', 'mare.QA money 500000')
    for e in CHAIN:
        qa_gate.hud('cmd', f'mare.QA buy {e}')
    qa_gate.coast('clock', '660')
    qa_gate.hud('cmd', f'mare.PoolSwim {count}')
    # Look away from the pool so the swimmers can appear, then come back.
    qa_gate.coast('pie', 'qa_away,0,-2500,200,0,-90')
    # Swimmers appear one at a time while nobody looks: wait until all are in the water (or the time runs out).
    t0 = time.time()
    while time.time() - t0 < wait:
        time.sleep(8)
        rows = dump()
        if len(rows) >= count and all(r['state'] != 'edge' for r in rows):
            break
    time.sleep(10)
    shots = [shot('deck_sul', 0, -330, 110, -14, 90, folder), shot('deck_norte', 0, 1050, 110, -14, -90, folder)]
    rows = dump()
    # One of each state first (floating, chatting, on the edge, jumping), then swimmers.
    order = {'float': 0, 'chat': 1, 'edge': 2, 'jump': 3, 'swim': 4}
    for r in sorted(rows, key=lambda r: order.get(r['state'], 5))[:4]:
        x, y, z = r['pos']
        # 3.5 m from the swimmer, from the nearest deck side, eye just above the water.
        side = -1 if y < 400 else 1
        shots.append(shot(f"perto_{r['i']}_{r['state']}", x + 120, y + side * 350, 80, -10, -90 if side > 0 else 90, folder))
    (folder / 'dump.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    from PIL import Image, ImageDraw
    tiles = []
    for p in [s for s in shots if s]:
        img = Image.open(p).convert('RGB').resize((800, 450))
        ImageDraw.Draw(img).text((8, 8), p.stem, fill='yellow')
        tiles.append(img)
    if tiles:
        sheet = Image.new('RGB', (1600, 450 * ((len(tiles) + 1) // 2)))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % 2) * 800, (i // 2) * 450))
        sheet.save(folder / 'sheet.jpg', quality=88)
    print(json.dumps({'folder': str(folder), 'swimmers': rows}, ensure_ascii=False))


if __name__ == '__main__':
    main()

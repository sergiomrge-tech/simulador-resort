"""Water slide QA (UMarePoolSwimWorld hotel pool "slide"): editor open with the MCP server, a NEW save profile.
Unlocks the Grand Hotel (QA money/fame/chapters), forces swimmers in the hotel pool and photographs each slide rider
up close while climbing, riding and after the splash. Output: D:/CodexTemp/qa/slide/<stamp>/sheet.jpg + dump.json.
Usage: python tools/ue58/qa/slide_qa.py [seconds=600]"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import qa_gate  # noqa: E402
import pool_swim_qa as psq  # noqa: E402
from mcp_client import UnrealClient  # noqa: E402

OUT = Path(r'D:\CodexTemp\qa\slide')
CHAIN = ['kiosk_tables', 'drinks', 'neon', 'grill', 'bar', 'pousada', 'pool', 'passeios']
CHAPTERS = ['pier', 'prainha', 'sabores', 'carnaval']


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    qa_gate.c = UnrealClient()
    folder = OUT / time.strftime('%Y%m%d-%H%M%S')
    folder.mkdir(parents=True, exist_ok=True)
    qa_gate.pie(True)
    qa_gate.hud('cmd', 'mare.QA money 900000')
    qa_gate.hud('cmd', 'mare.QA fame 10')
    for e in CHAIN:
        qa_gate.hud('cmd', f'mare.QA buy {e}')
    for ch in CHAPTERS:
        for _ in range(4):
            qa_gate.hud('cmd', f'mare.QA step {ch}')
    qa_gate.hud('cmd', 'mare.QA buy grand_hotel')
    # Everything of the demo owned: its end screen pauses the game until closed.
    time.sleep(3)
    qa_gate.hud('cmd', 'mare.ShowUI close')
    qa_gate.coast('clock', '660')
    qa_gate.hud('cmd', 'mare.PoolSwim 6')
    qa_gate.coast('pie', 'qa_away,-2600,6500,300,0,90')
    shots, seen, rows = [], set(), []
    t0 = time.time()
    while time.time() - t0 < seconds and len(seen) < 6:
        time.sleep(4)
        rows = psq.dump()
        for r in rows:
            if r['state'] in ('climb', 'ride', 'fly') or (r['state'] == 'swim' and ('ride', r['i']) in seen):
                key = (r['state'], r['i'])
                if key in seen:
                    continue
                seen.add(key)
                x, y, z = r['pos']
                # From the pool side, 6 m away, looking at the rider.
                cx, cy = x + 600, y - 150
                import math
                yaw = math.degrees(math.atan2(y - cy, x - cx))
                pitch = max(-30, min(20, math.degrees(math.atan2(z - (z if r['state'] == 'swim' else 250), 600))))
                shots.append(psq.shot(f"{r['state']}_{r['i']}", cx, cy, max(250, z - 40), pitch, yaw, folder))
                qa_gate.coast('pie', 'qa_away,-2600,6500,300,0,90')
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
    print(json.dumps({'folder': str(folder), 'shots': [str(s) for s in shots if s], 'swimmers': rows}, ensure_ascii=False))


if __name__ == '__main__':
    main()

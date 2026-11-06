"""Night photos of every interior, everything unlocked (06/11/2026, CHECKLIST 0: light comes from the lamps).

Editor open with the MCP server and a QA profile (-MareSaveRoot=D:/CodexTemp/<new>). Starts PIE if needed, unlocks the
whole game (mare.QA money/buy/step/fame), sets clear weather and the clock (default 22h), waits for Lumen and the
eye to settle (~25 s, CLAUDE.md 04/11) and captures each camera. Output: D:/CodexTemp/qa/night/<stamp>/*.png + sheet.jpg
Usage: python tools/ue58/qa/night_lights.py [--clock 1320] [--only name,name] [--no-unlock] [--cams "name=x,y,z,pitch,yaw;..."]
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from mcp_client import UnrealClient  # noqa: E402

c = UnrealClient()
SHOTS = Path(r'D:\CodexTemp\beach')
OUT = Path(r'D:\CodexTemp\qa\night') / time.strftime('%Y%m%d-%H%M%S')
CAMERAS = {   # pawn position (capsule centre) x,y,z, pitch, yaw
    'casa_sala': '4450,1900,120,-12,55',
    'casa_cozinha': '4640,2120,120,-14,55',
    'casa_banheiro': '4760,1760,120,-22,-90',
    'quiosque': '3700,-1080,100,-12,-75',
    # 06/11 (CHECKLIST 0, "barra atravessando a câmera"): with z 170 the eye floated at 2.44 m, between the back of the
    # "ABERTO" neon sign and its hanging rods (World_1296/1297, Region_neon) 4-57 cm from the lens. Pawn z ~100 = eye 1.74 m.
    'quiosque_barra': '3700,-1600,100,-5,90',
    'lobby': '-1250,6300,140,-6,180',
    'lobby_recepcao': '-2600,6150,140,-6,30',
    'suite': '-2800,6690,943,-10,-90',
    'pousada_recepcao': '200,1250,130,-10,120',
    'bangalo': '-1600,1470,140,-12,90',
}
EXPANSIONS = ('kiosk_tables', 'drinks', 'neon', 'grill', 'bar', 'pousada', 'pool', 'passeios')


def call(ts, tool, args):
    r = c.rpc('tools/call', {'name': 'call_tool', 'arguments': {'toolset_name': ts, 'tool_name': tool, 'arguments': args}})
    return '\n'.join(e.get('text', '') for e in r.get('content', []))


def hud(action, arg=''):
    return call('mare_mcp.MareMigrationTools', 'hotel_lobby', {'action': 'hud_' + action, 'arg': arg})


def coast(action, arg):
    return call('mare_mcp.MareMigrationTools', 'caribbean_coast', {'action': action, 'arg': arg})


def cmd(text):
    hud('cmd', text)
    time.sleep(.6)


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    cams = dict(CAMERAS)
    if arg('--cams'):
        cams = dict(item.split('=') for item in arg('--cams').split(';') if item)
    if arg('--only'):
        cams = {k: v for k, v in cams.items() if k in arg('--only').split(',')}
    if 'true' not in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower():
        call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
        time.sleep(45)
        cmd('mare.ShowUI play')
        time.sleep(10)
    if '--no-unlock' not in sys.argv:
        cmd('mare.QA money 900000')
        for exp in EXPANSIONS:
            cmd(f'mare.QA buy {exp}')
        for chapter in ('pier', 'prainha', 'sabores', 'carnaval'):
            for _ in range(3):
                cmd(f'mare.QA step {chapter}')
        cmd('mare.QA money 900000')
        cmd('mare.QA fame 9')   # grand_hotel needs fame 9 (definitions.json)
        cmd('mare.QA buy grand_hotel')
        cmd('mare.QA buy salao_jogos')
    # A new profile starts with the bus arrival and the letter: the intro holds the camera (shots all came out at the door).
    for _ in range(3):
        cmd('mare.ShowUI close')
        time.sleep(2)
    cmd('mare.Weather 1')
    coast('clock', arg('--clock', '1320'))
    time.sleep(25)
    OUT.mkdir(parents=True, exist_ok=True)
    got = []
    for name, spec in cams.items():
        src = SHOTS / f'pie-night_{name}.png'
        if src.exists():
            src.unlink()
        coast('pie', f'night_{name},{spec}')
        # Lumen and the eye settle after the jump. 06/11: 7 s left rooms seen for the first time with the daylight still in
        # Lumen's surface cache (the suite and the kiosk came out as if at noon at 22h); 15 s is clean.
        time.sleep(15)
        coast('pie', f'night_{name}!,0,0,0,0,0')
        for _ in range(30):
            if src.exists():
                time.sleep(1)
                (OUT / f'{name}.png').write_bytes(src.read_bytes())
                got.append(name)
                break
            time.sleep(1)
        else:
            print('no capture', name)
    from PIL import Image, ImageDraw
    if got:
        sheet = Image.new('RGB', (1280, 360 * ((len(got) + 1) // 2)))
        for i, name in enumerate(got):
            t = Image.open(OUT / f'{name}.png').convert('RGB').resize((640, 360))
            ImageDraw.Draw(t).text((10, 10), name, fill='yellow')
            sheet.paste(t, ((i % 2) * 640, (i // 2) * 360))
        sheet.save(OUT / 'sheet.jpg', quality=88)
    print(json.dumps({'folder': str(OUT), 'shots': got}))


if __name__ == '__main__':
    main()

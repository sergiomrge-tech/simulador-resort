"""Dress every MetaHuman build with its Fab outfit (Content/Data/outfits_fab.json) and rebuild it, through the editor
MCP, five builds per editor session (a MetaHuman build keeps ~10 GB alive; more in one session ran out of memory).

  python tools/ue58/dress_metahumans.py [Name ...]      log: D:/CodexTemp/dress.log
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UE = r'D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
PROJECT = ROOT / 'unreal/MareAlta/MareAlta.uproject'
MCP = 'D:/CodexTemp/claude-mcp/ue.py'
LOG = Path('D:/CodexTemp/dress.log')


def log(*parts):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(p) for p in parts)
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def call(action, arg, limit=600, timeout=2400):
    env = {**__import__('os').environ, 'MARE_MCP_TIMEOUT': str(timeout)}
    r = subprocess.run([sys.executable, MCP, 'call', 'mare_mcp.MareMigrationTools', 'hotel_lobby',
                        json.dumps({'action': action, 'arg': arg}), str(limit)], capture_output=True, text=True, env=env,
                       timeout=timeout + 60)
    return (r.stdout or r.stderr).strip()


def editor_ready(wait=600):
    for _ in range(wait // 10):
        r = subprocess.run([sys.executable, MCP, 'call', 'EditorToolset.EditorAppToolset', 'IsPIERunning', '{}', '300'],
                           capture_output=True, text=True)
        if 'returnValue' in r.stdout:
            return True
        time.sleep(10)
    return False


def restart_editor():
    subprocess.run(['powershell', '-NoProfile', '-Command',
                    'Get-Process UnrealEditor -ErrorAction SilentlyContinue | Stop-Process -Force'])
    time.sleep(8)
    subprocess.run(['powershell', '-NoProfile', '-Command',
                    "${env:UE-LocalDataCachePath}='D:\\Caches\\UnrealZen'; Start-Process '%s' -ArgumentList '%s',"
                    "'-ModelContextProtocolStartServer','-ModelContextProtocolPort=8000','-MareSaveRoot=D:/CodexTemp/claude-visual',"
                    "'-unattended','-MareSkipMenu'" % (UE, PROJECT)])
    return editor_ready()


def main(names):
    data = json.loads((ROOT / 'unreal/MareAlta/Content/Data/outfits_fab.json').read_text(encoding='utf-8'))
    names = names or list(data['people'])
    for i, name in enumerate(names):
        if i and i % 5 == 0:
            log('restart editor:', restart_editor())
        items = ','.join(data['items'][k] for k in data['people'][name])
        log(name, 'dress', call('mh_dress', f'{name}@@{items}', 400)[:300])
        log(name, 'build', call('mh_build', name, 200)[:200])
        log(name, 'save', call('mh_save', '', 80)[:80])
    log('DONE')


if __name__ == '__main__':
    main(sys.argv[1:])

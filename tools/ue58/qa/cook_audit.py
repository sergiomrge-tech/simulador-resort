"""Packaging audit: everything the game loads by path must be in the cooked build (PENDENCIAS P1 memória/pacote, 03/11).

    python tools/ue58/qa/cook_audit.py          (editor open with the MCP server; prints JSON, exit 1 when something is left out)

The game loads many assets by a path written in text (LoadObject/LoadClass in the C++, paths in Content/Data/*.json):
the cooker never sees those references. The MetaHumans, for one, were loaded with LoadClass("/Game/People/MetaHumans/
<Name>/MH_<Name>/BP_MH_<Name>") and only _HiGarments was in DirectoriesToAlwaysCook, so a new EXE would ship without
the people. This collects
  - every "/Game/..." string in the Content/Data/*.json files the C++ reads,
  - every TEXT("/Game/...") literal in Source/MareAlta, plain or a format string (%s/%d/%02d become regexes),
and asks the editor (hotel_lobby hud_cookaudit) which of them exist but are not reachable from the maps to cook and
DirectoriesToAlwaysCook (hard and soft references followed).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / 'unreal/MareAlta'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
OUT = Path('D:/CodexTemp/qa/cook_audit_spec.json')

# Format strings that are folders, not packages: the package the code then loads inside them.
FOLDER_TEMPLATES = {'/Game/People/MetaHumans/%s/MH_%s/': '/Game/People/MetaHumans/%s/MH_%s/BP_MH_%s'}
# MetaHuman paths are expanded with the names in the metahumans.json rosters (Zuri, the bald preset, and spare builds
# such as Mateo_Beach stay out of the cook).
PEOPLE = '/Game/People/MetaHumans/%s/MH_%s/BP_MH_%s'


def roster():
    data = json.loads((PROJECT / 'Content/Data/metahumans.json').read_text(encoding='utf-8-sig'))
    shoes = {'Dress', 'Flipflops', 'Sandals', 'Sneakers'}
    return sorted({n for k, v in data.items() if isinstance(v, list) and k != 'men' for n in v
                   if isinstance(n, str) and re.fullmatch(r'[A-Z][a-z]+(_[A-Z][a-z]+)*', n) and n not in shoes})


def to_regex(fmt):
    out, i = '', 0
    for m in re.finditer(r'%(?:0?\d*)([sd])', fmt):
        out += re.escape(fmt[i:m.start()]) + (r'[^/.]+' if m.group(1) == 's' else r'\d+')
        i = m.end()
    return out + re.escape(fmt[i:])


def collect():
    paths, patterns = set(), set()
    # Only the data files the game reads (named in the C++ outside comments); the others are editor build inputs.
    code = ' '.join(re.sub(r'//.*', '', line) for f in sorted((PROJECT / 'Source/MareAlta').glob('*.*'))
                     for line in f.read_text(encoding='utf-8', errors='replace').splitlines())
    for f in sorted((PROJECT / 'Content/Data').glob('*.json')):
        if f'"{f.stem}"' not in code and f'{f.stem}.json' not in code:
            continue
        for m in re.findall(r'"(/Game/[^"]+)"', f.read_text(encoding='utf-8-sig')):
            paths.add(m)
    for f in sorted((PROJECT / 'Source/MareAlta').glob('*.*')):
        for m in re.findall(r'TEXT\("(/Game/[^"]+)"\)', f.read_text(encoding='utf-8', errors='replace')):
            m = FOLDER_TEMPLATES.get(m, m)
            if m == PEOPLE:
                paths.update(PEOPLE.replace('%s', n) for n in roster())
            elif '%' in m:
                patterns.add(to_regex(m.split('.')[0]))
            else:
                paths.add(m)
    return sorted(paths), sorted(patterns)


def hud(action, arg):
    from mcp_client import UnrealClient   # same JSON-RPC client the QA gate uses
    r = UnrealClient().rpc('tools/call', {'name': 'call_tool', 'arguments': {
        'toolset_name': 'mare_mcp.MareMigrationTools', 'tool_name': 'hotel_lobby', 'arguments': {'action': 'hud_' + action, 'arg': arg}}})
    v = json.loads(''.join(e.get('text', '') for e in r.get('content', [])))['returnValue']
    return json.loads(v) if isinstance(v, str) else v


def main():
    paths, patterns = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'paths': paths, 'patterns': patterns}, indent=1), encoding='utf-8')
    res = hud('cookaudit', str(OUT))
    res = json.loads(res) if isinstance(res, str) else res
    print(json.dumps({'paths': len(paths), 'patterns': len(patterns), **res}, indent=1))
    return 1 if res['missing'] else 0


if __name__ == '__main__':
    sys.exit(main())

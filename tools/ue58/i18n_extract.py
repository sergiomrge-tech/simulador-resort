"""Collects every Portuguese text of the game for translation (MareLoc, Source/MareAlta/MareLoc.h).

Writes unreal/MareAlta/Content/Localization/Mare/source.json:
  "loctext": {"Namespace,Key": "texto"}   - LOCTEXT / NSLOCTEXT in the C++ code
  "strings": ["texto", ...]               - other C++ literals shown on screen (Printf formats become {0} {1} ...)
                                            and the texts of Content/Data/*.json (names, descriptions, dialogues)
and keeps en.json / es.json in step: new texts are added empty, texts that no longer exist are dropped.
Prints how many are still untranslated per language and writes todo_<lang>.json (the missing ones) for translation.

Usage: python tools/ue58/i18n_extract.py
"""
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta'
OUT = ROOT / 'Content' / 'Localization' / 'Mare'
LANGS = ['en', 'es']
LIT = re.compile(r'TEXT\("((?:[^"\\]|\\.)*)"\)')
LOCTEXT = re.compile(r'\bLOCTEXT\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')
NSLOCTEXT = re.compile(r'\bNSLOCTEXT\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')
NAMESPACE = re.compile(r'#define\s+LOCTEXT_NAMESPACE\s+"([^"]+)"')
PRINTF = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?(?:l|ll|h)?[sdifgu]')
WORD = re.compile(r'[A-Za-zÀ-ú]{3,}')
SKIP_PREFIX = ('/Game', '/Script', '/Engine', '/Niagara', '/Interchange', '/Mare', 'r.', 'mare.', 't.', 'sg.', 'fx.', 'MH_',
               'SKM_', 'MARE_', 'Data/', 'Localization/', 'Mare', 'BP_', 'M_', 'MI_', 'T_', 'S_', 'SM_', 'ABP_', 'Region_')
# JSON keys whose string values are internal (ids, paths, kinds), never shown.
JSON_SKIP_KEYS = {'model', 'hide', 'anchor', 'also', 'unlock', 'region', 'source', 'need', 'requires', 'expansion_order',
                  'id', 'path', 'mesh', 'material', 'kind', 'type', 'anim', 'pose', 'icon', 'sound', 'cue', 'asset', 'look',
                  'metahuman', 'tag', 'tags', 'map', 'level', 'class', 'texture', 'image', 'file', 'voice', 'dish', 'role'}


def unescape(s):
    return bytes(s, 'utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') if '\\' in s else s


def shown(s):
    """Heuristic: human text, not an identifier, key, path or console variable."""
    t = s.strip()
    if len(t) < 2 or t.startswith(SKIP_PREFIX) or t.startswith('@') or not WORD.search(t):
        return False
    if re.search(r'_\d{2,}$', t) or re.fullmatch(r'World_\d+.*', t) or t.endswith(('.glb', '.json', '.png', '.wav', '.ogg')):
        return False
    if re.fullmatch(r'[A-Za-z0-9_.\-/%]+', t) and not re.search(r'[À-ú]', t):
        # single token: keep it only if it looks like a Portuguese word starting lower-case or capitalised word
        # (all-caps words are painted signs: "ABERTO", "PIPOCA")
        return bool(re.fullmatch(r'[A-ZÀ-Ú]?[a-zà-ú]{3,}|[A-ZÀ-Ú]{4,}', t)) and t.lower() not in {'none', 'true', 'false', 'idle'}
    return True


def template(s):
    """Printf format -> {0} {1} ... (the runtime matches formatted strings against it)."""
    n = [0]

    def sub(_):
        n[0] += 1
        return '{%d}' % (n[0] - 1)
    return PRINTF.sub(sub, s.replace('%%', '%'))


def scan_code():
    loc, strings = {}, set()
    for f in sorted(glob.glob(str(ROOT / 'Source' / 'MareAlta' / '*.cpp')) + glob.glob(str(ROOT / 'Source' / 'MareAlta' / '*.h'))):
        if f.endswith('Tests.cpp') or 'MareLoc' in f or 'QA' in Path(f).stem or 'Bench' in Path(f).stem:
            continue
        text = Path(f).read_text(encoding='utf-8', errors='ignore')
        ns = None
        for line in text.splitlines():
            m = NAMESPACE.search(line)
            if m:
                ns = m.group(1)
            for nsx, key, src in NSLOCTEXT.findall(line):
                loc[f'{nsx},{key}'] = unescape(src)
            if ns:
                for key, src in LOCTEXT.findall(line):
                    loc[f'{ns},{key}'] = unescape(src)
            if 'UE_LOG' in line or line.strip().startswith('//') or 'LOCTEXT' in line:
                continue
            for s in LIT.findall(line):
                s = unescape(s)
                if shown(s):
                    strings.add(template(s) if PRINTF.search(s) else s)
    return loc, strings


def scan_data():
    strings = set()

    def walk(v, key=''):
        if isinstance(v, dict):
            for k, x in v.items():
                if not k.startswith('_') and not k.endswith('_en') and k not in JSON_SKIP_KEYS:
                    walk(x, k)
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
        elif isinstance(v, str) and shown(v):
            strings.add(v)
    for f in sorted(glob.glob(str(ROOT / 'Content' / 'Data' / '*.json'))):
        name = Path(f).name
        if name in ('actors.json', 'imported_meshes.json', 'deduplication.json', 'stacked_origin_removed.json', 'intro_import_hashes.json',
                    'actor_material_audit.json', 'model_aliases.json', 'map_build.json', 'nanite_architecture.json', 'grass_coverage.json'):
            continue
        try:
            doc = json.loads(Path(f).read_text(encoding='utf-8'))
            if name == 'world.json':   # only the painted texts and the residents' names are shown
                doc = {'texts': doc.get('texts', []), 'residents': doc.get('residents', [])}
            walk(doc)
        except Exception:
            pass
    return strings


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    loc, code = scan_code()
    data = scan_data()
    raw = code | data
    # Multi-line signs are split at the line break at runtime ("PISCINA<br>duche antes de entrar"): each line is a text too.
    raw |= {line.strip() for t in list(raw) if '\n' in t for line in t.split('\n') if shown(line) and '{' not in line}
    # Fragments glued by the code (" · avançar", " (cansado)") also show up alone once a composed text is split:
    # keep a stripped variant, translated from the fragment's own translation below.
    derived = {}

    def strip(t):
        t = t.strip()
        while t.startswith('<br>'):
            t = t[4:].strip()
        return t.lstrip('·').strip().rstrip(':').strip()
    for t in raw:
        core = strip(t)
        # "<br>{0} prontos" also arrives as "{0} prontos" after the split at <br>; a lone "{0}" is no text.
        if core and core != t and core not in raw and WORD.search(core) and (('{' not in core) or t.startswith('<br>')):
            derived[core] = t
    strings = sorted(raw | set(derived))
    (OUT / 'source.json').write_text(json.dumps({'_doc': __doc__.strip().splitlines()[0], 'loctext': loc, 'strings': strings},
                                                ensure_ascii=False, indent=1), encoding='utf-8')
    for lang in LANGS:
        path = OUT / f'{lang}.json'
        old = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        oldloc, oldstr = old.get('loctext', {}), old.get('strings', {})
        new = {'_doc': f'Translations ({lang}) of source.json; keys are the Portuguese texts. Empty = not translated yet.',
               'loctext': {k: oldloc.get(k, '') for k in sorted(loc)},
               'strings': {s: oldstr.get(s, '') for s in strings}}
        for core, frag in derived.items():
            if not new['strings'][core] and new['strings'].get(frag):
                new['strings'][core] = strip(new['strings'][frag])
        path.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding='utf-8')
        missing = {'loctext': {k: loc[k] for k in loc if not new['loctext'][k]},
                   'strings': [s for s in strings if not new['strings'][s]]}
        (OUT / f'todo_{lang}.json').write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{lang}: loctext {len(loc) - len(missing["loctext"])}/{len(loc)}  strings {len(strings) - len(missing["strings"])}/{len(strings)}')
    words = sum(len(s.split()) for s in strings) + sum(len(s.split()) for s in loc.values())
    print(f'textos: {len(loc)} loctext + {len(strings)} strings ({len(code)} do código, {len(data)} dos dados), ~{words} palavras')


if __name__ == '__main__':
    main()

"""Translation batches for MareLoc (tools/ue58/i18n_extract.py first).

  python tools/ue58/i18n_batch.py show <lang> <start> <count>   -> prints the untranslated texts with their index
  python tools/ue58/i18n_batch.py merge <lang> <file.json>       -> file: {"<index>": "translation", ...} (indexes from show;
                                                                   "L:<Namespace,Key>" for LOCTEXT entries)
Indexes refer to the sorted "strings" list of source.json, so they stay stable while source.json does not change.
"""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta' / 'Content' / 'Localization' / 'Mare'


def load(lang):
    src = json.loads((OUT / 'source.json').read_text(encoding='utf-8'))
    tr = json.loads((OUT / f'{lang}.json').read_text(encoding='utf-8'))
    return src, tr


def main():
    cmd, lang = sys.argv[1], sys.argv[2]
    sys.stdout.reconfigure(encoding='utf-8')
    src, tr = load(lang)
    if cmd == 'show':
        start, count = int(sys.argv[3]), int(sys.argv[4])
        rows = [(f'L:{k}', v) for k, v in src['loctext'].items() if not tr['loctext'].get(k)]
        rows += [(str(i), s) for i, s in enumerate(src['strings']) if not tr['strings'].get(s)]
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(dict(rows[start:start + count]), ensure_ascii=False, indent=0))
        print(f'# pendentes: {len(rows)}', file=sys.stderr)
    elif cmd == 'fill':
        # Untranslated single ASCII tokens (internal identifiers such as 'absent', 'biz:', 'deliver') keep their text.
        import re
        n = 0
        for st in src['strings']:
            if not tr['strings'].get(st) and re.fullmatch(r'[A-Za-z0-9_:.\-]+', st):
                tr['strings'][st] = st; n += 1
        (OUT / f'{lang}.json').write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{lang}: {n} identificadores mantidos')
    elif cmd == 'compose':
        # Fills what can be derived: internal identifiers kept as-is in English, and multi-line texts whose lines are
        # all translated (signs, the grandmother's letter). Numbers/prices keep their text.
        import re
        en = json.loads((OUT / 'en.json').read_text(encoding='utf-8'))['strings']
        nothing = lambda t: not re.search(r'[A-Za-zÀ-ú]{2,}', t.replace('R$', ''))
        n = 0
        for st in src['strings']:
            if tr['strings'].get(st):
                continue
            if en.get(st) == st:   # identifiers, names and language names stay as written
                tr['strings'][st] = st; n += 1
            elif '\n' in st:
                parts = [l if (not l.strip() or nothing(l)) else tr['strings'].get(l) for l in st.split('\n')]
                if all(p is not None for p in parts):
                    tr['strings'][st] = '\n'.join(parts); n += 1
        (OUT / f'{lang}.json').write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding='utf-8')
        left = [s for s in src['strings'] if not tr['strings'].get(s)] + [k for k in src['loctext'] if not tr['loctext'].get(k)]
        print(f'{lang}: +{n} montados, faltam {len(left)}', left[:10])
    elif cmd == 'merge':
        batch = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        n = 0
        for k, v in batch.items():
            if k.startswith('L:'):
                if k[2:] in tr['loctext']:
                    tr['loctext'][k[2:]] = v; n += 1
            else:
                s = src['strings'][int(k)]
                tr['strings'][s] = v; n += 1
        (OUT / f'{lang}.json').write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding='utf-8')
        left = sum(1 for v in tr['loctext'].values() if not v) + sum(1 for v in tr['strings'].values() if not v)
        print(f'{lang}: +{n}, faltam {left}')


if __name__ == '__main__':
    main()

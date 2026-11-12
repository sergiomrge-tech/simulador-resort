"""Emulates MareLoc::Tr (Source/MareAlta/MareLoc.cpp) in Python to find which PIECE of a composed text is missing.

  python tools/ue58/loc_emulate.py en "Fama 1 · Desconhecido" ...
  python tools/ue58/loc_emulate.py all --log D:/path/runtime.log    (every MARE_LOC_MISSING of an audit, all languages)

Prints, per text and language, the translation and the leaf pieces that have no entry (exact or template)."""
import json
import re
import sys
from pathlib import Path

LOC = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/Content/Localization/Mare'
SEPS = ['\n', '<br>', ' — ', ' · ', '   ', ': ', '| ']


def table(lang):
    d = json.loads((LOC / f'{lang}.json').read_text(encoding='utf-8-sig'))
    src = json.loads((LOC / 'source.json').read_text(encoding='utf-8-sig')).get('loctext', {})
    exact, templates = {}, []
    for k, v in (d.get('loctext') or {}).items():
        if v and k in src:
            exact[src[k]] = v
    for k, v in (d.get('strings') or {}).items():
        if not v:
            continue
        parts = split_template(k)
        if parts:
            templates.append((parts, v))
        else:
            exact[k] = v
    templates.sort(key=lambda t: -sum(len(p) for p in t[0]))
    done = []
    for v in list((d.get('strings') or {}).values()) + list((d.get('loctext') or {}).values()):
        parts = split_template(v) if v else None
        if parts and sum(len(p) for p in parts) >= 6:
            done.append(parts)
    return exact, templates, set(exact.values()), done


def split_template(key):
    parts, rest, count = [], key, 0
    while True:
        m = re.search(r'\{(\d{1,2})\}', rest)
        if not m:
            break
        parts.append(rest[:m.start()])
        rest = rest[m.end():]
        count += 1
    parts.append(rest)
    return parts if count else None


def match(parts, text):
    if parts[0] and not text.startswith(parts[0]):
        return None
    pos, vals = len(parts[0]), []
    for i in range(1, len(parts)):
        p = parts[i]
        if i == len(parts) - 1:
            if not p:
                nxt = len(text)
            elif text.endswith(p):
                nxt = len(text) - len(p)
            else:
                return None
        else:
            if not p:
                return None
            nxt = text.find(p, pos)
        if nxt < 0 or nxt < pos:
            return None
        val = text[pos:nxt]
        if any(s in val for s in ('. ', '! ', '? ', '\n')):
            return None
        vals.append(val)
        pos = nxt + len(p)
    return vals if pos == len(text) else None


def nothing(text):
    if re.match(r'#\d+ \S+$', text):
        return True
    run = longest = 0
    for ch in text.replace('R$', ''):
        if ch.isalpha():
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest < 2 or len(text) <= 3


def tr(t, text, missing):
    exact, templates, translated, done = t
    if not text:
        return text
    if text in exact:
        return exact[text]
    if text in translated or nothing(text):
        return text
    for parts, value in templates:
        vals = match(parts, text)
        if vals is not None:
            out = value
            for i, v in enumerate(vals):
                out = out.replace('{%d}' % i, exact.get(v, v))
            return out
    if any(match(parts, text) is not None for parts in done):
        return text
    m = re.search(r' \((\d+)/(\d+)\)$', text)
    if m:
        return tr(t, text[:m.start()], missing) + text[m.start():]
    for k, sep in enumerate(SEPS):
        if k == 2:   # after the line breaks: sentences
            for i in range(3, len(text) - 2):
                if text[i] in '.!?' and text[i + 1] == ' ' and text[i + 2].isupper():
                    return tr(t, text[:i + 1], missing) + ' ' + tr(t, text[i + 2:], missing)
        at = text.find(sep)
        if at < 0:
            continue
        left, right = text[:at], text[at + len(sep):]
        if left + sep in exact:
            return exact[left + sep] + tr(t, right, missing)
        return tr(t, left, missing) + sep + tr(t, right, missing)
    missing.append(text)
    return text


def main():
    args = sys.argv[1:]
    langs = [p.stem for p in LOC.glob('*.json') if p.stem != 'source' and not p.stem.startswith('todo_')] if args[0] == 'all' else [args[0]]
    texts = args[1:]
    if '--log' in args:
        log = args[args.index('--log') + 1]
        texts = sorted({l.split('MARE_LOC_MISSING ', 1)[1].rstrip().replace('\\n', '\n')
                        for l in open(log, encoding='utf-8', errors='replace') if 'MARE_LOC_MISSING ' in l})
    leaves = {}
    for lang in langs:
        t = table(lang)
        for text in texts:
            miss = []
            out = tr(t, text, miss)
            for m in miss:
                leaves.setdefault(m, set()).add(lang)
            if len(langs) == 1:
                print(repr(text[:90]), '->', repr(out[:90]), '| missing:', miss)
    if len(langs) > 1:
        for m, ls in sorted(leaves.items()):
            print(repr(m[:110]), sorted(ls) if len(ls) < len(langs) else 'ALL')


if __name__ == '__main__':
    main()

"""Fallback fonts for the translations, cut down to the characters the game uses (MareNotebookStyle.h loads them).

Patrick Hand (titles) and Nunito (text) cover the Latin languages; Patrick Hand has no Cyrillic, and neither has CJK.
  Caveat (OFL)      -> Cyrillic for the handwritten titles
  Noto Sans SC/JP/KR (OFL) -> Chinese / Japanese kana + kanji / Korean hangul
Run after every translation change (needs fontTools: a venv with `pip install fonttools`):
  <venv python> tools/ue58/i18n_fonts.py [--download]
Source fonts (Google Fonts, OFL) are kept in D:/CodexTemp/fonts-dl; --download fetches them.
"""
import json
import sys
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta' / 'Content'
LOC = ROOT / 'Localization' / 'Mare'
FONTS = ROOT / 'UI' / 'Fonts'
SRC = Path('D:/CodexTemp/fonts-dl')
GF = 'https://github.com/google/fonts/raw/main/ofl/'
SOURCES = {
    'NotoSansSC': 'notosanssc/NotoSansSC%5Bwght%5D.ttf',
    'NotoSansJP': 'notosansjp/NotoSansJP%5Bwght%5D.ttf',
    'NotoSansKR': 'notosanskr/NotoSansKR%5Bwght%5D.ttf',
    'Caveat': 'caveat/Caveat%5Bwght%5D.ttf',
}
# Language names shown in Options > Language in every language (MareOptions.cpp KnownCultures).
NAMES = '简体中文日本語한국어РусскийČeštinaRomânăMagyar'
PUNCT = '，。、；：？！“”‘’（）《》【】「」『』…—·～　０１２３４５６７８９％＋－×'


def texts(lang):
    p = LOC / f'{lang}.json'
    if not p.exists():
        return ''
    d = json.loads(p.read_text(encoding='utf-8'))
    return ''.join(d.get('loctext', {}).values()) + ''.join(d.get('strings', {}).values())


def build(name, chars, weight):
    src = SRC / urllib.request.url2pathname(SOURCES[name].split('/')[-1])
    if not src.exists():
        src = SRC / SOURCES[name].split('/')[-1]
    font = TTFont(str(src))
    if 'fvar' in font:
        font = instancer.instantiateVariableFont(font, {'wght': weight})
    opts = subset.Options()
    opts.layout_features = ['*']
    opts.name_IDs = ['*']
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    out = FONTS / f'{name}-Mare.ttf'
    font.save(str(out))
    print(f'{out.name}: {len(set(chars))} caracteres, {out.stat().st_size // 1024} KB')


def main():
    if '--download' in sys.argv:
        SRC.mkdir(parents=True, exist_ok=True)
        for rel in SOURCES.values():
            dst = SRC / rel.split('/')[-1]
            if not dst.exists():
                urllib.request.urlretrieve(GF + rel, dst)
    latin = ''.join(chr(c) for c in range(0x20, 0x17F))
    zh, ja, ko, ru = texts('zh-Hans'), texts('ja'), texts('ko'), texts('ru')
    build('NotoSansSC', latin + PUNCT + NAMES + zh, 500)
    build('NotoSansJP', latin + PUNCT + NAMES + ja, 500)
    build('NotoSansKR', latin + PUNCT + NAMES + ko, 500)
    cyr = ''.join(c for c in ru + NAMES if 0x400 <= ord(c) <= 0x52F) + ''.join(chr(c) for c in range(0x410, 0x450)) + 'Ёё'
    build('Caveat', latin + cyr, 500)


if __name__ == '__main__':
    main()

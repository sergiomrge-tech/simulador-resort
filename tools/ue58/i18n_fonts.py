"""Fallback fonts for the translations, cut down to the characters the game uses (MareNotebookStyle.h loads them).

Patrick Hand (titles) and Nunito (text) cover the Latin languages; Patrick Hand has no Cyrillic, and neither has CJK.
  Caveat (OFL)      -> Cyrillic for the handwritten titles
  Noto Sans SC/JP/KR (OFL) -> Chinese / Japanese kana + kanji / Korean hangul
Run after every translation change (needs fontTools):
  <venv python> tools/ue58/i18n_fonts.py [--download]
Source fonts default to D:/CodexTemp/fonts-dl; --source-dir overrides it on Linux or Windows.
Use --families NotoSansSC NotoSansJP NotoSansKR to rebuild only CJK. --download fetches sources and OFL licenses.
"""
import argparse
import json
import shutil
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
    FONTS.mkdir(parents=True, exist_ok=True)
    font.save(str(out))
    license_file = SRC / f'OFL-{name}.txt'
    if license_file.exists():
        shutil.copyfile(license_file, FONTS / license_file.name)
    print(f'{out.name}: {len(set(chars))} caracteres, {out.stat().st_size // 1024} KB')


def main():
    global SRC
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=SRC, help='Cache local das fontes completas; padrão preserva D:/CodexTemp/fonts-dl')
    parser.add_argument('--families', nargs='+', choices=list(SOURCES), default=list(SOURCES))
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    SRC = args.source_dir
    if args.download:
        SRC.mkdir(parents=True, exist_ok=True)
        for name in args.families:
            rel = SOURCES[name]
            dst = SRC / rel.split('/')[-1]
            if not dst.exists():
                urllib.request.urlretrieve(GF + rel, dst)
            license_path = SRC / f'OFL-{name}.txt'
            if not license_path.exists():
                urllib.request.urlretrieve(GF + rel.rsplit('/',1)[0] + '/OFL.txt', license_path)
    latin = ''.join(chr(c) for c in range(0x20, 0x17F))
    zh, ja, ko, ru = texts('zh-Hans'), texts('ja'), texts('ko'), texts('ru')
    # 09/11: the language page before the menu shows each language's own texts in any culture; out of 'ja' the kanji are
    # drawn by the Chinese font (MareNotebookStyle.h), so it also carries the Japanese page texts (選択, 変更, 確定).
    page = ('Escolha seu idioma', 'Você pode mudar depois em Opções.', 'Confirmar')
    ja_page = ''.join(json.loads((LOC / 'ja.json').read_text(encoding='utf-8')).get('strings', {}).get(k, '') for k in page) if (LOC / 'ja.json').exists() else ''
    if 'NotoSansSC' in args.families:build('NotoSansSC', latin + PUNCT + NAMES + zh + ja_page, 500)
    if 'NotoSansJP' in args.families:build('NotoSansJP', latin + PUNCT + NAMES + ja, 500)
    if 'NotoSansKR' in args.families:build('NotoSansKR', latin + PUNCT + NAMES + ko, 500)
    cyr = ''.join(c for c in ru + NAMES if 0x400 <= ord(c) <= 0x52F) + ''.join(chr(c) for c in range(0x410, 0x450)) + 'Ёё'
    if 'Caveat' in args.families:build('Caveat', latin + cyr, 500)


if __name__ == '__main__':
    main()

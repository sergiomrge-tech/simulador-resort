"""Fills the runtime pieces of Content/Data/i18n_pieces.json in every language after tools/ue58/i18n_extract.py
added them empty (09/11). Run: python tools/ue58/i18n_extract.py && python tools/ue58/i18n_fill_pieces.py"""
import json
from pathlib import Path

LOC = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/Content/Localization/Mare'
LANGS = ['de', 'en', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt-PT', 'ru', 'zh-Hans']
T = {
    '{0}h às {1}h': ['{0} bis {1} Uhr', '{0}h to {1}h', '{0}h a {1}h', '{0}h à {1}h', 'dalle {0} alle {1}', '{0}時～{1}時', '{0}시~{1}시',
                     '{0}u tot {1}u', '{0}:00–{1}:00', '{0}h às {1}h', 'с {0}:00 до {1}:00', '{0}点至{1}点'],
    'Dormir e encerrar o dia': ['Schlafen und den Tag beenden', 'Sleep and end the day', 'Dormir y terminar el día', 'Dormir et finir la journée',
                                'Dormire e chiudere la giornata', '寝て一日を終える', '잠자고 하루 마치기', 'Slapen en de dag afsluiten',
                                'Śpij i zakończ dzień', 'Dormir e terminar o dia', 'Лечь спать и завершить день', '睡觉并结束这一天'],
    'Jogo salvo no slot {0}.': ['Spiel auf Platz {0} gespeichert.', 'Game saved in slot {0}.', 'Partida guardada en la ranura {0}.',
                                "Partie sauvegardée sur l'emplacement {0}.", 'Partita salvata nello slot {0}.', 'スロット {0} に保存しました。',
                                '슬롯 {0}에 저장했습니다.', 'Spel opgeslagen in slot {0}.', 'Gra zapisana w slocie {0}.', 'Jogo guardado no espaço {0}.',
                                'Игра сохранена в слот {0}.', '游戏已保存到存档 {0}。'],
    'Left Shift': ['Umschalt links', 'Left Shift', 'Mayús izq.', 'Maj gauche', 'Maiusc sinistro', '左Shift', '왼쪽 Shift', 'Linker Shift',
                   'Lewy Shift', 'Shift esquerdo', 'Левый Shift', '左Shift'],
    'Left Ctrl': ['Strg links', 'Left Ctrl', 'Ctrl izq.', 'Ctrl gauche', 'Ctrl sinistro', '左Ctrl', '왼쪽 Ctrl', 'Linker Ctrl',
                  'Lewy Ctrl', 'Ctrl esquerdo', 'Левый Ctrl', '左Ctrl'],
    'Right Shift': ['Umschalt rechts', 'Right Shift', 'Mayús der.', 'Maj droite', 'Maiusc destro', '右Shift', '오른쪽 Shift', 'Rechter Shift',
                    'Prawy Shift', 'Shift direito', 'Правый Shift', '右Shift'],
    'Right Ctrl': ['Strg rechts', 'Right Ctrl', 'Ctrl der.', 'Ctrl droite', 'Ctrl destro', '右Ctrl', '오른쪽 Ctrl', 'Rechter Ctrl',
                   'Prawy Ctrl', 'Ctrl direito', 'Правый Ctrl', '右Ctrl'],
    'passo {0}/{1}': ['Schritt {0}/{1}', 'step {0}/{1}', 'paso {0}/{1}', 'étape {0}/{1}', 'passo {0}/{1}', 'ステップ {0}/{1}', '{0}/{1}단계',
                      'stap {0}/{1}', 'krok {0}/{1}', 'passo {0}/{1}', 'шаг {0}/{1}', '第 {0}/{1} 步'],
    'faltam R$ {0}': ['noch R$ {0}', 'R$ {0} to go', 'faltan R$ {0}', 'encore R$ {0}', 'mancano R$ {0}', 'あと R$ {0}', 'R$ {0} 남음',
                      'nog R$ {0}', 'brakuje R$ {0}', 'faltam R$ {0}', 'осталось R$ {0}', '还差 R$ {0}'],
    # 09/11 (C7) loading screen
    'Dica': ['Tipp', 'Tip', 'Consejo', 'Astuce', 'Suggerimento', 'ヒント', '팁', 'Tip', 'Wskazówka', 'Dica', 'Совет', '提示'],
    'Carregando...': ['Lädt...', 'Loading...', 'Cargando...', 'Chargement...', 'Caricamento...', '読み込み中...', '불러오는 중...',
                      'Laden...', 'Ładowanie...', 'A carregar...', 'Загрузка...', '加载中...'],
}
# Derived from existing translations of the same words
DERIVED = {'Fama {0}': ('Fama {0} · ', lambda v: v.rstrip().rstrip('·').rstrip()),
           'Food truck do Pastel': ('Food truck do pastel', lambda v: v[:1].upper() + v[1:]),
           'ducha antes de entrar': ('tome uma ducha antes de entrar', lambda v: v)}
PT_PT = {'ducha antes de entrar': 'duche antes de entrar'}
for i, lang in enumerate(LANGS):
    p = LOC / f'{lang}.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    s = d['strings']
    for key, values in T.items():
        if key in s and not s[key]:
            s[key] = values[i]
    for key, (src, fn) in DERIVED.items():
        if key in s and not s[key] and s.get(src):
            s[key] = PT_PT.get(key, fn(s[src])) if lang == 'pt-PT' else fn(s[src])
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    empty = [k for k, v in s.items() if not v]
    print(lang, 'empty:', len(empty), empty[:5])

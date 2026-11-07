"""Read-only length audit of Mare localization catalogs (standard library only).

python tools/ue58/i18n_length_audit.py --output docs/ue58/I18N_TAMANHO.json
The input catalogs are never rewritten. Suggestions are editorial artifacts,
not translations installed in the game. Counts use NFC code points of visible
text; <br> is one newline, other markup is removed, format tokens are retained.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
CATALOGS = ROOT / 'unreal/MareAlta/Content/Localization/Mare'
TOKEN = re.compile(r'\{\d+\}|%[-+#0]*\d*(?:\.\d+)?(?:ll|l|h)?[sdifgu](?![A-Za-z])')


def visible(text: str) -> str:
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    return unicodedata.normalize('NFC', re.sub(r'<[^>]+>', '', text))


def cells(text: str) -> int:
    # A risk heuristic, not Slate shaping/font measurement.
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in visible(text))


def is_expanded(source: str, translated: str) -> bool:
    a, b = len(visible(source)), len(visible(translated))
    # Strictly MORE than both limits; integer arithmetic avoids 30% rounding.
    return 10 * b > 13 * a and b - a > 25


def entries(source: dict):
    for key, text in source['loctext'].items():
        yield 'loctext', key, text
    for text in source['strings']:
        yield 'strings', text, text


def risk(section: str, text: str, translated: str) -> str:
    if text.startswith(('QA:', 'QA ', 'People ', 'Local lights ', 'Draw distance ', 'Night EV100', 'Everyday ', 'MetaHuman ', 'Volcano ')):
        return 'técnico: confirmar exposição; não é botão de jogador'
    a, b = len(visible(text)), len(visible(translated))
    if '\n' in visible(text) or '\n' in visible(translated) or a > 180:
        return 'cartão/diálogo: quebra e rolagem'
    if a <= 48 and b > 48:
        return 'texto curto: conferir botão/cartão no contexto'
    return 'cartão/aviso: conferir largura no celular'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def audit(catalogs: Path, top: int = 50) -> dict:
    source_path = catalogs / 'source.json'
    source = load(source_path)
    rows = list(entries(source))
    result = {'schema_version': 1, 'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'method': 'NFC, <br> = newline, other tags removed; placeholders retained; strict >30% AND >25 code points; rank extra chars desc, ratio desc, section, key. Width is heuristic, not rendered QA.',
              'source_entries': len(rows), 'source_loctext': len(source['loctext']),
              'source_strings': len(source['strings']), 'languages': {}}
    for path in sorted(catalogs.glob('*.json')):
        if path.stem == 'source' or path.stem.startswith('todo_'):
            continue
        data = load(path)
        expanded, missing, token_errors, wide_only = [], [], [], []
        for section, key, text in rows:
            translation = data.get(section, {}).get(key, '')
            if not isinstance(translation, str) or not translation:
                missing.append({'section': section, 'key': key})
                continue
            if Counter(TOKEN.findall(text)) != Counter(TOKEN.findall(translation)):
                token_errors.append({'section': section, 'key': key, 'source': text, 'translation': translation})
            a, b = len(visible(text)), len(visible(translation))
            row = {'section': section, 'key': key, 'source': text, 'translation': translation,
                   'pt_chars': a, 'translated_chars': b, 'extra_chars': b-a,
                   'ratio': round(b / a, 6) if a else None, 'risk': risk(section, text, translation)}
            if is_expanded(text, translation):
                expanded.append(row)
            elif cells(translation) - cells(text) > 25 and 10 * cells(translation) > 13 * cells(text):
                wide_only.append(row)
        expanded.sort(key=lambda r: (-r['extra_chars'], -(r['ratio'] or 0), r['section'], r['key']))
        wide_only.sort(key=lambda r: (-(cells(r['translation'])-cells(r['source'])),r['section'],r['key']))
        result['languages'][path.stem] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'checked': len(rows), 'translated': len(rows)-len(missing), 'expanded_count': len(expanded),
            'top': expanded[:top], 'all_expanded': expanded, 'missing': missing,
            'placeholder_mismatches': token_errors, 'width_only_count': len(wide_only), 'width_only_top': wide_only[:10]}
    return result


def self_test():
    assert not is_expanded('a'*100, 'b'*130)  # exactly 30%
    assert not is_expanded('a'*40, 'b'*65)  # exactly 25 more
    assert is_expanded('a'*40, 'b'*66)
    assert visible('Cafe\u0301<br>R$ {0}') == 'Café\nR$ {0}'
    assert cells('海') == 2 and len(visible('海')) == 1
    assert not TOKEN.findall('90% do preço, 15% a mais, 100% e fama')
    assert TOKEN.findall('Receber %d VIP, nota %.1f') == ['%d', '%.1f']
    assert TOKEN.findall('%d명') == ['%d']
    assert Counter(TOKEN.findall('{0} + {0}')) != Counter(TOKEN.findall('{0}'))
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        folder=Path(directory)
        samples={'source':{'loctext':{'X,A':'a'*40},'strings':['Pagar {0}']},
                 'en':{'loctext':{'X,A':'b'*66},'strings':{'Pagar {0}':'Pay {0}'}},
                 'ja':{'loctext':{},'strings':{'Pagar {0}':'支払う'}}}
        for name,data in samples.items():
            (folder/(name+'.json')).write_text(json.dumps(data),encoding='utf-8')
        before={p.name:p.read_bytes() for p in folder.iterdir()}
        value=audit(folder)
        assert value['languages']['en']['expanded_count']==1
        assert len(value['languages']['ja']['missing'])==1
        assert len(value['languages']['ja']['placeholder_mismatches'])==1
        assert before=={p.name:p.read_bytes() for p in folder.iterdir()}
        proposals={'source_sha256':value['source_sha256'],'languages':{
            'en':[{'section':'loctext','key':'X,A','current':'b'*66,'suggestion':'short'}]}}
        render_report(value,proposals)
        from copy import deepcopy
        for mutation in ('stale','not-shorter','lost-token'):
            candidate=deepcopy(proposals)
            mutated=deepcopy(value)
            if mutation=='stale':
                candidate['source_sha256']='bad'
            elif mutation=='not-shorter':
                candidate['languages']['en'][0]['suggestion']='b'*66
            else:
                row=mutated['languages']['en']['top'][0]
                row['source']='a'*37+'{0}'
                candidate['languages']['en'][0]['suggestion']='short'  # loses {0}
            try:
                render_report(mutated,candidate)
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid suggestion accepted: '+mutation)
    print('i18n_length_audit self-test: PASS')


def markdown_cell(text: str) -> str:
    return text.replace('\\', '\\\\').replace('|', '\\|').replace('\r', '').replace('\n', ' ⏎ ').replace('<', '&lt;').replace('>', '&gt;')


def render_report(result: dict, suggestions: dict) -> str:
    if suggestions.get('source_sha256') != result['source_sha256']:
        raise ValueError('Suggestions refer to a different source catalog')
    lines=['# Auditoria de tamanho das traduções — Pacote 5', '',
           'Referência editorial: 07/11/2026; base `2bea4d2d`. Fontes em `unreal/MareAlta/Content/Localization/Mare/`. Nenhuma chave ou tradução foi alterada.', '',
           '## Método e limites', '',
           f"Foram comparadas **{result['source_entries']} entradas por idioma**, incluindo {result['source_loctext']} LOCTEXT e {result['source_strings']} strings. O gatilho exige simultaneamente **mais de 30% e mais de 25 caracteres extras**. Conta-se NFC visível: `<br>` vale uma quebra; outras tags não contam; espaços e marcadores continuam contando. Ordenação: caracteres extras decrescentes, razão decrescente, seção e chave.", '',
           'Cada lista contém até os **50 piores** que realmente atingem ambos os limites. Nenhum idioma possui 50 casos; não foram inventados candidatos para completar a lista. O JSON irmão guarda todos os casos e hashes SHA-256. `I18N_SUGESTOES_CURTAS.json` guarda as propostas completas, separadas dos catálogos do jogo.', '',
           'Comprimento é triagem, não teste de recorte. Os locais indicados como botão/cartão são hipóteses pelo texto, não inspeção do widget. O Claude precisa medir fonte, escala, placeholders expandidos e quebras em 1280×720 e 1920×1080, teclado/controle, e verificar celular vertical com texto grande. Zero casos em japonês/chinês/coreano não prova que cabem: caracteres de largura dupla exigem inspeção. As versões curtas são sugestões editoriais; revisão nativa e teste visual continuam pendentes.', '',
           '## Resultado por idioma', '',
           '| Idioma | Entradas | Acima dos dois limites | Exibidas | Faltantes | Marcadores divergentes |',
           '|---|---:|---:|---:|---:|---:|']
    for lang,data in result['languages'].items():
        lines.append(f"| {lang} | {data['checked']} | {data['expanded_count']} | {len(data['top'])} | {len(data['missing'])} | {len(data['placeholder_mismatches'])} |")
    for lang,data in result['languages'].items():
        lines += ['',f'## {lang}', '']
        if not data['top']:
            lines += ['Nenhuma entrada ultrapassa simultaneamente os dois limites. Manter teste visual; não significa ausência de risco em botões curtos.', '']
            continue
        indexed={(row['section'],row['key']):row for row in suggestions.get('languages',{}).get(lang,[])}
        lines += [f"Arquivo: `unreal/MareAlta/Content/Localization/Mare/{lang}.json`. **{len(data['top'])} de até 50** casos.", '',
                  '| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |',
                  '|---|---|---|---|---|---:|---|']
        for index,row in enumerate(data['top'],1):
            proposal=indexed.get((row['section'],row['key']))
            if not proposal or proposal['current']!=row['translation']:
                raise ValueError(f'Missing or stale suggestion: {lang}/{row["key"]}')
            short=proposal['suggestion']
            if len(visible(short))>=row['translated_chars']:
                raise ValueError(f'Suggestion is not shorter: {lang}/{row["key"]}')
            if Counter(TOKEN.findall(short))!=Counter(TOKEN.findall(row['source'])):
                raise ValueError(f'Placeholders changed in suggestion: {lang}/{row["key"]}')
            # Keep whitespace of concatenated fragments; it is significant at runtime.
            for current,proposed in ((row['translation'],short),(row['source'],short)):
                if bool(current[:1].isspace())!=bool(proposed[:1].isspace()) or bool(current[-1:].isspace())!=bool(proposed[-1:].isspace()):
                    raise ValueError(f'Fragment whitespace changed: {lang}/{row["key"]}')
            lines.append(f"| {index} / {row['section']} | {markdown_cell(row['source'])} | {markdown_cell(row['translation'])} | {row['pt_chars']} → {row['translated_chars']}; +{row['extra_chars']}, +{(row['ratio']-1)*100:.1f}% | {markdown_cell(short)} | {len(visible(short))} | {row['risk']} |")
    lines += ['', '## Suplemento: largura estimada em coreano', '',
              'Os dois casos abaixo **não** atingem o corte por número de caracteres. A largura estimada Unicode os sinalizou porque Hangul ocupa mais espaço. A contagem de células não substitui a fonte da Unreal.', '',
              '| pt-BR | Coreano atual | Sugestão em coreano |', '|---|---|---|']
    for row in suggestions.get('width_only',{}).get('ko',[]):
        if Counter(TOKEN.findall(row['suggestion']))!=Counter(TOKEN.findall(row['key'])):
            raise ValueError('Width-only suggestion changes placeholders')
        lines.append('| '+' | '.join(markdown_cell(row[k]) for k in ('key','current','suggestion'))+' |')
    lines += ['', '## Aplicação pelo Claude', '',
              '1. Confirmar o local real da string. Não aplicar texto curto de diálogo a uma instrução diferente.',
              '2. Manter as chaves pt-BR. Alterar valores traduzidos só depois da revisão e propagar futuras mudanças do português nos 12 idiomas.',
              '3. Preservar `{0}`, `{1}`, `%d`, `%.1f`, R$, números, atalhos e espaços dos fragmentos. Não reduzir texto cortando no meio nem removendo instruções de segurança ou custo.',
              '4. Usar quebra/rolagem nos diálogos longos, dimensionar botões ao conteúdo e testar valores máximos. Não diminuir todas as fontes para esconder problemas.',
              '', '## Reprodução', '', '```sh',
              'python tools/ue58/i18n_length_audit.py --self-test',
              'python tools/ue58/i18n_length_audit.py --output docs/ue58/I18N_TAMANHO.json --suggestions docs/ue58/I18N_SUGESTOES_CURTAS.json --report docs/ue58/REVISAO_TRADUCOES_TAMANHO.md',
              '```', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogs', type=Path, default=CATALOGS)
    parser.add_argument('--top', type=int, default=50)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--suggestions', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args=parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.top < 1:
        parser.error('--top must be positive')
    if args.output and args.output.resolve().is_relative_to(args.catalogs.resolve()):
        parser.error('output must be outside input catalog directory')
    if args.report and not args.suggestions:
        parser.error('--report requires --suggestions')
    for output in (args.output,args.report):
        if output and output.resolve().is_relative_to(args.catalogs.resolve()):
            parser.error('outputs must be outside the catalog directory')
    result=audit(args.catalogs,args.top)
    if args.report:
        report=render_report(result,load(args.suggestions))
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(report,encoding='utf-8')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for lang, data in result['languages'].items():
        print(f"{lang}: {data['checked']} checked, {data['expanded_count']} expanded; top {len(data['top'])}; missing {len(data['missing'])}; token errors {len(data['placeholder_mismatches'])}; width only {data['width_only_count']}")


if __name__=='__main__':
    main()

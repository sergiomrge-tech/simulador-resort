"""Stop hook: keeps the work going while docs/ue58/PENDENCIAS_100.md has open items.

Open = lines "- [ ]" or "- [~]" without the tag [bloqueado-usuario] (items only Sergio can unblock).
When none are left, it asks for the full-game simulation and its new checklist
(docs/ue58/CHECKLIST_SIMULACAO.md); once that file exists it lets the session stop.
Escape hatch: create D:/CodexTemp/claude/PARAR_CHECKLIST. While a long background job runs, a marker
D:/CodexTemp/claude/AGUARDANDO younger than 45 min lets the session pause until the job wakes it. Only acts in the MareAltaUE58 checkout.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r'D:\Projetos\MareAltaUE58')
PENDING = ROOT / 'docs' / 'ue58' / 'PENDENCIAS_100.md'
SIMULATION = ROOT / 'docs' / 'ue58' / 'CHECKLIST_SIMULACAO.md'
ESCAPE = Path(r'D:\CodexTemp\claude\PARAR_CHECKLIST')
# Waiting on a long background job (build, full simulation) that will wake the session: a fresh marker lets it pause.
WAITING = Path(r'D:\CodexTemp\claude\AGUARDANDO')


def main():
    try:
        data = json.loads(sys.stdin.read() or '{}')
    except ValueError:
        data = {}
    cwd = str(data.get('cwd', '')).replace('\\', '/').lower()
    if 'mareAltaue58'.lower() not in cwd or ESCAPE.exists() or not PENDING.exists():
        return
    import time
    if WAITING.exists() and time.time() - WAITING.stat().st_mtime < 45 * 60:
        return
    def open_lines(path, section=None):
        """Open items of a checklist; with section, only those under that '## <section>' heading."""
        out, inside = [], section is None
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if section is not None and line.startswith('## '):
                inside = line.startswith('## ' + section)
            if inside and re.match(r'\s*- \[( |~)\]', line) and '[bloqueado-usuario]' not in line:
                out.append(re.sub(r'\s+', ' ', line.strip())[:160])
        return out

    # Order asked by Sergio (03/11): general correction (section 0, which ends with the full-game simulation),
    # then every error of the simulation checklist, and only then the rest (new mechanics).
    first = open_lines(PENDING, '0.')
    sim = open_lines(SIMULATION) if SIMULATION.exists() else []
    rest = [l for l in open_lines(PENDING) if l not in first]
    open_items = first or sim or rest
    where = ('seção 0 (correção geral) de docs/ue58/PENDENCIAS_100.md' if first else
             'docs/ue58/CHECKLIST_SIMULACAO.md (erros da simulação)' if sim else 'docs/ue58/PENDENCIAS_100.md')
    if open_items:
        reason = (f'{len(open_items)} itens abertos em {where}. '
                  'Continue sem parar com o próximo item (implementar, verificar por captura/teste, '
                  'marcar [x], commit e push). Próximos: ' + ' | '.join(open_items[:3]) +
                  ' — Item que só o Sergio pode destravar (ex.: login com senha): marque a linha com [bloqueado-usuario] e siga.')
    elif not SIMULATION.exists():
        reason = ('Checklist concluído. Agora rode a simulação do jogo inteiro (do começo ao Grand Hotel, '
                  'todos os sistemas) e escreva docs/ue58/CHECKLIST_SIMULACAO.md com os erros e pendências encontrados.')
    else:
        return
    print(json.dumps({'decision': 'block', 'reason': reason}))   # ASCII escapes: safe on any console code page


if __name__ == '__main__':
    main()

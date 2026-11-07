#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capturas REAIS 1920x1080 da demo + planos do trailer, com Unreal Editor e MCP abertos.

Preparação manual obrigatória: abrir projeto UE 5.8 no PC de testes, servidor MCP ativo,
PIE rodando em perfil QA/slot DESCARTÁVEL, janela 1920x1080 (16:9), idioma definido,
shaders prontos, iluminação aprovada. O script NAO cria imagens sintéticas, não faz
composição de arte, não troca o perfil pessoal e rejeita saída != 1920x1080.

Listagem segura sem editor: python tools/ue58/qa/marketing_shots.py --plan
Execução de captura em save QA: python tools/ue58/qa/marketing_shots.py --capture --qa-save-confirmed
Para fotografar todas as cenas com pessoas, carta, menus reais e minijogos, acrescentar
--interactive (o operador prepara cada enquadramento e confirma). --camera-json permite
sobrescrever câmeras com {"01_quiosque":{"x":...,"y":...,"z":...,"pitch":...,"yaw":...}}.
O script salva os 10 nomes de capturas (e 12 planos de trailer) e registra rejeições
em report.json. É infraestrutura de QA, NÃO homologação artística nem legal da build.

Proibido rodar com save real; mare.QA compra expansões, mare.PoolSwim força NPCs,
coast('clock') altera a hora. Não usar para medir duração orgânica de ~2 horas.
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import qa_gate  # noqa: E402
import pool_swim_qa  # noqa: E402
from mcp_client import UnrealClient  # noqa: E402

# Câmara da função coast('pie'): posição real do pawn em cm e pitch/yaw em graus.
# Presets apenas para os lugares aferidos em qa_gate.py/pool_swim_qa.py.
# Câmeras de outros locais devem ser verificadas in-editor antes de capturar.
SHOTS = [
    dict(id='01_quiosque', time=540, unlock=[], camera='3700,-1080,100,-12,-75',
         action='Atender cliente pelo lado interno, coco pronto na mão e mar ao fundo',
         ui='close', trailer=[2, 3, 4, 10], required='Produto real, NPC próximo e atendimento validado'),
    dict(id='02_carta_dilce', time=480, unlock=[], camera=None,
         action='Casa: carta verdadeira com Dona Dilce viva, valor R$ 1.000.000 e assinatura legível',
         ui='letter', trailer=[1], required='Só capturar após o Claude integrar a carta; não simular o texto'),
    dict(id='03_celular_financas', time=720, unlock=[], camera='3700,-1080,100,-12,-75',
         action='Celular: abrir finanças/dívida do save QA; valor verdadeiro e texto legível',
         ui='phone0', trailer=[5], required='Cartão de dívida integrado e valor consistente; não inventar pagamento'),
    dict(id='04_pousada', time=660, unlock=['pousada'], camera=None,
         action='Recepção da pousada, hóspede real negociando diária',
         ui='close', trailer=[6], required='Hóspede presente, negociação com custo correto'),
    dict(id='05_bar_coqueiro', time=1110, unlock=['bar'], camera=None,
         action='Bar do Coqueiro: drink, bancada e cliente do lado correto',
         ui='close', trailer=[6], required='Receita/resultado coerentes e utensílios apoiados'),
    dict(id='06_piscina_demo', time=840, unlock=['pool'], camera='0,-330,110,-14,90',
         action='Piscina da pousada com hóspedes/limpeza/picolés; SEM tobogã do hotel',
         ui='close', trailer=[7], required='Nadadores gerados sem câmera vê-los aparecer; corpos e cabelos corretos'),
    dict(id='07_pier_barco', time=600, unlock=['passeios'], camera=None,
         action='Píer: turistas com coletes e barco saindo',
         ui='close', trailer=[8], required='Bote real e NPCs embarcados; saída funcional'),
    dict(id='08_recife_snorkel', time=690, unlock=['passeios'], camera=None,
         action='Recife: turistas, corais e espécies em mergulho guiado',
         ui='close', trailer=[8], required='Cena submersa real, sem peixes acima da superfície'),
    dict(id='09_vila_rua', time=960, unlock=[], camera='4300,2900,100,-4,180',
         action='Vila: morador e negócio funcionando, diálogo ou favor real',
         ui='close', trailer=[9], required='NPC sem colisão e nome correto'),
    dict(id='10_mirante_pordosol', time=1050, unlock=['passeios'], camera=None,
         action='Mirante do farol: grupo de passeio e pôr do sol',
         ui='close', trailer=[10, 11], required='Sol e participantes na posição real da trilha'),
]
TRAILER = [
    (1, '00:00–00:06', 'Close carta/valor', '02_carta_dilce'),
    (2, '00:06–00:10', 'Quiosque e praia', '01_quiosque'),
    (3, '00:10–00:15', 'Placa fechado/aberto', '01_quiosque'),
    (4, '00:15–00:20', 'Pedido/coco/entrega', '01_quiosque'),
    (5, '00:20–00:25', 'Celular/dívida', '03_celular_financas'),
    (6, '00:25–00:31', 'Pousada e Bar do Coqueiro', '04_pousada+05_bar_coqueiro'),
    (7, '00:31–00:36', 'Piscina da demo', '06_piscina_demo'),
    (8, '00:36–00:42', 'Barco e recife', '07_pier_barco+08_recife_snorkel'),
    (9, '00:42–00:47', 'Diálogo de morador e favor', '09_vila_rua'),
    (10, '00:47–00:52', 'Quiosque melhorado ao entardecer', '01_quiosque'),
    (11, '00:52–00:56', 'Vista do Maré Alta', '10_mirante_pordosol'),
    (12, '00:56–01:00', 'Cartela editorial Steam (NÃO screenshot de gameplay)', 'editorial'),
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_png(path):
    if not path.exists():
        return 'arquivo ausente'
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.size != (1920, 1080):
                return f'resolução {im.size}; exigido 1920x1080'
            if im.mode not in ('RGB', 'RGBA'):
                return f'modo inesperado: {im.mode}'
    except Exception as exc:
        return f'PNG inválido ou Pillow indisponível: {exc}'
    return None


def command(text):
    return qa_gate.hud('cmd', text)


def wait_file(path, seconds=35):
    for _ in range(seconds):
        if path.exists() and path.stat().st_size > 10000:
            return True
        time.sleep(1)
    return False


def prepare_qa():
    # Todas as alterações feitas aqui são em save descartável, com confirmação CLI.
    command('r.SetRes 1920x1080w')
    command('mare.QA money 500000')
    # Dependências de expansão idênticas às da suíte de natação.
    for expansion in pool_swim_qa.CHAIN:
        command(f'mare.QA buy {expansion}')
    command('mare.QA buy passeios')
    command('mare.PoolSwim 6')
    # Cena de piscina: pessoas surgem fora do ângulo de visão, não na frente da câmera.
    qa_gate.coast('clock', '660')
    qa_gate.coast('pie', 'qa_marketing_away,0,-2500,200,0,-90')
    time.sleep(12)


def capture_scene(scene, folder, cameras, interactive):
    sid = scene['id']
    out = folder / f'{sid}_1920x1080.png'
    if interactive:
        print(f'\n{sid}: {scene["action"]}\nACEITE: {scene["required"]}')
        answer = input('Preparou a cena real? [s=sim / p=pular] ').strip().lower()
        if answer != 's':
            return {'id': sid, 'status': 'pulada', 'motivo': 'operador não aprovou a cena'}
    camera = cameras.get(sid, scene['camera'])
    if isinstance(camera, dict):
        camera = ','.join(str(camera[k]) for k in ('x', 'y', 'z', 'pitch', 'yaw'))
    if scene['time'] is not None:
        qa_gate.coast('clock', str(scene['time']))
    if camera:
        qa_gate.coast('pie', f'qa_{sid},{camera}')
        time.sleep(3)
    if scene['ui'] == 'letter':
        command('mare.ShowUI letter')
    elif scene['ui'].startswith('phone'):
        command('mare.ShowUI ' + scene['ui'])
    else:
        command('mare.ShowUI close')
    time.sleep(2)
    # mare.Shot fotografa a viewport com UI, sem pressupor preview; fallback coast toma quadro sem HUD.
    if out.exists():
        out.unlink()
    command('mare.Shot ' + out.as_posix())
    ok = wait_file(out)
    if not ok and camera and scene['ui'] == 'close':
        source = qa_gate.SHOTS / f'pie-qa_{sid}.png'
        if source.exists():
            source.unlink()
        qa_gate.coast('pie', f'qa_{sid}!,0,0,0,0,0')
        ok = wait_file(source)
        if ok:
            shutil.copy2(source, out)
    command('mare.ShowUI close')
    reason = validate_png(out) if ok else 'mare.Shot não gerou arquivo; revisar PIE/editor'
    return {'id': sid, 'status': 'rejeitada' if reason else 'capturada_para_revisao',
            'file': str(out) if out.exists() else None, 'reason': reason,
            'frame': 'captura real; aceitação artística e comercial pendente'}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--plan', action='store_true', help='Somente gerar plano JSON, sem conectar ao editor (padrão)')
    p.add_argument('--capture', action='store_true', help='Usar Unreal PIE real com MCP')
    p.add_argument('--qa-save-confirmed', action='store_true', help='Confirmo uso EXCLUSIVO de save descartável')
    p.add_argument('--interactive', action='store_true', help='Confirmar preparação/aceite de cada cena manualmente')
    p.add_argument('--camera-json', type=Path, help='Override das câmeras dos 10 planos')
    p.add_argument('--out', type=Path, default=Path('D:/CodexTemp/qa/marketing_shots'))
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    plan = {'base': 'docs/steam/trailer_roteiro.md', 'resolution': [1920, 1080],
            'screenshots': SHOTS, 'trailer': [{'n':n,'interval':when,'shot':title,'source':source}
                                          for n,when,title,source in TRAILER]}
    (a.out / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Plano: {a.out / "plan.json"} (10 capturas, 12 planos; imagens NÃO produzidas por --plan)')
    if not a.capture:
        return 0
    if not a.qa_save_confirmed:
        p.error('--capture exige --qa-save-confirmed; não usar saves pessoais')
    overrides = read_json(a.camera_json) if a.camera_json else {}
    qa_gate.c = UnrealClient()
    qa_gate.pie(True)
    prepare_qa()
    report = []
    try:
        for scene in SHOTS:
            report.append(capture_scene(scene, a.out, overrides, a.interactive))
            print(scene['id'], report[-1]['status'], report[-1].get('reason') or '')
    finally:
        command('mare.ShowUI close')
        command('mare.PoolSwim auto')
    results = {'resolution': [1920,1080], 'date': time.strftime('%Y-%m-%d %H:%M:%S'),
               'shots': report, 'trailer': TRAILER, 'approved': False,
               'note': 'Nenhuma cena é automaticamente aprovada para marketing; revisar enquadramento e direitos.'}
    (a.out / 'report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    failures = [r for r in report if r['status']!='capturada_para_revisao']
    print(f'Capturas geradas para revisão: {len(report)-len(failures)}/10; rejeitadas/puladas: {len(failures)}')
    return 0 if not failures else 2


if __name__ == '__main__':
    sys.exit(main())

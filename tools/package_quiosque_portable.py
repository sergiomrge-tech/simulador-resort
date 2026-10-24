"""Atualiza documentação e ZIP portátil sem incluir saves/configurações do jogador.

Executar após exportar/testar MareAltaResort.pck em build/rc2-playable.
O ZIP é preparado e verificado em D: antes de substituir o ZIP entregue em Downloads.
"""
from pathlib import Path
import argparse
import hashlib
import shutil
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--variant', choices=['base','passaros','refinado','louca'], default='base')
parser.add_argument('--output', type=Path, help='Destino opcional do ZIP, sem alterar a instalação')
options = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
PORTABLE = ROOT / 'build/rc2-playable'
STAGING = Path('D:/CodexTemp/marealta-quiosque-pratico')
variant_label = {'passaros':'Passaros_','refinado':'Refinado_','louca':'Louca_Balcao_'}.get(options.variant,'')
date_label = '2026-10-24' if options.variant=='louca' else '2026-10-23'
ZIP = options.output or Path('D:/Downloads') / ('MareAltaResort_1.1_RC2_' + variant_label + date_label + '.zip')

readme = '''MARÉ ALTA RESORT — 1.1.0 RC2 · ATUALIZAÇÃO 23/10/2026

Abra Jogar.vbs nesta pasta. O jogo guarda seu progresso em userdata/.
Para atualizar uma cópia anterior, substitua os arquivos do programa e mantenha
a pasta userdata/. O ZIP não inclui nem apaga saves.

NOVO NESTA REVISÃO
- Gestão no computador do balcão: E no monitor, seis áreas compactas. B só perto.
- Começa fechado: crie a empresa e use Abrir quiosque antes de receber clientes.
  Dormir fecha o quiosque novamente. A atualização preserva o progresso.
- Clientes pedem e retiram todos os itens no balcão antes de sentar à mesa.
- Balcão com madeira escura e base cinza, copos na bandeja, sem caixa branca,
  promoções com preços reais nas duas faces do expositor.
- Porta da casa abre/fecha com E e fecha após sair com o arco livre.
- Quadro HOJE com texto dentro da placa e acima do guarda-corpo, incluindo
  cardápio expandido. Cestos de vime com tampa encaixada, sem peça solta lateral.
- Cruzeiro detalhado: cabines com varandas, botes, radar e janelas iluminadas.
  Fica ancorado ao fundo à noite; o navio de madeira passa devagar de dia.
- Baleias saltando ao fundo, com respingos, espuma, ondas e som suave de queda.
  Nuvens no céu acompanham dia/noite e chuva. Animações respeitam a pausa.
- Um navio de madeira com velas por vez, passando devagar; cruzeiro ancorado à noite.
- Acabamento visual: contornos finos e discretos em pessoas, móveis e vegetação;
  água com cores naturais, transições suaves e espuma menos recortada;
  brilho noturno mais contido, preservando janelas e luminárias legíveis.
- Quiosque e mesas voltados para a praia. Anote/entregue aos dois clientes do
  balcão pelo lado de dentro. Mira nos clientes mais fácil, com número do pedido.
- Acabou um produto? E na geladeira/armário: Repor 10 mostra o preço dos insumos
  faltantes e compra ali mesmo. Depois pegue e entregue, sem etapa de preparo.
- Praia com quatro pessoas jogando vôlei, iate passando de dia e navio de
  cruzeiro iluminado ao fundo à noite. Quadra livre e barcos longe do cais/banho.
- Casa decorada com sofá, mesa de centro, TV, aparelho de som, estante,
  livros, relógio, planta e escultura de madeira. Modelos detalhados Poly Haven CC0.
- E na TV liga/desliga uma animação silenciosa do mar; E no som liga/desliga
  a música suave, com volume pela distância e respeito às configurações de áudio.
- Iluminação ambiente neutra no jogo inteiro, sem o banho azul do céu sobre
  paredes, móveis e pessoas. Madeira e materiais mantêm as texturas originais.
- Atendimento simplificado: pegue o produto pronto e entregue. Sem preparar,
  sem cronômetro. Compras abastecem o estoque; retirada desconta uma vez.
- Cores mais naturais no jogo inteiro: menor saturação, madeira/areia/telhas
  revisadas, menos aquecimento artificial. Porta da casa em madeira natural.
- Casa com piso claro, armários em tons suaves, pia/torneira, cortinas,
  persianas, molduras, prateleiras e iluminação neutra.
- Geladeira, armário, bancada e produtos aparecem mesmo antes de criar a empresa.
  E nos equipamentos orienta para o cadastro no computador quando necessário.
- Aventais ajustados ao corpo, com alças, cintura, bolso e dobras suaves;
  pesos contínuos no quadril para acompanhar as pernas ao andar e sentar.
- Sete refinamentos: roupas de praia, uniformes por função, aventais, gestos,
  piscadas, balcão equipado, sons suaves sem vozes e luz de entardecer/noite.
- Pessoas sem óculos escuros, chapéus ou bonés.
- Pessoas com proporções mais naturais, pele/cabelo suaves e roupas menos brilhantes.
- Refinamento: revestimento areia retangular e iluminação quente na área de trabalho.
- Quiosque com azulejos na cozinha, prateleira de madeira e coifa detalhada.
- Roupas com barra reta, sem cinto medieval; calçados baixos em cores neutras.
- Parede traseira de madeira com colisão, preservando as entradas laterais.
- Roupas Quaternius CC0 com pesos de animação originais, camisas, calças e calçados.
- Personagens sem chapéus ou bonés. Cabelos acompanham a cabeça ao sentar e andar.
- Funcionários do quiosque aparecem assim que contratados, inclusive fora do turno.
  Trabalham no horário configurado; funcionários de folga não comparecem.
- Geladeira com 12 bebidas expostas nas três prateleiras e etiquetas de estoque real.
- Quiosque refeito: geladeira, retirada de pratos, cozinha, caixa e liquidificador
  dentro da construção, com entrada pelas duas laterais. Sem anexo externo.
- Novo acabamento em madeira, cobertura de palha, luminárias de fibra e placa única.
- Computador com seis áreas: Quiosque, Compras, Equipe, Finanças, Resort, Vila e lazer.
- Pedidos numerados (#01...), lista discreta no canto e indicação de produto pronto.
- Textos e avisos menores; sem nomes grandes sobre as estações.

ATENDER
0. Abra o quiosque no computador. Espere o cliente escolher no balcão. Aproxime-se de quem tem E · #pedido e aperte E
   para anotar. O pedido aparece no HUD e no computador.
1. Entre pela lateral, mire na geladeira ou armário e aperte E.
2. Escolha Pegar e levar ao cliente. O produto vai imediatamente para sua mão.
3. E no cliente com o número/pedido correspondente para entregar.
4. O cliente leva o pedido inteiro à mesa. Receba as contas e recolha a louça.

Geladeira e armário sempre mostram os produtos vendidos, com etiquetas de estoque.
No zero, o exemplar de exposição fica visível e indica Repor estoque.
Use Compras para abastecer. Não é necessário preparar nenhum produto.
Detalhes: QUIOSQUE_PRATICO.md, ROTINAS_DO_QUIOSQUE.md e GESTAO_DO_QUIOSQUE.md.

CONTROLES
WASD andar · mouse olhar · E interagir · B gestão perto do computador · Shift correr · Esc menu
F11 tela cheia. O save de versões anteriores recebe os padrões compatíveis.

Inclui também as correções do cais, vidros neutros, barcos afastados do cais,
passos mais suaves e trilha sem vozes. A instalação antiga em D:/Games não é alterada.
'''
if options.variant in ('passaros','refinado','louca'):
    readme = readme.replace('NOVO NESTA REVISÃO\n','NOVO NESTA REVISÃO\n- Pássaros diurnos perto das árvores, com cantos direcionais suaves e intervalos.\n  Respeitam pausa, silêncio e volume de efeitos; silenciam à noite e na chuva.\n',1)
if options.variant in ('refinado','louca'):
    readme = readme.replace('NOVO NESTA REVISÃO\n','NOVO NESTA REVISÃO\n- Notebook detalhado CC0 com dados reais na tela, seis abas de gestão compactas.\n- Compras por produto: estoque atual, preço e Repor para 10, com entrega imediata.\n- Equipe com cartões compactos e botões legíveis; cardápio alinhado frente/verso.\n- Cabelos completos, circulação de moradores corrigida e ruas de pedra detalhadas.\n- Gatos e cães com olhos, focinho e boca; caminham e descansam com animação.\n',1)
if options.variant=='louca':
    readme=readme.replace('ATUALIZAÇÃO 23/10/2026','ATUALIZAÇÃO 24/10/2026')
    readme=readme.replace('NOVO NESTA REVISÃO\n','NOVO NESTA REVISÃO\n- Louça corresponde ao pedido consumido: suco deixa copo vazio, coco deixa o coco aberto.\n- Pratos/tigelas vazios para os alimentos; pedidos mistos deixam cada recipiente.\n- Registro preservado ao salvar/carregar; limpeza remove os objetos e libera a mesa.\n- Computador no centro do balcão, bandeja à esquerda e promoções à direita.\n',1)
(PORTABLE / 'LEIA-ME.txt').write_text(readme, encoding='utf-8')
for src, dst in [('QUIOSQUE_PRATICO.md','QUIOSQUE_PRATICO.md'),
                 ('ATUALIZACAO_2026-10-23.md','ATUALIZACAO_2026-10-23.md'),
                 ('COMPUTADOR_E_BALCAO.md','COMPUTADOR_E_BALCAO.md'),
                 ('PRAIA_E_ATENDIMENTO.md','PRAIA_E_ATENDIMENTO.md'),
                 ('ROTINAS_QUIOSQUE.md','ROTINAS_DO_QUIOSQUE.md'),
                 ('SIMULACAO_QUIOSQUE.md','GESTAO_DO_QUIOSQUE.md'),
                 ('REFINAMENTO_COMPLETO.md','REFINAMENTO_COMPLETO.md')]:
    shutil.copyfile(ROOT / 'docs' / src, PORTABLE / dst)

names = ['MareAltaResort.exe','MareAltaResort.pck','Jogar.vbs','LEIA-ME.txt',
         'ATUALIZACAO_2026-10-23.md',
         'PRAIA_E_ATENDIMENTO.md','COMPUTADOR_E_BALCAO.md',
         'QUIOSQUE_PRATICO.md','ROTINAS_DO_QUIOSQUE.md','GESTAO_DO_QUIOSQUE.md','REFINAMENTO_COMPLETO.md','icon.ico']
if options.variant in ('passaros','refinado','louca'):
    shutil.copyfile(ROOT / 'docs/PASSAROS.md', PORTABLE / 'PASSAROS.md')
    names.append('PASSAROS.md')
if options.variant in ('refinado','louca'):
    shutil.copyfile(ROOT / 'docs/REFINAMENTO_2026-10-23.md', PORTABLE / 'REFINAMENTO_2026-10-23.md')
    names.append('REFINAMENTO_2026-10-23.md')
if options.variant=='louca':
    shutil.copyfile(ROOT / 'docs/LOUCA_BALCAO_2026-10-24.md', PORTABLE / 'LOUCA_BALCAO_2026-10-24.md')
    names.append('LOUCA_BALCAO_2026-10-24.md')
checks = []
for name in names:
    with (PORTABLE / name).open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    checks.append(f'{digest}  {name}')
(PORTABLE / 'SHA256SUMS.txt').write_text('\n'.join(checks) + '\n',encoding='utf-8')
names.append('SHA256SUMS.txt')
STAGING.mkdir(parents=True,exist_ok=True)
staged = STAGING / ZIP.name
with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as z:
    for name in names:
        z.write(PORTABLE / name, 'MareAltaResort/' + name)
with zipfile.ZipFile(staged) as z:
    assert z.testzip() is None, 'ZIP CRC mismatch'
    assert len(z.namelist()) == len(names)
    assert not any('userdata' in name for name in z.namelist())
ZIP.parent.mkdir(parents=True,exist_ok=True)
if staged.resolve()!=ZIP.resolve(): shutil.copyfile(staged, ZIP)
print('PORTABLE_ZIP_OK', ZIP, ZIP.stat().st_size)
print(next(line for line in checks if line.endswith('MareAltaResort.pck')))

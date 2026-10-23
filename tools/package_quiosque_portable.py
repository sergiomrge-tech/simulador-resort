"""Atualiza documentação e ZIP portátil sem incluir saves/configurações do jogador.

Executar após exportar/testar MareAltaResort.pck em build/rc2-playable.
O ZIP é preparado e verificado em D: antes de substituir o ZIP entregue em Downloads.
"""
from pathlib import Path
import hashlib
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PORTABLE = ROOT / 'build/rc2-playable'
STAGING = Path('D:/CodexTemp/marealta-quiosque-pratico')
ZIP = Path.home() / 'Downloads/MareAltaResort_1.1_CaisCorrigido.zip'

readme = '''MARÉ ALTA RESORT — 1.1.0 RC2 · QUIOSQUE PRÁTICO

Abra Jogar.vbs nesta pasta. O jogo guarda seu progresso em userdata/.
Para atualizar uma cópia anterior, substitua os arquivos do programa e mantenha
a pasta userdata/. O ZIP não inclui nem apaga saves.

NOVO NESTA REVISÃO
- Sete refinamentos: roupas de praia, uniformes por função, aventais, gestos,
  piscadas, balcão equipado, sons suaves sem vozes e luz de entardecer/noite.
- Óculos menores com lentes ovais e armação escura, mais próximos do rosto.
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
- Celular com seis áreas: Quiosque, Compras, Equipe, Finanças, Resort, Vila e lazer.
- Pedidos numerados (#01...), lista discreta no canto e indicação de produto pronto.
- Textos e avisos menores; sem nomes grandes sobre as estações.

ATENDER
1. Entre pela lateral, mire na geladeira ou cozinha e aperte E.
2. Escolha Preparar; acompanhe o andamento na tela.
3. Quando pronto, E na geladeira ou retirada de pratos para pegar o produto.
4. E no cliente com o número/pedido correspondente para entregar.
5. Receba as contas no caixa e recolha a louça.

Geladeira e armário sempre mostram os produtos vendidos, com etiquetas de estoque.
No zero, o exemplar de exposição fica visível e indica Preparar mais. Prepare para
repor as unidades vendáveis; o exemplar não é vendido. Sem ingredientes, use Compras.
Detalhes: QUIOSQUE_PRATICO.md, ROTINAS_DO_QUIOSQUE.md e GESTAO_DO_QUIOSQUE.md.

CONTROLES
WASD andar · mouse olhar · E interagir · B celular · Shift correr · Esc menu
F11 tela cheia. O save de versões anteriores recebe os padrões compatíveis.

Inclui também as correções do cais, vidros neutros, barcos afastados do cais,
passos mais suaves e trilha sem vozes. A instalação antiga em D:/Games não é alterada.
'''
(PORTABLE / 'LEIA-ME.txt').write_text(readme, encoding='utf-8')
for src, dst in [('QUIOSQUE_PRATICO.md','QUIOSQUE_PRATICO.md'),
                 ('ROTINAS_QUIOSQUE.md','ROTINAS_DO_QUIOSQUE.md'),
                 ('SIMULACAO_QUIOSQUE.md','GESTAO_DO_QUIOSQUE.md'),
                 ('REFINAMENTO_COMPLETO.md','REFINAMENTO_COMPLETO.md')]:
    shutil.copyfile(ROOT / 'docs' / src, PORTABLE / dst)

names = ['MareAltaResort.exe','MareAltaResort.pck','Jogar.vbs','LEIA-ME.txt',
         'QUIOSQUE_PRATICO.md','ROTINAS_DO_QUIOSQUE.md','GESTAO_DO_QUIOSQUE.md','REFINAMENTO_COMPLETO.md','icon.ico']
checks = []
for name in names:
    with (PORTABLE / name).open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    checks.append(f'{digest}  {name}')
(PORTABLE / 'SHA256SUMS.txt').write_text('\n'.join(checks) + '\n',encoding='utf-8')
names.append('SHA256SUMS.txt')
STAGING.mkdir(parents=True,exist_ok=True)
staged = STAGING / ZIP.name
with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
    for name in names:
        z.write(PORTABLE / name, 'MareAltaResort/' + name)
with zipfile.ZipFile(staged) as z:
    assert z.testzip() is None, 'ZIP CRC mismatch'
    assert len(z.namelist()) == len(names)
    assert not any('userdata' in name for name in z.namelist())
shutil.copyfile(staged, ZIP)
print('PORTABLE_ZIP_OK', ZIP, ZIP.stat().st_size)
print(next(line for line in checks if line.endswith('MareAltaResort.pck')))

# Áudio, acabamento visual e prévia Windows — 28/10/2026

Pedido vigente: áudio completo e acabamento realista estilizado, incluindo natação
e um executável para teste. Projeto no D, branch `codex/ue58-migration`. Preservar
a instalação Godot aprovada e seus saves.

## Áudio nativo

41 SoundWave com fontes PCM editáveis em `unreal/MareAlta/SourceArt/Audio`.
38 sons vieram do áudio original/licenciado do repositório. Três sons de água são
síntese original de `tools/ue58/prepare_audio.py`, sem samples externos. O reggae
instrumental original foi preservado, sem música comercial ou vozes de fundo.

`UMareAudioWorld` combina música, ondas, vento, folhas, grilos e chuva. Pássaros e
gaivotas usam intervalos e atenuação espacial; pássaros silenciam à noite/chuva.
Há passos por superfície, entrada/movimento na água, filtro submerso, porta,
geladeira, retirada, pedido, pagamento, limpeza, celular e cliques. Sino, cachorro
e trovão respondem à localização/horário/clima. Sons de sistemas ainda não portados,
como o salto da baleia, ficam no catálogo para integração; isso não implementa
esses sistemas.

Esc contém volumes geral, música, efeitos e ambiente, persistidos no perfil UE.
Ambiente respeita efeitos. O volume geral controla o submix master, além do mute
das fontes, para silenciar também a cauda de efeitos. Loops mantêm a posição ao
ficar silenciosos. O mix reduz ambiente em interiores, filtra sob a água e respeita
a pausa. Limite de 16 vozes pontuais e intervalo mínimo por efeito.

## Refinamento visual

- Rotação de luzes, PlayerStart e câmeras corrigida. Usar sempre os argumentos
  `pitch=`, `yaw=`, `roll=` no Python: a ordem posicional desta instalação causou
  câmera apontada para o piso e luzes práticas orientadas lateralmente.
- Sol ligado ao relógio, luar suave e luzes práticas na casa/quiosque. Atualização
  a cada dois segundos evita reconstruir sombras a cada quadro.
- Exposição com margem para noite/sol físico, histograma revisto para preservar
  o exterior e preenchimento suave no interior. Texturas e cores preservadas,
  sem contorno toon. Sombras de contato e bloom discreto.
- Água com normais menos agressivas, ondas suaves e superfície sem colisão sólida.
- 111 Label3D exportados viraram TextRender, mais três faces internas de marca e
  status. Nome da empresa, aberto/fechado, preços e estoques respondem ao estado
  real. Promoções preservam cinco linhas para caber na placa, frente e verso.
- Caipirinha e petiscos incluídos na seleção nativa, mantendo produtos prontos,
  pagamento automático e retirada dentro do quiosque.
- Celular com resumo compacto de pedidos, equipe e oito estoques. Valores e saldo
  se atualizam sem reconstruir a página ou atrapalhar o campo de nome. A abertura
  antecipada indica o horário de atendimento, pode ser cancelada e não recebe
  clientes antes do expediente. O teste parte explicitamente das 10h para atender.

Não editar imagens de QA para simular melhoria. Depois de teleportar a câmera,
aguardar a estabilização temporal do Lumen; a captura imediata da casa tinha ruído
que não representava o resultado estável.

## Reprodução e cuidados

`AMarePreviewQA` exige `-MarePreviewQA` e perfil em `D:/CodexTemp/`. Testa teclas de
natação, terra, recuperação, catálogo de atores/sons, celular, pausa, save, noite,
chuva e restauração das configurações. Produz imagens e WAVs.

A UE5.8 grava o buffer do master antes do ganho de saída do submix. O teste também
confere roteamento do master e exige silêncio sustentado depois de estabilizarem
os buffers das fontes/efeitos. Não tratar essa captura como medição de latência
do hardware. PIE em segundo plano pode mutar o dispositivo: comparar com o jogo
fora do editor e, obrigatoriamente, com o pacote exportado.

Scripts: `tools/ue58/package_preview.ps1`, `test_preview_package.ps1`,
`check_audio_mix.py` e `assemble_preview.py`. A montagem da pasta/ZIP exige aprovação
funcional e visual no relatório; preserva instalações existentes e exclui userdata.

O primeiro cook preparou shaders em 25min10s. Usar `-iterativecooking` nos seguintes.
Não compilar a DLL enquanto editor/commandlet a mantém aberta, nem executar dois
UBT simultaneamente. Não alegar desempenho melhor sem medição. Abrir fontes Python
com encoding UTF-8 explícito: o Python da engine usa a página de código do Windows
como padrão e pode corromper acentos se read_text não especificar encoding.

## Estado da entrega

EXE Windows exportado com build/cook incremental/stage/archive concluídos.
22 verificações funcionais passaram fora do editor, incluindo o horário de
atendimento, natação, pausa, abertura, catálogos, save, noite e mix de chuva.
`MareAlta.Migration.NativeEconomy`: Success, 0 erros/avisos no relatório do teste.
O áudio foi medido no pacote: reprodução audível com pico abaixo de clipping,
silêncio sustentado com mute e pausa. Imagens reais revisadas de quiosque diurno e
noturno, casa, celular, pausa e água; sem montagem ou retoque.

Evidências em `docs/qa/ue58/av-package-20261028.json`,
`av-audio-mix-20261028.json`, `av-package-result-20261028.json`,
`native-economy-av-20261028.json` e imagens `av-20261028-*.png`.
Log de empacotamento: `D:/CodexTemp/ue58-package-audiovisual-20261028.log`.

Destino da pasta e ZIP: `D:/Downloads/MareAltaResort_UE58_AudioVisual_2026-10-28`.
Abrir `Jogar.vbs` ou `Jogar.cmd`. A prévia usa `userdata` ao lado do launcher;
essa pasta não entra no ZIP e não escreve na instalação Godot.

É uma prévia da migração. Permanecem outros negócios, atividades, salários,
capítulos restantes, clima completo e sistemas marinhos/animais. O herói usa câmera
em primeira pessoa, sem braços/corpo com animação de natação. Não substituir a
versão Godot aprovada por esta prévia.

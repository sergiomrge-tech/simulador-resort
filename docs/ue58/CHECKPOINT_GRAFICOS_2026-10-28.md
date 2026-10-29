# Checkpoint solicitado pelo usuário — 28/10/2026

**Retomado em 29/10:** o estado abaixo é histórico. Ler
[PENDENCIAS_2026-10-29.md](PENDENCIAS_2026-10-29.md) e
[GRAMADO_2026-10-29.md](GRAMADO_2026-10-29.md). Gramado já implementado e pacote
testado; o usuário pediu concluir todas as demais pendências, não parar neste lote.

O usuário pediu finalizar por limite. Não iniciar outros testes neste encerramento.
Projeto: `D:/Projetos/MareAltaUE58`, branch `codex/ue58-migration`.
Implementação gráfica até `47fe15b8`, já enviada ao GitHub. Nenhum editor ou jogo
estava rodando ao encerrar. As três pastas de Actors não rastreadas são anteriores;
não apagar nem adicionar sem investigação.

## Implementado

- Referência de configs/hardware e captura real, auditoria de 1.623 modelos.
- Nanite já existente preservado; dois candidatos rejeitados por transparência
  em Material Instances. Hotel derivado: 230.384 triângulos opacos Nanite +
  1.656 de vidro sem Nanite, fonte/colisor originais preservados. Bounds e soma
  dos triângulos conferidos; imagens reais antes/depois com mesma câmera.
- Lumen GI/reflexos software confirmados em execução. Qualidade ajustada e
  exposição adaptada a dia/noite, sem alteração de economia/gameplay.
- Plugin PCG, sete tipos de grafo e variantes leste (14 assets), 60 instâncias
  geradas no editor em duas faixas verdes, integradas em Coast. Mapa piloto
  `GraphicsPilot` preservado. Geração On Demand, bounds explícitos e NoCollision.
- Benchmark exportado em 1920x1080 nativo, commit `52fd8f51`: tudo ligado
  79,6 FPS médios, P95 16,203 ms, GPU 11,490 ms, numa câmera fixa do bosque.
  Os quatro cenários desse benchmark preservaram 60 instâncias e passaram no
  verificador sem erros de runtime/material. Isso não garante FPS em todo o mapa.

## Último pacote e validação pendente

`D:/Builds/MareAltaUE58_RenderIntegrado_2026-10-28/Windows`
foi compilado/empacotado com sucesso do commit `47fe15b8`. **Ainda não foi
executado/testado após a divisão do hotel.** Não anunciar como download final
nem sobrescrever instalações anteriores.

Retomar sequencialmente, sem outra cópia do jogo/editor disputando GPU:

1. `tools/ue58/test_graphics_package.ps1 -Package D:/Builds/MareAltaUE58_RenderIntegrado_2026-10-28/Windows -Hotel`
2. Analisar o diretório retornado com `tools/ue58/analyze_graphics_profile.py`.
   Esse teste inclui `hotel-legacy` para comparar o mesh original com o proxy
   Nanite; os testes anteriores desligavam Nanite globalmente, usando fallbacks.
3. Repetir benchmark padrão se necessário para a versão final.
4. `tools/ue58/test_preview_package.ps1 -Package D:/Builds/MareAltaUE58_RenderIntegrado_2026-10-28/Windows`
   Inspecionar as fotos de dia/noite, casa, quiosque, piscina, mar e materiais.
5. Validar áudio com `check_audio_mix.py`, e abertura com `test_intro_package.ps1`.
6. Conferir circulação e interiores reais de recepção/restaurante/quartos;
   esses setores ainda não receberam revisão individual completa de iluminação.
7. Atualizar relatório, commit/push e só então montar pacote/ZIP no D sem save
   antigo. O usuário dispensou preservar progresso para o próximo teste, mas
   não há necessidade de apagar seus arquivos anteriores.

Relatório principal: `GRAFICOS_AVANCADOS_2026-10-28.md`. Dados resumidos e imagens
versionados em `graphics-reference/`; CSVs e logs brutos em D:/CodexTemp.

A migração geral ainda tem pendências de gameplay/arte/abertura. Consultar também
`VARREDURA_EM_ANDAMENTO_2026-10-28.md`. Apresentar as três propostas de interface
somente depois de concluir os pedidos anteriores, conforme a ordem do usuário.

## Novo pedido do usuário — gerador de grama em toda a terra exposta

Registrado após o encerramento por limite; **ainda não implementado**.
O usuário quer um gerador de grama para toda área que não seja areia: cobrir o
piso onde hoje há somente terra, formando um gramado contínuo, sem ficar apenas
em pequenos tufos isolados com grandes espaços marrons entre eles.

Ao retomar:

- Integrar ao sistema PCG/material de terreno existente, com máscara de areia,
  terra e superfícies construídas. Cobrir toda a terra exposta apropriada do mapa,
  não apenas as duas faixas do piloto gráfico.
- Manter a praia de areia e sua transição natural para o gramado. Excluir pisos
  construídos, ruas, caminhos, interiores, piscinas, água, portas e áreas de
  interação; preservar circulação e rotas dos NPCs.
- Usar base de solo verde texturizada para cobertura contínua, complementada por
  grama 3D com densidade e altura naturais. Evitar terra marrom visível à distância
  por depender somente de tufos; não encobrir madeira, pedra ou areia com verde.
- Preservar a vegetação existente. Utilizar instâncias, distâncias de exibição e
  níveis de qualidade adequados à RTX4060Ti8GB, medindo o impacto real no frame.
- Conferir o resultado na câmera do jogador em várias regiões, perto e longe,
  de dia/noite e sob chuva; verificar navegação e não criar faixas brancas.

Este pedido deve entrar no próximo lote de trabalho junto às pendências acima.
O registro não representa implementação nem validação do gerador.

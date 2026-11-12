# Checkpoint de pausa — 29/10/2026

**Atualização posterior:** pequenos ajustes foram retomados e uma prévia foi
entregue. Ver [TESTE_VILA_2026-10-29.md](TESTE_VILA_2026-10-29.md): fonte 45cc1e69,
87 verificações e ZIP/pasta no D. As seções abaixo são histórico anterior a ela.

O usuário pediu finalizar e salvar porque o limite está acabando. **Pausar aqui.
Retomar somente após novo pedido.** Não tratar este checkpoint como migração
concluída. Nenhum editor, jogo ou build estava ativo ao encerrar.

## Repositório e referência testada

- Pasta: `D:/Projetos/MareAltaUE58`.
- Branch: `codex/ue58-migration`.
- GitHub: https://github.com/sergiomrge-tech/simulador-resort/tree/codex/ue58-migration
- Unreal 5.8.3 em `D:/UE_5.8`; alvo Windows/DX12/RTX 4060 Ti 8 GB.
- Última fonte testada no EXE: **`f7ab170d`**, precedida por `a646ebf0`.
- Pacote correspondente: `D:/Builds/MareAltaUE58_CasaAbertura_2026-10-29/Windows/MareAlta.exe`.
- 79/79 verificações; áudio audível/mute/pausa aprovado; abertura natural 12/12
  e avanço 11/11. Evidências em `PENDENCIAS_2026-10-29.md`.
- Perfil real do bosque após corpo/casa/abertura, 1920×1080 nativo:
  **75,8 FPS médios**, frame médio 13,195 ms, P95 14,561 ms, GPU 12,692 ms,
  game thread 3,707 ms, render thread 13,218 ms, memória local GPU ~3158 MB.
  Caminho: `D:/CodexTemp/ue58-render-profile-20261029-132139/summary.json`.
  Câmera fixa; não garante 60 FPS no mapa inteiro ou com a nova população.

## População em validação — testes iniciais PIE, ainda sem EXE novo

- `MareVillageWorld.h/.cpp`: subsistema separado do quiosque, cinco moradores
  físicos, pedestres nas rotas existentes, orçamento padrão 12/5 por qualidade,
  pausas/caminhada, diálogo compacto e registro de pessoas cumprimentadas.
- Integração em `MarePerson`, `MareServiceTarget` e `MareGame`: pessoas ambientes
  não entram nos pedidos do quiosque; E/Esc fecha diálogo e B evita sobreposição.
- Build de **MareAltaEditor Win64 Development aprovado** após essas alterações.
  Teste inicial PIE confirmou 5 moradores/12 pedestres e troca de aparência sem
  cabelo duplicado, com clip ativo. Ainda não há teste EXE da população.
- NavMesh existente ampliado para centro (5000,1800,250), extensões
  (6500,6000,1000). Rebuild real executado; rotas consultadas no editor.
- `village_routes.json`: oito rotas completas e cinco moradores projetados;
  três rotas antigas excluídas explicitamente por percurso parcial/fora da malha.
  Não usar trajetos rejeitados nem teleportar pessoas através de obstáculos.
- Ferramenta MCP `village_navigation(prepare/validate)` e módulo `mare_village.py`.
  Projeção pode retornar None: já tratado. O comando RebuildNavigation funcionou;
  não é necessário criar uma biblioteca C++ apenas para forçar essa reconstrução.

### Primeiros passos na retomada

1. Conferir Git, ler AGENTS, CONTINUAR, CLAUDE e este arquivo. O guia integral de
   pendências é `PENDENCIAS_2026-10-29.md`; históricos não substituem essa lista.
2. Executar a população em PIE com dados D:/CodexTemp separados. Conferir presença,
   aparência, circulação, paradas, pessoas presas, diálogo/E/Esc/B e persistência.
   Verificar que moradores/pedestres não viram clientes no save do quiosque.
3. Revisar `Setup`: se projeção falhar na primeira inicialização, moradores podem
   não reaparecer porque bReady depende das rotas. Validar/reparar se necessário.
   A correção pequena posterior usa GetViewDistanceQuality para o orçamento:
   presets personalizados não são mais tratados como qualidade baixa apenas
   porque GetOverallScalabilityLevel retorna -1. Validar essa seleção em execução.
4. Ajustar a captura do chuveiro: o ponto lateral (4805,1580) encosta no vidro.
   Testar posição livre à frente do box, sem aprovar a imagem atual. Controle
   abre/fecha já passou, efeito visual ainda precisa de inspeção correta.
5. Continuar capítulos/fama, pesca/fotos e negócios reais; implementar vôlei e
   animais animados. Depois arte/auditoria global, três opções de interface e
   regressão/desempenho/exportação final. Não encerrar apenas por ter pedestres.

## Pesquisa de animais — candidatos, sem instalação no jogo

- `tools/ue58/render_animal_source.py` faz render de FONTE no Blender/CPU, nunca
  captura do jogo. Animais antigos têm rig/Idle/Walking, mas são cartoon.
- Labrador do pack Pets and Companions HD foi baixado e examinado: **rejeitado**,
  anatomia/qualidade inadequadas. Não instalar só por a página dizer "HD".
- Gato Tabby Grab3D ficou visualmente melhor; candidato estático, sem rig:
  https://grab3d.com/api/v1/models/cat.json e https://grab3d.com/dl/cat/cat-light.glb
  A página/API declaram CC0 e origem assistida por IA. Variante light tem ~382 mil
  triângulos/1K; precisa redução, rig/skin/animação e validação antes de integrar.
  Fonte local `D:/CodexTemp/ue58-animal-candidates/tabby.glb`; metadados em
  `D:/CodexTemp/ue58-cat-cc0-candidate.json`. Não substituir modelos por estátuas.
- Renderizações da fonte em `D:/CodexTemp/ue58-animal-source-review/`.
- Blender portátil verificado: `D:/Tools/blender-5.2.2-windows-x64/blender.exe`.
  Blender MCP estava desconectado; usar o executável ou reconectar antes de chamar.

## Restrições e entrega

Preservar celular B, placa física vermelha/verde, sem preparo, atendimento no
balcão antes da mesa, um atendente e pagamento automático. Manter Lumen async=0
pela mitigação de estabilidade registrada. Gramado contínuo tem 177454 instâncias.
Não apagar as três pastas Actors antigas não rastreadas (dish_fries,
dish_fish_portion, player_home_door), saves, fontes ou instalações anteriores.

O EXE de f7ab170d **não contém este WIP da população**. Não sobrescrever esse
pacote antes de validar/exportar a continuação. Não foi publicada release nova
nem montado outro ZIP em Downloads neste lote; o download anterior permanece.

## Correção pequena após a pausa

Com autorização para apenas algo pequeno, o orçamento de pedestres passou a usar
a qualidade de distância real em vez do índice global (-1 em presets mistos).
Compilação MareAltaEditor Win64 Development aprovada após a mudança. Sem nova
execução do jogo ou exportação; o EXE testado continua sendo o de f7ab170d.
Demais pendências continuam pausadas até novo pedido.

### Pequenos ajustes autorizados posteriormente

O usuário autorizou continuar em pequenos lotes enquanto houver limite.
Inicialização da vila agora espera a navegação terminar e um ponto conhecido
ficar projetável antes de criar a população. Aparência registra corretamente
a variante carregada; reaplicá-la limpa cabelo anterior e reinicia o clip para
evitar peças acumuladas e animação vazia. Validar em PIE antes de exportar.

O primeiro probe PIE está em `D:/CodexTemp/ue58-small-fixes-20261029/`:
`village-probe-a.json` e `village-probe-b.json`. 11 dos 12 pedestres mudaram de
posição entre as leituras; um ficou bloqueado na praia. Pequena correção posterior
faz inverter o trajeto após duas tentativas bloqueadas, mesmo quando a solicitação
de caminho foi aceita. Sem teleporte. Compilação aprovada; repetir a observação.
Associados modelos femininos a Dona Rita/Lourdes e masculinos a Seu Zé/Padre Tomé.
Ferramentas MCP novas: village_runtime_probe e village_dialogue_probe, restritas
a perfis isolados D:/CodexTemp. Teste seguinte em pasta com sufixo `-b`.

# Progressão: fim do dia, fama e capítulos da vila — 01/11/2026

Primeiro lote da continuidade assumida pelo Claude (antes: Codex). Branch
`codex/ue58-migration`, Unreal 5.8.3, projeto `D:/Projetos/MareAltaUE58`.
**Não é a conversão completa e não gerou um novo executável.**

## Problema encontrado

A campanha principal travava no 6º objetivo, "O quiosque e o mar": o tipo
`chapter` não existia em `MissionAmount`, e os capítulos da vila (`prog.ch`) não
tinham código nativo. Também não havia salário: o atendente custava só a
contratação, e dormir não fechava o dia nem mostrava resultado. Para uma demo,
isso quebrava a progressão econômica nos primeiros 30–60 minutos.

## O que mudou

- `UMareSimulation::Sleep` agora fecha o dia: cobra o salário do atendente uma
  vez (`company.sim.wage_day`, como na versão Godot), não cobra cargos antigos
  de quiosque fundidos no atendente único (`company: true` nas definições), grava
  `ue_last_day` (entradas, saídas, salários, vendas, saldo), zera `day_in/day_out`
  e deixa a mensagem do resumo. Dia sempre avança para 08:00 (o relógio para em 24:00).
- Fama nativa a partir de `prog.fame_xp`, com os limites/nomes originais:
  +2 por produto entregue, +80 por capítulo. Nível aparece no HUD.
- Capítulos da vila portados: abertura em sequência, passo salvo em `prog.ch`,
  progresso de atender/vender contado só enquanto o passo está ativo
  (`<id>_serve/_sell`), entregar consome estoque uma vez, doar cobra uma vez,
  recompensa e fama apenas ao concluir. `MissionAmount("chapter")` libera a campanha.
- Mercadinho mínimo (`BuySupply`): compra atômica de insumos crus, usada no
  diálogo quando falta o item do passo "entregar". Não cria estoque grátis.
- Diálogo dos moradores: o personagem responsável pelo capítulo aberto mostra a
  história e o passo atual com o botão adequado (comprar faltantes, entregar,
  doar, concluir). O resultado aparece ao reabrir a conversa. E/Esc/B como antes.
- Celular: Missões ganha "Histórias da vila" (apenas acompanhamento; o avanço é
  presencial). Finanças mostra o dia atual e o resumo do último dia. Equipe
  informa salário pago ao dormir.
- HUD: aviso temporário (7 s) para mensagens fora do celular (dormir, capítulo, fama).
- WIP do Codex de 29/10 incluído após compilar e testar: dormir pela cama com
  fade, bloqueio de E/B durante o sono, mira na superfície do colchão/folha da
  porta. A mensagem de bom dia agora inclui o resumo do dia.

Regras mantidas: celular pelo B, placa física, balcão antes da mesa, sem preparo,
um atendente e pagamento automático.

## Validação executada

- Compilação `MareAltaEditor Win64 Development` com UnrealBuildTool (editor
  fechado, necessário para mudança de cabeçalhos): **sucesso**, sem avisos do módulo.
- Testes de automação **pelo MCP do editor** (`AutomationTestToolset`):
  `MareAlta.Migration.NativeEconomy` e o novo
  `MareAlta.Migration.DayCloseAndChapters` — **2/2 Success**, 0 erros/avisos.
  O novo teste cobre salário único, cargo legado não cobrado, reload sem cobrança
  dupla, compra/entrega de peixes, 15 atendimentos, doação, recompensa única,
  abertura do capítulo seguinte, objetivo `chapter` e persistência em disco.
- PIE pelo MCP com save isolado `D:/CodexTemp/claude-qa-20261101/slot1.json`
  (editor iniciado com `-MareSaveRoot`), ferramenta nova `progression_probe`:
  mira real no Seu Zé → diálogo passo 1/3 (0/4) com compra; compra R$ 28 e entrega
  → passo 2/3 (0/15); tentativa sem cumprir recusada; cama real → fade, Dia 2
  08:00, salário R$ 30 uma vez, `wage_day=1`, resumo no HUD, movimento liberado.
- Capturas reais do PIE (com UI, `Shot showui`) em
  `graphics-reference/progressao-20261101/`. Log do editor sem erros do projeto
  (apenas autotestes internos da engine na inicialização).

## Limitações

- **Executável não empacotado nem testado neste lote.** A prévia jogável continua a
  de 29/10 (`45cc1e69`). Não chamar este lote de jogável antes do pacote.
- O botão do diálogo foi exercitado chamando as mesmas funções da simulação; o clique
  Slate em si não foi automatizado.
- Passos de capítulo de fama/foto/receitas/negócios têm contagem nativa, mas foto (P),
  cozinha experimental e negócios ainda não existem na UE; capítulos 2–4 seguem bloqueados
  por esses sistemas. Pesca no píer também não existe (side mission "pescador").
- Fama ainda não altera demanda/clientes (na Godot, +4% de movimento por nível).
- `M_ClearWindowGlass.uasset` e `mare_home_kiosk_audit.py` (`repair`) do Codex não foram
  aplicados ao mapa; o material fica fora do commit até ser validado.

## Próxima prioridade

1. Empacotar e testar o EXE com este lote (dados isolados), incluindo dormir e o diálogo.
2. Fama influenciando chegada de clientes; pesca no píer e foto com P (destravam
   secundárias e o capítulo 2).
3. Operação real da pousada (diárias, hóspedes, camareira) ligada ao fechamento do dia.

Commit do lote: `e6028353` (push confirmado em origin/codex/ue58-migration).

# Maré Alta Resort — Eventos cômicos e NPCs memoráveis

**Registro de ideias aprovado pelo usuário em 31/10/2026.**
**Status: PLANEJADO, NÃO IMPLEMENTADO.**
**Ramo de referência:** `codex/ue58-migration` (Unreal Engine 5.8).
**Prioridade:** complemento de polimento e retenção, SEM desviar da conclusão do loop principal e da preparação da demo/Steam Next Fest de fevereiro de 2027.

## Visão criativa

Adicionar humor situacional, orgânico e ocasional ao simulador de quiosque/resort, mantendo o mundo **realista estilizado**, com cenários naturais e personagens coerentes. Mesclar situações plausíveis do cotidiano de praia com acontecimentos levemente exagerados, sem virar jogo de pastelão. Os momentos devem ser fáceis de entender em vídeos curtos, mas o jogo precisa continuar interessante sem eles.

**Regra de ouro:** eventos de humor não podem bloquear atendimento, arruinar a economia do jogador sem aviso, desrespeitar os saves ou quebrar a rotina dos NPCs. Evitar a mesma piada em sequência.

## Catálogo de eventos aprovados

### HUM-001 — Gaivota ladra de batatas (PRIORIDADE 1 / candidato à demo)
- **Gatilho:** há comida servida em mesa ou área da praia, uma gaivota próxima e não há evento similar em curso.
- **Cena:** gaivota pousa, pega uma batata/pequena porção e sai voando; turista reage, sem agressividade nem dano.
- **Gameplay:** reação do cliente e oportunidade **opcional** de resolver/repor o item; pode gerar breve comentário e satisfação/insatisfação moderada.
- **Regras:** nunca criar produto grátis no estoque, cobrar a entrega duas vezes, subtrair a porção duas vezes ou alterar pedido já pago sem transação explícita. Começar como evento visual com pequena reação, sem penalidade econômica, se a integração transacional ainda não estiver pronta.
- **Assets:** reutilizar aves existentes se puderem ser animadas com qualidade; animação de voo/pouso e prop em escala apropriada.

### HUM-002 — Turista influenciador exigente (PRIORIDADE 1 / candidato à demo)
- **Gatilho:** visitante especial ocasional na fila; sem interferir com a mecânica balcão antes da mesa.
- **Cena:** faz selfies, comenta que a iluminação não ficou boa, pede ângulo diferente ou mesa com vista; não ficar permanentemente atrasando a fila.
- **Gameplay:** atendimento bem-sucedido pode gerar um pequeno bônus temporário de reputação/visitas, integrado à economia quando existir suporte; no MVP, usar diálogo e reação sem bônus ainda.
- **Regras:** reservar/liberar mesa corretamente; sem duplicar pedidos, clientes ou recompensa ao carregar save; feedback visível e sem punição desproporcional.

### HUM-003 — Cachorro ladrão de chinelo (PRIORIDADE 2 / pós-demo se necessário)
- **Gatilho:** turista na areia, cachorro livre e NavMesh seguro.
- **Cena:** cachorro pega um chinelo e corre uma curta distância; turista reage de maneira engraçada.
- **Gameplay:** opcional localizar/recolher chinelo, recompensa social leve; deve ser ignorável.
- **Regras:** não prender NPC/animal, não cruzar área de banho/obstáculos, não exigir perseguição demorada; preservar personagem animal com rig/expressões/animações coerentes, sem modelos estáticos improvisados.

### HUM-004 — Guarda-sol levado pelo vento (PRIORIDADE 2 / pós-demo)
- **Gatilho:** rajada pontual, guarda-sol em local aberto e clima compatível.
- **Cena:** guarda-sol mal fixado rola brevemente; turista tenta alcançá-lo.
- **Gameplay:** interação opcional para recolocá-lo, sem dano a terceiros e sem interromper o funcionamento do quiosque.
- **Regras:** física controlada, colisões leves e trajetória segura; só um evento por vez; respeitar pausa e presets gráficos.

### HUM-005 — Turista que pergunta onde fica a praia (PRIORIDADE 1 / candidato à demo)
- **Gatilho:** diálogo aleatório raro ao passar pelo quiosque ou encontrar visitante.
- **Cena:** pergunta onde fica a praia quando já está olhando para ela; o jogador aponta ou responde.
- **Gameplay:** interação curta com reação e, opcionalmente, pequena variação de simpatia; sem telas excessivas.
- **Regras:** textos localizáveis PT-BR/EN, leitura fácil; E/Esc fecha diálogo e B não sobrepõe o celular.

### HUM-006 — Atendente iniciante atrapalhado (PRIORIDADE 2)
- **Gatilho:** traço de personalidade/experiência do **único atendente** do quiosque.
- **Cena:** quase deixa cair uma bandeja, hesita entre mesas ou faz uma animação de recuperação; humor visual suave.
- **Gameplay:** treinamento pode diminuir a frequência de tropeços/hesitações, quando o sistema de evolução dos funcionários estiver pronto.
- **Regras:** não reintroduzir cargos separados, preparo/cozinha ou pagamento manual. Preferir animação breve sem perder pedidos, produtos, dinheiro ou sincronismo com o balcão.

## Personagens recorrentes e diálogos

- **Seu Arnaldo:** turista reclamão, mas carismático; reclama mesmo quando está tudo bem. Exemplo original: “Essa água de coco está muito natural. Vocês não têm uma mais industrializada?”
- **Pescador contador de histórias:** cada encontro traz uma versão mais exagerada do tamanho de um peixe, sem virar um tutorial repetitivo.
- **Turista perdido:** pode reaparecer com dúvidas absurdas relacionadas à vila/praia.
- Falas curtas, variadas, sem humor ofensivo, sem vozes obrigatórias, respeitando o estilo de áudio suave e a ambientação brasileira. Evitar repetir o mesmo diálogo a cada visita.

## Ordem de implementação recomendada

1. **Primeiro concluir e estabilizar os sistemas essenciais existentes** da Unreal: negócios operacionais, progressão, campanhas, performance e testes. Humor não substitui esses requisitos.
2. **Lote A, menor escopo para a demo:** HUM-005 + diálogos de Seu Arnaldo/pescador; HUM-002 sem recompensas complexas; HUM-001 sem prejuízo econômico. Implementar um por vez e validar.
3. **Lote B, após o loop central estar estável:** HUM-003, HUM-004 e HUM-006, incluindo treinamento apenas se a gestão de funcionário já oferecer suporte.
4. **Lote C:** ampliar variações, reputação, reações de clientes, clipabilidade e balanceamento com dados de playtest.

## Diretrizes técnicas (UE 5.8)

- Eventos **serverless e locais**, controlados por gestor leve de eventos com IDs estáveis `HUM-001` etc., estados `idle/active/resolved`, intervalo mínimo, cooldown individual e limite global de um evento físico marcante por vez. Não implementar rede/multiplayer por causa disso.
- RNG com seed controlável nos testes e chance ajustável no balanceamento. Configurar frequência baixa para não cansar o jogador; não fixar percentuais antes do playtest.
- Usar subsistemas atuais de clientes, moradores, quiosque, física, navegação, áudio e `UMareSimulation`; preferir extensão modular, não reescrever o fluxo de atendimento.
- Saves: persistir apenas o necessário (evento/cooldown/recompensa única) sem invalidar saves antigos. Recarregar no meio de um evento não pode duplicar recompensa, pedido, produto ou cobrança.
- Visual: geometria/rigs coerentes com a direção realista estilizada; nada de personagens cartoon ou acessórios proibidos; VFX/SFX sutis; framerate e navegação com população.
- UX: legendas PT-BR/EN, HUD discreto e ações opcionais, sem obstáculos involuntários. Respeitar pausa, mute, controles de volume e acessibilidade.
- Criar assets apenas com autoria própria ou licença comercial compatível e documentada em `CREDITS.md`; preservar o trabalho na branch Unreal sem substituir a base Godot.

## Critérios de aceite e validação

- [ ] O evento dispara em condições coerentes e termina sozinho; repetir 100 ciclos de simulação não trava NPCs, fila ou NavMesh.
- [ ] Um evento por vez; cooldown e seed testáveis; diversidade suficiente para não repetir a mesma piada a cada minuto.
- [ ] Atendimento **no balcão antes da mesa**, um atendente, sem preparo, pagamento automático e estoque real continuam funcionando.
- [ ] Sem cobrança duplicada, retirada duplicada ou perda de produtos em eventos, saves ou reload.
- [ ] Reações e animações estão visíveis em capturas **reais do EXE da Unreal**, não apenas imagens conceituais.
- [ ] Eventos opcionais podem ser ignorados e não bloqueiam progresso/campanha.
- [ ] Testar pausa, silêncio, dia/noite, presets baixo/alto, física/colisões, nav e loading.
- [ ] Revisar diálogo em PT-BR e EN; texto legível no layout compacto; sem voz obrigatória.
- [ ] Executar testes da fonte e **do executável empacotado**, com saves isolados e sem destruir `userdata`.
- [ ] Registrar vídeo/clipe real quando estiver funcional para uso futuro de marketing; não divulgar recursos incompletos como implementados.

## Referências internas

- [AGENTS.md](../../AGENTS.md)
- [Guia vigente](../CONTINUAR.md)
- [Pendências UE de 29/10](PENDENCIAS_2026-10-29.md)
- [Teste da vila de 29/10](TESTE_VILA_2026-10-29.md)
- [Migração Unreal](MIGRACAO.md)

**Esta é uma proposta de design aprovada para planejamento; não é uma entrega jogável nem indicação de que os eventos já existem no código.**

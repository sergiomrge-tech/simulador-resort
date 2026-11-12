# Acessibilidade — estado do código e propostas (Pacote 9)

**Escopo:** revisão estática em `unreal/MareAlta/Source/MareAlta/*.cpp` da base `0ba71c4c`, sem alterar lógica, headers ou `.uasset`. O objetivo é oferecer opções reais na **demo**, sem prometer selo Steam de acessibilidade antes de testes com pessoas e periféricos.

| Recurso | Situação observada / onde | Lacuna | Esforço relativo | Demo |
|---|---|---|---|---|
| Tamanho de texto/UI | `MareGame.cpp:2219-2221`: opção `TextScale` de 85–150%; `MareOptions.cpp` persiste | Verificar todos os painéis Slate, dicas, menu, telefone, balões, fontes CJK a 150%; min 85% pode dificultar leitura | M (QA + layouts) | **P0** |
| Sons importantes em forma visual | `MareAudioWorld.cpp:118-133,187+` emite cues; `MareGame.cpp` tem `LastMessage` | Para fila, pedido, erro, evento, alarme, clima e interação sem som, assegurar aviso visual legível, texto e ícone opcional; evitar depender só de som | M/L | **P1** |
| Daltonismo | `MareGame.cpp:2222`: `bColorSafe`; minijogos `MareGame.cpp:1090+`, sem garantia de todos os alvos | Auditar cores de placa, raridade, avaliação, pedido, estrelas, aviso e zonas dos minijogos; reforçar por ícone, forma, padrões, +/− | M | **P0** |
| Remapear teclas | `MareOptions.cpp:249-259`: Bind troca atalhos conflitantes; `MareGame.cpp:2240+` exibe ações | Confirmar mouse, gamepad, minijogos com teclas fixas (Q/P), E, menu, retorno e acesso sem mouse; oferecer reset | M/L | **P1** |
| Segurar × apertar | `MareGame.cpp:1270+` minijogos usam segurar clique, timer; `MareGame.cpp:995` E por pressionamento | Alternativa de toque/ativar-desativar para ações longas, configuração de pressionar repetido ou manter, sem tornar obrigatórios combos rápidos | L | **P1** |
| Pausa a qualquer hora | `MareGame.cpp:2341-2359` bind `Pause` com `bExecuteWhenPaused=true` | Testar em conversa, sono, piscina, passeio, minijogos, intro e tela final; manter opção retomar e foco correto | M | **P0** |
| Velocidade dos minijogos | `MareGame.cpp:1106-1121,1223,1377,1608+` temporizadores controlam ritmo | Modo 0.75x/0.5x para janelas de reação e timers visuais, não desacelerar salário/relógio/economia inadvertidamente | L | **P1** |
| Modo sem pressa | `MareSimulation.cpp:451-491` dia/salários; progresso e NPCs por tempo | Opção de reduzir pressão em pedidos, pesca, surfe, visitas; reequilibrar sem explorar pagamentos/placa; sinalizar influência em pontuação | L/XL | **P2** |
| Música sem forçar volume 0 | `MareGame.cpp:2224+` tem slider `Music`; `radio_ui.json` propõe toggle | Implementar checkbox persistente que mantenha efeitos e ambiente; testar stream | P | **P0** |
| Subtítulos e sinais | `MareGame.cpp` exibe instruções em texto, `MareAudioWorld` sons espaciais | Para sons com informação de gameplay, oferecer indicadores direcionais (E/D/frente), sempre sem cor exclusiva; não chamar de legenda completa sem fala | M | **P1** |
| Controle em UI e textos longos | `MareGame.cpp` `MareGamepad::FocusSoon`, `SMareFit` | Testar foco, leitor de tela Steam, resolução ultrawide e HUD com escala alta; possível suporte futuro a narração de UI | M/L | **P1** |

Esforço P=pequeno (1–2 dias), M=médio (2–5 dias), L=grande (1–2 semanas), XL=multissistema (mais de 2 semanas), **estimativas de planejamento e não prazos prometidos**.

## Critérios mínimos para demo

1. Conseguir começar/pausar/salvar/encerrar e concluir primeiro pedido apenas por teclado; repetir com gamepad.
2. Informação crítica nunca depender somente de vermelho/verde ou de áudio. Inclua texto/ícones nos feedbacks de dinheiro, fama, pedidos e cronômetros.
3. Texto 150% completo sem corte em pt-BR/en/CJK; contraste adequado em praia ensolarada e à noite.
4. Natação e passeio sem tremor/flash inesperado; opções básicas visuais e áudio persistem após reiniciar.
5. Não afirmar suporte a leitor de tela, modo sem pressa ou remapeamento total até validar no build empacotado.

**Responsável pela implementação:** Claude, por exigir C++/Slate ou editor. **Sergio:** testar legibilidade e teclado/controle em PC real e coletar feedback de jogadores.

# Maré Alta Resort — GDD resumido (v0.1.0)

**Gênero:** simulador de pousada/resort em primeira pessoa (3D), celular deitado (paisagem).
**Cenário:** pousada de praia no Nordeste brasileiro — coqueiros, sapê, jangada, bossa nova.
**Referências (Steam):** Supermarket Simulator, TCG Card Shop Simulator, Waterpark Simulator, Hotel Renovator, Tropical Resort Simulator.

## Ciclo principal
Hóspede chega → fila na recepção → **check-in no balcão** (recebe a diária) → vai ao bangalô →
piscina / Bar do Coqueiro (vendas agrupadas em um aviso) → descansa → check-out (gorjeta + avaliação ★) →
bangalô fica **sujo** → jogador **arruma a cama, recolhe toalhas, joga o lixo fora** → bangalô livre.
Dinheiro compra **redes** (decoração entre coqueiros: +estrelas, +diária).

## Controles
- Celular: joystick à esquerda, arrastar à direita para olhar, botão **Interagir**, botão **Loja**.
- PC: WASD, mouse (clique para capturar, Esc solta), **E** interagir, **B** loja.

## Técnica
Godot 4.5.1 (renderer Mobile), Android arm64. Texturas e modelos Poly Haven (CC0) 1k (normais 512),
hóspedes Quaternius Universal Animation Library (CC0) com roupas pintadas por zonas de vértice,
áudio CC0 do OpenGameArt (ver assets/audio/CREDITS.txt). Céu com Sky.PROCESS_MODE_INCREMENTAL,
atualizado a cada 10 min de jogo. Save automático (user://mare_alta_save.json) a cada 45 s e ao pausar.

## Testes
- `godot --headless --path . -- --loop-test` → ciclo completo automatizado (LOOP_TEST PASS).
- `./shot_all.sh` → capturas em shots/ (xvfb + lavapipe, timeout de 150 s por captura).

## Próximos passos
Mais bangalôs/expansões, funcionários (camareira, barman), cardápio do bar, chuva, migração para Unreal Engine 5.

---

## v0.2.0 — Versão PC (Steam) — 17/10/2026

**Plataforma:** só Windows x86_64 (Steam). O Android foi descontinuado a pedido do usuário; o código do renderer Mobile continua no projeto, mas não é mais exportado.

**História e loop diário**
- O herói mora numa casinha azul da vila de pescadores, que tem interior: cama, cozinha com fogão e pia, mesa, guarda-roupa e janela para o mar.
- Ele acorda às 06:30 e vai pela calçada de pedra portuguesa até o **Quiosque Maré Alta** na praia, que abre das 08:00 às 18:00.
- No quiosque, os clientes chegam (no máximo 3 no balcão, paciência de 90 minutos de jogo) e pedem coco gelado (R$ 8), caipirinha (R$ 15) ou petiscos (R$ 22). Atender rápido rende +R$ 2 de gorjeta.
- O loop da pousada continua: check-in na recepção, limpeza dos bangalôs, bar e redes.
- **Objetivo com seta amarela:** dormir → limpar bangalô → check-in → turno no quiosque.
- **Depois das 20:00:** ele dorme na cama de casa, vai para o dia seguinte às 06:30 e o jogo salva. Os hóspedes fazem check-out durante a noite.
- **Às 02:00 sem ter dormido:** ele desmaia, acorda em casa e perde R$ 20.

**A vila**
- Rua de paralelepípedo com calçadas de pedra portuguesa (ondas) e meio-fio.
- 11 casas coloniais coloridas com telhado de barro, venezianas e alpendres, mais a Padaria e Mercadinho.
- Igreja de São Pedro com torre e sino (toca às 12h e às 18h).
- Praça com árvore, bancos e carrinho de café.
- Barraca da Dona Rita na praia, jangadas, bicicletas, postes com luz à noite e coqueiral.
- Moradores andam pelas calçadas: 14 caminhando e 3 sentados na praça.
- Sons da vila: murmúrio, cachorro, gaivotas e sino.

**Pronto para Steam:** menu principal, 3 slots, pausa, configurações completas, controle, PT-BR/EN e ícone. Detalhes em `docs/STEAM_PLAN.md`.

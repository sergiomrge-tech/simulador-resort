# Caminhada de conferência — vila, quiosque e hotel — 01/11/2026

Pedido: "ande pela vila e principalmente o quiosque e hotel 5 estrelas".

## Como foi feito (pelo MCP, sem gerar executável)

1. Regressão completa do jogo **dentro do PIE** (`-MarePreviewQA`, perfil
   `D:/CodexTemp/claude-pie-qa-084654`): **99/99** verificações — natação, celular, pausa,
   placa do quiosque, dia/noite/chuva, navios/baleias, porta da casa, rádio (todas as estações),
   expansões, **entrada do hotel livre e recepção após a compra**, recife, gramado, corpo/mãos,
   TV/som/sofá/chuveiro, vila (5 moradores, 12 pedestres, diálogo), capítulo do Seu Zé e dormir.
2. Atendimento real no quiosque com `gameplay_probe`:
   - com atendente contratado: o atendente anota, retira e entrega sozinho; pagamento
     automático por produto (R$ 702 → R$ 774);
   - sem atendente (perfil `claude-qa-hotel`): jogador anota com E no balcão, retira coco e suco
     na geladeira, entrega com E, pagamento automático (R$ 5.000 → R$ 5.026) e o cliente segue
     para a mesa.
3. Hotel: varredura de cápsula da marquise até a recepção livre; E no balcão abre o painel do
   hotel; renda noturna testada nos testes automáticos.

## Correção encontrada

- Não havia como **dispensar o atendente** (salário cobrado todo dia). Adicionado
  `DismissAttendant` (produto na mão dele volta ao estoque, sem reembolso) e o botão no celular
  alterna "Contratar atendente"/"Dispensar atendente". Testado no `NativeEconomy`.

## Limitações

- Nenhum defeito funcional reproduzido no quiosque nesta versão; se algo específico falhou na
  sua prévia antiga (29/10), descrever o passo para reproduzir.
- Hóspedes ainda não circulam no lobby; quartos/restaurante do hotel continuam como exterior.

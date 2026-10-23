# Refinamentos integrados — 23/10/2026

1. **Roupas de praia:** camisas simplificadas, bermudas na altura do joelho e
   calçados baixos. Malhas derivadas do pacote CC0 Quaternius com pesos originais.
2. **Equipe identificável:** cozinha em creme com avental, atendimento em verde
   petróleo, caixa em tom areia e limpeza em azul/cinza com avental. Identificação
   física no peito traz nome da empresa e função. A personalização de uniforme
   comprada no jogo continua podendo mudar sua cor.
3. **Trabalho:** abertura/fechamento suave da geladeira, alcance do braço no
   preparo, breve gesto de retirada, transporte apoiado e entrega ao cliente.
   A movimentação usa o esqueleto importado e limites reais do braço; reservas e
   consumo de estoque mantêm as regras anteriores. Não é uma simulação física
   de dedos ou ingredientes individuais: os gestos acompanham as ações do jogo.
4. **Expressão:** piscadas dessincronizadas, pequenos movimentos de atenção e
   sobrancelhas discretamente diferentes ao esperar ou consumir um pedido.
5. **Balcão:** cardápio com receitas disponíveis, porta-guardanapos com papel
   dobrado, utensílios e bandeja marcada para pedidos prontos. Equipamentos ficam
   dentro e as entradas laterais continuam livres. A bandeja marca a área visual;
   retirada de estoque continua nas estações, pelo E.
6. **Som:** cinco efeitos originais curtos, posicionais e baixos (geladeira,
   preparo, retirada, conclusão e caixa), com limite de repetição e sem vozes.
   Respeitam a configuração de áudio/SFX do jogo.
7. **Luz:** interior fica gradualmente mais quente entre 16h30 e 19h30; luzes
   adicionais destacam a placa à noite. Não alteram o horário de funcionamento.

Fontes Blender editáveis e com texturas incorporadas em `art/blender/`:
`resort_outfit_male.blend`, `resort_outfit_female.blend` e
`kiosk_counter_details.blend`. Geradores em `tools/gen_compatible_clothing.py`,
`tools/gen_counter_details.py` e `tools/gen_kiosk_soft_audio.py`.

Validação: `--loop-test --practical-test`, `--loop-test --company-test` e ciclo
geral `--loop-test`, sempre com dados de teste separados do progresso do jogador.

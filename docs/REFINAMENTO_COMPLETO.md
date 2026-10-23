# Refinamentos integrados — 23/10/2026

Revisão do avental: superfície ajustada ao volume da roupa, alça no pescoço,
faixa na cintura, bolso duplo, bordas costuradas e dobras suaves. A parte inferior
acompanha os ossos das pernas com transição contínua no quadril. É uma malha
animada pelo esqueleto; não usa simulação física de tecido.
Óculos escuros removidos de todos os personagens a pedido do Sergio.

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

Revisão avental/sem óculos validada na fonte (`apron3-no-glasses.log`) e no
executável/PCK (`apron-pack-visual.log`: PRACTICAL_TEST PASS;
`apron-pack-loop.log`: LOOP_TEST PASS). Conferidos retrato, preparo, caminhada
e pose sentada. Permanecem os avisos já conhecidos de liberação de materiais/RID
ao encerrar os testes; não houve SCRIPT ERROR nem recurso ausente nessa revisão.
SHA256 do PCK: `25b4bfcd4e6827f0c314c31901e5d3f961ecee8a8b88d2539f6920dadaf5cc1b`.

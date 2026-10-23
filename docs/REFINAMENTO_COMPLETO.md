# Refinamentos integrados — 23/10/2026

> **Regra vigente — 23/10: sem preparo.** Pegar o produto pronto na geladeira,
> armário ou cozinha e entregar. Sem cronômetro e sem precisar cozinheiro.
> Compras abastecem o estoque; retirada desconta uma vez. Referências históricas
> a preparo abaixo foram substituídas por este fluxo. Saves antigos recuperam
> unidades já pagas sem consumir o estoque novamente.


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

## Casa e equipamentos invisíveis — 23/10
Casa com piso em pedra clara, paredes suaves, iluminação neutra, marcenaria verde
acinzentada, portas/puxadores, pia com cuba e torneira, azulejos, prateleiras,
livros, cortinas de malha com dobras, persianas externas e molduras.
Fonte player_home_details.blend salva/reaberta, com imagens incorporadas.

Correção do quiosque vazio em saves sem empresa: KioskOperations não pode usar
company_enabled para esconder os móveis/expositores. O cadastro controla a gestão,
o atendimento e o item na mão; a presença dos equipamentos é permanente. E na
estação antes do cadastro abre o app empresa. Não cria empresa nem cobra sozinho.
Fonte home-operations-final.log: PRACTICAL_TEST PASS incluindo cenário sem empresa.

## Cores naturais no jogo inteiro — pedido de 23/10
Retirado o aumento automático de saturação/valor do Toon e o clareamento
alaranjado de modelos importados. Madeira, areia e terracota usam paleta mais
natural; normal/roughness/metálico/AO dos modelos deixam de ser apagados pelo
adaptador. Saturação ambiental moderada também no ciclo dia/noite e chuva.
Pessoas sem reforço extra de saturação. Tapete da casa em linho neutro e porta
em tom de madeira. Geometria e estilo dos personagens foram preservados.

## Validação casa/cores/equipamentos — 23/10/2026
Fonte natural-practical.log e pacote natural-pack-practical.log: PRACTICAL_TEST
PASS, incluindo equipamentos visíveis sem empresa. Inspeção do interior
home_natural.png, fachada home_exterior_pack.png, quiosque restaurado,
pessoas e entardecer/noite. Sem SCRIPT ERROR/recursos ausentes nos testes finais.
Persistem os avisos de liberação de material/RID ao encerrar o motor.
PCK SHA256: 33bf471c1900967bf72671bfc613336ac5b44469ef567d4bad554ccef53330f5.

Validação da retirada direta: fonte passou empresa, prático, gestão, simulação e
ciclo geral; executável passou empresa e prático. Preparo de saves antigos vira
unidade pronta uma vez, sem novo débito. Conferida practical_station.png no PCK.
PCK SHA256: 8d95b71f92fdd3de2b877175fdbabb9fe1c91a7cd97ca68e0edfc67ecba6a192.

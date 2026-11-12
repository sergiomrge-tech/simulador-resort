# Retorno do teste UE — 28/10/2026

O usuário rejeitou a experiência da prévia: visual insuficiente, interações pouco
claras, ausência de pessoas, objetos deslocados e expansões aparentando já ativas.
Esses relatos são defeitos pendentes; os 22 checks antigos não os cobriam.

## Expansões — lote validado

Causa confirmada: o exportador preservava `region`, mas o runtime mostrava todos
os grupos importados, independentemente de `State.unlocked`. O perfil padrão tem
esse objeto vazio. A correção liga visibilidade e colisão das regiões à compra,
inclui letreiros e atualiza imediatamente ao comprar. Compras já registradas são
preservadas. Não editar nem limpar o save do usuário para resolver apresentação.

A inspeção visual detectou dois problemas adicionais: os 208 objetos do Grand
Hotel estavam sem região, assim como 35 objetos de cinco negócios. Os grupos
foram separados sem reimportar ou simplificar modelos: 12.910 instâncias antes e
depois, agora em 1.721 grupos não vazios. O hotel segue `unlocked.grand_hotel`;
os negócios seguem `prog.biz.<id>.lvl`. O terreno da piscina recebe uma cobertura
com o mesmo material de gramado enquanto bloqueado, removida ao comprar. Isso
evita enxergar o fundo azul através do buraco existente na malha do terreno.

`mare_expansions.repair()` é idempotente e verifica os marcadores semânticos do
export antigo antes de corrigir regiões. O exportador foi atualizado para manter
a propriedade do hotel e dos negócios; os helpers do hotel também preservam a
identificação dos objetos que adicionam diretamente ao World.

Licença de drinks libera caipirinha; chapa libera petiscos. Novos pedidos,
retirada e reposição respeitam as licenças. Pedidos anteriores à correção continuam
atendíveis sem conceder permanentemente a licença. Expositores físicos permanecem
visíveis como referência, conforme a preferência original.

Celular distingue expansão comprada de disponível para compra. Incluídas mira
central, interação por clique além de E e indicação inicial B/criar/abrir.

O NativeEconomy foi ampliado com compra, pré-requisitos, cobrança única,
persistência, licença e continuidade de pedidos antigos. O QA do executável foi
ampliado para conferir visibilidade/colisão real das sete expansões com geometria,
dos cinco negócios, cobertura do terreno e desbloqueio físico após compra.

Verificação concluída: NativeEconomy `Success`, zero erros/avisos no relatório do
teste. O EXE exportado passou em **40 verificações**, saiu com código 0 e não teve
Error/Ensure/Fatal no log de execução. Imagens reais antes/depois da compra foram
revisadas: gramado contínuo e hotel ausente antes; piscina e pousada presentes
após a compra de sua cadeia, com o hotel ainda ausente. Áudio audível sem clipping
(pico 0,061), silêncio sustentado com mute e pausa. Perfil de teste separado:
`D:/CodexTemp/ue58-package-qa-20261028-074759`.

Evidências versionadas em `docs/qa/ue58/expansion-*-20261028.*`.
Build testado: `D:/Builds/MareAltaUE58_Expansoes_2026-10-28/Windows`.
Não confundir este resultado com validação das sete frentes abaixo.

Pacote local: `D:/Downloads/MareAltaResort_UE58_Expansoes_2026-10-28` e ZIP de
mesmo nome. A pasta pronta recebeu cópias verificadas do slot e GameUserSettings
da instalação UE usada no último teste do usuário; os originais foram preservados.
O ZIP não contém esses dados, e passou na verificação CRC.

Publicação verificada: [prévia 20261028.2](https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-ue58-preview.20261028.2).
Fonte `70425f6b418df3d15bb1b8d7705960e8fd9a6383`, ZIP 1.676.050.977 bytes,
asset `uploaded`, digest GitHub igual ao SHA-256 local:
`398ad2bb5d8e56a95f0f3c20cdb0133f2d06abd5e37260ba2fe3f2717aacfb2c`.
Release marcada como prévia, sem substituir a entrega Godot.

## Escopo autorizado que continua pendente

O usuário aprovou sete frentes. Esta correção de expansões não conclui o lote:

1. Corpo/mãos do jogador e animações de pegar, carregar, portas e nadar.
2. Atendimento natural, produtos apoiados nas mãos, consumo/louça correspondentes,
   ciclo completo de um único atendente.
3. Acabamento e disposição prática do quiosque com modelos detalhados.
4. Pessoas na praia/vila, vôlei, um veleiro lento por vez, cruzeiro noturno ancorado,
   baleias ao fundo com efeitos de água.
5. Casa funcional com banheiro, sofá, TV, som e sono.
6. Campanha e secundárias ligadas à progressão real.
7. Medição de desempenho na RTX 4060 Ti e otimização com comparação verificável.

As expansões comerciais além do quiosque ainda não têm simulação integral na UE.
Não chamar a conversão de concluída por mostrar seus prédios ou botões.

## Preservação e localização

Projeto ativo `D:/Projetos/MareAltaUE58`, branch `codex/ue58-migration`.
Godot e instalações anteriores preservados. QA apenas em perfil separado no
`D:/CodexTemp`. Downloads e novos pacotes no D. Não sobrescrever a prévia anterior
nem confundir código enviado com executável publicado.

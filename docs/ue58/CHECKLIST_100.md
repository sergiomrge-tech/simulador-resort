# Checklist total — o que falta para o jogo ficar 100% (12/11/2026)

Pedido do Sergio (12/11): "faça um checklist total para o jogo ficar 100%, sem a parte da Steam, que é minha; HUD atual
está ok". Esta lista passa a ser a ordem de trabalho. O histórico e o detalhe do que já foi feito continuam em
[`PLANO_E_CHECKLIST_2026-11-08.md`](PLANO_E_CHECKLIST_2026-11-08.md).

**Fora desta lista:** tudo da Steam (conta, App ID, página, integração, conquistas, nuvem, preço, trailer, Next Fest,
playtest), que é do Sergio; HUD/celular (resolvido: o atual fica); co-op online e Steam Workshop (pós-lançamento).

**Como ler:** `[ ]` = falta fazer. `[?]` = os documentos antigos listam como aberto e eu não conferi item a item no
jogo; o primeiro passo é conferir, e só vira trabalho se a conferência reprovar. 👤 = depende do Sergio.

Cada item fecha com portão de QA PASS, foto analisada, commit e push. Pacote só no fim de cada bloco.

---

## Bloco 0 — Prioridade do Sergio (12/11): humor e campanha

"Se não foi feito, coloque no topo da lista." / "Faça uma revisão completa da campanha do jogo e faça melhorias."

### 0.1 Eventos cômicos (importante para vender)
Sete eventos existem no código (`MareComicEvents.cpp`, `comic_events.json`): gaivota ladra de batatas, influenciador
exigente, guarda-sol levado pelo vento, turista perdido, atendente atrapalhado, Seu Arnaldo reclama, pescador e o peixe.
O cachorro ladrão de chinelo do desenho original não existe (os cachorros saíram do jogo em 03/11). Os 10 critérios de
aceite de `HUMOR_EVENTOS_COMICOS.md` nunca foram marcados.
- [ ] Filmar os 7 eventos no jogo, do começo ao fim, e analisar quadro a quadro (em andamento, 12/11).
- [ ] Animação própria por evento: hoje quem chama alterna dois gestos genéricos. Cada evento precisa de um gesto que conte a piada sem ler o texto.
- [ ] Corrigir o que a filmagem reprovar (postura, mãos, objeto na mão, gaivota, guarda-sol, bandeja).
- [ ] Substituto para o evento do cachorro (ou mais eventos), para a piada não se repetir.
- [ ] Conferir os 10 critérios de aceite do documento, inclusive 100 ciclos sem travar e capturas no executável.
- [ ] Clipe de cada evento no executável, para uso em divulgação.

### 0.2 Campanha principal (revisão completa e melhorias)
- [ ] Mapa da campanha como está: começo, dívida, capítulos da vila, expansões, marcos, final; o que o jogador sabe que tem de fazer a cada momento.
- [ ] Lista de problemas (buracos de objetivo, trechos sem novidade, textos, recompensas, ritmo) com prova.
- [ ] Melhorias aprovadas pelo Sergio implementadas, testadas e traduzidas.
- [ ] Campanha jogada do zero ao fim no executável depois das melhorias (liga com o Bloco 4).

---

## Bloco 1 — Acabamento do que já existe

### 1.1 Recife
- [ ] Peixes do recife com cara de desenho: trocar pelas malhas realistas (os 8 peixes de `gen_fish.py` já existem para o livro de pesca; avaliar reuso antes de modelar outros).
- [ ] Horizonte subaquático vazio: névoa de profundidade, relevo distante, cardumes ao longe.
- [ ] Conferir o snorkel inteiro depois da troca (passeio do início ao fim, fotos de perto e de longe).

### 1.2 Pessoas
- [ ] Cabelo comprido de quem senta fica rígido no nível Alto: reduzir a inclinação da cabeça nas poses sentadas (a física foi descartada: custa ~12 FPS). 👤 ou aceitar como está.
- [ ] Vestir os papéis que faltam com as 11 roupas gratuitas já baixadas (praia, social do hotel, uniforme da equipe, moradores).
- [ ] Calçados variados (chinelo, tênis, sapato social); ninguém descalço fora da areia.
- [ ] Camiseta azul-escura da Dona Roberta ainda parece lisa na sombra.
- [ ] Biquínis: conferir de perto a textura de tecido nas 6 banhistas.
- [ ] Casal da mesa do restaurante do hotel inclina o tronco demais.
- [?] Conversa em pé com gesto melhor que o `Idle_Talking`.
- [?] Variedade de moradores e turistas (cores, cabelos, idades) sem repetir a mesma pessoa lado a lado.

### 1.3 Cenário
- [ ] Casa do jogador: calçada de cimento em volta (tirar a grama sob ela) e caixa do relógio com cara de medidor.
- [ ] Farol: faixa lisa da encosta acima das pedras; um dos três modelos de pedra sai quase preto.
- [ ] Igreja: pilares listrados ou em um mármore só. 👤 decidir.
- [ ] Móveis e louças do Fab baixados e sem uso: usar onde melhoram o cenário ou apagar do projeto.
- [?] Props que vieram do Godot ainda em low poly (fogueira da festa junina e outros): auditoria e troca.
- [?] Toalha da cama do bangalô; fila de hóspedes visível na recepção do hotel.

---

## Bloco 2 — Jogabilidade que ainda não existe

- [ ] Horário de pico próprio por expansão: manhã no quiosque e na piscina, tarde nos passeios e negócios, fim de tarde no bar, noite no restaurante e no salão de jogos.
- [ ] Preparativos de festa comprados na véspera aparecem no mapa (faixa, bandeirinhas, luzes).
- [?] Festas e eventos do calendário (junina, quermesse, DJ, tempestade, maré alta): conferir um por um na UE, com foto.
- [?] Equipe automatiza com renda menor que o jogador fazendo pessoalmente: conferir os números.
- [?] Personalização com 5 opções em tudo (quiosque, expansões, hotel, piscina, tobogã, casa): contar o que falta.
- [?] Dica de primeira vez em cada sistema (balcão, celular, recepção, limpeza, negócios, passeios, pesca, foto): conferir a cobertura.

---

## Bloco 3 — Ilha viva (Fase 2)

A ilha é grande e bonita, mas ainda é cenário. Ordem proposta por mim, do mais barato para o mais caro; 👤 pode trocar a ordem ou cortar itens.

- [ ] Pontos de parada nas trilhas: mirante na Trilha Norte, banco com vista na Oeste, placas de trilha.
- [ ] Turistas e moradores passeando nas trilhas e nas praias novas (estender a navegação estática).
- [ ] Passeio de barco de volta completa à ilha, usando o barco da chegada.
- [ ] Praia norte com uso: pesca de praia, coleta de cocos e conchas, quiosque secundário (expansão paga).
- [ ] Ponto turístico no morro: estátua original de braços abertos. Sistema grande: subir o esforço do modelo antes.
- [ ] Casa do herói com 1 andar (expansão paga): quarto em cima com varanda. Sistema grande: subir o esforço do modelo antes.

---

## Bloco 4 — Prova final do jogo completo

A demo já foi simulada do zero ao fim. O jogo completo, não.

- [ ] Simulação do jogo completo do zero até quitar a dívida (~20 h de campanha, em tempo acelerado): 0 erros no log, 0 pessoas deslizando, 0 fora do assento, save recarregado idêntico.
- [ ] Jogar cada expansão do jogo completo uma vez no executável: Grand Hotel (quartos, VIPs, eventos, restaurante, salão de jogos), passeios, negócios da vila.
- [ ] Pente fino visual do mapa inteiro, de dia e de noite, depois das mudanças grandes de 11/11 (igreja, recepção do hotel, casa, farol, píer).
- [ ] Áudio: medir a mixagem (`measure_mix.py`) com os sons novos; conferir que toda ação tem efeito sonoro.
- [ ] Traduções: auditoria `-MareLocAudit` no executável nos 12 idiomas; teste de layout com alemão e russo (textos mais longos não podem cortar).
- [ ] Saves: carregar um save de versão antiga, backup antes de gravar, 3 slots.
- [ ] Desempenho no pacote final: Padrão e Baixo nos 5 setores, e um teste longo sem travar.
- [ ] Créditos: `CREDITS.md` e tela de créditos conferidos contra todos os assets de terceiros em uso.
- [ ] Pacote Shipping do **jogo completo** (hoje só a demo é empacotada): QA do executável, abertura, tamanho.
- [ ] Limpeza do repositório: arquivos `todo_*.json` soltos, documentos antigos marcados como histórico.

---

## Bloco 5 — Só o Sergio 👤 (fora a Steam)

**Julgar o que foi feito em 11/11:**
- [ ] Ouvir o órgão numa missa (7h–8h ou 17h30–19h): timbre e volume.
- [ ] Pintura do teto da recepção do hotel: o traço está como queria?

**Testes que precisam de você:**
- [ ] Rodar a demo num PC sem a Unreal.
- [ ] Controle físico (Xbox/PlayStation) no executável.
- [ ] Geração de quadros do DLSS (clicando na janela durante o teste).

**Decisões:**
- [ ] Crianças e famílias: comprar pacote pago ou seguir sem.
- [ ] Traduções: revisão nativa; transliterar nomes próprios em chinês, japonês e russo; mais idiomas (cs, hu, ro, da, fi)?
- [ ] Qual é o som ambiente "que não muda nem desliga" notado no teste da demo.
- [ ] Confirmar o nome "Coconut Simulator".

# Direção do projeto — diretor geral e agentes (11/11/2026)

Pedido do Sergio (11/11): "crie um sistema em que o Fable 5.2 é o diretor geral desse projeto e coordena outros agentes
da Claude para que seja mais eficiente e econômico".

A sessão principal (Claude Fable 5.2) é o **diretor geral**. Ela fala com o Sergio, decide, revisa e entrega. O trabalho
braçal vai para agentes mais baratos, definidos em [`.claude/agents/`](../../.claude/agents). O diretor continua dono do
resultado: relatório de agente é informação, não prova.

## Quem faz o quê

| Agente | Modelo | Para quê | Pode escrever? |
|---|---|---|---|
| **diretor** (sessão principal) | Fable 5.2 | Falar com o Sergio, design, especificação, revisão final de fotos e de código, editor da Unreal pelo MCP, git, memória | tudo |
| `batedor` | Haiku | Achar código/dado no repositório; procurar asset gratuito na web com licença | não |
| `artesao-bpy` | Sonnet | Modelar no Blender por script, gerar GLB e prévias | geradores em `tools/ue58`, saída em `D:/Assets/Mare` |
| `programador` | Sonnet | Implementar mudança de código já especificada | só os arquivos listados no pedido |
| `tradutor` | Sonnet | Traduzir chaves novas para os 12 idiomas | arquivos de localização |
| `inspetor` | Sonnet | Analisar lotes de capturas, item a item | não |
| `operador` | Haiku | Rodar portão, pacote, testes do executável, benchmark, instalação | não (só executa rotinas) |

## O que o diretor nunca delega

- Conversa com o Sergio e qualquer decisão de gosto, de design ou de escopo.
- A decisão de "está pronto": o diretor confere o diff, roda ou manda rodar o portão e olha as fotos decisivas ele mesmo.
- Commit, push, memória do projeto, `CLAUDE.md` e os checklists.
- Trabalho no editor da Unreal pelo MCP (montar nível, materiais, importações, PIE). Exceção: o `operador`, quando o
  diretor entrega a vez da máquina para uma rotina pronta.

## Recursos de uso exclusivo (um por vez)

1. **Editor da Unreal / MCP / PIE** — uma única sessão. Enquanto o portão, um PIE ou um pacote roda, ninguém mais usa.
2. **Compilação e empacotamento** — nunca com alguém editando `Source/` ou `Content/Data` (o pacote de 11/11d saiu com
   dados novos e código antigo por isso).
3. **Índice do git** — só o diretor.
4. **Um arquivo, um escritor** — dois agentes nunca recebem o mesmo arquivo. Trabalho em paralelo só com conjuntos de
   arquivos disjuntos (ex.: `artesao-bpy` num gerador novo, `tradutor` nos idiomas, `batedor` procurando assets).

## Quando delegar (regra de bolso)

- Delegue o que dá para pedir em um texto curto e conferir em um minuto: busca ampla, modelo no bpy, tradução, lote de
  fotos, rotina longa de máquina, mudança de código bem delimitada.
- Faça você mesmo: o que cabe em menos de ~5 chamadas de ferramenta, o que depende do contexto fresco da conversa, e
  tudo que é diagnóstico de defeito visual (isolar ator por ator no editor).
- O modelo mais barato que resolve: Haiku para procurar e executar, Sonnet para produzir, Fable só para dirigir e
  revisar. Não suba o modelo de um agente sem motivo dito.
- Em paralelo sempre que os arquivos forem disjuntos e nenhum precisar do editor.

## Como pedir (molde do pedido)

Todo pedido a um agente leva, em texto próprio do diretor (nunca "com base no que vimos"):

1. **Objetivo** em uma frase e por que existe (o pedido do Sergio que originou).
2. **Arquivos / área**: caminhos exatos que pode ler e, se for o caso, escrever.
3. **Restrições** que se aplicam, copiadas do `CLAUDE.md` (não confiar que o agente vai achar).
4. **Pronto é**: critério verificável (teste que passa, prévia de 3 ângulos, `strings N/N`, PASS do portão).
5. **Formato do retorno**: caminhos, números, dúvidas. Curto.

## Como receber

- Ler o relatório e conferir o essencial: abrir o diff, rodar o teste, olhar a prévia. Divergência entre o relatório e
  o resultado se resolve olhando o resultado.
- O que o agente disser que "ficou aquém" entra na lista de pendências ou volta para ele com instrução mais precisa
  (continuar o mesmo agente com `SendMessage`, não abrir outro do zero).
- Só depois: integrar no editor, portão, commit, foto e resumo ao Sergio.

## Fluxo típico de uma entrega

1. Diretor especifica (e pergunta ao Sergio só o que é decisão dele).
2. Em paralelo: `batedor` procura asset gratuito; `programador` escreve o código; `tradutor` espera as chaves.
3. Sem asset bom: `artesao-bpy` modela. Diretor aprova a prévia.
4. Diretor importa e monta no editor (MCP), tira as fotos; lotes grandes vão ao `inspetor`.
5. `tradutor` fecha os idiomas; diretor roda `python tools/ue58/qa/data_lint.py --json` (0 erros) antes do portão.
6. `operador` roda portão e, no fim do lote, pacote, testes do executável e instalação.
7. Diretor confere, faz commit e push, atualiza checklist e `CLAUDE.md`, e resume ao Sergio com foto.

## Registro

Cada delegação que valer registro (o que foi pedido, a quem, quanto ajudou, o que deu errado) entra em uma linha na
tabela abaixo, para o sistema melhorar com o uso.

| Data | Agente | Tarefa | Resultado |
|---|---|---|---|
| 11/11 | batedor (Haiku) | Procurar modelos gratuitos e realistas das 8 espécies da pescaria | Em 1 minuto: 0 de 8 (só low poly, cartum, esqueletos de museu e pagos). Decisão: modelar todos. Admitiu o que não verificou (busca por nome científico), o que é o comportamento certo. |
| 11/11 | artesão (Sonnet) | Modelar os 8 peixes no bpy com textura própria e renderizar as figuras de perfil | 3 rodadas (14 + 18 + 1,5 min): a primeira saiu com cores e garoupa fracas; com a lista de 10 correções do diretor ficou boa; garoupa precisou de uma terceira. Lição: o pedido já deve trazer cores em números e o defeito típico a evitar; a autocrítica dele foi honesta e bateu com a revisão. |


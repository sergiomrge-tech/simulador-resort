# Licenças e créditos de terceiros — checklist comercial (Pacote 9)

**Data da leitura:** 07/11/2026 · commit de referência `0ba71c4c`. Este é o inventário **rastreável nos textos/scripts do Git**, não um parecer legal nem aprovação da build. Não é possível atestar a licença de cada `.uasset` ou dos acervos fora do Git sem conferir aquisição e cook. Antes do Steam release, Sergio deve assinar uma planilha de cada item efetivamente empacotado. Fonte principal: [CREDITS.md](../CREDITS.md), `tools/ue58/radio_tracks.json`, `assets/ui/icons/CREDITS.txt`, `unreal/MareAlta/Content/Python/mare_custom.py`, `tools/ue58/gen_*.py`.

## Inventário de fornecedores e obrigações

| Acervo / componente | Presença ou função no jogo | Licença / uso comercial | Atribuição na tela/documento | Licença / prova |
|---|---|---|---|---|
| **Unreal Engine 5.8** (Epic Games) | Motor e runtime da build principal | Unreal EULA, royalties e regras aplicáveis à distribuição | **Obrigatória se o jogo possui créditos: duas linhas oficiais literais** | https://www.unrealengine.com/eula/unreal |
| **MetaHuman** | Personagens humanos do resort | Termos Unreal Engine; distribuição integrada no produto | Identificar Epic/MetaHuman por transparência; verificar termos de conteúdo externo | https://www.metahuman.com/license |
| **Fab** | Roupas, móveis, bicicletas, vegetação, adereços via biblioteca local | Fab Standard License **permite obra comercial com asset incorporado**, não redistribuição standalone; algumas aquisições podem ter **outras** licenças | Fab Standard não exige atribuição ao publisher; contratos individuais CC BY exigem | https://www.fab.com/eula |
| **Poly Haven** | Texturas de areia, rochas, madeira, plantas; modelos e decorações | CC0 1.0 | Não obrigatória, listar fonte por cortesia | https://polyhaven.com/license |
| **Quaternius** | Vegetação, gramado, animais, personagens/animações legadas | CC0 (conferir pacote individual) | Não obrigatória, recomendada | https://quaternius.com |
| **Kenney** | Food/Pirate Kits e partículas | CC0 | Não obrigatória, recomendada | https://kenney.nl |
| **ambientCG** | Textura Wicker002 e outros materiais | CC0 | Não obrigatória, recomendada | https://ambientcg.com |
| **OpenGameArt** | `music_bossa`, oceano, pássaros, gaivotas, passos, porta, moeda, murmúrios | **CC0 apenas para os itens específicos de CREDITS.md**; não inferir que todo OpenGameArt seja CC0 | Por item, não obrigatória se CC0; conservar página e licença | https://opengameart.org |
| **game-icons.net** — Delapouite, Lorc | Ícones da interface; removido fundo preto e alteradas cores | **CC BY 3.0** | **OBRIGATÓRIA**: autores, fonte, link da licença, indicar alterações. A lista dos ícones está em `assets/ui/icons/CREDITS.txt` | https://game-icons.net e https://creativecommons.org/licenses/by/3.0/ |
| **Nunito** — Vernon Adams / Cyreal / Jacques Le Bailly | UI Nunito SemiBold e ExtraBold | SIL OFL 1.1 | Distribuir íntegra da OFL com as fontes; nomes de copyright conforme texto | https://fonts.google.com/specimen/Nunito |
| **Noto Sans JP / KR / SC** — Google | Glifos para japonês, coreano e chinês | SIL OFL 1.1 | Preservar `Content/UI/Fonts/OFL-NotoSansJP.txt`, `OFL-NotoSansKR.txt`, `OFL-NotoSansSC.txt` na distribuição | https://fonts.google.com/noto |
| **Patrick Hand** | Fonte manuscrita da UI | SIL OFL 1.1 | Preservar `Content/UI/Fonts/OFL-PatrickHand.txt` | https://fonts.google.com/specimen/Patrick+Hand |
| **Caveat** — Impallari Type | Fonte manuscrita para cirílico | SIL OFL 1.1 | **PENDENTE**: `Caveat-Mare.ttf` existe, porém não foi localizado `OFL-Caveat.txt` entre os arquivos rastreados no Git; incluir licença antes de empacotar | https://fonts.google.com/specimen/Caveat |
| **NVIDIA DLSS (condicional)** | DLLs/plugins se incluídos na versão final (fora do Git) | NVIDIA RTX SDK EULA específica da versão | Respeitar notices e regras de redistribuição da versão real, não presumir apenas pelo download | https://developer.nvidia.com/rtx/dlss |
| **Godot Engine (condicional)** | Motor da fase legada; não é dependência presumida do jogo UE | MIT **se efetivamente distribuído** | Incluir copyright/licença somente se binários/trechos do Godot entrarem na build | https://godotengine.org/license |
| **Música/arte procedural próprias** | `tools/ue58/gen_radio_music.py`, objetos Blender `gen_*.py`, síntese numpy | Obra original **desde que** não use amostras, modelos ou imagens protegidos sem licença | Identificar autoria real; inspecionar entradas de bibliotecas externas dos geradores | Rastrear os scripts e assets exportados |
| **Open Lo-Fi — B. Tahir, 12 candidatas** | `radio_cc0_01` a `radio_cc0_12` no catálogo do rádio | CC0 declarado pelo fornecedor, *mas* faixa gerada via Suno e Content ID **não verificado** | Nenhuma obrigatória segundo CC0, porém publicar autor e fonte por cortesia; **HOLD para lançamento e lives** | https://github.com/btahir/open-lofi e [RADIO_MUSICAS.md](ue58/RADIO_MUSICAS.md) |

## Verificação de bibliotecas externas `info.json` — bloqueador documental

- `unreal/MareAlta/Content/Python/mare_custom.py:10,27` lê diretórios locais `D:/Assets/PolyHaven`, `D:/Assets/Fab`, `D:/Assets/Mare` e procura `<slug>/info.json`. **Nenhum `info.json` está versionado na árvore examinada** (25.129 caminhos). Portanto não é possível vincular **cada** `.uasset` ao autor, URL e licença exclusivamente pelo Git.
- Os geradores `tools/ue58/gen_*.py` constroem malhas via Blender e por vezes leem arquivos de acervos externos. **Gerar malha por Python não torna original um modelo de entrada externo.** Pedir relatório dos caminhos de importação, hash dos originais e `info.json` correspondentes.
- Auditoria obrigatória no computador de build: exportar inventário `/Game/Custom/**`, `/Game/World/**`, `/Game/Audio/**`, MetaHuman, roupas e Fab. Cruzar com `Content/Data/custom_assets.json`, Script de importação e comprovantes **antes de distribuir**. Se não houver licença comprovada, substituir ou remover do pacote, não só ocultar na tela.

## Rádio: publicação vs streaming

`tools/ue58/radio_tracks.json` marca as 12 candidatas `approved_for_game_release=false` e `content_id_clearance=not_verified`. A declaração CC0 do Open Lo-Fi **não equivale** a comprovação de ausência de reivindicações automáticas em YouTube/Twitch. A autorização geral para uso comercial/stream pela licença pode coexistir com avisos ou claims. **Decisão de release: manter as faixas em HOLD até ouvir os áudios, validar a cadeia de titularidade e o risco real de Content ID; ou retirar faixas não aprovadas da build.** Como `radio.json` e `audio.json` são intocáveis neste pacote, o Claude/Sergio fará o gate sem aprovar músicas por omissão. As faixas originais sintetizadas não têm a mesma pendência do fornecedor, mas devem ser comprovadas.

## Avisos obrigatórios Unreal

O item 7(a) do EULA da Unreal determina, **se houver créditos no jogo**, os dois avisos abaixo, atualizando o ano corrente:

> Coconut Coast: Resort Simulator uses Unreal® Engine. Unreal® is a trademark or registered trademark of Epic Games, Inc. in the United States of America and elsewhere.

> Unreal® Engine, Copyright 1998 – 2026, Epic Games, Inc. All rights reserved.

Fonte: https://www.unrealengine.com/eula/unreal (verificar texto vigente imediatamente antes do lançamento). MetaHuman segue licença Unreal. Não usar logos/trademarks da Epic além do permitido sem licença específica.

## Como cumprir CC BY 3.0 de game-icons.net

Proposta visível na tela de créditos e em `CREDITS.md` distribuído:

**Ícones adaptados de game-icons.net por Delapouite e Lorc — CC BY 3.0 — https://creativecommons.org/licenses/by/3.0/. Alterações: fundo preto removido e cores aplicadas no jogo. Ícones e seus respectivos criadores: `assets/ui/icons/CREDITS.txt`.**

O crédito da equipe técnica **não substitui** a atribuição de autores dos ícones. Confirmar se o arquivo atualizado acompanha o build empacotado.

## Fontes: auditoria OFL

Os textos presentes em `Content/UI/Fonts/`: `OFL-NotoSansJP.txt`, `OFL-NotoSansKR.txt`, `OFL-NotoSansSC.txt`, `OFL-Nunito.txt`, `OFL-PatrickHand.txt`. Fonte `Caveat-Mare.ttf` aparece no mesmo diretório, **sem OFL específico rastreado**. Verificar copyright do subset e reserva de nome; incorporar os textos no diretório de licenças da distribuição Windows, não confiar que `.uasset` de fontes carrega a licença.

## Gate de comercialização / roteiro do Sergio

| Estado | Item | Dono | Ação obrigatória |
|---|---|---|---|
| **BLOQUEADOR** | 12 candidatas Open Lo-Fi sem prova de Content ID | Sergio + Claude | Aprovar individualmente ou excluir da build; testar gravações de live |
| **BLOQUEADOR** | Metadados locais `info.json` de Fab/PolyHaven/Mare indisponíveis no Git | Sergio | Exportar lista dos arquivos da instalação + comprovações/URL/licença por asset |
| **BLOQUEADOR** | Avisos UE + autores CC BY incompletos nos créditos do jogo | Claude | Integrar `credits.json` à UI real e final da dívida; verificar na build |
| **BLOQUEADOR** | Licença Caveat não rastreada com fonte | Claude | Juntar OFL e copyrights efetivos na distribuição |
| **CONDICIONAL** | DLLs NVIDIA DLSS e assets Fab/MetaHuman | Claude + Sergio | Comparar todos os termos com a build cozinhada |
| **PÓS-INTEGRAÇÃO** | Créditos localizados em 13 idiomas | Claude | Consumer e testes de UI; títulos em `Content/Data/credits.json` |
| **VALIDAÇÃO** | Hashes/links e listagem completa | Sergio | Assinar inventário versão/build + registrar provas datadas |

Este documento não autoriza publicar uma build bloqueada. A atribuição necessária deve estar visível e os arquivos de licença devem ser distribuídos adequadamente.

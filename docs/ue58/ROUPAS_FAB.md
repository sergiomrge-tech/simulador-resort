# Roupas do Fab para as MetaHumans (02/11/2026)

Roupas reais, gratuitas e paramétricas (o guarda-roupa da MetaHuman ajusta a peça a qualquer corpo), baixadas
do Fab com a conta do Sergio (licença Fab Standard, uso comercial permitido; contrato aceito em 02/11 com
autorização dele no chat). Ficam fora do git por tamanho e licença (`.gitignore`); esta lista permite baixar de novo.

| Peça | Autor | Anúncio (uid) | Arquivo | Instala em |
|---|---|---|---|---|
| Bermuda (MetaHuman Shorts) | Epic Games | 1904a7ee-66f6-4e09-9d4a-b3eea464b761 | oa_shorts.mhpkg (278 MB) | /Game/Outfits/Shorts |
| Camisetas (T Shirt Variants: curta, 3/4, longa…) | Epic Games | 1b1009ae… | oa_tshirtvariants.mhpkg (1,8 GB) | /Game/Outfits/OA_Crewneckt, OA_Tshirt* |
| Camiseta por dentro (Tucked T Shirt Variants) | Epic Games | 839b9239-5ea4-40a0-90b3-076e0d9959f7 | oa_tuckedtshirtvariants.mhpkg (1,9 GB) | /Game/Outfits/OA_CrewnecktTk, OA_TshirtTk* |
| Cropped (Crop Top Variants) | Epic Games | 39bcebb4… | oa_croptopvariants.mhpkg (1,4 GB) | /Game/Outfits/OA_TCrop* |
| Chinelo (FlipFlops) | Epic Games | 73272acc… | oa_flipflops.mhpkg (210 MB) | /Game/Outfits/Flipflops |
| Sapatilha (Flats) | Epic Games | 735c8256-e1b2-4157-b411-9e53ed6f34f2 | oa_flats.mhpkg (251 MB) | /Game/Outfits/Flats |
| Mocassim (Loafers) | Epic Games | 2f631109-17ab-4c87-a78c-5148927de957 | oa_loafers.mhpkg (251 MB) | /Game/Outfits/Loafers |
| Vestido curto (Customizable Mini Dress_01) | Mukilartz | 8a2c223f… | oa_minidress01_variant.mhpkg (94 MB) | /Game/OutFits/MiniDress01 |
| Maiô (The Aeron Swimsuit) | QuingKhaos | da1bb5d0… | khaosmdf379_ue57.mhpkg (819 MB) | /Game/Outfits/KhaosMDF379 |
| Casual masculino (camisa, bermuda, tênis) | Wizark Studios | c556fd02-6daa-46a8-b8d9-9994a781905e | oa_casual_m_outfit.mhpkg (273 MB) | /Game/MetaOutfits/Casual_M_Outfit |
| Casual feminino | Wizark Studios | 575d159d-f0ad-44e1-982c-bf36274f97a7 | oa_casual_f_outfit.mhpkg (313 MB) | /Game/MetaOutfits/Casual_F_Outfit |

Pacotes guardados em `D:\CodexTemp\fab`.

## Como baixar sem passar pelo C:
No Chrome logado no Fab, a API `GET /i/listings/<uid>/asset-formats` lista os arquivos e
`GET /i/listings/<uid>/asset-formats/metahuman/files/<fileUid>/download-info` devolve o link assinado (dura
poucos minutos): baixar na hora com `curl` direto no D:. O download comum do Chrome deixa `.tmp` no C:.

## Como instalar
O `.mhpkg` é um ZIP com `Manifest.json`. A base de instalação NÃO é sempre a pasta do `objectPath`: nos pacotes
de variantes (camisetas, cropped) os caminhos do ZIP são relativos a `/Game/Outfits`. Calcular a base comparando
`dependentPackages` com os nomes do ZIP e extrair os `.uasset` em `Content/<base sem /Game/>` com o editor fechado.

## Como vestir uma MetaHuman
`mare_metahuman.dress_variant(nome, sufixo, [WI_...])` (ação MCP `mh_dress`, "Mateo@Beach@/Game/.../WI_A,/Game/.../WI_B")
duplica `MH_<nome>` em `MH_<nome>_<sufixo>`, adiciona as peças ao slot `Outfits` (várias peças juntas) e
`build('<nome>_<sufixo>')` constrói. Prova: `MH_Mateo_Beach` com camiseta, bermuda e chinelo
(`docs/ue58/graphics-reference/roupa-fab-mateo-20261102.jpg`). Builds de MetaHuman: no máximo 5 por sessão do
editor (memória).

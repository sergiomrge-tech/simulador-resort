# Maré Alta Resort — Palácio de Memória

Regras aprendidas com erros reais deste projeto. Leia antes de mexer em qualquer coisa.
Cada "cômodo" guarda um tipo de erro: o que aconteceu, a regra e como conferir.
Ao corrigir um erro novo, acrescente uma linha no cômodo certo (ou crie um cômodo).

Projeto: Godot 4.5.1, Forward+, GDScript, estilo cartoon (referência: Barfender CO-OP).
Base de trabalho: v0.6.5 recuperada; versões atuais em `project.godot` / `export_presets.cfg`.

---

## 🚪 Hall de entrada — regras fixas do Sergio
- **Nada de low poly**, principalmente móveis, casas e pessoas. Cilindro/esfera com poucos lados, caixa crua e corpo facetado são proibidos.
- Visual cartoon colorido, iluminação quente e neon, personagens caricatos, gestão pelo celular.
- O jogo começa só com o quiosque e evolui por expansões.
- Quiosque abre às 8h e fecha às 18h (21h com neon); depois do horário não chega cliente.
- Cliente senta, lê o cardápio, pede e fica comendo ou bebendo com animação. Não levanta logo depois de atendido.
- Ninguém atravessa o quiosque nem as mesas.
- Prompt de interação fica embaixo, nunca no centro da tela.
- Entrega final = instalador (NSIS) em `D:\Jujuba\MareAltaResort\builds\vX.Y.Z\` + push no GitHub.

## 🧱 Sala das Faces — geometria gerada por código
- **Erro (v0.7.1–0.7.3):** `rounded_box`, `arch` e o telhado detalhado foram montados com triângulos anti-horários. A Godot considera **horário = frente**. Resultado: todas as caixas do jogo do avesso, "paredes transparentes" com o interior da casa aparecendo.
- **Regra:** toda malha feita com `SurfaceTool` passa por `B.fix_winding(arr)` / `B.cw_mesh(arr)`, que acertam a ordem pela normal.
- **Conferir:** render com a câmera colada numa parede (`--cam=`). Se aparecer o que está atrás, a malha está do avesso.

## 🎈 Sala das Coisas Flutuantes — apoio e altura
- **Erro:** garrafas e rádio fora da estante (estante com 1,24 m de largura e garrafas espalhadas por 2,8 m); pranchas inclinadas sem nada atrás; cordas de 5–8 mm invisíveis (vaso e cocos pareciam voar); cordas que não chegavam até a viga.
- **Erro:** cooler e caixote posicionados dentro da parede lateral do quiosque (parede de 0,6 m de espessura em x = ±2,0).
- **Regra:** todo objeto precisa de um apoio visível. Calcule a altura do topo da superfície (centro + metade da altura) e a extensão da peça **antes** de posicionar.
- **Regra:** corda ou corrente tem pelo menos 12 mm de raio e vai do objeto até a viga ou o beiral, com o comprimento calculado.
- **Regra:** antes de colocar um prop, confira as paredes e os móveis em volta (posição ± metade do tamanho, já com a rotação).
- **Conferir:** render de perto (`--cam=`) de cada canto novo.

## 🧭 Sala dos Nós Perdidos — transformações
- **Erro:** `look_at_from_position(cyl.position, ...)` usa posição **global**, mas recebia a posição **local** de um filho. As barras da bicicleta e as cordas da rede foram parar longe, e só sobravam as rodas.
- **Regra:** para cilindro ou cápsula entre dois pontos locais, use `B._beam(parent, a, b, raio, mat)`. Nunca use `look_at*` em nó filho com coordenadas locais.

## 🪜 Sala do Chão — z-fighting e contorno
- **Erro:** o deslocamento em y para evitar z-fighting crescia sem limite (`0.008 * n`), virando degraus no chão.
- **Regra:** use deslocamento cíclico: `y + passo * (n % 4)`.
- **Erro:** o contorno cartoon usava a 2ª derivada da profundidade linear, que gera linhas tracejadas em todo piso visto de lado (o "chão tremendo" ao andar).
- **Regra:** o contorno usa a 2ª derivada de **1/profundidade**, que é linear na tela sobre planos. O contorno só funciona sem MSAA (use FXAA).

## 👥 Sala das Pessoas
- O corpo vem de `assets/models/ual/guest.glb` (manequim Quaternius), com zonas de cor gravadas em `COLOR.r` por `tools/color_zones.py`. Se trocar ou suavizar a malha, **rode o color_zones de novo**.
- Chapéus e cabelos ficam presos ao osso `Head`, e a cabeça é aumentada pelo `head_scaler`. Confira se a aba não corta os olhos (aba de palha em y ≥ 0,245).
- Pedestres: 12 no modo HD e 5 no leve (o Sergio pediu metade). Não aumente sem pedir.
- Bloqueios (`block_rects`) cobrem mesa **e** cadeiras. O bloco que contém o destino final do NPC não barra a chegada dele (`_slide_out_of_blocks`).
- **Blender (bpy 5.x):** não use `bpy.ops.object.modifier_move_up` em script (laço infinito). Use `obj.modifiers.move(i, 0)`. Nunca chame um script de `inspect.py` (conflita com o módulo padrão do Python).

## 🖥️ Sala do Vídeo
- DirectX 12: opção "API gráfica" grava um `override.cfg` ao lado do .exe (com volta automática para o Vulkan).
- DLSS **não existe na Godot**. O upscaler é o FSR 2.2 / FSR 1, na opção "Upscaling" + "Escala 3D".

## 🧪 Sala da Conferência — antes de entregar
1. `godot --headless --check-only -s scripts/X.gd` em todo script editado. Erros "Identifier not found: Core/Quality/Economy" são normais (autoloads). Qualquer outro erro bloqueia.
2. Erros já cometidos: função duplicada no mesmo arquivo (`oil_lamp`); `var w: = M.algo` sem tipo (use `var w: Material = ...`).
3. Prints: `./shot.sh nome` ou câmera livre com `--cam=x,y,z,yaw,pitch[,hora]` (ver `main.gd`). Olhe de perto paredes, móveis, pessoas e chão.
4. `tests/loop_test.gd` precisa dar LOOP_TEST PASS.
5. Versão em `project.godot`, `export_presets.cfg` e `installer/setup.nsi`; depois exporte, rode o `makensis`, entregue no PC e faça o push.
6. Arquivos acima de 30 MB para o PC: primeiro `SendUserFile`, depois commit com o `fileUuid`.

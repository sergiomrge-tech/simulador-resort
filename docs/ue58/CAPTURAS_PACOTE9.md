# Capturas automatizadas para Steam — Pacote 9

O executável `tools/ue58/qa/marketing_shots.py` registra 10 enquadramentos da **demo**, resolução obrigatória 1920×1080, e associa as capturas aos 12 planos de 60 segundos do [roteiro](../steam/trailer_roteiro.md). Ele reaproveita `qa_gate.py` (`pie`, `hud`, `coast`) e `pool_swim_qa.py` (`CHAIN`). Somente funciona para captura com Unreal Editor aberto, servidor MCP ativo e perfil QA descartável.

**Prévia segura no PC** (sem engine): `python tools/ue58/qa/marketing_shots.py --plan`.

**Captação real** (editores/servidor/editor jogo teste): `python tools/ue58/qa/marketing_shots.py --capture --qa-save-confirmed --interactive`.

Arquivos: `D:/CodexTemp/qa/marketing_shots/01_quiosque_1920x1080.png` ... `10_mirante_pordosol_1920x1080.png`, `plan.json`, `report.json`. Modo interativo obriga confirmação física de cada cena. Para locais não cartografados, usar `--camera-json D:/.../cameras.json` com `{ "04_pousada": {"x": 0,"y":0,"z":150,"pitch":-10,"yaw":45} }` **apenas substituindo as coordenadas pelos valores medidos no editor**. O exemplo 0,0 é ilustrativo, não câmera aprovada.

**Atenção:** `mare.Shot` e a captura por `coast('pie')` precisam do editor configurado para a viewport real de 1920×1080; a ferramenta **rejeita** imagens de tamanho diverso, não estica/resample. Os novos clipes do Open Lo-Fi e a carta/saldo da dívida são bloqueadores até aprovação. O modo QA compra expansões e força nadadores: não usar no save real, não anunciar cena como progressão alcançada em 2h sem provar. No trailer, a cartela editorial não é gameplay nem screenshot da loja.

# Maré Alta Resort 🌴

Simulador de quiosque e pousada em primeira pessoa numa vila de pescadores do Nordeste brasileiro, feito em **Godot 4.5.1** para PC (Windows/Steam).

- **v0.6.5** (base recuperada do build) — quiosque, pousada, bangalôs com melhorias, estoque, equipe, clima, vila e serra.
- **v0.7 (em desenvolvimento)** — começa só com o quiosque e evolui até o resort; visual cartoon colorido; gestão pelo celular; personagens caricatos.

## Rodar
1. Godot **4.5.1** (padrão, não .NET). Abra `project.godot`.
2. Assets realistas antigos (Poly Haven) são opcionais: `tools/fetch_assets.*`. O jogo roda sem eles.
3. Teste automático: `godot --headless --audio-driver Dummy --path . -- --loop-test` → `LOOP_TEST PASS`.

Créditos e licenças em [`CREDITS.md`](CREDITS.md).

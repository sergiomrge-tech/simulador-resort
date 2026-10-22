# Fontes artísticas do quiosque

`kiosk_facade.blend`, `kiosk_neon_trim.blend`, `kiosk_roof.blend`,
`kiosk_workbench.blend` e `kiosk_blender.blend` são modelos originais deste projeto,
gerados por `tools/gen_kiosk_facade.py`. O arquivo principal contém a textura de
madeira incorporada. Todos os arquivos são reabertos pelo gerador para conferir a
portabilidade, sem depender de caminhos de uma sessão do artista.

Blender 4.5.3, metros, Z para cima e frente em -Y. As peças preservam coordenadas
arquitetônicas: chão em Z=0; faixa de neon entre Z=1,952 e 2,548; base da cobertura
em Z=2,84. O telhado tem doze fiadas de feixes sobrepostos. A exportação para
Godot é GLB em `assets/models/gen/`, com materiais separados para pintura, madeira,
latão, corda, marfim e luz. Fontes artísticas são ignoradas pelo importador Godot
(`art/.gdignore`) e não entram no pacote jogável.

Madeira: textura CC0 `oak_wood_planks` da Poly Haven, já usada no projeto. Demais
materiais e malhas são autorais. Consultar também `CREDITS.md`.

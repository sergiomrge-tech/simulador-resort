"""Panelled wooden house door with brass hardware, hinge at origin.

Adds kick plate, letter slot, peephole and deeper panel moulding so the
entrance reads as a real door rather than a flat slab.
"""
import sys
from pathlib import Path
import bpy
_TOOLS = Path(__file__).resolve().parent if "__file__" in dir() else Path("/workspace/tools")
if str(_TOOLS) not in sys.path:
	sys.path.insert(0, str(_TOOLS))
from gen_coastal_traffic import box, save

root = Path(__file__).resolve().parents[1] if "__file__" in dir() else Path("/workspace")
facade_src = root / "tools/gen_kiosk_facade.py"
if not facade_src.exists():
	facade_src = Path("/workspace/tools/gen_kiosk_facade.py")
	root = Path("/workspace")
exec(facade_src.read_text(encoding="utf-8").split("# Balcão:")[0])
doorwood = material("home_door_oak", (0.58, 0.43, 0.29), texture="oak_wood_planks_diff.jpg")
darkwood = material("home_door_shadow", (0.32, 0.22, 0.14), texture="oak_wood_planks_diff.jpg")
# Stiles and rails.
for x in [-1.095, -0.055]:
	box("Door stile", (0.11, 0.065, 2.2), (x, 0, 1.1), doorwood, 0.008)
for z in [0.065, 0.74, 1.47, 2.135]:
	box("Door rail", (1.04, 0.065, 0.13), (-0.575, 0, z), doorwood, 0.008)
# Recessed panels with moulding on both faces.
for z in [0.40, 1.10, 1.80]:
	box("Recessed door panel", (0.93, 0.028, 0.57), (-0.575, 0, z), darkwood, 0.008)
	for face in [-1, 1]:
		for x in [-1.035, -0.115]:
			box("Panel moulding", (0.028, 0.028, 0.57), (x, face * 0.028, z), doorwood, 0.007)
		for zz in [z - 0.285, z + 0.285]:
			box("Panel moulding", (0.94, 0.028, 0.028), (-0.575, face * 0.028, zz), doorwood, 0.007)
# Kick plate + threshold feel.
box("Brass kick plate", (1.02, 0.012, 0.22), (-0.575, 0.038, 0.16), brass, 0.004)
box("Inner kick plate", (1.02, 0.012, 0.22), (-0.575, -0.038, 0.16), brass, 0.004)
# Letter slot.
box("Letter slot plate", (0.28, 0.014, 0.06), (-0.575, 0.04, 1.42), brass, 0.003)
box("Letter slot opening", (0.22, 0.02, 0.018), (-0.575, 0.0, 1.42), darkwood, 0.002)
# Peephole ring.
lathe("Door peephole", [(0.012, 0), (0.012, 0.02)], (-0.575, 0.04, 1.72), brass)
# Handles + hinges.
for face in [-1, 1]:
	box("Handle escutcheon", (0.035, 0.018, 0.16), (-0.99, face * 0.046, 1.0), brass, 0.008)
	path("Brass handle", [(-0.99, face * 0.055, 1.03), (-0.99, face * 0.10, 1.03), (-0.87, face * 0.10, 1.03)], 0.014, brass)
for z in [0.25, 1.1, 1.95]:
	lathe("Door hinge", [(0.017, 0), (0.017, 0.10)], (-0.005, 0, z), brass)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.convert(target="MESH")
save("player_home_door")

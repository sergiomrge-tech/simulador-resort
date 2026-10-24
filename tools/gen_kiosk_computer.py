"""Original desktop terminal: bevelled monitor, stand, keyboard and mouse.

Materials stay graphite / aluminium — never mint or teal. Godot may import
linear colours as sRGB; keep authored RGB already in the mid-grey range so
the back does not wash out cyan under toon + cool lights.
"""
import sys
from pathlib import Path
import bpy

_TOOLS = Path(__file__).resolve().parent if "__file__" in dir() else Path("/workspace/tools")
if str(_TOOLS) not in sys.path:
	sys.path.insert(0, str(_TOOLS))
from gen_coastal_traffic import box, save
from gen_code_props import mat

bpy.ops.wm.read_factory_settings(use_empty=True)
# Mid graphite (not near-black linear — that turns mint under cool fill lights).
case = mat("terminal graphite", (0.18, 0.19, 0.20), 0.72)
edge = mat("terminal aluminium", (0.55, 0.56, 0.55), 0.42, metal=0.35)
glass = mat("terminal glass", (0.08, 0.09, 0.10), 0.15)
screen = mat("terminal screen", (0.10, 0.12, 0.13), 0.55)
paper = mat("terminal dashboard", (0.78, 0.80, 0.78), 0.85)
key = mat("terminal keys", (0.22, 0.23, 0.24), 0.7)

# Base plate + neck (aluminium bezel family).
box((0.24, 0.15, 0.018), (0, 0, 0.009), edge)
box((0.045, 0.04, 0.16), (0, 0.015, 0.092), edge)
# Monitor shell (graphite plastic).
box((0.44, 0.045, 0.285), (0, 0, 0.31), case, 0.018)
# Rear vent ribs (readable from behind — kills the flat mint slab look).
for i in range(5):
	box((0.34, 0.006, 0.012), (0, 0.024, 0.24 + i * 0.035), edge, 0.002)
# Front glass / screen / soft dashboard tiles.
box((0.409, 0.009, 0.252), (0, -0.025, 0.31), glass)
box((0.391, 0.006, 0.235), (0, -0.031, 0.31), screen)
for row in range(2):
	for col in range(3):
		box((0.102, 0.003, 0.075), (-0.123 + col * 0.123, -0.036, 0.26 + row * 0.1), paper, 0.005)
# Keyboard + mouse.
box((0.32, 0.115, 0.015), (0, -0.18, 0.010), case)
for row in range(4):
	for col in range(12):
		box((0.020, 0.017, 0.008), (-0.14 + col * 0.025, -0.22 + row * 0.025, 0.021), key, 0.003)
box((0.065, 0.10, 0.025), (0.235, -0.18, 0.017), case, 0.012)
box((0.008, 0.022, 0.008), (0.235, -0.19, 0.033), edge, 0.003)
save("kiosk_computer")

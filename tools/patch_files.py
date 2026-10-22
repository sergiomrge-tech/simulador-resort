"""Lista fontes do patch, inclusive modelos carregados dinamicamente e ignorados pelo Git."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def patch_files(base):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").splitlines()

    files = set(git("diff", "--name-only", base, "--", "scripts", "shaders", "scenes", "assets", "*.tscn"))
    files.update(git("ls-files", "--others", "--exclude-standard", "--", "scripts", "shaders", "scenes", "assets"))
    # qnat não estava no pacote 1.0 e é ignorado pelo Git. O diff sozinho nunca o inclui.
    files.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "assets/models/qnat").glob("*.gltf"))
    real = (ROOT / "scripts/real.gd").read_text(encoding="utf-8")
    aliases = real.split("const ALIAS: = {", 1)[1].split("}", 1)[0]
    for key in re.findall(r':\s*"([^"]+)"', aliases):
        if key.startswith("g:"):
            files.add(f"assets/models/gen/{key[2:]}.glb")
        elif ":" not in key:
            for folder in ("models", "models_hd"):
                files.add(f"assets/{folder}/{key}/{key}.gltf")
    missing = [p for p in files if p.endswith((".gltf", ".glb")) and not (ROOT / p).is_file()]
    if missing:
        raise RuntimeError("Modelos do patch ausentes: " + ", ".join(sorted(missing)))
    if not any(p.startswith("assets/models/qnat/") for p in files):
        raise RuntimeError("Patch sem qnat: execute tools/fetch_assets.py antes de exportar")
    return sorted(p for p in files if (ROOT / p).is_file() and Path(p).suffix in {
        ".gd", ".gdshader", ".glb", ".gltf", ".ogg", ".tscn", ".tres", ".png", ".jpg"
    })


if __name__ == "__main__":
    print("\n".join(patch_files(sys.argv[1])))

"""Abre o pacote exportado, constrói toda a v1 e exige print e log sem recursos ausentes."""
from pathlib import Path
import argparse
import os
import re
import shutil
import subprocess


def run(engine, pack):
    root = Path(__file__).resolve().parents[1]
    shots = root / "shots"
    shots.mkdir(exist_ok=True)
    shot = shots / "smoke.png"
    shot.unlink(missing_ok=True)
    command = [engine, "--main-pack", str(Path(pack).resolve()), "--rendering-driver", "opengl3",
               "--rendering-method", "gl_compatibility", "--resolution", "1280x720", "--",
               "--shot=smoke", "--cam=60,4,20,180,-10,12", "--quality=1", "--v1", f"--out={shot}"]
    if os.name != "nt" and not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        command = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24", *command]
    log = shots / "smoke.log"
    with log.open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Smoke excedeu 600 s: {log}") from exc
    errors = re.findall(r"^.*(?:not found|SCRIPT ERROR|REAL_MISSING).*$", log.read_text(encoding="utf-8", errors="replace"), re.I | re.M)
    if result.returncode or not shot.is_file() or errors:
        raise RuntimeError(f"Smoke falhou (exit={result.returncode}, print={shot.is_file()}):\n" + "\n".join(errors[:20]) + f"\nLog: {log}")
    print(f"SMOKE_EXPORT PASS: {pack}; {shot}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine")
    parser.add_argument("pack")
    args = parser.parse_args()
    run(args.engine, args.pack)

#!/usr/bin/env python3
"""Cria índice de paths .uasset comprovados por git ls-tree (sem abrir nem modificar assets).
Uso: python tools/ue58/qa/build_package_index.py --output /tmp/pacote8-index.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = "unreal/MareAlta/Content/"
DATA = ROOT / CONTENT / "Data"

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def build():
    revision = git("rev-parse", "HEAD")
    paths = git("ls-tree", "-r", "--name-only", "HEAD", "unreal/MareAlta/Content").splitlines()
    packages = sorted({"/Game/" + p[len(CONTENT):-7] for p in paths if p.startswith(CONTENT) and p.endswith(".uasset")})
    sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*.json"))}
    return {
        "revision": revision,
        "_doc": "Índice do Git, paths .uasset reais da árvore na revision e SHA256 dos Data JSON da coleta; não demonstra LoadObject nem valida conteúdo binário.",
        "scope": ["Todos os packages .uasset registrados no Git sob unreal/MareAlta/Content"],
        "packages": packages,
        "data_sha256": sha,
    }

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--log-chunks", action="store_true", help="envia partes delimitadas ao log CI para registrar o índice no repositório")
    a = cli.parse_args()
    index = build()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(index, ensure_ascii=False, indent=1) + "\n"
    a.output.write_text(txt, encoding="utf-8")
    print(f"Índice: {len(index['packages'])} packages Git, {len(index['data_sha256'])} JSON, {a.output}")
    if a.log_chunks:
        # JSON ASCII compacto em blocos pequenos; o conector recupera os logs e verifica o SHA.
        payload = json.dumps(index, ensure_ascii=True, separators=(",", ":"))
        for n in range(0, len(payload), 3500):
            print(f"PACOTE8_INDEX_{n//3500:04d}={payload[n:n+3500]}")
        print("PACOTE8_INDEX_END=" + hashlib.sha256(payload.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()

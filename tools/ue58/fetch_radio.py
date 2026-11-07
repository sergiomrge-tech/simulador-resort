#!/usr/bin/env python3
"""Baixa arquivo CC0 verificado do Open Lo-Fi, extrai 12 faixas em D:/Assets/Audio/radio/.
O download NÃO significa liberação de Content ID; artefatos são somente candidatos.
Uso:
 python tools/ue58/fetch_radio.py --list
 python tools/ue58/fetch_radio.py --download
 python tools/ue58/fetch_radio.py --download --dest D:/Assets/Audio/radio/
 python tools/ue58/fetch_radio.py --audit
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tools/ue58/radio_tracks.json"
DEFAULT = Path("D:/Assets/Audio/radio/")


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dest_guard(dest: Path):
    root = ROOT.resolve()
    path = dest.resolve()
    if path == root or root in path.parents:
        raise ValueError(f"não escreva áudio dentro do repositório: {path}")
    return path


def download(url, target):
    request = urllib.request.Request(url, headers={"User-Agent": "CoconutCoast-RadioQA/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as out:
        for block in iter(lambda: response.read(1024 * 1024), b""):
            out.write(block)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--dest", type=Path, default=DEFAULT)
    cli.add_argument("--download", action="store_true", help="baixa ZIP ~555 MB e extrai apenas as 12 faixas")
    cli.add_argument("--audit", action="store_true", help="confere hashes dos arquivos locais registrados")
    cli.add_argument("--list", action="store_true")
    args = cli.parse_args()
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dest = dest_guard(args.dest)
    if args.list:
        for track in m["tracks"]:
            print(f"{track['filename']} | {track['license']} | CID: {track['content_id_clearance']}")
        return 0
    if not args.download and not args.audit:
        cli.error("informe --download, --audit ou --list")
    dest.mkdir(parents=True, exist_ok=True)
    audit_path = dest / "radio_hashes_local.json"
    if args.download:
        archive = dest / "openlofi-v1.0.0.zip"
        if not archive.exists() or sha256(archive) != m["archive_sha256"]:
            if archive.exists():
                archive.unlink()
            with tempfile.NamedTemporaryFile(prefix=".radio-", suffix=".zip", dir=dest, delete=False) as tmp:
                partial = Path(tmp.name)
            try:
                print("Baixando ZIP oficial (~555 MB)...")
                download(m["archive_url"], partial)
                digest = sha256(partial)
                if digest != m["archive_sha256"]:
                    raise ValueError(f"SHA256 do ZIP divergiu: {digest} (esperado {m['archive_sha256']})")
                os.replace(partial, archive)
            finally:
                partial.unlink(missing_ok=True)
        if sha256(archive) != m["archive_sha256"]:
            raise ValueError("SHA256 inválido: pacote recusado")
        with zipfile.ZipFile(archive) as z:
            names = {Path(name).name: name for name in z.namelist() if name.lower().endswith(".mp3")}
            for track in m["tracks"]:
                name = track["filename"]
                if Path(name).name != name or name not in names:
                    raise ValueError(f"arquivo ausente/inseguro no ZIP: {name}")
                data = z.read(names[name])
                digest = hashlib.sha256(data).hexdigest()
                if track.get("sha256") and digest != track["sha256"]:
                    raise ValueError("SHA256 individual inesperado: " + name)
                final = dest / name
                with tempfile.NamedTemporaryFile(prefix=".track-", suffix=".part", dir=dest, delete=False) as tmp:
                    partial = Path(tmp.name)
                    tmp.write(data)
                os.replace(partial, final)
                print(f"{name} sha256={digest}")
        print("Aviso: conteúdo SOMENTE PARA QA; NÃO aprovado para lives até confirmação de Content ID.")
    if args.audit or args.download:
        report = {"archive_sha256": m["archive_sha256"], "stream_safe_approved": False, "files": {}}
        failures = []
        for track in m["tracks"]:
            path = dest / track["filename"]
            if not path.is_file():
                failures.append("ausente: " + path.name)
                continue
            digest = sha256(path)
            if track.get("sha256") and digest != track["sha256"]:
                failures.append("HASH INCORRETO: " + path.name)
            report["files"][path.name] = {"sha256": digest, "size_bytes": path.stat().st_size,
                                         "license": track["license"], "stream_safe_approved": False}
        audit_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Hash audit: {len(report['files'])}/{len(m['tracks'])}. Registro: {audit_path}")
        for fail in failures:
            print(f"ERRO: {fail}", file=sys.stderr)
        return int(bool(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())

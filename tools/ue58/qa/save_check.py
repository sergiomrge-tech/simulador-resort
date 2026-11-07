#!/usr/bin/env python3
"""Checagem estrutural read-only do save JSON contra Data/default_save.json."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "unreal/MareAlta/Content/Data/default_save.json"
FIXTURES = Path(__file__).with_name("fixtures")

class InvalidSave(ValueError):
    pass

def pairs(items):
    d = {}
    for k, v in items:
        if k in d:
            raise InvalidSave("chave duplicada: " + k)
        d[k] = v
    return d

def parse(path):
    def nonfinite(v):
        raise InvalidSave("número não finito: " + v)
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=pairs, parse_constant=nonfinite)
    except (OSError, ValueError, UnicodeError) as e:
        raise InvalidSave(f"{path}: {e}") from e

def ptr(parts):
    return "/" + "/".join(str(x).replace("~", "~0").replace("/", "~1") for x in parts)

def validate(save, default):
    errors, missing, notices = [], [], []
    def walk(obj, template, path=()):
        p = ptr(path)
        if isinstance(template, dict):
            if not isinstance(obj, dict):
                errors.append(f"{p}: esperado objeto")
                return
            for k, v in template.items():
                if k not in obj:
                    missing.append(ptr(path + (k,)))
                else:
                    walk(obj[k], v, path + (k,))
        elif isinstance(template, list):
            if not isinstance(obj, list):
                errors.append(f"{p}: esperado lista")
            elif template:
                for i, elem in enumerate(obj):
                    walk(elem, template[0], path + (i,))
        elif isinstance(template, bool):
            if type(obj) is not bool:
                errors.append(f"{p}: esperado booleano")
        elif isinstance(template, (float, int)):
            if type(obj) not in (int, float) or not math.isfinite(obj):
                errors.append(f"{p}: esperado número finito")
        elif isinstance(template, str):
            if not isinstance(obj, str):
                errors.append(f"{p}: esperado texto")
    if not isinstance(save, dict):
        return ["/: esperado objeto principal"], [], []
    walk(save, default)
    for k in ("money", "day", "minutes"):
        v = save.get(k)
        if type(v) in (float, int) and v < 0:
            errors.append(f"/{k}: não pode ser negativo")
    v = save.get("v")
    if v is not None:
        if type(v) not in (int, float) or not math.isfinite(v) or v < 1 or int(v) != v:
            errors.append("/v: deve ser inteiro positivo")
        elif v < default.get("v", 0):
            notices.append(f"save legado v{v:g}; migrar sem descartar campos extras")
        elif v > default.get("v", 0):
            notices.append("save de versão futura; não sobrescrever automaticamente")
    return errors, missing, notices

def inspect(path, default, backup=False):
    used = Path(path)
    try:
        data = parse(used)
    except InvalidSave as first:
        if not backup:
            return {"arquivo": str(used), "status": "corrompido", "erros": [str(first)], "faltantes": [], "avisos": []}
        used = Path(str(used) + ".bak")
        try:
            data = parse(used)
        except InvalidSave as second:
            return {"arquivo": str(path), "status": "corrompido", "erros": [str(first), str(second)],
                    "faltantes": [], "avisos": []}
    errors, missing, notices = validate(data, default)
    if used != Path(path):
        notices.insert(0, "leitura do .bak; nenhum arquivo foi alterado")
    return {"arquivo": str(used), "status": "invalido" if errors else "incompleto" if missing else "ok",
            "erros": errors, "faltantes": missing, "avisos": notices}

def self_test(default):
    current = inspect(FIXTURES / "save_atual.json", default)
    old = inspect(FIXTURES / "save_antigo.json", default)
    bad = inspect(FIXTURES / "save_corrompido.json", default)
    assert current["status"] == "ok", current
    assert old["status"] == "incompleto" and old["faltantes"], old
    assert bad["status"] == "corrompido" and bad["erros"], bad
    altered = parse(FIXTURES / "save_atual.json")
    altered["money"] = True
    assert any("/money" in x for x in validate(altered, default)[0])
    print("save_check --self-test: 4/4 cenários aprovados")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("save", nargs="?", type=Path)
    p.add_argument("--default", type=Path, default=DEFAULT)
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict-missing", action="store_true")
    p.add_argument("--fallback-bak", action="store_true")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    try:
        d = parse(a.default)
    except InvalidSave as e:
        p.error(str(e))
    if a.self_test:
        self_test(d)
        return 0
    if not a.save:
        p.error("informe um caminho de save ou use --self-test")
    r = inspect(a.save, d, a.fallback_bak)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"{r['status'].upper()}: {r['arquivo']}")
        for key in ("erros", "faltantes", "avisos"):
            for row in r[key]:
                print(f"  {key}: {row}")
    return int(bool(r["erros"] or (a.strict_missing and r["faltantes"])))

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Gera o catálogo de itens do Maré Alta Resort com um CÓDIGO ESTÁVEL por item.

Saídas:
  docs/ITENS.md          tabelas por categoria (código, nome, chave, onde é usado)
  docs/itens.json        o mesmo em formato de máquina
  docs/itens_registro.json   chave -> código (NÃO apague: garante que o código nunca muda)

Como funciona: o código de um item é gravado no registro na primeira vez que ele aparece
e nunca é reutilizado nem renumerado. Item novo = próximo número livre da categoria.
Rode:  python3 tools/gen_item_catalog.py
Para pedir uma alteração futura basta dizer o código, ex.: "troque MOD-017 por outro modelo".

Categorias (prefixo):
  MOD  modelo 3D real (Poly Haven / Kenney / Quaternius / gerado no Blender) usado no jogo
  NAT  modelo 3D da natureza (Quaternius q:) usado no jogo
  PRC  construtor procedural de props.gd (peça montada por código)
  CEN  construtor de cenário em details.gd / world*.gd (função que monta um conjunto)
  PRT  parte do corpo/cabelo/roupa dos personagens (assets/models/ubc, ual)
  DSH  prato/bebida do cardápio       SUP insumo do estoque
  EXP  expansão do resort             STF funcionário
  UPG  melhoria de bangalô (nível)    QST missão da vila
  VIP  cliente famoso                 EVT evento do dia
  NOU  modelo baixado mas ainda sem uso no código (disponível)
  TEX  textura/material (assets/tex, tex_hd)   AUD  som/música   ICO  ícone de interface
  FNT  fonte                                   SHD  shader        ANI  animação de personagem
  PCA  peça construída por código dentro de uma função (caixa, cilindro, parede, telhado…)
  MAT  material nomeado M.xxx (textura + cor)  COR  cor de paleta (pele, camisa, cabelo…)
  SCR  script (módulo do jogo)                 PES  nome de personagem (moradores/hóspedes)
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
REG_PATH = "docs/itens_registro.json"
registry = json.load(open(REG_PATH, encoding="utf-8")) if os.path.exists(REG_PATH) else {}

SCRIPTS = sorted(f for f in os.listdir("scripts") if f.endswith(".gd"))
SRC = {f: open("scripts/" + f, encoding="utf-8").read().split("\n") for f in SCRIPTS}


def code_for(cat, key):
    full = cat + ":" + key
    if full in registry:
        return registry[full]
    n = 1 + max([int(c.split("-")[1]) for k, c in registry.items() if k.startswith(cat + ":")] or [0])
    registry[full] = "%s-%03d" % (cat, n)
    return registry[full]


def enclosing_func(lines, idx):
    for j in range(idx, -1, -1):
        m = re.match(r"\s*(?:static\s+)?func\s+(\w+)", lines[j])
        if m:
            return m.group(1)
    return ""


def uses_of(literal):
    """Todas as linhas dos scripts que citam "literal" entre aspas."""
    out = []
    pat = re.compile(r'"' + re.escape(literal) + r'"')
    for f, lines in SRC.items():
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith("#"):
                continue
            if pat.search(ln):
                out.append({"arquivo": f, "linha": i + 1, "funcao": enclosing_func(lines, i)})
    return out


items = []


def add(cat, key, nome, fonte="", usos=None, extra=None):
    d = {"codigo": code_for(cat, key), "categoria": cat, "chave": key, "nome": nome, "fonte": fonte,
         "usos": usos or []}
    if extra:
        d.update(extra)
    items.append(d)


def humanize(k):
    k = re.sub(r"^[kqg]:", "", k)
    k = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", k)
    return re.sub(r"[_\-]+", " ", k).strip().capitalize()


# ---------------------------------------------------------------- modelos 3D baixados/gerados
def list_models():
    out = []  # (chave_no_codigo, fonte, caminho)
    base = "assets/models"
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, d + ".gltf")):
            out.append((d, "Poly Haven (CC0)", p + "/" + d + ".gltf"))
    for f in sorted(os.listdir(base + "/kenney")) if os.path.isdir(base + "/kenney") else []:
        if f.endswith(".glb"):
            out.append(("k:" + f[:-4], "Kenney (CC0)", base + "/kenney/" + f))
    for f in sorted(os.listdir(base + "/gen")) if os.path.isdir(base + "/gen") else []:
        if f.endswith(".glb"):
            out.append(("g:" + f[:-4], "Gerado no Blender (tools/gen_*.py)", base + "/gen/" + f))
    if os.path.isdir(base + "/qnat"):
        for f in sorted(os.listdir(base + "/qnat")):
            if f.endswith(".gltf"):
                out.append(("q:" + f[:-5], "Quaternius (CC0)", base + "/qnat/" + f))
    return out


props_src = "\n".join(SRC.get("props.gd", []))
builders = set(re.findall(r'"(\w+)"\s*:\s*(?:func|\w)', props_src[props_src.find("_builders = {"):props_src.find("_builders = {") + 3000]))

models = list_models()
seen_keys = set()
for key, fonte, path in models:
    seen_keys.add(key)
    usos = uses_of(key)
    if key.startswith("q:"):
        cat = "NAT"
    elif not usos and not key.startswith("g:"):
        cat = "NOU"
    else:
        cat = "MOD"
    if not usos and cat == "MOD" and key.startswith("g:"):
        cat = "NOU"
    extra = {"arquivo_modelo": path}
    if key in builders:
        extra["tambem_procedural"] = True
    add(cat, key, humanize(key), fonte, usos, extra)

# construtores procedurais (props.gd)
for i, ln in enumerate(SRC.get("props.gd", [])):
    m = re.match(r"static func ([a-z]\w*)\(", ln)
    if m and not m.group(1).startswith("_") and m.group(1) not in ("has", "build", "m", "glow"):
        fn = m.group(1)
        usos = [u for u in uses_of(fn)] + [
            {"arquivo": "props.gd", "linha": i + 1, "funcao": fn}]
        add("PRC", fn, humanize(fn), "props.gd (código)", usos[-1:])

# construtores de cenário (details.gd): cada função estática é um conjunto montado por código
for fname in ("details.gd", "build.gd", "world.gd", "world_village.gd", "village_life.gd", "guests.gd"):
    for i, ln in enumerate(SRC.get(fname, [])):
        m = re.match(r"(?:static )?func (\w+)\(", ln)
        if m and m.group(1) not in ("_ready", "_process", "_physics_process", "_init"):
            fn = m.group(1)
            add("CEN", fname[:-3] + "." + fn, humanize(fn), fname + " (código)",
                [{"arquivo": fname, "linha": i + 1, "funcao": fn}])

# partes dos personagens
for base in ("assets/models/ubc", "assets/models/ual", "assets/models/clothing"):
    if os.path.isdir(base):
        for f in sorted(os.listdir(base)):
            if f.endswith((".gltf", ".glb")):
                add("PRT", base.split("/")[-1] + "/" + f, humanize(os.path.splitext(f)[0]),
                    "Quaternius UBC/UAL (CC0)", [], {"arquivo_modelo": base + "/" + f})


# ---------------------------------------------------------------- tabelas do Economy
def block(name):
    txt = "\n".join(SRC["economy.gd"])
    m = re.search(r"const %s: = [\{\[]" % name, txt)
    if not m:
        return ""
    start = m.start()
    nxt = re.search(r"\n(?:const|func|var|static)\b", txt[m.end():])
    return txt[start:m.end() + (nxt.start() if nxt else len(txt))]


def line_of(text):
    for i, ln in enumerate(SRC["economy.gd"]):
        if text in ln:
            return i + 1
    return 0


def top_entries(name):
    """Pares (chave, bloco_texto) das entradas com um tab de recuo."""
    b = block(name)
    parts = re.split(r'\n\t"(\w+)":\s*\{', b)
    return [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def field(txt, f, default=""):
    m = re.search(r'"%s":\s*("([^"]*)"|[-\d.]+)' % f, txt)
    if not m:
        return default
    return m.group(2) if m.group(2) is not None else m.group(1)


eco = lambda k: [{"arquivo": "economy.gd", "linha": line_of('"%s"' % k), "funcao": ""}]

for k, t in top_entries("DISHES"):
    add("DSH", k, field(t, "name"), "economy.gd", eco(k), {"preco": field(t, "price")})
for k, t in top_entries("SUPPLIES"):
    add("SUP", k, field(t, "name"), "economy.gd", eco(k), {"custo": field(t, "cost")})
for k, t in top_entries("EXPANSIONS"):
    add("EXP", k, field(t, "name"), "economy.gd", eco(k),
        {"custo": field(t, "cost"), "estrelas": field(t, "stars"), "descricao": field(t, "blurb")})
for k, t in top_entries("STAFF"):
    add("STF", k, field(t, "name"), "economy.gd", eco(k),
        {"contratacao": field(t, "hire"), "salario": field(t, "wage"), "descricao": field(t, "blurb")})
for k, t in top_entries("UPGRADES"):
    cat_name = field(t, "name")
    for n, tm in enumerate(re.findall(r'\{"name":\s*"([^"]*)",\s*"cost":\s*(\d+),\s*"rate":\s*(\d+)', t)):
        add("UPG", "%s_%d" % (k, n), "%s — nível %d: %s" % (cat_name, n, tm[0]), "economy.gd", eco(k),
            {"custo": tm[1], "diaria_extra": tm[2]})
for k, t in top_entries("QUESTS"):
    add("QST", k, field(t, "title"), "economy.gd", eco(k),
        {"quem": field(t, "giver"), "onde": field(t, "where"), "recompensa": field(t, "reward"),
         "descricao": field(t, "desc")})
for k, t in top_entries("DAY_EVENTS"):
    pass
vb = block("VIPS")
for m in re.finditer(r'\{"id":\s*"(\w+)",\s*"name":\s*"([^"]*)",\s*"title":\s*"([^"]*)"', vb):
    add("VIP", m.group(1), m.group(2), "economy.gd", eco(m.group(1)), {"descricao": m.group(3)})
eb = block("DAY_EVENTS")
for m in re.finditer(r'"(\w+)":\s*\{"name":\s*"([^"]*)",\s*"blurb":\s*"([^"]*)"', eb):
    add("EVT", m.group(1), m.group(2), "economy.gd", eco(m.group(1)), {"descricao": m.group(3)})


# ---------------------------------------------------------------- texturas, sons, ícones, fontes, shaders, animações, scripts, nomes
def files_in(base, exts):
    out = []
    for dp, dn, fn in os.walk(base):
        for f in sorted(fn):
            if f.endswith(exts):
                out.append(os.path.join(dp, f).replace("\\", "/"))
    return sorted(out)


tex = {}
for base in ("assets/tex", "assets/tex_hd"):
    for f in files_in(base, (".jpg", ".png")):
        stem = os.path.splitext(os.path.basename(f))[0]
        stem = re.sub(r"_(diff|nor|rough|arm|disp|ao)$", "", stem)
        tex.setdefault(stem, []).append(f)
for stem, fl in sorted(tex.items()):
    add("TEX", stem, humanize(stem), "Poly Haven/ambientCG (CC0) ou gerado", uses_of(stem), {"arquivos": fl})

for f in files_in("assets/audio", (".ogg", ".wav", ".mp3")):
    stem = os.path.splitext(os.path.basename(f))[0]
    add("AUD", stem, humanize(stem), "assets/audio", uses_of(stem), {"arquivo_modelo": f})
for f in files_in("assets/ui/icons", (".svg", ".png")):
    stem = os.path.splitext(os.path.basename(f))[0]
    add("ICO", stem, humanize(stem), "assets/ui/icons", uses_of(stem), {"arquivo_modelo": f})
for f in files_in("assets/fonts", (".ttf", ".otf")):
    add("FNT", os.path.basename(f), humanize(os.path.splitext(os.path.basename(f))[0]), "assets/fonts",
        uses_of(f), {"arquivo_modelo": f})
for f in files_in("shaders", (".gdshader",)):
    stem = os.path.splitext(os.path.basename(f))[0]
    add("SHD", stem, humanize(stem), "shaders", uses_of("res://shaders/" + os.path.basename(f)), {"arquivo_modelo": f})

# animações do esqueleto dos personagens (JSON dentro do .glb)
import struct
try:
    raw = open("assets/models/ual/guest.glb", "rb").read()
    jl = struct.unpack("<I", raw[12:16])[0]
    gj = json.loads(raw[20:20 + jl])
    for a in gj.get("animations", []):
        nm = a.get("name", "")
        add("ANI", nm, humanize(nm), "UAL (Quaternius CC0)", uses_of(nm))
except Exception as e:
    print("sem animações:", e)

# scripts
for f in SCRIPTS:
    desc = ""
    for ln in SRC[f][:8]:
        if ln.startswith("##"):
            desc = ln.lstrip("# ").strip()
            break
    add("SCR", f, f, "scripts/", [{"arquivo": f, "linha": 1, "funcao": ""}],
        {"linhas": len(SRC[f]), "descricao": desc})

# nomes de pessoas
gm = re.search(r"const NAMES: = \[(.*?)\]", "\n".join(SRC["guest.gd"]), re.S)
if gm:
    for nm in re.findall(r'"([^"]+)"', gm.group(1)):
        add("PES", nm, nm, "guest.gd", [])

# detalhes extras de pratos / insumos
dish_stage = {}
for k, t in top_entries("DISH_STAGES") if False else []:
    pass
sb = block("DISH_STAGES")
for m in re.finditer(r'"(\w+)":\s*\[(.*?)\],?\n', sb):
    for it in items:
        if it["categoria"] == "DSH" and it["chave"] == m.group(1):
            it["etapas"] = re.findall(r'\["([^"]+)",\s*([\d.]+)\]', m.group(2))
spoil = dict(re.findall(r'"(\w+)":\s*([\d.]+)', block("SPOIL")))
for it in items:
    if it["categoria"] == "SUP" and it["chave"] in spoil:
        it["estraga_por_dia"] = spoil[it["chave"]]


# ---------------------------------------------------------------- materiais M.xxx
mat_defs = {}
for f, lines in SRC.items():
    for i, ln in enumerate(lines):
        m = re.match(r"\s*M\.(\w+)\s*=\s*(.*)", ln)
        if m and m.group(1) not in mat_defs:
            mat_defs[m.group(1)] = (f, i + 1, m.group(2).strip()[:110])
for name, (f, ln, expr) in sorted(mat_defs.items()):
    usos = []
    pat = re.compile(r"\bM\." + name + r"\b")
    for ff, lines in SRC.items():
        for i, l2 in enumerate(lines):
            if pat.search(l2) and not re.match(r"\s*M\." + name + r"\s*=", l2):
                usos.append({"arquivo": ff, "linha": i + 1, "funcao": enclosing_func(lines, i)})
    add("MAT", name, humanize(name), "%s:%d" % (f, ln), usos, {"definicao": expr})

# ---------------------------------------------------------------- paletas de cor dos personagens
gtxt = "\n".join(SRC["guest.gd"])
for pal, rot in (("SKINS", "Pele"), ("SHIRTS", "Camisa"), ("SHORTS", "Bermuda"), ("HAIRS", "Cabelo"), ("PRINT_COLS", "Estampa")):
    m = re.search(r"const %s: = \[(.*?)\]\n" % pal, gtxt, re.S)
    if m:
        for n, c in enumerate(re.findall(r"Color\(([^)]*)\)", m.group(1))):
            add("COR", "%s_%d" % (pal, n), "%s %d" % (rot, n + 1), "guest.gd", [], {"rgb": c.replace(" ", "")})

# ---------------------------------------------------------------- peças construídas por código (dentro das funções)
PIECE = re.compile(r"\b(B\.(?:box|cyl|sphere|wall|platform|hip_roof|arch|label|_beam|rounded_box|model)|Real\.place|D\.[a-z_]+|P\.build|MeshInstance3D\.new)\(")
PIECE_FILES = ("world.gd", "world_village.gd", "details.gd", "build.gd", "props.gd", "palm.gd", "guest.gd", "people.gd", "main.gd", "guests.gd", "village_life.gd")
ordinals = {}
for f in PIECE_FILES:
    lines = SRC.get(f, [])
    for i, ln in enumerate(lines):
        st = ln.strip()
        if st.startswith("#") or st.startswith("func ") or st.startswith("static func "):
            continue
        for m in PIECE.finditer(ln):
            fn = enclosing_func(lines, i) or "(topo)"
            callee = m.group(1)
            k = (f, fn, callee)
            ordinals[k] = ordinals.get(k, 0) + 1
            args = ln[m.end():].strip().rstrip(")")[:110]
            mat = re.search(r"\bM\.(\w+)", ln)
            lit = re.search(r'"([^"]{3,40})"', ln)
            comentario = ""
            if i > 0 and lines[i - 1].strip().startswith("#"):
                comentario = lines[i - 1].strip().lstrip("# ")[:90]
            indent = len(ln) - len(ln.lstrip("\t"))
            laco = any(re.match(r"\t{0,%d}(for|while)\b" % (indent - 1), lines[j].lstrip("\n")[:indent + 6].replace("\t", "\t")) and (len(lines[j]) - len(lines[j].lstrip("\t"))) < indent for j in range(max(0, i - 6), i))
            nome = (lit.group(1) if lit and "Real.place" in callee or (lit and "model" in callee) else callee.split(".")[-1] + (" " + mat.group(1) if mat else ""))
            add("PCA", "%s|%s|%s|%d" % (f, fn, callee, ordinals[k]), nome.replace("_", " "),
                "%s (código)" % f, [{"arquivo": f, "linha": i + 1, "funcao": fn}],
                {"chamada": callee, "args": args, "material": mat.group(1) if mat else "", "em_laco": laco,
                 "comentario": comentario})

# ---------------------------------------------------------------- saída
items.sort(key=lambda d: (d["categoria"], d["codigo"]))
os.makedirs("docs", exist_ok=True)
json.dump(registry, open(REG_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
json.dump(items, open("docs/itens.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

TITULOS = [
    ("MOD", "Modelos 3D em uso (reais, baixados da web)"),
    ("NAT", "Natureza (Quaternius)"),
    ("PRC", "Peças procedurais de props.gd (montadas por código — candidatas a virar modelo real)"),
    ("CEN", "Construtores de cenário e lógica (funções de world, details, build, vila, hóspedes)"),
    ("PRT", "Partes dos personagens"),
    ("DSH", "Pratos e bebidas"), ("SUP", "Insumos"), ("EXP", "Expansões"), ("STF", "Funcionários"),
    ("UPG", "Melhorias de bangalô"), ("QST", "Missões"), ("VIP", "Clientes famosos"), ("EVT", "Eventos do dia"),
    ("NOU", "Modelos baixados ainda sem uso (disponíveis)"),
    ("TEX", "Texturas e materiais"), ("AUD", "Sons e músicas"), ("ICO", "Ícones de interface"),
    ("FNT", "Fontes"), ("SHD", "Shaders"), ("ANI", "Animações dos personagens"),
    ("PCA", "Peças construídas por código (uma linha = uma peça; ver coluna Função)"),
    ("MAT", "Materiais nomeados (M.xxx)"), ("COR", "Cores de paleta dos personagens"),
    ("SCR", "Scripts (módulos do jogo)"), ("PES", "Nomes de personagens"),
]
by = {}
for d in items:
    by.setdefault(d["categoria"], []).append(d)

out = ["# Catálogo de itens — Maré Alta Resort", "",
       "Gerado por `python3 tools/gen_item_catalog.py` — **não edite à mão**. Os códigos ficam em "
       "`docs/itens_registro.json` e nunca mudam. Para pedir uma alteração, cite o código "
       "(ex.: \"troque o modelo de MOD-017\").", "",
       "Total: %d itens. " % len(items) + " · ".join("%s %d" % (c, len(by.get(c, []))) for c, _ in TITULOS), ""]
for cat, titulo in TITULOS:
    lst = by.get(cat, [])
    if not lst:
        continue
    out += ["## %s — %s (%d)" % (cat, titulo, len(lst)), ""]
    if cat == "PCA":
        out += ["| Código | Peça | Função | Chamada | Material | Linha | Obs |", "|---|---|---|---|---|---|---|"]
        for d in lst:
            u = d["usos"][0]
            obs = (d.get("comentario") or "") + (" [em laço]" if d.get("em_laco") else "")
            out.append("| %s | %s | `%s` | `%s` | %s | %s:%d | %s |" % (d["codigo"], d["nome"], u["funcao"], d["chamada"], d["material"] or "—", u["arquivo"], u["linha"], obs.replace("|", "/")))
    elif cat in ("MOD", "NAT", "NOU", "PRC", "CEN", "PRT", "TEX", "AUD", "ICO", "FNT", "SHD", "ANI", "SCR", "PES", "PCA", "MAT", "COR"):
        out += ["| Código | Nome | Chave | Fonte | Usado em |", "|---|---|---|---|---|"]
        for d in lst:
            u = d["usos"]
            lugares = ", ".join(sorted({"%s:%d" % (x["arquivo"], x["linha"]) for x in u})[:4])
            if len(u) > 4:
                lugares += " (+%d)" % (len(u) - 4)
            out.append("| %s | %s | `%s` | %s | %s |" % (d["codigo"], d["nome"], d["chave"], d["fonte"], lugares or "—"))
    else:
        out += ["| Código | Nome | Chave | Dados |", "|---|---|---|---|"]
        for d in lst:
            dados = "; ".join("%s=%s" % (k, v) for k, v in d.items()
                              if k in ("preco", "custo", "estrelas", "contratacao", "salario", "diaria_extra",
                                       "recompensa", "quem", "onde") and v != "")
            if d.get("descricao"):
                dados = (dados + " — " if dados else "") + d["descricao"]
            out.append("| %s | %s | `%s` | %s |" % (d["codigo"], d["nome"], d["chave"], dados))
    out.append("")
open("docs/ITENS.md", "w", encoding="utf-8").write("\n".join(out))
print("itens:", len(items), {c: len(v) for c, v in by.items()})

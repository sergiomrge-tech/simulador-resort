#!/usr/bin/env python3
"""Corpos CC0 (MakeHuman hm08) no esqueleto do Quaternius UAL.

O basemesh e os targets macro saíram como CC0 em setembro de 2020
(Data Collection AB / Joel Palmius / Jonas Hauquier; malha original de
Manuel Bastioni). O addon MPFB2 não entra no build: ele só empacota este
mesmo hm08. As animações continuam as do guest.glb (CC0, Quaternius),
com os ossos renomeados para SkeletonProfileHumanoid — o descanso é o
mesmo, então os clipes não são reescritos.

Uso: python3 tools/gen_people.py [--limit N]
Requer Blender 4.x no PATH ou em $BLENDER.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools", ".mh_cache")
OUT_DIR = os.path.join(ROOT, "assets", "people")
GUEST_GLB = os.path.join(ROOT, "assets", "models", "ual", "guest.glb")
RAW = "https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data"

# id, role, gender, race, age, weight (-1 thin .. +1 heavy), breast, hair, outfit, scale
CHARS = [
    ("ana", "guest", "f", "cauc", "young", -0.15, 0.45, "bob", "swim_f", 0.97),
    ("joao", "guest", "m", "mixed", "young", 0.2, 0.0, "short", "swim_m", 1.02),
    ("maria", "guest", "f", "afri", "young", 0.35, 0.6, "long", "tee_pants", 0.98),
    ("pedro", "guest", "m", "cauc", "old", 0.45, 0.0, "crop", "tee_pants", 0.96),
    ("luiza", "guest", "f", "asian", "young", -0.45, 0.4, "pony", "swim_f", 0.95),
    ("rafael", "guest", "m", "cauc", "young", 0.55, 0.0, "messy", "tee_shorts", 1.03),
    ("camila", "housekeeper", "f", "mixed", "young", 0.1, 0.5, "bun", "uniform", 0.98),
    ("bruno", "bartender", "m", "afri", "young", 0.25, 0.0, "crop", "bartender", 1.01),
    ("beatriz", "receptionist", "f", "cauc", "young", -0.05, 0.5, "long", "reception", 1.0),
    ("diego", "guest", "m", "afri", "young", -0.2, 0.0, "short", "swim_m", 1.0),
    ("fernanda", "guest", "f", "mixed", "young", 0.5, 0.7, "wavy", "tee_shorts", 0.99),
    ("lucas", "guest", "m", "asian", "young", -0.35, 0.0, "messy", "tee_shorts", 0.97),
]

# Tom de pele é multiplicado em Godot por cima do albedo neutro.
SKIN = {
    "ana": (0.93, 0.74, 0.60),
    "joao": (0.72, 0.52, 0.38),
    "maria": (0.40, 0.26, 0.18),
    "pedro": (0.80, 0.62, 0.48),
    "luiza": (0.86, 0.70, 0.56),
    "rafael": (0.90, 0.72, 0.58),
    "camila": (0.62, 0.44, 0.32),
    "bruno": (0.32, 0.20, 0.14),
    "beatriz": (0.84, 0.64, 0.50),
    "diego": (0.28, 0.18, 0.13),
    "fernanda": (0.55, 0.36, 0.26),
    "lucas": (0.78, 0.60, 0.46),
}
HAIR_COL = {
    "ana": (0.10, 0.06, 0.04),
    "joao": (0.06, 0.04, 0.03),
    "maria": (0.04, 0.03, 0.02),
    "pedro": (0.45, 0.42, 0.40),
    "luiza": (0.12, 0.07, 0.04),
    "rafael": (0.18, 0.10, 0.05),
    "camila": (0.08, 0.05, 0.03),
    "bruno": (0.03, 0.02, 0.02),
    "beatriz": (0.22, 0.12, 0.06),
    "diego": (0.05, 0.03, 0.02),
    "fernanda": (0.15, 0.08, 0.04),
    "lucas": (0.08, 0.05, 0.03),
}
CLOTH = {
    "swim_f": ((0.85, 0.18, 0.32), (0.10, 0.10, 0.12), (0.35, 0.22, 0.14)),
    "swim_m": ((0.20, 0.45, 0.72), (0.12, 0.28, 0.55), (0.35, 0.22, 0.14)),
    "tee_pants": ((0.90, 0.88, 0.82), (0.18, 0.22, 0.38), (0.16, 0.12, 0.10)),
    "tee_shorts": ((0.20, 0.55, 0.62), (0.85, 0.72, 0.40), (0.22, 0.16, 0.12)),
    "uniform": ((0.86, 0.90, 0.92), (0.18, 0.28, 0.42), (0.12, 0.12, 0.13)),
    "bartender": ((0.95, 0.95, 0.93), (0.10, 0.10, 0.12), (0.08, 0.08, 0.09)),
    "reception": ((0.94, 0.94, 0.96), (0.12, 0.16, 0.32), (0.10, 0.10, 0.12)),
}

RENAME = {
    "root": "Root",
    "pelvis": "Hips",
    "spine_01": "Spine",
    "spine_02": "Chest",
    "spine_03": "UpperChest",
    "neck_01": "Neck",
    "Head": "Head",
    "clavicle_l": "LeftShoulder",
    "upperarm_l": "LeftUpperArm",
    "lowerarm_l": "LeftLowerArm",
    "hand_l": "LeftHand",
    "thigh_l": "LeftUpperLeg",
    "calf_l": "LeftLowerLeg",
    "foot_l": "LeftFoot",
    "ball_l": "LeftToes",
    "clavicle_r": "RightShoulder",
    "upperarm_r": "RightUpperArm",
    "lowerarm_r": "RightLowerArm",
    "hand_r": "RightHand",
    "thigh_r": "RightUpperLeg",
    "calf_r": "RightLowerLeg",
    "foot_r": "RightFoot",
    "ball_r": "RightToes",
}
for side, prefix in (("l", "Left"), ("r", "Right")):
    RENAME["thumb_01_%s" % side] = prefix + "ThumbMetacarpal"
    RENAME["thumb_02_%s" % side] = prefix + "ThumbProximal"
    RENAME["thumb_03_%s" % side] = prefix + "ThumbDistal"
    for a, b in (("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Little")):
        RENAME["%s_01_%s" % (a, side)] = prefix + b + "Proximal"
        RENAME["%s_02_%s" % (a, side)] = prefix + b + "Intermediate"
        RENAME["%s_03_%s" % (a, side)] = prefix + b + "Distal"

PARENT = {
    "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest", "Neck": "UpperChest", "Head": "Neck",
    "LeftShoulder": "UpperChest", "LeftUpperArm": "LeftShoulder", "LeftLowerArm": "LeftUpperArm", "LeftHand": "LeftLowerArm",
    "RightShoulder": "UpperChest", "RightUpperArm": "RightShoulder", "RightLowerArm": "RightUpperArm", "RightHand": "RightLowerArm",
    "LeftUpperLeg": "Hips", "LeftLowerLeg": "LeftUpperLeg", "LeftFoot": "LeftLowerLeg", "LeftToes": "LeftFoot",
    "RightUpperLeg": "Hips", "RightLowerLeg": "RightUpperLeg", "RightFoot": "RightLowerLeg", "RightToes": "RightFoot",
}
CHILD = {v: k for k, v in PARENT.items() if k not in ("LeftShoulder", "RightShoulder", "LeftUpperLeg", "RightUpperLeg")}
# O peito não entrega peso à clavícula (isso puxa o tronco para o braço).
CHILD["UpperChest"] = "Neck"
CHILD["Hips"] = "Spine"


def _need(name, url, alts):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if os.path.isfile(path) and os.path.getsize(path) > 400:
        return path
    for alt in alts:
        if os.path.isfile(alt) and os.path.getsize(alt) > 400:
            shutil.copy(alt, path)
            return path
    print("baixando", name, flush=True)
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "mare-alta-gen-people"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def ensure_cache():
    base = _need("base.obj", RAW + "/3dobjs/base.obj", ["/tmp/base.obj"])
    names = [
        "african-female-young.target", "african-male-young.target",
        "asian-female-young.target", "asian-male-young.target",
        "caucasian-female-young.target", "caucasian-male-young.target",
        "caucasian-male-old.target", "african-male-old.target", "caucasian-female-old.target",
        "universal-female-young-averagemuscle-maxweight.target",
        "universal-female-young-averagemuscle-minweight.target",
        "universal-male-young-averagemuscle-maxweight.target",
        "universal-male-young-averagemuscle-minweight.target",
        "female-young-averagemuscle-averageweight-maxcup-averagefirmness.target",
        "eye-left-closure.target", "eye-right-closure.target",
    ]
    macro = {
        "african-female-young.target", "african-male-young.target", "asian-female-young.target",
        "asian-male-young.target", "caucasian-female-young.target", "caucasian-male-young.target",
        "caucasian-male-old.target", "african-male-old.target", "caucasian-female-old.target",
    }
    breast = "female-young-averagemuscle-averageweight-maxcup-averagefirmness.target"
    eyes = {"eye-left-closure.target", "eye-right-closure.target"}
    for name in names:
        if name in macro:
            url = RAW + "/targets/macrodetails/" + name
        elif name == breast:
            url = RAW + "/targets/breast/" + name
        elif name in eyes:
            url = RAW + "/targets/expression/units/caucasian/" + name
        else:
            url = RAW + "/targets/macrodetails/" + name
        _need(name, url, [os.path.join("/tmp/mh", name)])
    return base


def host():
    ensure_cache()
    blender = os.environ.get("BLENDER", "/tmp/blender-4.2.11-linux-x64/blender")
    if not os.path.isfile(blender):
        blender = "blender"
    cmd = [blender, "-b", "--python", os.path.abspath(__file__), "--"] + sys.argv[1:]
    print(" ".join(cmd), flush=True)
    raise SystemExit(subprocess.call(cmd))


def blender_main():
    import bpy
    import bmesh
    import numpy as np
    from mathutils import Vector

    limit = 0
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    os.makedirs(OUT_DIR, exist_ok=True)
    _textures(np)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GUEST_GLB)
    arm = None
    for obj in list(bpy.data.objects):
        if obj.type == "ARMATURE":
            arm = obj
        elif obj.type == "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    if arm is None:
        raise SystemExit("armadura do guest.glb não encontrada")
    arm.name = "Armature"
    print("ossos", len(arm.data.bones), "ações", len(bpy.data.actions), flush=True)
    print("nomes", [b.name for b in arm.data.bones][:12], flush=True)

    # Renomeia para o perfil humanóide. O Blender atualiza os fcurves das ações.
    pending = []
    for bone in arm.data.bones:
        if bone.name in RENAME and RENAME[bone.name] != bone.name:
            pending.append((bone, RENAME[bone.name]))
    for bone, new in pending:
        bone.name = "__tmp__" + new
    for bone, new in pending:
        bone.name = new
    sample = ""
    for act in bpy.data.actions:
        for fc in act.fcurves:
            sample = fc.data_path
            break
        if sample:
            break
    print("ações", [a.name for a in bpy.data.actions], flush=True)
    print("fcurve", sample, flush=True)
    print("tem LeftUpperArm", "LeftUpperArm" in arm.data.bones, flush=True)
    for act in bpy.data.actions:
        if "Idle_Loop" in act.name and "Talk" not in act.name and "Torch" not in act.name and not act.name.startswith("Crouch") and "Pistol" not in act.name:
            for fc in act.fcurves:
                if "arm" in fc.data_path.lower():
                    print("arm fcurve", act.name, fc.data_path, flush=True)
                    sample = fc.data_path
                    break
            break
    # O importador glTF do Blender cola "_Armature" no nome. O jogo procura Idle_Loop.
    for act in bpy.data.actions:
        if act.name.endswith("_Armature"):
            act.name = act.name[: -len("_Armature")]
    if "upperarm_" in sample or "pelvis" in sample:
        # O rename não propagou. Troca os caminhos na mão.
        repl = [(old, new) for old, new in RENAME.items() if old != new]
        repl.sort(key=lambda kv: len(kv[0]), reverse=True)
        for act in bpy.data.actions:
            for fc in act.fcurves:
                path = fc.data_path
                for old, new in repl:
                    path = path.replace('"%s"' % old, '"%s"' % new)
                fc.data_path = path
        print("fcurves reescritos", flush=True)

    _pose_check(bpy, arm)
    _rest(bpy, arm)

    V, VT, groups = _parse_obj(np)
    eye_l = _load_target(np, "eye-left-closure.target")
    eye_r = _load_target(np, "eye-right-closure.target")
    blink_delta = (np.concatenate([eye_l[0], eye_r[0]]), np.concatenate([eye_l[1], eye_r[1]]))

    chars = CHARS if limit <= 0 else CHARS[:limit]
    roster = []
    for spec in chars:
        cid = spec[0]
        print("corpo", cid, flush=True)
        morph, blink = _morph(np, V, spec, blink_delta)
        src, chains, faces_body, faces_eye, faces_teeth, uvs_ok = _place(np, arm, morph, blink, groups)
        _build_char(bpy, np, arm, cid, spec, src, chains, faces_body, faces_eye, faces_teeth, VT)
        top, bot, shoe = CLOTH[spec[8]]
        roster.append({
            "id": cid, "role": spec[1], "outfit": spec[8], "scale": spec[9],
            "skin": list(SKIN[cid]), "hair": list(HAIR_COL[cid]),
            "top": list(top), "bottom": list(bot), "shoes": list(shoe),
        })

    _rest(bpy, arm)
    _push_nla(arm)
    import json
    with open(os.path.join(OUT_DIR, "roster.json"), "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1)
    out = os.path.join(OUT_DIR, "people.glb")
    bpy.ops.export_scene.gltf(
        filepath=out,
        export_format="GLB",
        export_yup=True,
        export_apply=False,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_skins=True,
        export_morph=True,
        export_morph_normal=False,
        export_morph_tangent=False,
        export_rest_position_armature=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
    )
    print("WROTE", out, os.path.getsize(out), flush=True)


def _pose_check(bpy, arm):
    act = None
    for a in bpy.data.actions:
        if a.name == "Idle_Loop":
            act = a
            break
    if act is None:
        for a in bpy.data.actions:
            low = a.name.lower()
            if low.startswith("idle_loop"):
                act = a
                break
    if act is None:
        print("POSE_CHECK sem Idle_Loop", flush=True)
        return
    if arm.animation_data is None:
        arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        tr.mute = True
    arm.animation_data.action = act
    scene = bpy.context.scene
    mid = int((act.frame_range[0] + act.frame_range[1]) * 0.5)
    scene.frame_set(mid)
    bpy.context.view_layer.update()
    hand = arm.pose.bones["LeftHand"].head.z
    shoulder = arm.pose.bones["LeftUpperArm"].head.z
    print("POSE_CHECK hand_z %.3f shoulder_z %.3f drop %.3f frame %d" % (hand, shoulder, shoulder - hand, mid), flush=True)
    arm.animation_data.action = None
    if shoulder - hand < 0.12:
        raise SystemExit("idle não baixou o braço — clipe não ligou no osso novo")


def _rest(bpy, arm):
    if arm.animation_data:
        arm.animation_data.action = None
        for tr in arm.animation_data.nla_tracks:
            tr.mute = True
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()


def _push_nla(arm):
    import bpy
    if arm.animation_data is None:
        arm.animation_data_create()
    # Limpa tracks mudos do import para não duplicar na exportação.
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    for act in bpy.data.actions:
        uses = False
        for fc in act.fcurves:
            if 'pose.bones[' in fc.data_path:
                uses = True
                break
        if not uses:
            continue
        tr = arm.animation_data.nla_tracks.new()
        tr.name = act.name
        start = int(act.frame_range[0])
        tr.strips.new(act.name, start, act)
        tr.mute = True
    arm.animation_data.action = None


def _parse_obj(np):
    path = os.path.join(CACHE, "base.obj")
    verts = []
    vt = [(0.0, 0.0)]
    groups = {}
    cur = "default"
    groups[cur] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                x, y, z = line.split()[1:4]
                verts.append((float(x), float(y), float(z)))
            elif line.startswith("vt "):
                u, v = line.split()[1:3]
                vt.append((float(u), float(v)))
            elif line.startswith("g "):
                cur = line.split()[1]
                groups.setdefault(cur, [])
            elif line.startswith("f "):
                corners = []
                for tok in line.split()[1:]:
                    bits = tok.split("/")
                    vi = int(bits[0]) - 1
                    ti = int(bits[1]) if len(bits) > 1 and bits[1] else 0
                    corners.append((vi, ti))
                if len(corners) >= 3:
                    groups[cur].append(corners)
    V = np.array(verts, dtype=np.float64)
    VT = np.array(vt, dtype=np.float32)
    print("obj", len(V), "grupos", len(groups), "faces corpo", len(groups.get("body", [])), flush=True)
    return V, VT, groups


def _load_target(np, name):
    idx = []
    delta = []
    path = os.path.join(CACHE, name)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line or line[0] == "#" or line[0].isalpha():
                continue
            p = line.split()
            if len(p) < 4:
                continue
            idx.append(int(p[0]))
            delta.append((float(p[1]), float(p[2]), float(p[3])))
    return np.array(idx, dtype=np.int32), np.array(delta, dtype=np.float64) if idx else (np.zeros(0, np.int32), np.zeros((0, 3)))


def _apply(V, tgt, w):
    if w == 0 or len(tgt[0]) == 0:
        return
    ii, dd = tgt
    V[ii] += dd * w


def _targets_for(spec):
    gender, race, age, weight, breast = spec[2], spec[3], spec[4], spec[5], spec[6]
    out = []
    if age == "old":
        if gender == "m":
            out.append(("caucasian-male-old.target" if race != "afri" else "african-male-old.target", 0.85))
        else:
            out.append(("caucasian-female-old.target", 0.8))
    else:
        table = {
            ("f", "cauc"): ("caucasian-female-young.target", 0.9),
            ("m", "cauc"): ("caucasian-male-young.target", 0.9),
            ("f", "afri"): ("african-female-young.target", 0.95),
            ("m", "afri"): ("african-male-young.target", 0.95),
            ("f", "asian"): ("asian-female-young.target", 0.85),
            ("m", "asian"): ("asian-male-young.target", 0.85),
        }
        if race == "mixed":
            if gender == "f":
                out.append(("african-female-young.target", 0.55))
                out.append(("caucasian-female-young.target", 0.4))
            else:
                out.append(("african-male-young.target", 0.5))
                out.append(("caucasian-male-young.target", 0.4))
        elif (gender, race) in table:
            out.append(table[(gender, race)])
    g = "female" if gender == "f" else "male"
    if weight > 0.05:
        out.append(("universal-%s-young-averagemuscle-maxweight.target" % g, 0.55 * weight))
    elif weight < -0.05:
        out.append(("universal-%s-young-averagemuscle-minweight.target" % g, 0.6 * -weight))
    if gender == "f" and breast > 0 and age != "old":
        out.append(("female-young-averagemuscle-averageweight-maxcup-averagefirmness.target", breast))
    return out


_TGT_CACHE = {}


def _morph(np, base, spec, blink_delta):
    V = base.copy()
    for name, w in _targets_for(spec):
        if name not in _TGT_CACHE:
            _TGT_CACHE[name] = _load_target(np, name)
        _apply(V, _TGT_CACHE[name], w)
    blink = V.copy()
    _apply(blink, blink_delta, 1.0)
    return V, blink


def _chain_of(name):
    if name.startswith("l-") and any(k in name for k in ("shoulder", "elbow", "hand", "finger", "clavicle", "scapula")):
        return "larm"
    if name.startswith("r-") and any(k in name for k in ("shoulder", "elbow", "hand", "finger", "clavicle", "scapula")):
        return "rarm"
    if any(k in name for k in ("upper-leg", "knee", "ankle", "foot", "toe")):
        return "lleg" if name.startswith("l-") else "rleg"
    if any(k in name for k in ("eye", "lid", "jaw", "mouth", "tongue", "head")):
        return "head"
    return "torso"


def _rot_between(np, a, b):
    a = a / (np.linalg.norm(a) + 1e-12)
    b = b / (np.linalg.norm(b) + 1e-12)
    c = float(np.dot(a, b))
    if c > 0.9999:
        return np.eye(3)
    if c < -0.9999:
        axis = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        axis = np.cross(a, axis)
        axis = axis / np.linalg.norm(axis)
        return 2.0 * np.outer(axis, axis) - np.eye(3)
    v = np.cross(a, b)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]], dtype=np.float64)
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def _bone_head(arm, name):
    import numpy as np
    b = arm.data.bones[name]
    p = arm.matrix_world @ b.head_local
    return np.array([p.x, p.y, p.z], dtype=np.float64)


def _bone_tail(arm, name):
    import numpy as np
    b = arm.data.bones[name]
    p = arm.matrix_world @ b.tail_local
    return np.array([p.x, p.y, p.z], dtype=np.float64)


def _xform(np, V, s, y_min, shift):
    out = np.empty_like(V)
    out[:, 0] = V[:, 0] * s + shift[0]
    out[:, 1] = -V[:, 2] * s + shift[1]
    out[:, 2] = (V[:, 1] - y_min) * s + shift[2]
    return out


def _place(np, arm, morph, blink, groups):
    # Junta os centróides no espaço do MakeHuman e leva tudo ao descanso do esqueleto.
    joints = {}
    for name, faces in groups.items():
        if not name.startswith("joint-") or not faces:
            continue
        idxs = {c[0] for face in faces for c in face}
        if not idxs:
            continue
        ii = np.fromiter(idxs, dtype=np.int32)
        joints[name[6:]] = morph[ii].mean(axis=0)
    y_min = float(morph[:, 1].min())
    y_max = float(morph[:, 1].max())
    s = 1.83 / max(y_max - y_min, 1e-6)
    pelvis = _xform(np, joints["pelvis"][None, :], s, y_min, np.zeros(3))[0]
    shift = _bone_head(arm, "Hips") - pelvis
    morph_b = _xform(np, morph, s, y_min, shift)
    blink_b = _xform(np, blink, s, y_min, shift)
    src = {k: _xform(np, v[None, :], s, y_min, shift)[0] for k, v in joints.items()}

    def _tip(prefix, origin_key, along_key):
        cands = [src[k] for k in src if k.startswith(prefix)]
        if not cands:
            d = src[origin_key] - src[along_key]
            d = d / (np.linalg.norm(d) + 1e-8)
            return src[origin_key] + d * 0.08
        origin = src[origin_key]
        along = origin - src[along_key]
        along = along / (np.linalg.norm(along) + 1e-8)
        return max(cands, key=lambda p: float(np.dot(p - origin, along)))

    src["l-fingertip"] = _tip("l-finger", "l-hand", "l-elbow")
    src["r-fingertip"] = _tip("r-finger", "r-hand", "r-elbow")
    src["l-toe-tip"] = _tip("l-toe", "l-foot-1", "l-ankle")
    src["r-toe-tip"] = _tip("r-toe", "r-foot-1", "r-ankle")
    # Topo do crânio: vértices altos perto da cabeça.
    hj = src["head"]
    near = morph_b[np.linalg.norm(morph_b[:, :2] - hj[:2], axis=1) < 0.11]
    top_z = float(near[:, 2].max()) if len(near) else hj[2] + 0.16
    src["head_top"] = np.array([hj[0], hj[1], top_z])

    dst = {
        "pelvis": _bone_head(arm, "Hips"),
        "spine-2": _bone_head(arm, "Spine"),
        "spine-3": _bone_head(arm, "Chest"),
        "spine-4": _bone_head(arm, "UpperChest"),
        "neck": _bone_head(arm, "Neck"),
        "head": _bone_head(arm, "Head"),
        "head_top": _bone_tail(arm, "Head"),
        "l-shoulder": _bone_head(arm, "LeftUpperArm"),
        "l-elbow": _bone_head(arm, "LeftLowerArm"),
        "l-hand": _bone_head(arm, "LeftHand"),
        "l-fingertip": _bone_tail(arm, "LeftHand"),
        "r-shoulder": _bone_head(arm, "RightUpperArm"),
        "r-elbow": _bone_head(arm, "RightLowerArm"),
        "r-hand": _bone_head(arm, "RightHand"),
        "r-fingertip": _bone_tail(arm, "RightHand"),
        "l-upper-leg": _bone_head(arm, "LeftUpperLeg"),
        "l-knee": _bone_head(arm, "LeftLowerLeg"),
        "l-ankle": _bone_head(arm, "LeftFoot"),
        "l-foot-1": _bone_head(arm, "LeftToes"),
        "l-toe-tip": _bone_tail(arm, "LeftToes"),
        "r-upper-leg": _bone_head(arm, "RightUpperLeg"),
        "r-knee": _bone_head(arm, "RightLowerLeg"),
        "r-ankle": _bone_head(arm, "RightFoot"),
        "r-foot-1": _bone_head(arm, "RightToes"),
        "r-toe-tip": _bone_tail(arm, "RightToes"),
    }
    segs = [
        ("Hips", "pelvis", "spine-2", "torso", (0.8, 1.25)),
        ("Spine", "spine-2", "spine-3", "torso", (0.8, 1.25)),
        ("Chest", "spine-3", "spine-4", "torso", (0.8, 1.25)),
        ("UpperChest", "spine-4", "neck", "torso", (0.8, 1.25)),
        ("Neck", "neck", "head", "torso", (0.85, 1.2)),
        ("Head", "head", "head_top", "head", (0.94, 1.08)),
        ("LeftShoulder", "neck", "l-shoulder", "larm", (0.75, 1.4)),
        ("LeftUpperArm", "l-shoulder", "l-elbow", "larm", (0.7, 1.5)),
        ("LeftLowerArm", "l-elbow", "l-hand", "larm", (0.7, 1.5)),
        ("LeftHand", "l-hand", "l-fingertip", "larm", (0.8, 1.25)),
        ("RightShoulder", "neck", "r-shoulder", "rarm", (0.75, 1.4)),
        ("RightUpperArm", "r-shoulder", "r-elbow", "rarm", (0.7, 1.5)),
        ("RightLowerArm", "r-elbow", "r-hand", "rarm", (0.7, 1.5)),
        ("RightHand", "r-hand", "r-fingertip", "rarm", (0.8, 1.25)),
        ("LeftUpperLeg", "l-upper-leg", "l-knee", "lleg", (0.7, 1.5)),
        ("LeftLowerLeg", "l-knee", "l-ankle", "lleg", (0.7, 1.5)),
        ("LeftFoot", "l-ankle", "l-foot-1", "lleg", (0.75, 1.4)),
        ("LeftToes", "l-foot-1", "l-toe-tip", "lleg", (0.75, 1.4)),
        ("RightUpperLeg", "r-upper-leg", "r-knee", "rleg", (0.7, 1.5)),
        ("RightLowerLeg", "r-knee", "r-ankle", "rleg", (0.7, 1.5)),
        ("RightFoot", "r-ankle", "r-foot-1", "rleg", (0.75, 1.4)),
        ("RightToes", "r-foot-1", "r-toe-tip", "rleg", (0.75, 1.4)),
    ]
    # Cadeia de cada vértice = junta mais próxima.
    jnames = list(src.keys())
    jpos = np.stack([src[k] for k in jnames], axis=0)
    # Só juntas "reais" (sem as pontas sintéticas) para classificar.
    real = [i for i, k in enumerate(jnames) if k not in ("head_top", "l-fingertip", "r-fingertip", "l-toe-tip", "r-toe-tip")]
    jreal = jpos[real]
    jchain = [_chain_of(jnames[i]) for i in real]
    diff = morph_b[:, None, :] - jreal[None, :, :]
    dist = np.linalg.norm(diff, axis=2)
    nearest = dist.argmin(axis=1)
    chain_id = {"torso": 0, "head": 1, "larm": 2, "rarm": 3, "lleg": 4, "rleg": 5}
    chains = np.array([chain_id[jchain[i]] for i in nearest], dtype=np.int8)

    extra = {
        0: {"Head", "LeftShoulder", "RightShoulder", "LeftUpperLeg", "RightUpperLeg"},
        1: {"Neck"},
        2: {"UpperChest", "Neck"},
        3: {"UpperChest", "Neck"},
        4: {"Hips"},
        5: {"Hips"},
    }
    warped, primary, primary_t = _warp(np, morph_b, chains, segs, src, dst, chain_id, extra)
    blink_w, _, _ = _warp(np, blink_b, chains, segs, src, dst, chain_id, extra)

    # Erro nas juntas que são extremidades de segmento.
    err = 0.0
    for key, bone in (("l-hand", "LeftHand"), ("l-elbow", "LeftLowerArm"), ("l-shoulder", "LeftUpperArm"), ("head", "Head"), ("l-knee", "LeftLowerLeg"), ("l-ankle", "LeftFoot")):
        # Acha um vértice de junta não existe na malha; mede o ponto da junta warpeado.
        pass
    probe = np.stack([src["l-hand"], src["l-elbow"], src["head"], src["l-knee"], src["pelvis"]], axis=0)
    probe_c = np.array([2, 2, 1, 4, 0], dtype=np.int8)
    probe_w, _, _ = _warp(np, probe, probe_c, segs, src, dst, chain_id, extra)
    goal = np.stack([dst["l-hand"], dst["l-elbow"], dst["head"], dst["l-knee"], dst["pelvis"]], axis=0)
    miss = np.linalg.norm(probe_w - goal, axis=1)
    print("  encaixe mão/cotovelo/cabeça/joelho/pelve cm", " ".join("%.1f" % (m * 100) for m in miss), flush=True)
    if float(miss.max()) > 4.0:
        raise SystemExit("encaixe do esqueleto passou de 4 cm")

    body_f = groups.get("body", [])
    eye_f = groups.get("helper-l-eye", []) + groups.get("helper-r-eye", [])
    teeth_f = groups.get("helper-upper-teeth", []) + groups.get("helper-lower-teeth", [])
    return {
        "warped": warped, "blink": blink_w, "primary": primary, "primary_t": primary_t,
        "chains": chains, "chain_id": chain_id, "dst": dst, "src": src,
    }, chains, body_f, eye_f, teeth_f, True


def _warp(np, V, chains, segs, src, dst, chain_id, extra):
    n = len(V)
    sN = len(segs)
    mapped = np.zeros((sN, n, 3), dtype=np.float64)
    dists = np.zeros((sN, n), dtype=np.float64)
    ts = np.zeros((sN, n), dtype=np.float64)
    names = []
    seg_chain = np.zeros(sN, dtype=np.int8)
    for si, (bname, ka, kb, chain, clamp) in enumerate(segs):
        names.append(bname)
        seg_chain[si] = chain_id[chain]
        a = src[ka]
        b = src[kb]
        da = dst[ka]
        db = dst[kb]
        sd = b - a
        sl = float(np.linalg.norm(sd)) + 1e-8
        sy = sd / sl
        up = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(up, sy))) > 0.92:
            up = np.array([0.0, 1.0, 0.0])
        sx = np.cross(up, sy)
        sx = sx / (np.linalg.norm(sx) + 1e-12)
        sz = np.cross(sy, sx)
        dd = db - da
        dl = float(np.linalg.norm(dd)) + 1e-8
        R = _rot_between(np, sy, dd / dl)
        dx, dy, dz = R @ sx, R @ sy, R @ sz
        ratio = float(np.clip(dl / sl, clamp[0], clamp[1]))
        rel = V - a
        axial = rel @ sy
        px = rel @ sx
        pz = rel @ sz
        mapped[si] = da + (axial * ratio)[:, None] * dy + px[:, None] * dx + pz[:, None] * dz
        t = axial / sl
        tc = np.clip(t, 0.0, 1.0)
        closest = a + tc[:, None] * sd
        dists[si] = np.linalg.norm(V - closest, axis=1)
        ts[si] = tc
    allowed = np.zeros((sN, n), dtype=bool)
    for si, bname in enumerate(names):
        same = chains == seg_chain[si]
        allowed[si] = same
        for cid, bones in extra.items():
            if bname in bones:
                allowed[si] |= chains == cid
    dists_m = np.where(allowed, dists, 1e6)
    part = np.argpartition(dists_m, 1, axis=0)[:2]
    dsel = np.take_along_axis(dists_m, part, axis=0)
    order = np.argsort(dsel, axis=0)
    part = np.take_along_axis(part, order, axis=0)
    i1 = part[0]
    i2 = part[1]
    idx = np.arange(n)
    d1 = dists_m[i1, idx]
    d2 = dists_m[i2, idx]
    w1 = 1.0 / (d1 * d1 + 1e-8)
    w2 = 1.0 / (d2 * d2 + 1e-8)
    w2 = np.where((d2 > d1 * 2.5) | (d2 > 0.16), 0.0, w2)
    bad = d1 > 1e5
    if np.any(bad):
        ig = dists[:, bad].argmin(axis=0)
        i1 = i1.copy()
        i1[bad] = ig
        w2 = w2.copy()
        w2[bad] = 0.0
        d1 = np.where(bad, 0.0, d1)
    m1 = mapped[i1, idx]
    m2 = mapped[i2, idx]
    out = (m1 * w1[:, None] + m2 * w2[:, None]) / (w1 + w2)[:, None]
    t1 = ts[i1, idx]
    return out, np.array(names, dtype=object)[i1], t1


def _build_char(bpy, np, arm, cid, spec, src, chains, body_f, eye_f, teeth_f, VT):
    warped = src["warped"]
    blink = src["blink"]
    primary = src["primary"]
    primary_t = src["primary_t"]
    outfit = spec[8]
    dst = src["dst"]

    def pack(faces, with_blink):
        used = sorted({c[0] for face in faces for c in face})
        remap = {old: i for i, old in enumerate(used)}
        vv = warped[used]
        bb = blink[used] if with_blink else None
        ff = []
        uvs = []
        for face in faces:
            if len({c[0] for c in face}) < 3:
                continue
            ff.append([remap[c[0]] for c in face])
            uvs.append([c[1] for c in face])
        prim = primary[used]
        tt = primary_t[used]
        ch = chains[used]
        return vv, bb, ff, uvs, prim, tt, ch

    bv, bb, bf, bu, prim, tt, ch = pack(body_f, True)
    kinds = _cloth(np, bv, prim, tt, ch, outfit, dst)
    obj = _mesh_obj(bpy, np, cid + "_body", bv, bf, bu, VT, kinds, ["Skin", "Top", "Bottom", "Shoes"], cid)
    _weights(obj, prim, tt)
    _blink_key(bpy, obj, bb)
    _armature(obj, arm)
    _lod(bpy, obj, cid)
    if eye_f:
        ev, _, ef, eu, ep, et, ec = pack(eye_f, False)
        eobj = _mesh_obj(bpy, np, cid + "_eyes", ev, ef, None, VT, None, ["Eyes"], cid, eye=True)
        _one_group(eobj, "Head")
        _armature(eobj, arm)
    if teeth_f:
        tv, _, tf, tu, tp, ttp, tc = pack(teeth_f, False)
        tobj = _mesh_obj(bpy, np, cid + "_teeth", tv, tf, tu, VT, None, ["Teeth"], cid)
        _one_group(tobj, "Head")
        _armature(tobj, arm)
    _hair(bpy, np, arm, cid, spec[7], bv, bf, dst)


def _cloth(np, V, prim, tt, ch, outfit, dst):
    hip = float(dst["pelvis"][2])
    knee = float(dst["l-knee"][2])
    ankle = float(dst["l-ankle"][2])
    neck = float(dst["neck"][2])
    chest = float(dst["spine-4"][2])
    kind = np.zeros(len(V), dtype=np.int8)  # 0 skin 1 top 2 bottom 3 shoes
    sleeves = outfit in ("tee_pants", "tee_shorts", "uniform", "bartender", "reception")
    long_sleeve = outfit in ("uniform", "bartender", "reception")
    pants = outfit in ("tee_pants", "uniform", "bartender", "reception")
    for i in range(len(V)):
        bone = str(prim[i])
        z = float(V[i, 2])
        if bone in ("Head",) or ch[i] == 1:
            kind[i] = 0
            continue
        if bone in ("LeftHand", "RightHand"):
            kind[i] = 0
            continue
        if bone in ("LeftFoot", "RightFoot", "LeftToes", "RightToes"):
            kind[i] = 0 if outfit.startswith("swim") else 3
            continue
        if bone in ("LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "LeftShoulder", "RightShoulder"):
            if long_sleeve and bone in ("LeftLowerArm", "RightLowerArm", "LeftUpperArm", "RightUpperArm", "LeftShoulder", "RightShoulder"):
                kind[i] = 1
            elif sleeves and bone in ("LeftUpperArm", "RightUpperArm", "LeftShoulder", "RightShoulder"):
                kind[i] = 1
            else:
                kind[i] = 0
            continue
        if bone in ("LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg"):
            if pants and z > ankle + 0.045:
                kind[i] = 2
            elif outfit == "tee_shorts" and z > knee + 0.02:
                kind[i] = 2
            elif outfit.startswith("swim") and z > knee + 0.10:
                kind[i] = 2
            else:
                kind[i] = 0 if not pants else 3
            continue
        # tronco
        if z < hip + 0.05:
            kind[i] = 2
        elif outfit == "swim_m":
            kind[i] = 0
        elif outfit == "swim_f":
            kind[i] = 1 if (chest - 0.10) < z < (chest + 0.045) else 0
        elif z > neck - 0.015:
            kind[i] = 0
        else:
            kind[i] = 1
    return kind


def _mesh_obj(bpy, np, name, verts, faces, uvs, VT, kinds, slots, cid, eye=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces)
    mesh.update()
    if eye:
        c = verts.mean(axis=0)
        r = float(np.linalg.norm(verts - c, axis=1).mean()) + 1e-6
        uv = mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                vi = mesh.loops[li].vertex_index
                d = verts[vi] - c
                uv.data[li].uv = (0.5 + float(d[0]) / (r * 2.4), 0.5 + float(d[2]) / (r * 2.4))
    elif uvs is not None:
        uv = mesh.uv_layers.new(name="UVMap")
        for poly, face_uv in zip(mesh.polygons, uvs):
            for li, ti in zip(poly.loop_indices, face_uv):
                uv.data[li].uv = (float(VT[ti, 0]), float(VT[ti, 1]))
    for poly in mesh.polygons:
        poly.use_smooth = True
    if kinds is not None:
        mats = []
        for slot in slots:
            mat = _mat(bpy, cid + "_" + slot, slot)
            mats.append(mat)
            mesh.materials.append(mat)
        for poly in mesh.polygons:
            ks = [int(kinds[vi]) for vi in poly.vertices]
            # maioria
            poly.material_index = max(set(ks), key=ks.count)
    else:
        mat = _mat(bpy, cid + "_" + slots[0], slots[0])
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    tris = sum(max(0, len(p.vertices) - 2) for p in mesh.polygons)
    print("  ", name, "tris", tris, flush=True)
    return obj


def _mat(bpy, name, kind):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    colors = {
        "Skin": (0.75, 0.58, 0.48, 1),
        "Top": (0.2, 0.4, 0.7, 1),
        "Bottom": (0.15, 0.18, 0.35, 1),
        "Shoes": (0.12, 0.1, 0.09, 1),
        "Eyes": (0.9, 0.9, 0.9, 1),
        "Teeth": (0.92, 0.9, 0.86, 1),
        "Hair": (0.08, 0.05, 0.03, 1),
        "HairCard": (0.08, 0.05, 0.03, 1),
    }
    if bsdf:
        bsdf.inputs["Base Color"].default_value = colors.get(kind, (0.8, 0.8, 0.8, 1))
        rough = {"Skin": 0.55, "Eyes": 0.12, "Teeth": 0.4, "Hair": 0.55, "HairCard": 0.6}.get(kind, 0.78)
        bsdf.inputs["Roughness"].default_value = rough
    return mat


def _weights(obj, prim, tt):
    groups = {}
    for i, bone in enumerate(prim):
        bone = str(bone)
        t = float(tt[i])
        w = {bone: 1.0}
        if bone in ("LeftHand", "RightHand", "Head"):
            w = {bone: 1.0}
        elif t > 0.7 and bone in CHILD:
            a = (t - 0.7) / 0.3
            other = CHILD[bone]
            w = {bone: 1.0 - 0.72 * a, other: 0.72 * a}
        elif t < 0.3 and bone in PARENT:
            a = (0.3 - t) / 0.3
            other = PARENT[bone]
            w = {bone: 1.0 - 0.72 * a, other: 0.72 * a}
        s = sum(w.values())
        for k, val in w.items():
            groups.setdefault(k, []).append((i, val / s))
    for name, pairs in groups.items():
        vg = obj.vertex_groups.new(name=name)
        for i, val in pairs:
            vg.add([i], float(val), "REPLACE")


def _one_group(obj, bone):
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def _armature(obj, arm):
    mod = obj.modifiers.new("Arm", "ARMATURE")
    mod.object = arm
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()


def _blink_key(bpy, obj, blink_verts):
    bpy.context.view_layer.objects.active = obj
    obj.shape_key_add(name="Basis", from_mix=False)
    sk = obj.shape_key_add(name="blink", from_mix=False)
    for i, co in enumerate(blink_verts):
        sk.data[i].co = (float(co[0]), float(co[1]), float(co[2]))
    sk.value = 0.0


def _lod(bpy, src, cid):
    tris = sum(max(0, len(p.vertices) - 2) for p in src.data.polygons)
    # LOD0 fica inteiro: o shape key do piscar não sobrevive ao decimate.
    # O corpo hm08 cabe na faixa (~15–30k). LOD1/LOD2 são cópias sem o piscar.
    print("  ", src.name, "lod0", tris, flush=True)
    for suffix, target in (("lod1", 8000), ("lod2", 2800)):
        obj = src.copy()
        obj.data = src.data.copy()
        obj.name = cid + "_" + suffix
        obj.data.name = cid + "_" + suffix
        bpy.context.scene.collection.objects.link(obj)
        _drop_shapes(bpy, obj)
        ratio = min(1.0, target / max(tris, 1))
        _decimate_inplace(bpy, obj, ratio)
        nt = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
        print("  ", obj.name, "tris", nt, flush=True)


def _drop_shapes(bpy, obj):
    if obj.data.shape_keys is None:
        return
    bpy.context.view_layer.objects.active = obj
    # Remove do fim para o começo.
    while obj.data.shape_keys and len(obj.data.shape_keys.key_blocks):
        obj.shape_key_remove(obj.data.shape_keys.key_blocks[-1])


def _decimate_inplace(bpy, obj, ratio):
    if ratio >= 0.98:
        return
    arm_obj = None
    for m in list(obj.modifiers):
        if m.type == "ARMATURE":
            arm_obj = m.object
            obj.modifiers.remove(m)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="OBJECT")
    mod = obj.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = max(0.02, min(1.0, ratio))
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except RuntimeError as exc:
        print("  decimate falhou", obj.name, exc, flush=True)
        if mod.name in obj.modifiers:
            obj.modifiers.remove(mod)
    if arm_obj is not None:
        _armature(obj, arm_obj)


def _hair(bpy, np, arm, cid, style, body_v, body_f, dst):
    hj = dst["head"]
    # Normais por vértice a partir das faces do corpo.
    nrm = np.zeros_like(body_v)
    for face in body_f:
        if len(face) < 3:
            continue
        i0, i1, i2 = face[0], face[1], face[2]
        # índices locais não batem com body_v — body_f ainda é índice global.
        # Recalcula com as posições já no objeto (malha body).
        break
    obj = bpy.data.objects.get(cid + "_body")
    if obj is None:
        return
    mesh = obj.data
    mesh.update()
    # Vértices do escalpo: acima da junta da cabeça, não na cara (cara é -Y).
    scalp_idx = []
    scalp_n = []
    for v in mesh.vertices:
        p = v.co
        if p.z < hj[2] - 0.01:
            continue
        if p.y < hj[1] - 0.025 and p.z < hj[2] + 0.06:
            continue
        n = v.normal
        if n.y < -0.35 and p.z < hj[2] + 0.05:
            continue
        scalp_idx.append(v.index)
        scalp_n.append((n.x, n.y, n.z))
    if len(scalp_idx) < 30:
        print("  cabelo pouco escalpo", len(scalp_idx), flush=True)
        return
    sv = np.array([mesh.vertices[i].co[:] for i in scalp_idx], dtype=np.float64)
    sn = np.array(scalp_n, dtype=np.float64)
    # Touca: faces cujo três primeiros vértices estão no escalpo.
    scalp_set = set(scalp_idx)
    cap_faces = []
    for poly in mesh.polygons:
        if all(vi in scalp_set for vi in poly.vertices):
            cap_faces.append([vi for vi in poly.vertices])
    # A touca duplica só os vértices usados.
    if cap_faces:
        used = sorted({i for f in cap_faces for i in f})
        remap = {old: k for k, old in enumerate(used)}
        cv = []
        for i in used:
            p = mesh.vertices[i].co
            n = mesh.vertices[i].normal
            cv.append((p.x + n.x * 0.006, p.y + n.y * 0.006, p.z + n.z * 0.006))
        cf = [[remap[i] for i in f] for f in cap_faces]
        cap = _mesh_obj(bpy, np, cid + "_hair", np.array(cv), cf, None, None, None, ["Hair"], cid)
        _one_group(cap, "Head")
        _armature(cap, arm)
    _cards(bpy, np, arm, cid, style, sv, sn, hj)


def _cards(bpy, np, arm, cid, style, sv, sn, hj):
    length = {"crop": 0.02, "short": 0.045, "messy": 0.07, "bob": 0.13, "pony": 0.055, "bun": 0.04, "long": 0.30, "wavy": 0.28}.get(style, 0.08)
    n_cards = 10 if style == "crop" else 18 if style in ("bob", "long", "wavy") else 14
    ang = np.arctan2(sv[:, 0] - hj[0], sv[:, 1] - hj[1])
    roots = []
    for i in range(n_cards):
        a0 = -np.pi + i * (2 * np.pi / n_cards)
        a1 = a0 + (2 * np.pi / n_cards)
        m = (ang >= a0) & (ang < a1) & (sv[:, 2] > hj[2] - 0.01)
        if not np.any(m):
            continue
        sel = np.where(m)[0]
        j = sel[np.argmax(sv[sel, 2])]
        roots.append(j)
    verts = []
    faces = []
    uvs = []

    def add_ribbon(origin, normal, direction, leng, steps, width):
        direction = direction / (np.linalg.norm(direction) + 1e-8)
        side = np.cross(direction, normal)
        if np.linalg.norm(side) < 1e-4:
            side = np.cross(direction, np.array([1.0, 0.0, 0.0]))
        side = side / (np.linalg.norm(side) + 1e-8)
        cols = []
        for s in range(steps + 1):
            lift = 0.008 + 0.012 * (s / max(steps, 1))
            base = origin + direction * (leng * s / max(steps, 1))
            # Gruda no escalpo enquanto estiver perto.
            d = sv - base
            k = int(np.argmin(np.linalg.norm(d, axis=1)))
            if np.linalg.norm(d[k]) < 0.055 and s < steps:
                base = sv[k] + sn[k] * lift
            else:
                base = base + normal * lift * 0.3
            # Não atravessa a cara.
            if base[1] < hj[1] - 0.08 and base[2] < hj[2] + 0.02 and s > 0:
                break
            cols.append((base - side * width, base + side * width))
        if len(cols) < 2:
            return
        base_i = len(verts)
        for a, b in cols:
            verts.append(a)
            verts.append(b)
        for s in range(len(cols) - 1):
            i = base_i + s * 2
            faces.append([i, i + 1, i + 3, i + 2])
            v0 = s / (len(cols) - 1)
            v1 = (s + 1) / (len(cols) - 1)
            uvs.append([(0, v0), (1, v0), (1, v1), (0, v1)])

    for j in roots:
        origin = sv[j]
        normal = sn[j]
        out = origin - hj
        out[2] = 0
        if np.linalg.norm(out) < 1e-4:
            out = np.array([0.0, 1.0, 0.0])
        out = out / np.linalg.norm(out)
        fall = out * 0.35 + np.array([0.0, 0.15, -1.0])
        if style == "wavy":
            fall = fall + np.array([0.2 * np.sin(j), 0.0, 0.0])
        add_ribbon(origin, normal, fall, length, 4 if length > 0.12 else 3, 0.02)
    if style == "pony":
        back = sv[int(np.argmax(sv[:, 1]))]
        add_ribbon(back, np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.45, -1.0]), 0.26, 5, 0.028)
    if style == "bun":
        back = sv[int(np.argmax(sv[:, 1] + sv[:, 2] * 0.2))]
        for k in range(6):
            a = k / 6 * np.pi * 2
            d = np.array([np.cos(a) * 0.6, 0.8, np.sin(a) * 0.6])
            add_ribbon(back, np.array([0.0, 1.0, 0.2]), d, 0.04, 2, 0.016)
    # Franja curta na linha do cabelo.
    if style in ("bob", "long", "wavy", "pony"):
        fringe = np.where((sv[:, 2] > hj[2] + 0.02) & (sv[:, 1] < hj[1] + 0.01))[0]
        if len(fringe):
            fringe = fringe[np.argsort(sv[fringe, 0])]
            step = max(1, len(fringe) // 5)
            for j in fringe[::step][:5]:
                add_ribbon(sv[j], sn[j], np.array([0.0, -0.3, -1.0]), 0.045, 2, 0.018)
    if len(verts) < 8:
        return
    hair = _mesh_obj(bpy, np, cid + "_haircard", np.array(verts, dtype=np.float64), faces, None, None, None, ["HairCard"], cid)
    uv = hair.data.uv_layers.new(name="UVMap")
    for poly, face_uv in zip(hair.data.polygons, uvs):
        for li, (u, v) in zip(poly.loop_indices, face_uv):
            uv.data[li].uv = (float(u), float(v))
    _one_group(hair, "Head")
    _armature(hair, arm)
    # Material com máscara (recorte) para o glTF.
    mat = hair.data.materials[0]
    _hair_nodes(bpy, mat)


def _hair_nodes(bpy, mat):
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        return
    img = bpy.data.images.load(os.path.join(OUT_DIR, "hair_alpha.png"), check_existing=True)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.45
    nt.links.new(tex.outputs["Alpha"], gt.inputs[0])
    nt.links.new(gt.outputs[0], bsdf.inputs["Alpha"])
    if hasattr(mat, "use_backface_culling"):
        mat.use_backface_culling = False


def _textures(np):
    os.makedirs(OUT_DIR, exist_ok=True)
    rng = np.random.default_rng(7)
    n = 1024
    acc = np.zeros((n, n), np.float32)
    amp = 1.0
    for size in (4, 8, 16, 32, 64, 128, 256):
        g = rng.random((size, size)).astype(np.float32)
        up = np.repeat(np.repeat(g, n // size, 0), n // size, 1)
        if up.shape[0] != n:
            up = up[:n, :n]
        acc += up * amp
        amp *= 0.55
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-8)
    # Albedo quase neutro: o tom vem da cor do material. Poros escuros, bem suaves.
    shade = 0.90 + 0.10 * acc
    shade = np.clip(shade, 0.82, 1.0)
    rgb = np.stack([
        np.clip(shade * 1.02, 0, 1),
        np.clip(shade * 0.94, 0, 1),
        np.clip(shade * 0.88, 0, 1),
    ], axis=-1)
    _save_png(np, os.path.join(OUT_DIR, "skin_albedo.png"), rgb)
    dx = np.roll(acc, -1, 1) - np.roll(acc, 1, 1)
    dy = np.roll(acc, -1, 0) - np.roll(acc, 1, 0)
    nx, ny, nz = -dx * 1.4, -dy * 1.4, np.full_like(acc, 2.4)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5], axis=-1)
    _save_png(np, os.path.join(OUT_DIR, "skin_normal.png"), normal)
    # Tecido: trama fraca.
    c = 512
    cloth = 0.78 + 0.22 * np.repeat(np.repeat(rng.random((32, 32)).astype(np.float32), c // 32, 0), c // 32, 1)
    threads = (np.indices((c, c))[0] % 4 == 0) | (np.indices((c, c))[1] % 4 == 0)
    cloth = np.clip(cloth - threads * 0.05, 0, 1)
    crgb = np.stack([cloth, cloth * 0.98, cloth * 0.94], axis=-1)
    _save_png(np, os.path.join(OUT_DIR, "cloth.png"), crgb)
    # Olho.
    e = 512
    yy, xx = np.mgrid[0:e, 0:e]
    u = (xx + 0.5) / e - 0.5
    v = (yy + 0.5) / e - 0.5
    r = np.sqrt(u * u + v * v)
    eye = np.ones((e, e, 3), np.float32)
    eye[:, :] = (0.93, 0.90, 0.88)
    iris = r < 0.20
    ang = np.arctan2(v, u)
    spokes = 0.5 + 0.5 * np.sin(ang * 18.0)
    eye[iris] = np.array([0.28, 0.16, 0.08]) * (0.75 + 0.35 * acc[:e, :e][iris][:, None] * 0 + 1)
    # recompute iris color with spokes
    base_iris = np.stack([
        0.32 + 0.18 * spokes,
        0.16 + 0.08 * spokes,
        0.07 + 0.04 * spokes,
    ], axis=-1)
    eye[iris] = base_iris[iris]
    eye[r < 0.075] = (0.02, 0.015, 0.012)
    eye[(r > 0.185) & (r < 0.21)] *= 0.45
    # brilho
    eye[(u + 0.04) ** 2 + (v - 0.04) ** 2 < 0.00035] = (0.95, 0.95, 0.93)
    _save_png(np, os.path.join(OUT_DIR, "eye.png"), np.clip(eye, 0, 1))
    # Cabelo: fios verticais com alfa.
    h, w = 512, 256
    alpha = np.zeros((h, w), np.float32)
    for _ in range(90):
        x = int(rng.integers(0, w))
        ww = int(rng.integers(1, 3))
        a = float(rng.uniform(0.55, 1.0))
        shift = int(rng.integers(-6, 7))
        col = np.linspace(0, shift, h)
        xs = np.clip((np.arange(h) * 0 + x + col).astype(int), 0, w - 1)
        for t in range(ww):
            alpha[np.arange(h), np.clip(xs + t, 0, w - 1)] = np.maximum(
                alpha[np.arange(h), np.clip(xs + t, 0, w - 1)], a)
    gap = rng.random((h, w)) > 0.18
    alpha *= gap
    # raiz mais opaca
    alpha[:24, :] = np.maximum(alpha[:24, :], 0.85)
    hair = np.zeros((h, w, 4), np.float32)
    # Cinza claro: a cor do fio vem do albedo no Godot (loiro escuro também funciona).
    hair[:, :, 0] = 0.82
    hair[:, :, 1] = 0.82
    hair[:, :, 2] = 0.82
    hair[:, :, 3] = np.clip(alpha, 0, 1)
    _save_png(np, os.path.join(OUT_DIR, "hair_alpha.png"), hair)


def _save_png(np, path, rgb):
    # Escrita direta para não depender do PIL dentro do Blender.
    import struct
    import zlib
    h, w = rgb.shape[:2]
    if rgb.shape[2] == 4:
        raw = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    else:
        raw = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    # PNG de cima para baixo.
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    color = 6 if raw.shape[2] == 4 else 2
    ihdr = struct.pack(">IIBBBBB", w, h, 8, color, 0, 0, 0)
    rows = b"".join(b"\x00" + raw[i].tobytes() for i in range(h))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
        _IN = True
    except ImportError:
        _IN = False
    if _IN:
        blender_main()
    else:
        host()

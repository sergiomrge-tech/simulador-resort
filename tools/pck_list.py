"""Lista o conteúdo de um .pck da Godot 4 (maiores arquivos e total por extensão). Uso: python3 tools/pck_list.py build/win/MareAltaResort.pck"""
import struct, sys, collections
p = sys.argv[1]
f = open(p, "rb")
magic = f.read(4)
assert magic == b"GDPC", magic
ver, ma, mi, pa = struct.unpack("<IIII", f.read(16))
flags = struct.unpack("<I", f.read(4))[0]
base = struct.unpack("<Q", f.read(8))[0]
diroff = None
if ver >= 3:
    diroff = struct.unpack("<Q", f.read(8))[0]
    f.seek(diroff)
else:
    f.read(16 * 4)
n = struct.unpack("<I", f.read(4))[0]
items = []
for i in range(n):
    l = struct.unpack("<I", f.read(4))[0]
    name = f.read(l).rstrip(b"\0").decode("utf-8", "replace")
    off, size = struct.unpack("<QQ", f.read(16))
    f.read(16)  # md5
    fl = struct.unpack("<I", f.read(4))[0] if ver >= 2 else 0
    items.append((size, name))
items.sort(reverse=True)
tot = sum(s for s, _ in items)
print("files", n, "total MB", tot // 1048576)
groups = collections.Counter()
for s, nm in items:
    k = nm.split("/")[2] if nm.startswith("res://.godot/imported") else "/".join(nm.split("/")[2:4])
    ext = nm.rsplit(".", 1)[-1]
    groups[ext] += s
for k, v in groups.most_common(12):
    print("ext", k, v // 1048576, "MB")
for s, nm in items[:40]:
    print(s // 1048576, "MB", nm)

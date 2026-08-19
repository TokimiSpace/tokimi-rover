# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Write a millimetre-unit 3MF and clean binary STL from an .npz dump.

Run with a Python that has lib3mf + numpy (the cad-khana uv tool env):
  ~/.local/share/uv/tools/cad-khana/bin/python npz_to_3mf.py \
      /path/to/mesh.npz /path/to/out.3mf

The STL is written next to the 3MF (same name, .stl). Input comes from
dump_clean_triangulation.py; this script re-verifies edge pairing,
orientation, and degeneracy before writing, and asserts lib3mf's own
IsManifoldAndOriented check.
"""

import struct
import sys
from collections import Counter

import lib3mf
import numpy as np

MODEL_NAME = "TOKIMI_ROVER_TOP_COVER_SUPERCAR_V3"
STL_HEADER = b"TOKIMI SUPERCAR V3 clean triangulation"

NPZ, DST = sys.argv[1], sys.argv[2]
data = np.load(NPZ)
verts = data["verts"]
tris = data["tris"]
print(f"verts {len(verts)}, tris {len(tris)}")

edge_count = Counter()
directed = Counter()
for a, b, c in tris:
    assert a != b and b != c and a != c, "index-degenerate triangle"
    for u, v in ((a, b), (b, c), (c, a)):
        directed[(u, v)] += 1
        edge_count[(min(u, v), max(u, v))] += 1
bad_pairing = sum(1 for n in edge_count.values() if n != 2)
bad_orientation = sum(1 for n in directed.values() if n > 1)
assert bad_pairing == 0, f"{bad_pairing} edges not shared exactly twice"
assert bad_orientation == 0, f"{bad_orientation} repeated directed edges"

wrapper = lib3mf.Wrapper()
model = wrapper.CreateModel()
model.SetUnit(lib3mf.ModelUnit.MilliMeter)
mesh = model.AddMeshObject()
mesh.SetName(MODEL_NAME)

positions = []
for x, y, z in verts:
    p = lib3mf.Position()
    p.Coordinates[0] = float(x)
    p.Coordinates[1] = float(y)
    p.Coordinates[2] = float(z)
    positions.append(p)
triangles = []
for a, b, c in tris:
    t = lib3mf.Triangle()
    t.Indices[0] = int(a)
    t.Indices[1] = int(b)
    t.Indices[2] = int(c)
    triangles.append(t)
mesh.SetGeometry(positions, triangles)
assert mesh.IsManifoldAndOriented(), "lib3mf rejected the mesh"

model.AddBuildItem(mesh, wrapper.GetIdentityTransform())
model.QueryWriter("3mf").WriteToFile(DST)
print("WROTE", DST)

stl_path = DST.rsplit(".", 1)[0] + ".stl"
normals = np.cross(
    verts[tris[:, 1]] - verts[tris[:, 0]],
    verts[tris[:, 2]] - verts[tris[:, 0]],
)
lengths = np.linalg.norm(normals, axis=1, keepdims=True)
normals = (normals / np.clip(lengths, 1e-30, None)).astype(np.float32)
with open(stl_path, "wb") as fh:
    fh.write(STL_HEADER.ljust(80, b"\0"))
    fh.write(struct.pack("<I", len(tris)))
    record = np.zeros(
        len(tris),
        dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")],
    )
    record["n"] = normals
    record["v"] = verts[tris]
    record.tofile(fh)
print("WROTE", stl_path)

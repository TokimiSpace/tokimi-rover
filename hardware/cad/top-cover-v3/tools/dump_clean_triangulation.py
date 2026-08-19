# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Dump a topology-aware triangulation of the cover mesh to .npz.

Run inside Blender:
  Blender --background <cover.blend> --python dump_clean_triangulation.py \
      -- /path/to/out.npz

Why this exists: Blender's STL exporter triangulates via render-level
loop triangles, which is NOT topology-aware — coplanar ngon pairs from
boolean output can pick coincident diagonals, producing "fin" edges
(4 triangle-uses per edge) that are non-manifold at triangle level even
though the polygon mesh verifies clean. bmesh's BEAUTY triangulation is
topology-aware and produces a fin-free triangulation of the identical
surface. Feed the .npz to npz_to_3mf.py for 3MF + clean STL export.
"""

import sys

import bmesh
import bpy
import numpy as np

out_path = sys.argv[sys.argv.index("--") + 1]

obj = next(
    o for o in bpy.data.objects
    if o.type == "MESH" and o.name.startswith("TOKIMI_ROVER_TOP_COVER")
)
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.triangulate(
    bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY"
)

fin_edges = [e for e in bm.edges if len(e.link_faces) != 2]
if fin_edges:
    raise RuntimeError(
        f"{len(fin_edges)} fin edges survived BEAUTY triangulation — "
        "refusing to dump a non-manifold triangulation."
    )

bm.verts.index_update()
verts = np.array([v.co[:] for v in bm.verts], dtype=np.float32)
tris = np.array(
    [[loop.vert.index for loop in face.loops] for face in bm.faces],
    dtype=np.int64,
)
np.savez(out_path, verts=verts, tris=tris)
print(f"DUMPED verts={len(verts)} tris={len(tris)} -> {out_path}")
bm.free()

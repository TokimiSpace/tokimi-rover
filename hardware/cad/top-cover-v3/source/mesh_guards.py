# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""Shared mesh-integrity guards for the rover cover build scripts.

Blender 5.2's EXACT boolean solver is nondeterministic on this geometry:
across otherwise-identical runs it has (a) deleted the entire shell while
processing a healthy manifold cutter, and (b) succeeded but left behind
non-manifold edges or self-intersecting face pairs — at a different
boolean each run. Every boolean therefore goes through
``defensive_boolean_apply``, which rejects a result that collapses the
shell, adds non-manifold edges, or adds self-intersections, and falls
back EXACT -> MANIFOLD -> nudged EXACT before failing loudly.

``finishing_bevel`` applies the V2 craftsmanship chamfer with the same
philosophy: adaptive width with a full sanity check, reverting to the
un-beveled mesh rather than ever shipping a broken one.
"""

import math

import bmesh
import bpy
from mathutils.bvhtree import BVHTree


def non_manifold_count(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    count = sum(1 for edge in bm.edges if not edge.is_manifold)
    bm.free()
    return count


def self_intersection_count(mesh):
    """Count intersecting face pairs (excluding shared-vertex adjacency)."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm, epsilon=0.00001)
    pairs = set()
    for index_a, index_b in tree.overlap(tree):
        if index_a == index_b:
            continue
        face_a = bm.faces[index_a]
        face_b = bm.faces[index_b]
        verts_a = {vertex.index for vertex in face_a.verts}
        if verts_a & {vertex.index for vertex in face_b.verts}:
            continue
        pairs.add(tuple(sorted((index_a, index_b))))
    bm.free()
    return len(pairs)


def mesh_is_sane(mesh, coordinate_bound=500.0):
    """Finite in-bounds verts, manifold everywhere, no self-intersections."""
    for vertex in mesh.vertices:
        coordinates = vertex.co
        if not all(math.isfinite(value) for value in coordinates):
            return False
        if any(abs(value) > coordinate_bound for value in coordinates):
            return False
    return (
        non_manifold_count(mesh) == 0
        and self_intersection_count(mesh) == 0
    )


def _apply_with_solver(target, operand, operation, name, solver):
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new(name=name, type="BOOLEAN")
    modifier.operation = operation
    modifier.solver = solver
    modifier.object = operand
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def defensive_boolean_apply(target, operand, operation, name):
    """Drop-in replacement for the base scripts' boolean_apply."""
    before_verts = len(target.data.vertices)
    nm_before = non_manifold_count(target.data)
    si_before = self_intersection_count(target.data)
    snapshot = target.data.copy()
    operand_snapshot = operand.data.copy()

    def bad():
        if len(target.data.vertices) < max(100, before_verts * 0.3):
            return "collapse"
        nm_now = non_manifold_count(target.data)
        if nm_now > nm_before:
            return f"non-manifold {nm_before}->{nm_now}"
        si_now = self_intersection_count(target.data)
        if si_now > si_before:
            return f"self-intersection {si_before}->{si_now}"
        return None

    def restore_target():
        broken = target.data
        target.data = snapshot.copy()
        bpy.data.meshes.remove(broken)

    _apply_with_solver(target, operand, operation, name, "EXACT")
    reason = bad()
    if reason:
        print(f"BOOLEAN GUARD: {name} EXACT rejected ({reason}); trying MANIFOLD")
        restore_target()
        try:
            _apply_with_solver(
                target, operand, operation, f"{name}_manifold", "MANIFOLD"
            )
        except TypeError:
            # Solver enum not available in this Blender build.
            print("BOOLEAN GUARD: MANIFOLD solver unavailable")
        reason = bad()
    if reason:
        print(f"BOOLEAN GUARD: {name} MANIFOLD rejected ({reason}); trying nudged EXACT")
        restore_target()
        operand.data = operand_snapshot.copy()
        operand.location.x += 0.013
        operand.location.z += 0.013
        _apply_with_solver(
            target, operand, operation, f"{name}_nudged", "EXACT"
        )
        reason = bad()
    if reason:
        restore_target()
        raise RuntimeError(
            f"Boolean {name} rejected under EXACT, MANIFOLD, and nudged "
            f"EXACT (last: {reason}) — refusing to continue with a "
            "damaged shell."
        )

    bpy.data.meshes.remove(snapshot)
    bpy.data.meshes.remove(operand_snapshot)
    bpy.data.objects.remove(operand, do_unlink=True)


def finishing_bevel(
    obj,
    widths=(0.45, 0.30, 0.20),
    segments=2,
    angle_floor_deg=28.0,
    smooth_angle_deg=35.0,
    label="finishing bevel",
):
    """Adaptive craftsmanship chamfer with revert-on-failure.

    Bevels manifold edges sharper than ``angle_floor_deg`` (skipping tiny
    edges and sliver faces), trying each width until the result passes
    ``mesh_is_sane``. Reverts to the input mesh if every width fails.
    Always applies smooth-by-angle shading. Returns the applied width or
    None.
    """
    mesh = obj.data
    backup = mesh.copy()
    angle_floor = math.radians(angle_floor_deg)
    applied_width = None

    for width in widths:
        bm = bmesh.new()
        bm.from_mesh(backup)
        bm.normal_update()
        bevel_edges = []
        for edge in bm.edges:
            if not edge.is_manifold:
                continue
            if edge.calc_length() < 0.4:
                continue
            face_a, face_b = edge.link_faces
            if face_a.calc_area() < 0.05 or face_b.calc_area() < 0.05:
                continue
            angle = edge.calc_face_angle(None)
            if angle is None or angle < angle_floor:
                continue
            bevel_edges.append(edge)
        bmesh.ops.bevel(
            bm,
            geom=bevel_edges,
            offset=width,
            offset_type="OFFSET",
            segments=segments,
            profile=0.7,
            affect="EDGES",
            clamp_overlap=True,
            loop_slide=True,
        )
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        if mesh_is_sane(mesh):
            print(f"{label} applied: {len(bevel_edges)} edges at width {width}")
            applied_width = width
            break
        print(f"{label} at width {width} failed sanity; narrowing")

    if applied_width is not None:
        bpy.data.meshes.remove(backup)
    else:
        old_name = mesh.name
        obj.data = backup
        bpy.data.meshes.remove(mesh)
        backup.name = old_name
        print(f"{label} REVERTED (all widths failed)")

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(smooth_angle_deg))
    except AttributeError:
        bpy.ops.object.shade_smooth()

    return applied_width

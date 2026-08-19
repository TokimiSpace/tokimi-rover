# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""TOKIMI ROVER TOP COVER — SUPERCAR V3 (breadboard tower + dropped tail).

Layers on top of the V2 craftsmanship pass (executed up to but not
including its base.build() call, exactly like V2 layers on the supercar
pass). Three changes:

  1. Tail drop: the rear overhang (x > 227.5) sweeps down by 30 mm at the
     tail tip, smoothstep-tapered from the rear mounts. The 55 mm rear
     contact planes and pads are protected by the existing mount clamp.
  2. Breadboard tower: the open U-arch becomes a solid rear-raked slab
     (rake 0.44 kept) with a front-open pocket for a solderless
     breadboard 85 x 58 x 10 mm (pocket 58.4 wide x 86 along the raked
     axis x 10.4 deep, 5 mm top lip, shelf at the bottom). Standard
     breadboards carry adhesive backing; the pocket is a press-fit cradle.
  3. USB-C pass-through: a 14 x 8 mm vertical slot through the pocket
     shelf and the deck shell, so a Type-C plug passes from the pocket
     into the hull interior.

Locked envelope unchanged: 260x155 plan, 195x100 M3 centers, 3.5 mm
holes, 15/55 mm contact planes, 2.5 mm shell, 19x36 OLED, 29x78 camera
roof clearance. Tower metrics (height/opening) are deliberately changed
and reported as such.
"""

import json
import math
import os
from pathlib import Path

import bmesh
import bpy

SOURCE_DIR = Path(__file__).resolve().parent
V2_SCRIPT = str(SOURCE_DIR / "build_rover_top_cover_supercar_v2.py")

# Execute the V2 pass definitions only — everything before its
# base.build() call — so PCHIP surfacing, doubled sampling, panel lines,
# mesh guards, and all supercar overrides land exactly as shipped.
with open(V2_SCRIPT, "r", encoding="utf-8") as handle:
    v2_source = handle.read()
v2_defs = v2_source.split("\nbase.build()")[0]
exec(compile(v2_defs, V2_SCRIPT, "exec"))

STEM = "tokimi_rover_top_cover_supercar_v3_195x100mm"
base.MODEL_NAME = "TOKIMI ROVER TOP COVER — SUPERCAR V3 / BREADBOARD TOWER"
base.OBJ_OBJECT_NAME = "TOKIMI_ROVER_TOP_COVER_SUPERCAR_V3"
base.OBJ_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}.obj")
base.BLEND_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}.blend")
base.PREVIEW_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}_preview.png")
base.TOP_PREVIEW_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}_top.png")
base.REPORT_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}_validation.json")

# ---------------------------------------------------------------------------
# Change 1: tail drop
# ---------------------------------------------------------------------------
TAIL_DROP_MM = 30.0
TAIL_DROP_START_X = base.REAR_X  # 227.5 — rear mounts stay untouched

_v2_raw_inner_surface_z = base.raw_inner_surface_z


def v3_raw_inner_surface_z(x, y):
    z = _v2_raw_inner_surface_z(x, y)
    if x > TAIL_DROP_START_X:
        t = (x - TAIL_DROP_START_X) / (base.LENGTH - TAIL_DROP_START_X)
        z -= TAIL_DROP_MM * base.smoothstep(t)
    return z


base.raw_inner_surface_z = v3_raw_inner_surface_z

# ---------------------------------------------------------------------------
# Change 2: breadboard tower (solid raked slab with front-open pocket)
# ---------------------------------------------------------------------------
BREADBOARD = (85.0, 58.0, 10.0)  # length x width x thickness, mm
# Pocket oversize accounts for the 0.45 mm finishing bevel rounding the
# pocket's concave corners (intrusion ~0.19 mm): a sharp-cornered
# 58 x 85 x 10 board still clears with >=0.4 mm per side.
POCKET_W = 58.8
POCKET_AXIS_LEN = 86.0
POCKET_DEPTH = 10.8
SHELF_W = 8.0  # pocket floor height above slab base, along the raked axis
TOP_LIP_W = 5.0

TOWER_RAKE = 0.44
_axis_scale = math.sqrt(1.0 + TOWER_RAKE * TOWER_RAKE)
_pocket_dw = POCKET_AXIS_LEN / _axis_scale  # z-extent of the pocket
TOWER_H = SHELF_W + _pocket_dw + TOP_LIP_W  # ~91.7
SLAB_BASE_HALF_W = 35.0
SLAB_TOP_HALF_W = 33.0
SLAB_BASE_DEPTH = 20.0
SLAB_TOP_DEPTH = 16.0

base.TOWER_RAKE = TOWER_RAKE
base.TOWER_OUTER_WIDTH = 2 * SLAB_BASE_HALF_W
base.TOWER_DEPTH = SLAB_BASE_DEPTH
base.TOWER_HEIGHT = TOWER_H
base.TOWER_VISIBLE_OPENING = (0.0, 0.0)  # solid slab: no aesthetic window

USB_SLOT_XY = (8.0, 14.0)  # x-depth x y-width; Type-C plug is ~12.4 x 6.5
USB_SLOT_CENTER_X = base.TOWER_FOOT_X + 4.0
# z_max must clear the raked pocket floor across the slot's whole x-range
# (floor plane reaches z~83.2 at the slot's rear edge) or the slot ends up
# a blind hole inside the shelf instead of breaking into the pocket.
USB_SLOT_Z = (42.0, 88.0)


def v3_breadboard_tower():
    """Solid rear-raked slab with shell-conforming flared roots."""
    base_z = base.outer_surface_z(base.TOWER_FOOT_X, base.CENTER_Y) - 3.0
    height = TOWER_H
    root_embed = 2.2
    root_blend_height = 28.0
    root_front_flare = 3.5
    root_depth_flare = 8.0

    yz_points = [
        (-SLAB_BASE_HALF_W, 0.0),
        (-(SLAB_BASE_HALF_W + SLAB_TOP_HALF_W) / 2.0, height * 0.45),
        (-SLAB_TOP_HALF_W, height),
        (SLAB_TOP_HALF_W, height),
        ((SLAB_BASE_HALF_W + SLAB_TOP_HALF_W) / 2.0, height * 0.45),
        (SLAB_BASE_HALF_W, 0.0),
    ]
    if base.polygon_area_2d(yz_points) < 0.0:
        yz_points.reverse()

    def slab_vertex(y_local, z_local, is_back):
        blend_t = base.smoothstep(
            min(max(z_local / root_blend_height, 0.0), 1.0)
        )
        root_weight = 1.0 - blend_t
        x_front = (
            base.TOWER_FOOT_X
            + TOWER_RAKE * z_local
            - root_front_flare * root_weight
        )
        local_depth = (
            base.lerp(SLAB_BASE_DEPTH, SLAB_TOP_DEPTH, z_local / height)
            + root_depth_flare * root_weight
        )
        x = x_front + (local_depth if is_back else 0.0)
        nominal_z = base_z + z_local
        conforming_z = (
            base.outer_surface_z(x, base.CENTER_Y + y_local)
            - root_embed
            + z_local
        )
        z = base.lerp(conforming_z, nominal_z, blend_t)
        return (x, base.CENTER_Y + y_local, z)

    vertices = []
    for y_local, z_local in yz_points:
        vertices.append(slab_vertex(y_local, z_local, False))
    for y_local, z_local in yz_points:
        vertices.append(slab_vertex(y_local, z_local, True))

    count = len(yz_points)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append(
            (index, next_index, count + next_index, count + index)
        )

    mesh = bpy.data.meshes.new("Supercar_V3_Breadboard_Tower_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("SUPERCAR_V3_BREADBOARD_TOWER", mesh)
    bpy.context.collection.objects.link(obj)
    _recalc_outward(obj)
    return obj


def _recalc_outward(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def v3_pocket_cutter():
    """Front-open raked box: breadboard pocket through the slab front."""
    base_z = base.outer_surface_z(base.TOWER_FOOT_X, base.CENTER_Y) - 3.0
    half_w = POCKET_W / 2.0
    w0, w1 = SHELF_W, SHELF_W + _pocket_dw
    # Front face 7 mm proud of the (unflared) slab front so the pocket is
    # open; back face leaves >=4.5 mm of slab wall at every height.
    d_front = -7.0
    d_back = POCKET_DEPTH * _axis_scale  # perpendicular depth -> x offset

    vertices = []
    for w in (w0, w1):
        x_front = base.TOWER_FOOT_X + TOWER_RAKE * w
        for d in (d_front, d_back):
            for u in (-half_w, half_w):
                # z compensates for d so the floor and lip planes are
                # PERPENDICULAR to the raked axis (slope -rake per unit x)
                # — a horizontal floor would let the tilted breadboard's
                # lower front corner dig into the shelf.
                vertices.append(
                    (
                        x_front + d,
                        base.CENTER_Y + u,
                        base_z + w - TOWER_RAKE * d,
                    )
                )
    # vertex order per level: fl, fr, bl, br  (f=front, l=-u)
    faces = [
        (0, 1, 3, 2),  # bottom
        (4, 6, 7, 5),  # top
        (0, 4, 5, 1),  # front
        (2, 3, 7, 6),  # back
        (0, 2, 6, 4),  # left
        (1, 5, 7, 3),  # right
    ]
    mesh = bpy.data.meshes.new("V3_Breadboard_Pocket_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("V3_BREADBOARD_POCKET", mesh)
    bpy.context.collection.objects.link(obj)
    _recalc_outward(obj)
    return obj


def v3_usb_slot_cutter():
    """Vertical Type-C pass-through: pocket shelf -> hull interior."""
    half_x = USB_SLOT_XY[0] / 2.0
    half_y = USB_SLOT_XY[1] / 2.0
    polygon = [
        (USB_SLOT_CENTER_X - half_x, base.CENTER_Y - half_y),
        (USB_SLOT_CENTER_X + half_x, base.CENTER_Y - half_y),
        (USB_SLOT_CENTER_X + half_x, base.CENTER_Y + half_y),
        (USB_SLOT_CENTER_X - half_x, base.CENTER_Y + half_y),
    ]
    return base.create_multi_xy_prism(
        "V3_USB_C_SLOT", [polygon], z_min=USB_SLOT_Z[0], z_max=USB_SLOT_Z[1]
    )


base.create_camera_arch = v3_breadboard_tower

_v2_panel_line_cutters = base.create_tower_window_cutters


def v3_tower_cutters():
    return list(_v2_panel_line_cutters()) + [
        v3_pocket_cutter(),
        v3_usb_slot_cutter(),
    ]


base.create_tower_window_cutters = v3_tower_cutters

# ---------------------------------------------------------------------------
# Build, review renders, extend the report
# ---------------------------------------------------------------------------
base.build()

cover = bpy.data.objects["TOKIMI_ROVER_TOP_COVER_SUPERCAR_V2"]
cover.name = "TOKIMI_ROVER_TOP_COVER_SUPERCAR_V3"
TOWER_BASE_Z = base.outer_surface_z(base.TOWER_FOOT_X, base.CENTER_Y) - 3.0

scene = bpy.context.scene
scene.display.shading.show_cavity = True
camera = bpy.data.objects["RENDER_CAMERA"]
camera.data.type = "PERSP"
camera.data.lens = 50.0

review_views = {
    "front34": (-230.0, -260.0, 240.0),
    "rear34": (500.0, 300.0, 270.0),
    "side": (130.0, -450.0, 95.0),
    "tower_detail": (60.0, -180.0, 190.0),
}
view_paths = {}
for view_name, location in review_views.items():
    camera.location = location
    target = (
        (160.0, base.CENTER_Y, 110.0)
        if view_name == "tower_detail"
        else (130.0, base.CENTER_Y, 60.0)
    )
    base.point_at(camera, target)
    path = os.path.join(base.OUTPUT_DIR, f"{STEM}_{view_name}.png")
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    view_paths[view_name] = os.path.basename(path)

# Make Blender's bundled Smooth by Angle node group local so the published
# editable file has no external library dependency or machine-specific path.
for node_group in list(bpy.data.node_groups):
    if node_group.library:
        node_group.make_local()
while len(bpy.data.libraries):
    bpy.data.libraries.remove(bpy.data.libraries[0])
scene.render.filepath = f"//{STEM}_tower_detail.png"
bpy.ops.wm.save_as_mainfile(filepath=base.BLEND_PATH)

with open(base.REPORT_PATH, "r", encoding="utf-8") as handle:
    report = json.load(handle)
report["design_style"] = (
    "modern supercar V3 — dropped tail (30 mm), solid raked breadboard "
    "tower with front pocket and USB-C pass-through"
)
report["v3_changes"] = {
    "tail_drop_mm": TAIL_DROP_MM,
    "tail_drop_span_x_mm": [TAIL_DROP_START_X, base.LENGTH],
    "breadboard_mm": list(BREADBOARD),
    "pocket_mm": {
        "width": POCKET_W,
        "along_raked_axis": POCKET_AXIS_LEN,
        "depth": POCKET_DEPTH,
        "shelf_above_slab_base": SHELF_W,
        "top_lip": TOP_LIP_W,
        "note": "front-open cradle; breadboard adhesive backing + press fit",
    },
    "usb_c_slot_mm": {
        "cross_section_xy": list(USB_SLOT_XY),
        "center_x": USB_SLOT_CENTER_X,
        "z_span": list(USB_SLOT_Z),
    },
    "tower": {
        "height_above_local_deck_mm": TOWER_H,
        "base_z_mm": round(TOWER_BASE_Z, 3),
        "foot_x_mm": base.TOWER_FOOT_X,
        "rake": TOWER_RAKE,
        "solid_slab": True,
        "note": "U-arch aesthetic window removed; camera roof clearance "
        "at deck level is unchanged",
    },
}
report["review_previews"] = view_paths
with open(base.REPORT_PATH, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, ensure_ascii=False)

print(f"TOKIMI_SUPERCAR_V3_BLEND={base.BLEND_PATH}")
print(f"TOKIMI_SUPERCAR_V3_OBJ={base.OBJ_PATH}")

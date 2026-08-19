# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

"""TOKIMI ROVER TOP COVER — SUPERCAR V2 (craftsmanship + printability pass).

Builds on the supercar/tree-support styling pass without duplicating it:
the supercar script is executed up to (but not including) its base.build()
call, then this file layers on:

  1. Monotone-cubic (PCHIP) table interpolation — removes the piecewise-
     linear creases that made every hand-authored styling table read as
     flat facets on the hood, tub, and side insets.
  2. Doubled shell sampling (161 x-stations, 81 y-stations) so the now-
     smooth surfaces are actually resolved by the mesh.
  3. A finishing pass after all Booleans: angle-limited bevel (0.45 mm,
     2 segments) plus smooth-by-angle shading. This is simultaneously the
     printability fix — every M3 hole rim, pad edge, and hex-vent rim
     gains a small printed chamfer, and hard rims stop leaving blobby
     seam artifacts.
  4. Engraved panel lines (hood shut-line U plus two rear-deck vents cut
     0.5 mm into the skin) via the previously unused tower-window-cutter
     hook, for a machined shut-line read instead of a monolithic shell.

The approved mechanical envelope is inherited untouched: 260x155 plan,
195x100 M3 centers, 3.5 mm holes, 15/55 mm contact planes, 2.5 mm shell,
19x36 OLED, 29x78 camera clearance.
"""

import functools
import importlib.util
import json
import math
import os
from pathlib import Path

import bpy

SOURCE_DIR = Path(__file__).resolve().parent
SUPERCAR_SCRIPT = str(SOURCE_DIR / "build_rover_top_cover_supercar.py")

# Execute the supercar pass definitions only — everything before its
# base.build() call — so all of its overrides land on `base` exactly as in
# the shipped tree-support version.
with open(SUPERCAR_SCRIPT, "r", encoding="utf-8") as handle:
    supercar_source = handle.read()
supercar_defs = supercar_source.split("\nbase.build()")[0]
exec(compile(supercar_defs, SUPERCAR_SCRIPT, "exec"))

STEM = "tokimi_rover_top_cover_supercar_v2_195x100mm"
base.MODEL_NAME = "TOKIMI ROVER TOP COVER — SUPERCAR V2"
base.OBJ_OBJECT_NAME = "TOKIMI_ROVER_TOP_COVER_SUPERCAR_V2"
base.OBJ_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}.obj")
base.BLEND_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}.blend")
base.PREVIEW_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}_preview.png")
base.TOP_PREVIEW_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}_top.png")
base.REPORT_PATH = os.path.join(base.OUTPUT_DIR, f"{STEM}_validation.json")

BEVEL_WIDTH_MM = 0.45
BEVEL_SEGMENTS = 2
BEVEL_ANGLE_LIMIT_DEG = 28.0
SMOOTH_SHADE_ANGLE_DEG = 35.0
GROOVE_WIDTH_MM = 1.2
GROOVE_DEPTH_MM = 0.5


# ---------------------------------------------------------------------------
# 1. Smooth (monotone cubic / PCHIP) table interpolation
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def _pchip_slopes(table):
    xs = [point[0] for point in table]
    ys = [point[1] for point in table]
    n = len(xs)
    widths = [xs[i + 1] - xs[i] for i in range(n - 1)]
    secants = [(ys[i + 1] - ys[i]) / widths[i] for i in range(n - 1)]
    slopes = [0.0] * n
    slopes[0] = secants[0]
    slopes[-1] = secants[-1]
    for i in range(1, n - 1):
        if secants[i - 1] * secants[i] <= 0.0:
            slopes[i] = 0.0
        else:
            weight_a = 2.0 * widths[i] + widths[i - 1]
            weight_b = widths[i] + 2.0 * widths[i - 1]
            slopes[i] = (weight_a + weight_b) / (
                weight_a / secants[i - 1] + weight_b / secants[i]
            )
    return tuple(slopes)


def pchip_interpolate_table(table, value):
    """Fritsch–Carlson monotone cubic: smooth, overshoot-free tables."""
    if value <= table[0][0]:
        return table[0][1]
    if value >= table[-1][0]:
        return table[-1][1]
    table = tuple(tuple(point) for point in table)
    slopes = _pchip_slopes(table)
    for i in range(len(table) - 1):
        x0, y0 = table[i]
        x1, y1 = table[i + 1]
        if x0 <= value <= x1:
            h = x1 - x0
            t = (value - x0) / h
            t2 = t * t
            t3 = t2 * t
            h00 = 2.0 * t3 - 3.0 * t2 + 1.0
            h10 = t3 - 2.0 * t2 + t
            h01 = -2.0 * t3 + 3.0 * t2
            h11 = t3 - t2
            return (
                h00 * y0
                + h10 * h * slopes[i]
                + h01 * y1
                + h11 * h * slopes[i + 1]
            )
    return table[-1][1]


base.interpolate_table = pchip_interpolate_table


# ---------------------------------------------------------------------------
# 2. Doubled shell sampling so the smooth surfaces are actually resolved
# ---------------------------------------------------------------------------
def v2_create_shell():
    base_x_values = [base.LENGTH * i / 160.0 for i in range(161)]
    key_x_values = [
        0.0,
        8.0,
        12.0,
        15.0,
        18.0,
        base.FRONT_X,
        44.0,
        55.0,
        60.0,
        68.0,
        85.0,
        95.0,
        100.0,
        115.0,
        120.0,
        135.0,
        140.0,
        145.0,
        165.0,
        170.0,
        180.0,
        190.0,
        195.0,
        200.0,
        205.0,
        215.0,
        220.0,
        base.REAR_X,
        235.0,
        240.0,
        245.0,
        248.0,
        250.0,
        260.0,
    ]
    x_values = sorted(set(base_x_values + key_x_values))
    nx = len(x_values)
    ny = 81
    vertices = []
    faces = []

    def top_index(i, j):
        return i * ny + j

    bottom_offset = nx * ny

    def bottom_index(i, j):
        return bottom_offset + i * ny + j

    for z_function in (base.outer_surface_z, base.inner_surface_z):
        for x in x_values:
            inset = base.side_inset(x)
            y_min = inset
            y_max = base.WIDTH - inset
            for j in range(ny):
                y = base.lerp(y_min, y_max, j / (ny - 1))
                vertices.append((x, y, z_function(x, y)))

    for i in range(nx - 1):
        for j in range(ny - 1):
            faces.append(
                (
                    top_index(i, j),
                    top_index(i + 1, j),
                    top_index(i + 1, j + 1),
                    top_index(i, j + 1),
                )
            )
            faces.append(
                (
                    bottom_index(i, j),
                    bottom_index(i, j + 1),
                    bottom_index(i + 1, j + 1),
                    bottom_index(i + 1, j),
                )
            )

    for i in range(nx - 1):
        faces.append(
            (
                top_index(i, 0),
                bottom_index(i, 0),
                bottom_index(i + 1, 0),
                top_index(i + 1, 0),
            )
        )
        faces.append(
            (
                top_index(i, ny - 1),
                top_index(i + 1, ny - 1),
                bottom_index(i + 1, ny - 1),
                bottom_index(i, ny - 1),
            )
        )

    for j in range(ny - 1):
        faces.append(
            (
                top_index(0, j),
                top_index(0, j + 1),
                bottom_index(0, j + 1),
                bottom_index(0, j),
            )
        )
        faces.append(
            (
                top_index(nx - 1, j),
                bottom_index(nx - 1, j),
                bottom_index(nx - 1, j + 1),
                top_index(nx - 1, j + 1),
            )
        )

    mesh = bpy.data.meshes.new("Supercar_V2_Shell_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("TOKIMI_ROVER_TOP_COVER_SUPERCAR_V2", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


base.create_angular_shell = v2_create_shell


# ---------------------------------------------------------------------------
# 3. Engraved panel lines through the unused tower-window-cutter hook
# ---------------------------------------------------------------------------
def conforming_groove(name, start_xy, end_xy, width, depth, rise=3.0):
    """Closed prism whose floor tracks the outer skin `depth` mm deep."""
    x0, y0 = start_xy
    x1, y1 = end_xy
    length = math.hypot(x1 - x0, y1 - y0)
    steps = max(2, int(length / 2.5))
    direction = ((x1 - x0) / length, (y1 - y0) / length)
    normal = (-direction[1] * width / 2.0, direction[0] * width / 2.0)

    left = []
    right = []
    for i in range(steps + 1):
        t = i / steps
        cx = base.lerp(x0, x1, t)
        cy = base.lerp(y0, y1, t)
        left.append((cx + normal[0], cy + normal[1]))
        right.append((cx - normal[0], cy - normal[1]))

    top_z = (
        max(
            base.outer_surface_z(px, py)
            for px, py in left + right
        )
        + rise
    )

    vertices = []
    # Per sample: [left_top, right_top, left_bottom, right_bottom]
    for i in range(steps + 1):
        lx, ly = left[i]
        rx, ry = right[i]
        vertices.append((lx, ly, top_z))
        vertices.append((rx, ry, top_z))
        vertices.append((lx, ly, base.outer_surface_z(lx, ly) - depth))
        vertices.append((rx, ry, base.outer_surface_z(rx, ry) - depth))

    def vid(sample, corner):
        return sample * 4 + corner

    faces = []
    for i in range(steps):
        # Top (facing +Z), floor (facing -Z), and both side walls.
        faces.append((vid(i, 0), vid(i, 1), vid(i + 1, 1), vid(i + 1, 0)))
        faces.append((vid(i, 3), vid(i, 2), vid(i + 1, 2), vid(i + 1, 3)))
        faces.append((vid(i, 2), vid(i, 0), vid(i + 1, 0), vid(i + 1, 2)))
        faces.append((vid(i, 1), vid(i, 3), vid(i + 1, 3), vid(i + 1, 1)))
    faces.append((vid(0, 0), vid(0, 2), vid(0, 3), vid(0, 1)))
    faces.append(
        (
            vid(steps, 0),
            vid(steps, 1),
            vid(steps, 3),
            vid(steps, 2),
        )
    )

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def v2_panel_line_cutters():
    """Hood shut-line U plus two short rear-deck vents, engraved 0.5 mm.

    Clearances honoured: hex field one starts at x=49 (transverse line at
    x=45); HOOD_SPEAR trim spans y 45-57 / 98-110 (lines at 59.5 / 95.5);
    the tapered hex field reaches lateral 17.3 mm by x=70.6, so the side
    lines stop at x=68 to clear the last hex column; camera-arch root ends
    by x~173 and the rear vents start at x=232 behind it.
    """
    groove_specs = (
        ("PANEL_LINE_HOOD_FRONT", (45.0, 59.5), (45.0, 95.5)),
        ("PANEL_LINE_HOOD_LEFT", (45.0, 59.5), (68.0, 59.5)),
        ("PANEL_LINE_HOOD_RIGHT", (45.0, 95.5), (68.0, 95.5)),
        ("PANEL_LINE_TAIL_LEFT", (232.0, 65.0), (246.0, 65.0)),
        ("PANEL_LINE_TAIL_RIGHT", (232.0, 90.0), (246.0, 90.0)),
    )
    return [
        conforming_groove(
            name,
            start,
            end,
            width=GROOVE_WIDTH_MM,
            depth=GROOVE_DEPTH_MM,
        )
        for name, start, end in groove_specs
    ]


base.create_tower_window_cutters = v2_panel_line_cutters


# ---------------------------------------------------------------------------
# 4. Guards (shared mesh_guards module): defensive booleans + finishing
#    bevel with adaptive width and full sanity checks
# ---------------------------------------------------------------------------
_guards_spec = importlib.util.spec_from_file_location(
    "tokimi_mesh_guards",
    str(SOURCE_DIR / "mesh_guards.py"),
)
guards = importlib.util.module_from_spec(_guards_spec)
_guards_spec.loader.exec_module(guards)

base.boolean_apply = guards.defensive_boolean_apply

_original_clean_mesh = base.clean_mesh


def v2_clean_mesh(obj):
    _original_clean_mesh(obj)
    if not obj.name.startswith("TOKIMI_ROVER_TOP_COVER"):
        return
    guards.finishing_bevel(
        obj,
        widths=(BEVEL_WIDTH_MM, 0.30, 0.20),
        segments=BEVEL_SEGMENTS,
        angle_floor_deg=BEVEL_ANGLE_LIMIT_DEG,
        smooth_angle_deg=SMOOTH_SHADE_ANGLE_DEG,
        label="SUPERCAR V2 finishing bevel",
    )
    _original_clean_mesh(obj)


base.clean_mesh = v2_clean_mesh


# ---------------------------------------------------------------------------
# Build, then re-render brighter review views and extend the report
# ---------------------------------------------------------------------------
base.build()

cover = bpy.data.objects["TOKIMI_ROVER_TOP_COVER_SUPERCAR_V2"]

scene = bpy.context.scene
scene.display.shading.show_cavity = True
camera = bpy.data.objects["RENDER_CAMERA"]
camera.data.type = "PERSP"
camera.data.lens = 50.0

review_views = {
    "front34": (-230.0, -260.0, 230.0),
    "rear34": (490.0, 300.0, 260.0),
    "side": (130.0, -420.0, 90.0),
}
view_paths = {}
for view_name, location in review_views.items():
    camera.location = location
    base.point_at(camera, (130.0, base.CENTER_Y, 55.0))
    path = os.path.join(base.OUTPUT_DIR, f"{STEM}_{view_name}.png")
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    view_paths[view_name] = path

bpy.ops.wm.save_as_mainfile(filepath=base.BLEND_PATH)

with open(base.REPORT_PATH, "r", encoding="utf-8") as handle:
    report = json.load(handle)
report["design_style"] = (
    "modern supercar, low side wings, raised center tub — V2 smooth "
    "surfacing with finishing bevel and engraved panel lines"
)
report["v2_improvements"] = {
    "surface_interpolation": "monotone cubic (PCHIP) styling tables",
    "shell_sampling": "161 x-stations x 81 y-stations (was ~110 x 41)",
    "finishing_bevel_mm": BEVEL_WIDTH_MM,
    "finishing_bevel_segments": BEVEL_SEGMENTS,
    "panel_line_depth_mm": GROOVE_DEPTH_MM,
    "printability": (
        "bevel doubles as chamfer on M3 hole rims, pad edges, and vent "
        "rims; contact planes and locked dimensions unchanged"
    ),
}
report["review_previews"] = view_paths
with open(base.REPORT_PATH, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, ensure_ascii=False)

print(f"TOKIMI_SUPERCAR_V2_BLEND={base.BLEND_PATH}")
print(f"TOKIMI_SUPERCAR_V2_OBJ={base.OBJ_PATH}")

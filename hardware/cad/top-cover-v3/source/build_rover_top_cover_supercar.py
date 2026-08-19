# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

import importlib.util
import json
import math
import os
from pathlib import Path

import bpy


SOURCE_DIR = Path(__file__).resolve().parent
BASE_SCRIPT = str(SOURCE_DIR / "build_rover_top_cover_angular.py")
spec = importlib.util.spec_from_file_location("tokimi_rover_angular_base", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


# ---------------------------------------------------------------------------
# TOKIMI ROVER TOP COVER — modern supercar surfacing pass
#
# The approved mechanical envelope is deliberately inherited unchanged:
#   260 x 155 mm plan
#   M3 centers 195 x 100 mm
#   3.5 mm holes
#   15 / 55 mm front/rear mounting contact planes
#   2.5 mm shell, 4.0 mm mounting pads
#   19 x 36 mm OLED opening
#   29 x 78 mm camera roof clearance
#
# The styling pass concentrates volume along the centerline while keeping
# low side wings, so usable electronics space is increased rather than lost.
# ---------------------------------------------------------------------------
base.MODEL_NAME = "TOKIMI ROVER TOP COVER — SUPERCAR / TREE SUPPORT"
base.OBJ_OBJECT_NAME = "TOKIMI_ROVER_TOP_COVER_SUPERCAR_TREE_SUPPORT"
base.OUTPUT_DIR = os.environ.get(
    "TOKIMI_CAD_OUTPUT_DIR",
    str(SOURCE_DIR.parent / "generated"),
)
base.OBJ_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm.obj",
)
base.BLEND_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm.blend",
)
base.PREVIEW_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm_preview.png",
)
base.TOP_PREVIEW_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm_top.png",
)
base.REPORT_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm_validation.json",
)
SIDE_PREVIEW_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm_side.png",
)
FRONT_PREVIEW_PATH = os.path.join(
    base.OUTPUT_DIR,
    "tokimi_rover_top_cover_supercar_tree_support_195x100mm_front.png",
)
base_add_render_scene = base.add_render_scene


def supercar_raw_inner_surface_z(x, y):
    """Raised center tub with low, swept side wings."""
    longitudinal = base.interpolate_table(
        (
            (0.0, -4.0),
            (15.0, -2.5),
            (base.FRONT_X, 0.0),
            (55.0, 3.5),
            (85.0, 6.5),
            (115.0, 8.5),
            (145.0, 9.5),
            (170.0, 8.0),
            (200.0, 4.5),
            (base.REAR_X, 0.0),
            (245.0, -1.5),
            (260.0, -3.0),
        ),
        x,
    )

    lateral_distance = abs(y - base.CENTER_Y)
    low_wing_to_spine = base.interpolate_table(
        (
            (0.0, 9.0),
            (18.0, 8.5),
            (32.0, 6.0),
            (45.0, 2.5),
            (58.0, -0.5),
            (70.0, -2.5),
            (77.5, -4.0),
        ),
        lateral_distance,
    )

    # This is the usable-volume feature: a broad center tub rises above the
    # side wings without changing the four exact mounting contact regions.
    center_rise = base.interpolate_table(
        (
            (0.0, 0.0),
            (25.0, 2.0),
            (55.0, 8.0),
            (90.0, 13.0),
            (120.0, 17.0),
            (150.0, 18.0),
            (175.0, 14.0),
            (205.0, 8.0),
            (235.0, 3.0),
            (260.0, 0.0),
        ),
        x,
    )
    if lateral_distance <= 20.0:
        center_factor = 1.0
    elif lateral_distance >= 52.0:
        center_factor = 0.0
    else:
        center_factor = 1.0 - base.smoothstep(
            (lateral_distance - 20.0) / 32.0
        )

    return (
        base.baseline_z(x)
        + longitudinal
        + low_wing_to_spine
        + center_rise * center_factor
    )


def supercar_side_inset(x):
    """Long wedge nose, pinched waist, and a full-width rear haunch."""
    return base.interpolate_table(
        (
            (0.0, 20.0),
            (10.0, 15.0),
            (22.0, 8.0),
            (base.FRONT_X, 4.0),
            (55.0, 0.0),
            (100.0, 2.0),
            (145.0, 7.0),
            (190.0, 2.0),
            (base.REAR_X, 0.0),
            (245.0, 8.0),
            (260.0, 24.0),
        ),
        x,
    )


def supercar_outer_surface_z(x, y):
    """Approximate a 2.5 mm normal wall on the steep center shoulders."""
    inner = base.inner_surface_z(x, y)
    step = 0.4
    x_low = max(0.0, x - step)
    x_high = min(base.LENGTH, x + step)
    y_low = max(0.0, y - step)
    y_high = min(base.WIDTH, y + step)
    dz_dx = (
        base.inner_surface_z(x_high, y)
        - base.inner_surface_z(x_low, y)
    ) / max(x_high - x_low, 0.001)
    dz_dy = (
        base.inner_surface_z(x, y_high)
        - base.inner_surface_z(x, y_low)
    ) / max(y_high - y_low, 0.001)
    slope_scale = math.sqrt(1.0 + dz_dx * dz_dx + dz_dy * dz_dy)
    vertical_offset = min(
        4.0,
        max(base.SHELL_THICKNESS, base.SHELL_THICKNESS * slope_scale),
    )
    return inner + vertical_offset


def supercar_hex_field_cutter():
    """Two tapered heat-extraction fields instead of rectangular grilles."""
    polygons = []
    radius = 1.9
    x_pitch = 5.4
    y_pitch = 5.0

    def add_tapered_field(x_min, x_max, half_width_front, half_width_rear):
        # Each column is distributed SYMMETRICALLY about the vehicle
        # centerline: even columns place a hex on the centerline and march
        # outward, odd (staggered) columns straddle it by half a pitch.
        # The previous bottom-anchored loop dumped the remainder gap on
        # one side, so the whole field sat visibly off-center.
        column = 0
        x = x_min
        while x <= x_max + 0.01:
            t = (x - x_min) / max(x_max - x_min, 1.0)
            half_width = base.lerp(half_width_front, half_width_rear, t)
            if column % 2:
                steps = int((half_width - y_pitch / 2.0) // y_pitch)
                offsets = [
                    (step + 0.5) * y_pitch for step in range(-steps - 1, steps + 1)
                ]
            else:
                steps = int(half_width // y_pitch)
                offsets = [
                    step * y_pitch for step in range(-steps, steps + 1)
                ]
            for offset in offsets:
                y = base.CENTER_Y + offset
                polygons.append(
                    [
                        (
                            x
                            + radius
                            * math.cos(math.radians(30.0 + 60.0 * index)),
                            y
                            + radius
                            * math.sin(math.radians(30.0 + 60.0 * index)),
                        )
                        for index in range(6)
                    ]
                )
            column += 1
            x += x_pitch

    add_tapered_field(49.0, 76.0, 9.0, 17.0)
    add_tapered_field(124.0, 148.0, 18.0, 11.0)
    return base.create_multi_xy_prism("SUPERCAR_HEAT_EXTRACTORS", polygons)


def supercar_side_window_cutter():
    """Two concentrated swept intakes per side."""
    left_openings = [
        # Forward guide intake.
        [
            (63.0, 20.0),
            (88.0, 20.0),
            (112.0, 37.0),
            (102.0, 43.0),
            (79.0, 34.0),
            (67.0, 33.0),
        ],
        # Main side intake.
        [
            (132.0, 23.0),
            (160.0, 20.0),
            (198.0, 28.0),
            (189.0, 39.0),
            (160.0, 37.0),
            (143.0, 44.0),
        ],
    ]
    openings = list(left_openings)
    openings.extend(base.mirror_polygon_y(points) for points in left_openings)
    return base.create_multi_xy_prism("SUPERCAR_SWEPT_INTAKES", openings)


def supercar_rail_and_panel_objects():
    """A small hierarchy of strong shoulder lines and quiet secondary trim."""
    objects = []

    left_features = (
        (
            "LOW_SPLITTER",
            [
                (28.0, 4.5),
                (74.0, 3.5),
                (113.0, 7.0),
                (105.0, 12.0),
                (33.0, 13.0),
            ],
            2.4,
        ),
        (
            "HEADLIGHT_BLADE",
            [
                (28.0, 39.0),
                (46.0, 42.0),
                (38.0, 50.0),
                (29.0, 51.0),
            ],
            1.3,
        ),
        (
            "REAR_AERO_BLADE",
            [
                (183.0, 31.0),
                (211.0, 19.0),
                (219.0, 27.0),
                (198.0, 37.5),
                (184.0, 39.0),
            ],
            3.4,
        ),
        (
            "HOOD_SPEAR",
            [
                (38.0, 45.0),
                (80.0, 47.0),
                (94.0, 54.0),
                (86.0, 57.0),
                (50.0, 53.0),
            ],
            2.2,
        ),
    )
    for name, polygon, height in left_features:
        objects.append(
            base.create_conforming_polygon_solid(
                f"{name}_LEFT",
                polygon,
                height=height,
            )
        )
        objects.append(
            base.create_conforming_polygon_solid(
                f"{name}_RIGHT",
                base.mirror_polygon_y(polygon),
                height=height,
            )
        )

    # A broad, low fascia ties the two front corners into one supercar nose.
    objects.append(
        base.create_conforming_polygon_solid(
            "CONTINUOUS_FRONT_FASCIA",
            [
                (1.0, 31.0),
                (15.0, 25.0),
                (22.0, 31.0),
                (25.0, 44.0),
                (25.0, 111.0),
                (22.0, 124.0),
                (15.0, 130.0),
                (1.0, 124.0),
            ],
            height=1.2,
        )
    )

    # Low center badge piece extends the spine without a tall pyramid.
    objects.append(
        base.create_conforming_polygon_solid(
            "LOW_CENTER_NOSE",
            [
                (2.0, 65.0),
                (23.0, 62.0),
                (28.0, 68.0),
                (28.0, 87.0),
                (23.0, 93.0),
                (2.0, 90.0),
            ],
            height=0.9,
        )
    )
    return objects


def supercar_flat_mount_boss(name, x, y, contact_z):
    """Embed by 0.01 mm into the shell without crossing the contact plane."""
    embed = 0.01
    depth = base.PAD_TOTAL_THICKNESS - embed
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=base.PAD_RADIUS,
        depth=depth,
        location=(x, y, contact_z + embed + depth / 2.0),
    )
    boss = bpy.context.active_object
    boss.name = name
    return boss


def supercar_camera_arch():
    """Tapered camera arch with shell-conforming, flared integral roots."""
    base_z = base.outer_surface_z(base.TOWER_FOOT_X, base.CENTER_Y) - 3.0
    height = base.TOWER_HEIGHT
    inner_height = base.TOWER_VISIBLE_OPENING[1]
    root_embed = 2.2
    root_blend_height = 28.0
    root_front_flare = 3.5
    root_depth_flare = 8.0

    # The upper corners taper like a windscreen while keeping a broad center
    # aperture and camera sightline. The feet flare toward the deck so the
    # arch grows out of the shell instead of reading as a separate flat part.
    yz_points = [
        (-41.0, 0.0),
        (-37.0, height * 0.42),
        (-34.0, height * 0.78),
        (-29.0, height),
        (29.0, height),
        (34.0, height * 0.78),
        (37.0, height * 0.42),
        (41.0, 0.0),
        (18.0, 0.0),
        (21.0, inner_height * 0.45),
        (20.0, inner_height * 0.82),
        (14.0, inner_height),
        (-14.0, inner_height),
        (-20.0, inner_height * 0.82),
        (-21.0, inner_height * 0.45),
        (-18.0, 0.0),
    ]
    if base.polygon_area_2d(yz_points) < 0.0:
        yz_points.reverse()

    def arch_vertex(y_local, z_local, is_back):
        blend_t = base.smoothstep(
            min(max(z_local / root_blend_height, 0.0), 1.0)
        )
        root_weight = 1.0 - blend_t
        x_front = (
            base.TOWER_FOOT_X
            + base.TOWER_RAKE * z_local
            - root_front_flare * root_weight
        )
        local_depth = (
            base.lerp(17.0, 11.5, z_local / height)
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
        vertices.append(arch_vertex(y_local, z_local, False))
    for y_local, z_local in yz_points:
        vertices.append(arch_vertex(y_local, z_local, True))

    count = len(yz_points)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append(
            (
                index,
                next_index,
                count + next_index,
                count + index,
            )
        )

    mesh = bpy.data.meshes.new("Supercar_Camera_Arch_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("SUPERCAR_CAMERA_ARCH", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def supercar_tower_side_plates():
    """Use slicer-generated tree supports instead of permanent side frames."""
    return ()


def supercar_tower_window_cutters():
    """The open U-shaped camera arch needs no secondary side apertures."""
    return []


def supercar_add_render_scene(cover):
    base_add_render_scene(cover)
    cover.color = (0.045, 0.12, 0.20, 1.0)
    camera = bpy.data.objects.get("RENDER_CAMERA")
    camera.data.lens = 64.0
    camera.location = (-255.0, -335.0, 310.0)
    base.point_at(camera, (128.0, base.CENTER_Y, 68.0))


base.raw_inner_surface_z = supercar_raw_inner_surface_z
base.side_inset = supercar_side_inset
base.create_hex_field_cutter = supercar_hex_field_cutter
base.create_side_window_cutter = supercar_side_window_cutter
base.create_rail_and_brace_objects = supercar_rail_and_panel_objects
base.create_flat_mount_boss = supercar_flat_mount_boss
base.create_camera_arch = supercar_camera_arch
base.create_tower_side_plates = supercar_tower_side_plates
base.create_tower_window_cutters = supercar_tower_window_cutters
base.add_render_scene = supercar_add_render_scene
base.TOWER_RAKE = 0.44
base.TOWER_OUTER_WIDTH = 76.0
base.TOWER_DEPTH = 17.0
base.TOWER_HEIGHT = 62.0
base.TOWER_VISIBLE_OPENING = (42.0, 50.0)
base.CAMERA_CORNER_RADIUS = 4.5
base.RECUT_OLED = False
base.RECUT_CAMERA = False
base.TRIANGULATE_OBJ = False


base.build()


# Add a low side render so the retained center volume and wedge profile can
# be judged independently of the top and three-quarter views.
camera = bpy.data.objects.get("RENDER_CAMERA")
camera.data.type = "ORTHO"
camera.data.ortho_scale = 325.0
camera.location = (125.0, -480.0, 108.0)
base.point_at(camera, (128.0, base.CENTER_Y, 72.0))
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 620
bpy.context.scene.render.filepath = SIDE_PREVIEW_PATH
bpy.ops.render.render(write_still=True)

# Direct front view verifies that both arch roots follow the raised center
# shell and do not read as a flat, separate part resting on the deck.
camera.data.ortho_scale = 112.0
camera.location = (-260.0, base.CENTER_Y, 96.0)
base.point_at(camera, (168.0, base.CENTER_Y, 96.0))
bpy.context.scene.render.resolution_x = 1000
bpy.context.scene.render.resolution_y = 760
bpy.context.scene.render.filepath = FRONT_PREVIEW_PATH
bpy.ops.render.render(write_still=True)


with open(base.REPORT_PATH, "r", encoding="utf-8") as handle:
    report = json.load(handle)
report["design_style"] = "modern supercar, low side wings, raised center tub"
report["support_strategy"] = (
    "All permanent left/right camera-side cabin frames, front connector "
    "posts, and FRONT_SHOULDER + MID_SHOULDER beam pairs are removed; "
    "use slicer-generated Tree/Organic supports"
)
report["shell_thickness_strategy"] = (
    "2.5 mm nominal shell with 4.0 mm mounting pads and raised shoulder ribs"
)
report["camera_arch_root_strategy"] = (
    "Each flared root follows its local shell height, embeds 2.2 mm into the "
    "deck, and blends to the nominal rear-raked arch over 28 mm of height"
)
report["oled_orientation"] = (
    "19 mm front-to-rear (X) x 36 mm across vehicle width (Y)"
)
report["critical_dimensions_locked"] = {
    "overall_plan_mm": [260.0, 155.0],
    "mount_spacing_mm": [195.0, 100.0],
    "mount_centers_xy_mm": [
        [32.5, 27.5],
        [32.5, 127.5],
        [227.5, 27.5],
        [227.5, 127.5],
    ],
    "m3_hole_diameter_mm": 3.5,
    "front_contact_height_mm": 15.0,
    "rear_contact_height_mm": 55.0,
    "oled_opening_xy_mm": [19.0, 36.0],
    "camera_roof_clearance_xy_mm": [29.0, 78.0],
}
report["center_inner_surface_samples_mm"] = {
    str(x): round(supercar_raw_inner_surface_z(x, base.CENTER_Y), 3)
    for x in (55.0, 90.0, 120.0, 150.0, 175.0, 205.0)
}
report["additional_preview"] = SIDE_PREVIEW_PATH
report["front_joint_preview"] = FRONT_PREVIEW_PATH
report["print_notes"] = [
    "OBJ coordinates are millimetres.",
    "PETG recommended.",
    "Do not place the four mounting pads directly on the print bed.",
    "Enable slicer-generated Tree/Organic supports beneath the nose, center "
    "shell, side shoulders, and camera bridge.",
    "No permanent left/right camera-side frames or former FRONT_SHOULDER "
    "and MID_SHOULDER beams are part of this version.",
    "Use 4 or more perimeters around the intakes, mounting pads, and tower.",
    "Run a low-cost fit check before the final print.",
]
with open(base.REPORT_PATH, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2, ensure_ascii=False)

print(f"TOKIMI_SUPERCAR_SIDE={SIDE_PREVIEW_PATH}")
print(f"TOKIMI_SUPERCAR_FRONT={FRONT_PREVIEW_PATH}")

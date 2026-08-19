# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

import bpy
import bmesh
import json
import math
import os
from mathutils import Vector
from pathlib import Path


# ---------------------------------------------------------------------------
# TOKIMI ROVER TOP COVER — angular project-styling version
# Blender coordinates and OBJ coordinates are millimetres.
# +X rearward, +Y vehicle-right, +Z upward.
# ---------------------------------------------------------------------------
MODEL_NAME = "TOKIMI ROVER TOP COVER — ANGULAR"
OBJ_OBJECT_NAME = "TOKIMI_ROVER_TOP_COVER_ANGULAR"
LENGTH = 260.0
WIDTH = 155.0
CENTER_Y = WIDTH / 2.0
SHELL_THICKNESS = 2.5

FRONT_X = 32.5
REAR_X = 227.5
LEFT_Y = 27.5
RIGHT_Y = 127.5
FRONT_CONTACT_Z = 15.0
REAR_CONTACT_Z = 55.0
HOLE_DIAMETER = 3.5
HOLE_RADIUS = HOLE_DIAMETER / 2.0
PAD_RADIUS = 8.0
PAD_TOTAL_THICKNESS = 4.0
FINAL_RECUT_OVERSIZE = 0.04
RECUT_OLED = True
RECUT_CAMERA = True
TRIANGULATE_OBJ = True

# The OLED long edge is across the vehicle, matching the owner-approved layout.
OLED_CENTER = (102.0, CENTER_Y)
OLED_OPENING = (19.0, 36.0)  # X by Y
OLED_BEZEL_OUTER = (27.0, 44.0)
OLED_CORNER_RADIUS = 2.5

# The exact module clearance remains a plan-view slot beneath/behind the arch.
CAMERA_ROOF_CENTER = (205.0, CENTER_Y)
CAMERA_ROOF_OPENING = (29.0, 78.0)  # X by Y
CAMERA_CORNER_RADIUS = 3.0

# Visible forward optical arch from the project styling pass.
TOWER_FOOT_X = 151.0
TOWER_DEPTH = 17.0
TOWER_RAKE = 0.30
TOWER_OUTER_WIDTH = 84.0
TOWER_HEIGHT = 78.0
TOWER_VISIBLE_OPENING = (42.0, 66.0)  # Y by Z, aesthetic/optical window

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SOURCE_DIR.parent
OUTPUT_DIR = os.environ.get(
    "TOKIMI_CAD_OUTPUT_DIR",
    str(PROJECT_DIR / "generated"),
)
OBJ_PATH = os.path.join(
    OUTPUT_DIR,
    "tokimi_rover_top_cover_angular_195x100mm.obj",
)
BLEND_PATH = os.path.join(
    OUTPUT_DIR,
    "tokimi_rover_top_cover_angular_195x100mm.blend",
)
PREVIEW_PATH = os.path.join(
    OUTPUT_DIR,
    "tokimi_rover_top_cover_angular_195x100mm_preview.png",
)
TOP_PREVIEW_PATH = os.path.join(
    OUTPUT_DIR,
    "tokimi_rover_top_cover_angular_195x100mm_top.png",
)
REPORT_PATH = os.path.join(
    OUTPUT_DIR,
    "tokimi_rover_top_cover_angular_195x100mm_validation.json",
)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def interpolate_table(table, value):
    if value <= table[0][0]:
        return table[0][1]
    if value >= table[-1][0]:
        return table[-1][1]
    for index in range(len(table) - 1):
        x0, y0 = table[index]
        x1, y1 = table[index + 1]
        if x0 <= value <= x1:
            return lerp(y0, y1, (value - x0) / (x1 - x0))
    return table[-1][1]


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def configure_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0

    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studio_light = "paint.sl"
    shading.studiolight_intensity = 1.15
    shading.color_type = "OBJECT"
    shading.background_type = "VIEWPORT"
    shading.background_color = (0.006, 0.012, 0.022)
    shading.show_shadows = True
    shading.shadow_intensity = 0.55
    shading.show_cavity = True
    shading.cavity_type = "WORLD"
    shading.cavity_ridge_factor = 2.0
    shading.cavity_valley_factor = 1.5
    shading.show_specular_highlight = True


def baseline_z(x):
    return FRONT_CONTACT_Z + (
        (x - FRONT_X)
        * (REAR_CONTACT_Z - FRONT_CONTACT_Z)
        / (REAR_X - FRONT_X)
    )


def raw_inner_surface_z(x, y):
    # Hand-authored, piecewise-linear styling offsets make planar/faceted
    # hood zones instead of the previous smooth quadratic plate.
    longitudinal = interpolate_table(
        (
            (0.0, -2.0),
            (FRONT_X, 0.0),
            (58.0, 2.0),
            (95.0, 4.0),
            (135.0, 6.0),
            (175.0, 5.0),
            (215.0, 2.0),
            (REAR_X, 0.0),
            (260.0, -2.0),
        ),
        x,
    )
    lateral_distance = abs(y - CENTER_Y)
    lateral = interpolate_table(
        (
            (0.0, 8.0),
            (18.0, 7.0),
            (32.5, 4.0),
            (50.0, 0.0),
            (65.0, -1.2),
            (77.5, -3.0),
        ),
        lateral_distance,
    )
    return baseline_z(x) + longitudinal + lateral


MOUNT_CENTERS = (
    (FRONT_X, LEFT_Y, FRONT_CONTACT_Z),
    (FRONT_X, RIGHT_Y, FRONT_CONTACT_Z),
    (REAR_X, LEFT_Y, REAR_CONTACT_Z),
    (REAR_X, RIGHT_Y, REAR_CONTACT_Z),
)


def inner_surface_z(x, y):
    value = raw_inner_surface_z(x, y)
    # Flat, exact standoff contact regions: the previous version incorrectly
    # let the reinforcement extend below the stated 15/55 mm planes.
    for mount_x, mount_y, contact_z in MOUNT_CENTERS:
        distance = math.hypot(x - mount_x, y - mount_y)
        if distance <= 9.0:
            return contact_z
        if distance < 14.0:
            t = smoothstep((distance - 9.0) / 5.0)
            return lerp(contact_z, value, t)
    return value


def outer_surface_z(x, y):
    return inner_surface_z(x, y) + SHELL_THICKNESS


def side_inset(x):
    return interpolate_table(
        (
            (0.0, 18.0),
            (12.0, 5.0),
            (FRONT_X, 0.0),
            (60.0, 0.0),
            (100.0, 2.0),
            (140.0, 5.0),
            (180.0, 4.0),
            (220.0, 1.0),
            (REAR_X, 0.0),
            (248.0, 5.0),
            (260.0, 18.0),
        ),
        x,
    )


def create_angular_shell():
    base_x_values = [LENGTH * i / 80.0 for i in range(81)]
    key_x_values = [
        0.0,
        8.0,
        12.0,
        15.0,
        18.0,
        FRONT_X,
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
        REAR_X,
        235.0,
        240.0,
        245.0,
        248.0,
        250.0,
        260.0,
    ]
    x_values = sorted(set(base_x_values + key_x_values))
    nx = len(x_values)
    ny = 41
    vertices = []
    faces = []

    def top_index(i, j):
        return i * ny + j

    bottom_offset = nx * ny

    def bottom_index(i, j):
        return bottom_offset + i * ny + j

    for z_function in (outer_surface_z, inner_surface_z):
        for x in x_values:
            inset = side_inset(x)
            y_min = inset
            y_max = WIDTH - inset
            for j in range(ny):
                y = lerp(y_min, y_max, j / (ny - 1))
                vertices.append((x, y, z_function(x, y)))

    for i in range(nx - 1):
        for j in range(ny - 1):
            top = (
                top_index(i, j),
                top_index(i + 1, j),
                top_index(i + 1, j + 1),
                top_index(i, j + 1),
            )
            bottom = (
                bottom_index(i, j),
                bottom_index(i, j + 1),
                bottom_index(i + 1, j + 1),
                bottom_index(i + 1, j),
            )
            faces.extend((top, bottom))

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

    mesh = bpy.data.meshes.new("Angular_Rover_Shell_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("TOKIMI_ROVER_TOP_COVER_ANGULAR", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def polygon_area_2d(points):
    return sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    ) / 2.0


def ensure_ccw(points):
    points = list(points)
    if polygon_area_2d(points) < 0.0:
        points.reverse()
    return points


def append_xy_prism(vertices, faces, points, z_min, z_max):
    points = ensure_ccw(points)
    offset = len(vertices)
    count = len(points)
    vertices.extend((x, y, z_min) for x, y in points)
    vertices.extend((x, y, z_max) for x, y in points)
    faces.append(tuple(offset + i for i in reversed(range(count))))
    faces.append(tuple(offset + count + i for i in range(count)))
    for i in range(count):
        next_i = (i + 1) % count
        faces.append(
            (
                offset + i,
                offset + next_i,
                offset + count + next_i,
                offset + count + i,
            )
        )


def create_multi_xy_prism(name, polygons, z_min=-20.0, z_max=180.0):
    vertices = []
    faces = []
    for points in polygons:
        append_xy_prism(vertices, faces, points, z_min, z_max)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def rounded_rect_points(cx, cy, size_x, size_y, radius, segments=8):
    hx = size_x / 2.0
    hy = size_y / 2.0
    radius = min(radius, hx, hy)
    points = []
    corners = (
        (cx + hx - radius, cy - hy + radius, -90.0),
        (cx + hx - radius, cy + hy - radius, 0.0),
        (cx - hx + radius, cy + hy - radius, 90.0),
        (cx - hx + radius, cy - hy + radius, 180.0),
    )
    for corner_x, corner_y, start_angle in corners:
        for index in range(segments):
            angle = math.radians(start_angle + 90.0 * index / segments)
            points.append(
                (
                    corner_x + radius * math.cos(angle),
                    corner_y + radius * math.sin(angle),
                )
            )
    return points


def create_rounded_xy_prism(
    name,
    center,
    size,
    radius,
    z_min=-20.0,
    z_max=180.0,
):
    return create_multi_xy_prism(
        name,
        [
            rounded_rect_points(
                center[0],
                center[1],
                size[0],
                size[1],
                radius,
            )
        ],
        z_min,
        z_max,
    )


def create_hex_field_cutter():
    polygons = []

    def add_field(x_min, x_max, y_min, y_max):
        radius = 2.15
        x_pitch = 5.7
        y_pitch = 5.2
        column = 0
        x = x_min
        while x <= x_max:
            y = y_min + (y_pitch / 2.0 if column % 2 else 0.0)
            while y <= y_max:
                polygons.append(
                    [
                        (
                            x + radius * math.cos(math.radians(30.0 + 60.0 * i)),
                            y + radius * math.sin(math.radians(30.0 + 60.0 * i)),
                        )
                        for i in range(6)
                    ]
                )
                y += y_pitch
            column += 1
            x += x_pitch

    add_field(48.0, 76.0, 58.0, 97.0)
    add_field(124.0, 148.0, 57.0, 98.0)
    return create_multi_xy_prism("HONEYCOMB_CUTTERS", polygons)


def mirror_polygon_y(points):
    return [(x, WIDTH - y) for x, y in reversed(points)]


def create_side_window_cutter():
    left_windows = [
        [(43.0, 18.0), (70.0, 20.0), (86.0, 39.0), (56.0, 36.0)],
        [(83.0, 19.0), (115.0, 20.0), (136.0, 44.0), (101.0, 39.0)],
        [(128.0, 20.0), (161.0, 18.0), (184.0, 41.0), (149.0, 44.0)],
        [(176.0, 19.0), (207.0, 16.0), (218.0, 35.0), (194.0, 40.0)],
    ]
    all_windows = list(left_windows)
    all_windows.extend(mirror_polygon_y(points) for points in left_windows)
    return create_multi_xy_prism("SIDE_LATTICE_WINDOWS", all_windows)


def create_flat_mount_boss(name, x, y, contact_z):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=PAD_RADIUS,
        depth=PAD_TOTAL_THICKNESS,
        location=(x, y, contact_z + PAD_TOTAL_THICKNESS / 2.0),
    )
    boss = bpy.context.active_object
    boss.name = name
    return boss


def create_conforming_polygon_solid(
    name,
    points,
    height,
    embed=0.8,
):
    points = ensure_ccw(points)
    center_x = sum(point[0] for point in points) / len(points)
    center_y = sum(point[1] for point in points) / len(points)
    vertices = [
        (
            center_x,
            center_y,
            outer_surface_z(center_x, center_y) + height,
        ),
        (
            center_x,
            center_y,
            outer_surface_z(center_x, center_y) - embed,
        ),
    ]
    top_center = 0
    bottom_center = 1
    top_ring = []
    bottom_ring = []
    for x, y in points:
        top_ring.append(len(vertices))
        vertices.append((x, y, outer_surface_z(x, y) + height))
        bottom_ring.append(len(vertices))
        vertices.append((x, y, outer_surface_z(x, y) - embed))

    faces = []
    for index in range(len(points)):
        next_index = (index + 1) % len(points)
        faces.append((top_center, top_ring[index], top_ring[next_index]))
        faces.append(
            (
                bottom_center,
                bottom_ring[next_index],
                bottom_ring[index],
            )
        )
        faces.append(
            (
                top_ring[index],
                bottom_ring[index],
                bottom_ring[next_index],
                top_ring[next_index],
            )
        )

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_rail_and_brace_objects():
    left_rails = [
        [(16.0, 6.0), (82.0, 4.5), (82.0, 15.0), (20.0, 18.0)],
        [(80.0, 5.0), (157.0, 8.0), (155.0, 19.5), (80.0, 16.5)],
        [(154.0, 8.0), (239.0, 6.0), (248.0, 17.0), (154.0, 21.0)],
        [(33.0, 38.0), (116.0, 45.0), (110.0, 53.0), (39.0, 47.0)],
        [(108.0, 45.0), (177.0, 46.0), (171.0, 55.0), (107.0, 54.0)],
        [(168.0, 46.0), (229.0, 35.0), (237.0, 44.0), (174.0, 57.0)],
    ]
    left_braces = [
        [(52.0, 15.0), (60.0, 14.5), (83.0, 40.0), (72.0, 39.0)],
        [(91.0, 17.0), (101.0, 17.5), (127.0, 43.0), (115.0, 42.0)],
        [(136.0, 19.0), (147.0, 18.0), (173.0, 42.0), (160.0, 44.0)],
        [(183.0, 18.0), (194.0, 16.0), (218.0, 36.0), (204.0, 41.0)],
    ]
    objects = []
    for group_name, polygons, height in (
        ("OUTER_RAIL", left_rails[:3], 3.2),
        ("INNER_RAIL", left_rails[3:], 2.6),
        ("DIAGONAL_BRACE", left_braces, 3.0),
    ):
        for index, polygon in enumerate(polygons):
            objects.append(
                create_conforming_polygon_solid(
                    f"{group_name}_L_{index + 1}",
                    polygon,
                    height=height,
                )
            )
            objects.append(
                create_conforming_polygon_solid(
                    f"{group_name}_R_{index + 1}",
                    mirror_polygon_y(polygon),
                    height=height,
                )
            )

    # Nose badge/cross-member evokes the front fascia without adding chassis.
    objects.append(
        create_conforming_polygon_solid(
            "FRONT_BADGE_PLATE",
            [(10.0, 55.0), (34.0, 58.0), (34.0, 97.0), (10.0, 100.0)],
            height=2.2,
        )
    )
    return objects


def create_conforming_bezel_ring():
    outer = rounded_rect_points(
        OLED_CENTER[0],
        OLED_CENTER[1],
        OLED_BEZEL_OUTER[0],
        OLED_BEZEL_OUTER[1],
        radius=3.5,
    )
    inner = rounded_rect_points(
        OLED_CENTER[0],
        OLED_CENTER[1],
        OLED_OPENING[0],
        OLED_OPENING[1],
        radius=2.5,
    )
    count = len(outer)
    vertices = []
    outer_top = []
    inner_top = []
    outer_bottom = []
    inner_bottom = []

    for x, y in outer:
        outer_top.append(len(vertices))
        vertices.append((x, y, outer_surface_z(x, y) + 1.6))
    for x, y in inner:
        inner_top.append(len(vertices))
        vertices.append((x, y, outer_surface_z(x, y) + 1.6))
    for x, y in outer:
        outer_bottom.append(len(vertices))
        vertices.append((x, y, outer_surface_z(x, y) - 0.8))
    for x, y in inner:
        inner_bottom.append(len(vertices))
        vertices.append((x, y, outer_surface_z(x, y) - 0.8))

    faces = []
    for index in range(count):
        next_index = (index + 1) % count
        faces.extend(
            (
                (
                    outer_top[index],
                    outer_top[next_index],
                    inner_top[next_index],
                    inner_top[index],
                ),
                (
                    outer_bottom[index],
                    inner_bottom[index],
                    inner_bottom[next_index],
                    outer_bottom[next_index],
                ),
                (
                    outer_top[index],
                    outer_bottom[index],
                    outer_bottom[next_index],
                    outer_top[next_index],
                ),
                (
                    inner_top[index],
                    inner_top[next_index],
                    inner_bottom[next_index],
                    inner_bottom[index],
                ),
            )
        )

    mesh = bpy.data.meshes.new("OLED_Bezel_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("OLED_RECESSED_BEZEL", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_camera_arch():
    base_z = outer_surface_z(TOWER_FOOT_X, CENTER_Y) - 1.0
    half_outer = TOWER_OUTER_WIDTH / 2.0
    half_inner = TOWER_VISIBLE_OPENING[0] / 2.0
    inner_height = TOWER_VISIBLE_OPENING[1]

    # Concave U-shaped polygon in local (Y,Z). It directly forms a hollow
    # forward-facing arch and avoids a fragile portrait-window boolean.
    yz_points = [
        (-half_outer, 0.0),
        (-half_outer + 8.0, TOWER_HEIGHT - 8.0),
        (-half_outer + 17.0, TOWER_HEIGHT),
        (half_outer - 17.0, TOWER_HEIGHT),
        (half_outer - 8.0, TOWER_HEIGHT - 8.0),
        (half_outer, 0.0),
        (half_inner, 0.0),
        (half_inner - 1.5, inner_height - 7.0),
        (half_inner - 7.0, inner_height),
        (-half_inner + 7.0, inner_height),
        (-half_inner + 1.5, inner_height - 7.0),
        (-half_inner, 0.0),
    ]
    if polygon_area_2d(yz_points) < 0.0:
        yz_points.reverse()

    vertices = []
    for y_local, z_local in yz_points:
        x = TOWER_FOOT_X + TOWER_RAKE * z_local
        vertices.append((x, CENTER_Y + y_local, base_z + z_local))
    for y_local, z_local in yz_points:
        x = TOWER_FOOT_X + TOWER_RAKE * z_local + TOWER_DEPTH
        vertices.append((x, CENTER_Y + y_local, base_z + z_local))

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

    mesh = bpy.data.meshes.new("Camera_Arch_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new("CAMERA_FORWARD_ARCH", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_axis_y_prism(name, xz_points, y_min, y_max):
    xz_points = ensure_ccw(xz_points)
    count = len(xz_points)
    vertices = [(x, y_min, z) for x, z in xz_points]
    vertices.extend((x, y_max, z) for x, z in xz_points)
    faces = [tuple(range(count)), tuple(reversed(range(count, 2 * count)))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append(
            (
                index,
                count + index,
                count + next_index,
                next_index,
            )
        )
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_tower_side_plates():
    base_z = outer_surface_z(TOWER_FOOT_X, CENTER_Y) - 1.2
    rear_z = outer_surface_z(220.0, 38.0)
    xz_outline = [
        (147.5, base_z),
        (TOWER_FOOT_X + TOWER_RAKE * TOWER_HEIGHT, base_z + TOWER_HEIGHT),
        (
            TOWER_FOOT_X + TOWER_RAKE * TOWER_HEIGHT + TOWER_DEPTH,
            base_z + TOWER_HEIGHT,
        ),
        (220.0, rear_z + 6.0),
        (220.0, rear_z - 0.8),
        (160.0, base_z - 0.8),
    ]
    left = create_axis_y_prism(
        "CAMERA_BUTTRESS_LEFT",
        xz_outline,
        35.0,
        46.0,
    )
    right = create_axis_y_prism(
        "CAMERA_BUTTRESS_RIGHT",
        xz_outline,
        WIDTH - 46.0,
        WIDTH - 35.0,
    )
    return left, right


def create_tower_window_cutters():
    base_z = outer_surface_z(TOWER_FOOT_X, CENTER_Y) - 1.0
    rear_z = outer_surface_z(220.0, 38.0)
    front_window = [
        (159.0, base_z + 8.0),
        (173.5, base_z + 58.0),
        (187.0, base_z + 58.0),
        (174.0, base_z + 12.0),
    ]
    rear_window = [
        (190.0, base_z + 51.0),
        (210.0, rear_z + 13.0),
        (216.0, rear_z + 8.0),
        (200.0, base_z + 47.0),
    ]
    cutters = []
    for side_name, y_min, y_max in (
        ("LEFT", 32.0, 49.0),
        ("RIGHT", WIDTH - 49.0, WIDTH - 32.0),
    ):
        cutters.append(
            create_axis_y_prism(
                f"TOWER_FRONT_SIDE_WINDOW_{side_name}",
                front_window,
                y_min,
                y_max,
            )
        )
        cutters.append(
            create_axis_y_prism(
                f"TOWER_REAR_SIDE_WINDOW_{side_name}",
                rear_window,
                y_min,
                y_max,
            )
        )
    return cutters


def join_objects(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    return joined


def boolean_apply(target, operand, operation, name):
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new(name=name, type="BOOLEAN")
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = operand
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(operand, do_unlink=True)


def print_stage(label, obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = (
        min(corner.x for corner in corners),
        min(corner.y for corner in corners),
        min(corner.z for corner in corners),
    )
    maximum = (
        max(corner.x for corner in corners),
        max(corner.y for corner in corners),
        max(corner.z for corner in corners),
    )
    print(
        "STAGE",
        label,
        "verts",
        len(obj.data.vertices),
        "bbox",
        tuple(round(value, 3) for value in minimum),
        tuple(round(value, 3) for value in maximum),
    )


def clean_mesh(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.validate(verbose=False)
    obj.data.update()


def mesh_components(bm):
    unseen = set(bm.faces)
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            face = stack.pop()
            for edge in face.edges:
                for linked_face in edge.link_faces:
                    if linked_face in unseen:
                        unseen.remove(linked_face)
                        stack.append(linked_face)
    return components


def mesh_metrics(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    boundary = sum(1 for edge in bm.edges if edge.is_boundary)
    zero_area = sum(1 for face in bm.faces if face.calc_area() < 1e-8)
    components = mesh_components(bm)
    volume = abs(bm.calc_volume(signed=True))
    bm.free()

    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector(
        (
            min(corner.x for corner in corners),
            min(corner.y for corner in corners),
            min(corner.z for corner in corners),
        )
    )
    maximum = Vector(
        (
            max(corner.x for corner in corners),
            max(corner.y for corner in corners),
            max(corner.z for corner in corners),
        )
    )
    dimensions = maximum - minimum
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "polygons": len(obj.data.polygons),
        "non_manifold_edges": non_manifold,
        "boundary_edges": boundary,
        "connected_face_components": components,
        "zero_area_faces": zero_area,
        "volume_mm3": round(volume, 3),
        "bbox_min_mm": [round(value, 4) for value in minimum],
        "bbox_max_mm": [round(value, 4) for value in maximum],
        "dimensions_mm": [round(value, 4) for value in dimensions],
    }


def export_manifold_obj(obj, filepath):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
    if TRIANGULATE_OBJ:
        bmesh.ops.triangulate(
            bm,
            faces=list(bm.faces),
            quad_method="BEAUTY",
            ngon_method="BEAUTY",
        )
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()

    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"# {MODEL_NAME}\n")
        handle.write("# Units: millimetres\n")
        handle.write("# +X rearward, +Y vehicle-right, +Z upward\n")
        handle.write(f"o {OBJ_OBJECT_NAME}\n")
        for vertex in bm.verts:
            handle.write(
                f"v {vertex.co.x:.6f} {vertex.co.y:.6f} {vertex.co.z:.6f}\n"
            )
        for face in bm.faces:
            indices = [loop.vert.index + 1 for loop in face.loops]
            handle.write("f " + " ".join(str(index) for index in indices) + "\n")
    bm.free()


def make_material():
    material = bpy.data.materials.new("PETG_Graphite")
    material.diffuse_color = (0.025, 0.045, 0.07, 1.0)
    return material


def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_render_scene(cover):
    cover.data.materials.append(make_material())
    cover.color = (0.08, 0.13, 0.19, 1.0)

    bpy.ops.mesh.primitive_plane_add(
        size=1000.0,
        location=(LENGTH / 2.0, CENTER_Y, 0.0),
    )
    floor = bpy.context.active_object
    floor.name = "RENDER_FLOOR"
    floor.color = (0.008, 0.013, 0.022, 1.0)

    bpy.ops.object.camera_add(location=(-180.0, -250.0, 285.0))
    camera = bpy.context.active_object
    camera.name = "RENDER_CAMERA"
    camera.data.lens = 58.0
    point_at(camera, (125.0, CENTER_Y, 52.0))
    bpy.context.scene.camera = camera


def create_m3_hole_cutter(name, x, y):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=HOLE_RADIUS,
        depth=220.0,
        location=(x, y, 70.0),
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def build():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clear_scene()
    configure_scene()
    cover = create_angular_shell()
    print_stage("shell", cover)

    # True side openings and honeycomb fields create the design's lattice
    # rather than merely drawing dark decorative panels.
    boolean_apply(
        cover,
        create_side_window_cutter(),
        "DIFFERENCE",
        "Cut_Side_Lattice_Windows",
    )
    print_stage("side_windows", cover)
    boolean_apply(
        cover,
        create_hex_field_cutter(),
        "DIFFERENCE",
        "Cut_Honeycomb_Fields",
    )
    print_stage("honeycomb", cover)

    oled_cutter = create_rounded_xy_prism(
        "OLED_19x36_CLEARANCE",
        OLED_CENTER,
        OLED_OPENING,
        radius=OLED_CORNER_RADIUS,
    )
    boolean_apply(cover, oled_cutter, "DIFFERENCE", "Cut_OLED_Clearance")
    print_stage("oled", cover)

    camera_roof_cutter = create_rounded_xy_prism(
        "CAMERA_ROOF_29x78_CLEARANCE",
        CAMERA_ROOF_CENTER,
        CAMERA_ROOF_OPENING,
        radius=CAMERA_CORNER_RADIUS,
    )
    boolean_apply(
        cover,
        camera_roof_cutter,
        "DIFFERENCE",
        "Cut_Camera_Roof_Clearance",
    )
    print_stage("camera_roof", cover)

    bosses = [
        create_flat_mount_boss(
            f"MOUNT_BOSS_{index + 1}",
            x,
            y,
            contact_z,
        )
        for index, (x, y, contact_z) in enumerate(MOUNT_CENTERS)
    ]
    boolean_apply(
        cover,
        join_objects(bosses, "ALL_MOUNT_BOSSES"),
        "UNION",
        "Union_Flat_Mount_Bosses",
    )
    print_stage("bosses", cover)

    rail_objects = create_rail_and_brace_objects()
    # Apply overlapping lattice pieces one at a time. Joining them before the
    # Boolean produces a self-intersecting operand that Blender 5.2 can
    # misinterpret as the complete union and discard the underlying shell.
    for index, rail_object in enumerate(rail_objects, start=1):
        boolean_apply(
            cover,
            rail_object,
            "UNION",
            f"Union_Rail_Or_Brace_{index:02d}",
        )
        print_stage(f"rail_{index:02d}", cover)
    print_stage("rails", cover)

    boolean_apply(
        cover,
        create_conforming_bezel_ring(),
        "UNION",
        "Union_OLED_Bezel",
    )
    print_stage("bezel", cover)

    boolean_apply(
        cover,
        create_camera_arch(),
        "UNION",
        "Union_Forward_Camera_Arch",
    )
    print_stage("arch", cover)

    tower_side_plates = list(create_tower_side_plates())
    if tower_side_plates:
        boolean_apply(
            cover,
            join_objects(
                tower_side_plates,
                "BOTH_CAMERA_BUTTRESSES",
            ),
            "UNION",
            "Union_Camera_Buttresses",
        )
    print_stage("buttresses", cover)

    tower_window_cutters = create_tower_window_cutters()
    # Apply disconnected tower apertures independently. Joining them into one
    # Boolean operand can make Exact Boolean interpret the complement as the
    # cutter and delete nearly the entire shell.
    for index, tower_window_cutter in enumerate(
        tower_window_cutters,
        start=1,
    ):
        boolean_apply(
            cover,
            tower_window_cutter,
            "DIFFERENCE",
            f"Cut_Tower_Side_Window_{index:02d}",
        )
    print_stage("tower_windows", cover)

    # Re-establish the two functional openings after every additive styling
    # operation. Rails, bezels, arches, or buttresses must never partially
    # refill the approved OLED and camera footprints. The camera re-cut is
    # deliberately limited to the deck/module volume so the elevated arch
    # can still bridge over it.
    if RECUT_OLED:
        oled_final_cutter = create_rounded_xy_prism(
            "OLED_FINAL_19x36_CLEARANCE",
            OLED_CENTER,
            (
                OLED_OPENING[0] + FINAL_RECUT_OVERSIZE,
                OLED_OPENING[1] + FINAL_RECUT_OVERSIZE,
            ),
            radius=OLED_CORNER_RADIUS + FINAL_RECUT_OVERSIZE / 2.0,
        )
        boolean_apply(
            cover,
            oled_final_cutter,
            "DIFFERENCE",
            "ReCut_Exact_OLED_Clearance",
        )
    print_stage("oled_final", cover)

    if RECUT_CAMERA:
        camera_final_cutter = create_rounded_xy_prism(
            "CAMERA_FINAL_29x78_CLEARANCE",
            CAMERA_ROOF_CENTER,
            (
                CAMERA_ROOF_OPENING[0] + FINAL_RECUT_OVERSIZE,
                CAMERA_ROOF_OPENING[1] + FINAL_RECUT_OVERSIZE,
            ),
            radius=CAMERA_CORNER_RADIUS + FINAL_RECUT_OVERSIZE / 2.0,
            z_min=-20.0,
            z_max=100.0,
        )
        boolean_apply(
            cover,
            camera_final_cutter,
            "DIFFERENCE",
            "ReCut_Exact_Camera_Deck_Clearance",
        )
    print_stage("camera_final", cover)

    m3_cutters = [
        create_m3_hole_cutter(f"M3_HOLE_{index + 1}", x, y)
        for index, (x, y, _contact_z) in enumerate(MOUNT_CENTERS)
    ]
    boolean_apply(
        cover,
        join_objects(m3_cutters, "ALL_M3_CLEARANCE_CUTTERS"),
        "DIFFERENCE",
        "Cut_Four_M3_Clearances",
    )
    print_stage("m3", cover)

    clean_mesh(cover)
    cover["units"] = "millimetres"
    cover["coordinate_system"] = (
        "Origin at front-left outer bounding box; "
        "+X rearward; +Y vehicle-right; +Z upward"
    )
    cover["material_recommendation"] = "PETG"
    cover["shell_thickness_mm"] = SHELL_THICKNESS
    cover["mount_pad_total_thickness_mm"] = PAD_TOTAL_THICKNESS
    cover["camera_roof_clearance_mm"] = CAMERA_ROOF_OPENING
    cover["camera_visible_arch_opening_yz_mm"] = TOWER_VISIBLE_OPENING
    cover["oled_clearance_xy_mm"] = OLED_OPENING

    metrics = mesh_metrics(cover)
    report = {
        "model": MODEL_NAME,
        "units": "mm",
        "coordinate_system": {
            "origin": "front-left outer bounding-box corner",
            "x_positive": "rear",
            "y_positive": "vehicle right",
            "z_positive": "up",
        },
        "overall_plan_mm": [LENGTH, WIDTH],
        "nominal_roof_incline_degrees": round(
            math.degrees(
                math.atan(
                    (REAR_CONTACT_Z - FRONT_CONTACT_Z)
                    / (REAR_X - FRONT_X)
                )
            ),
            4,
        ),
        "mounts": [
            {
                "center_xy_mm": [x, y],
                "flat_contact_z_mm": contact_z,
                "hole_diameter_mm": HOLE_DIAMETER,
                "pad_total_thickness_mm": PAD_TOTAL_THICKNESS,
            }
            for x, y, contact_z in MOUNT_CENTERS
        ],
        "oled": {
            "center_xy_mm": list(OLED_CENTER),
            "opening_xy_mm": list(OLED_OPENING),
            "bezel_outer_xy_mm": list(OLED_BEZEL_OUTER),
        },
        "camera": {
            "roof_module_clearance_center_xy_mm": list(CAMERA_ROOF_CENTER),
            "roof_module_clearance_xy_mm": list(CAMERA_ROOF_OPENING),
            "visible_forward_arch_opening_yz_mm": list(
                TOWER_VISIBLE_OPENING
            ),
            "tower_height_above_local_deck_mm": TOWER_HEIGHT,
        },
        "shell_thickness_mm": SHELL_THICKNESS,
        "mesh": metrics,
        "print_notes": [
            "OBJ coordinates are millimetres.",
            "PETG recommended.",
            "Print the cover bottom-down with supports beneath the tower bridge.",
            "Use 4 or more perimeters around the lattice and camera tower.",
            "Run a low-cost fit check before the final print.",
        ],
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    export_manifold_obj(cover, OBJ_PATH)
    add_render_scene(cover)
    bpy.context.scene.render.filepath = PREVIEW_PATH
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.render.render(write_still=True)

    camera = bpy.data.objects.get("RENDER_CAMERA")
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 300.0
    camera.location = (LENGTH / 2.0, CENTER_Y, 470.0)
    point_at(camera, (LENGTH / 2.0, CENTER_Y, 35.0))
    bpy.context.scene.render.filepath = TOP_PREVIEW_PATH
    bpy.ops.render.render(write_still=True)

    print("TOKIMI_ANGULAR_RESULT=" + json.dumps(report, separators=(",", ":")))
    print(f"TOKIMI_ANGULAR_OBJ={OBJ_PATH}")
    print(f"TOKIMI_ANGULAR_BLEND={BLEND_PATH}")
    print(f"TOKIMI_ANGULAR_PREVIEW={PREVIEW_PATH}")
    print(f"TOKIMI_ANGULAR_TOP={TOP_PREVIEW_PATH}")
    print(f"TOKIMI_ANGULAR_REPORT={REPORT_PATH}")


if __name__ == "__main__":
    build()

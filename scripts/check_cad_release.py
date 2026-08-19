#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate the committed Tokimi Rover top-cover release without dependencies."""

from __future__ import annotations

import hashlib
import json
import math
import posixpath
import re
import stat
import struct
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAD_ROOT = PROJECT_ROOT / "hardware" / "cad" / "top-cover-v3"
STEM = "tokimi_rover_top_cover_supercar_v3_195x100mm"
PDF_NAME = "tokimi_rover_top_cover_supercar_v3_m3_fitcheck_195x100mm_A4_1to1.pdf"

THREE_MF = CAD_ROOT / "exports" / f"{STEM}.3mf"
OBJ = CAD_ROOT / "exports" / f"{STEM}.obj"
STL = CAD_ROOT / "exports" / f"{STEM}.stl"
PDF = CAD_ROOT / "templates" / PDF_NAME
VALIDATION = CAD_ROOT / "validation" / f"{STEM}_validation.json"
MANIFEST = CAD_ROOT / "MANIFEST.sha256"

SOURCE_FILES = (
    "requirements.txt",
    "source/build_rover_top_cover_angular.py",
    "source/build_rover_top_cover_supercar.py",
    "source/build_rover_top_cover_supercar_v2.py",
    "source/build_rover_top_cover_supercar_v3.py",
    "source/mesh_guards.py",
    "tools/dump_clean_triangulation.py",
    "tools/generate_m3_fitcheck_pdf.py",
    "tools/npz_to_3mf.py",
    "checks/rover_cover_envelope.py",
    "checks/verify_cover_envelope_khana.py",
)

PREVIEW_FILES = tuple(
    f"previews/{STEM}_{suffix}.png"
    for suffix in (
        "front34",
        "preview",
        "rear34",
        "side",
        "top",
        "tower_detail",
    )
)

HARDWARE_ARTIFACTS = (
    f"editable/{STEM}.blend",
    f"exports/{STEM}.3mf",
    f"exports/{STEM}.obj",
    f"exports/{STEM}.stl",
    f"templates/{PDF_NAME}",
    f"validation/{STEM}_validation.json",
)

REQUIRED_FILES = (
    "README.md",
    "NOTICE.md",
    "MANIFEST.sha256",
    *SOURCE_FILES,
    *HARDWARE_ARTIFACTS,
    *PREVIEW_FILES,
    *(f"{name}.license" for name in HARDWARE_ARTIFACTS),
    *(f"{name}.license" for name in PREVIEW_FILES),
)

MANIFEST_ARTIFACTS = frozenset((*HARDWARE_ARTIFACTS, *PREVIEW_FILES))
TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".license",
    ".md",
    ".obj",
    ".py",
    ".sha256",
    ".svg",
    ".txt",
    ".yaml",
    ".yml",
}

EXPECTED_VERTICES = 28_734
EXPECTED_TRIANGLES = 57_760
EXPECTED_POLYGON_EDGES = 53_780
EXPECTED_POLYGONS = 24_900
EXPECTED_PLAN = (260.0, 155.0)
EXPECTED_HEIGHT = 162.9501
EXPECTED_MOUNT_SPAN = (195.0, 100.0)
EXPECTED_HOLE_DIAMETER = 3.5
EXPECTED_MODEL_NAME = "TOKIMI_ROVER_TOP_COVER_SUPERCAR_V3"
COORDINATE_TOLERANCE = 1e-3


class CadCheckError(RuntimeError):
    """A release invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CadCheckError(message)


def close(actual: float, wanted: float, tolerance: float = COORDINATE_TOLERANCE) -> bool:
    return math.isclose(actual, wanted, rel_tol=0.0, abs_tol=tolerance)


def finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def require_pair(actual: object, wanted: tuple[float, float], label: str) -> None:
    require(isinstance(actual, list) and len(actual) == 2, f"{label} must be a two-item list")
    require(
        all(finite_number(value) for value in actual),
        f"{label} must contain finite numbers",
    )
    require(
        close(float(actual[0]), wanted[0]) and close(float(actual[1]), wanted[1]),
        f"{label} is {actual}, expected {list(wanted)}",
    )


def check_required_files() -> None:
    missing = [name for name in REQUIRED_FILES if not (CAD_ROOT / name).is_file()]
    require(not missing, "missing CAD release file(s):\n  " + "\n  ".join(missing))

    for relative in SOURCE_FILES:
        text = (CAD_ROOT / relative).read_text(encoding="utf-8")
        require(
            "SPDX-FileCopyrightText:" in text,
            f"missing SPDX copyright notice: {relative}",
        )
        require(
            "SPDX-License-Identifier: CERN-OHL-W-2.0" in text,
            f"wrong or missing CERN-OHL-W-2.0 notice: {relative}",
        )

    for relative in HARDWARE_ARTIFACTS:
        check_sidecar(relative, "CERN-OHL-W-2.0")
    for relative in PREVIEW_FILES:
        check_sidecar(relative, "CERN-OHL-W-2.0")

    notices = {
        "README.md": "CC-BY-4.0",
        "NOTICE.md": "CC-BY-4.0",
        "MANIFEST.sha256": "CERN-OHL-W-2.0",
    }
    for relative, expected_license in notices.items():
        text = (CAD_ROOT / relative).read_text(encoding="utf-8")
        require(
            f"SPDX-License-Identifier: {expected_license}" in text,
            f"wrong or missing {expected_license} notice: {relative}",
        )


def check_sidecar(relative: str, expected_license: str) -> None:
    sidecar = CAD_ROOT / f"{relative}.license"
    text = sidecar.read_text(encoding="utf-8")
    require("SPDX-FileCopyrightText:" in text, f"missing copyright in {sidecar.relative_to(PROJECT_ROOT)}")
    require(
        f"SPDX-License-Identifier: {expected_license}" in text,
        f"{sidecar.relative_to(PROJECT_ROOT)} must declare {expected_license}",
    )


def tracked_cad_files() -> set[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "hardware/cad"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return set()

    files: set[Path] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            relative = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CadCheckError("git reported a non-UTF-8 path under hardware/cad") from exc
        candidate = PROJECT_ROOT / relative
        if candidate.is_file():
            files.add(candidate)
    return files


def check_no_local_paths() -> None:
    candidates = tracked_cad_files()
    candidates.update(
        CAD_ROOT / relative
        for relative in REQUIRED_FILES
        if Path(relative).suffix.lower() in TEXT_SUFFIXES
    )

    failures: list[str] = []
    for path in sorted(candidates):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise CadCheckError(f"cannot read {path.relative_to(PROJECT_ROOT)}: {exc}") from exc
        for marker in (b"/Users/", b"/Volumes/"):
            if marker in data:
                failures.append(f"{path.relative_to(PROJECT_ROOT)} contains {marker.decode()}")

    require(not failures, "local absolute path(s) found:\n  " + "\n  ".join(failures))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_manifest_path(raw_name: str) -> tuple[str, Path]:
    name = raw_name.strip()
    if name.startswith("*"):
        name = name[1:]
    require(name != "", "manifest contains an empty path")
    require("\\" not in name and "\0" not in name, f"unsafe manifest path: {raw_name!r}")

    pure = PurePosixPath(name)
    require(not pure.is_absolute(), f"absolute manifest path: {name}")
    require(".." not in pure.parts, f"manifest path traversal: {name}")

    repo_prefix = PurePosixPath("hardware/cad/top-cover-v3")
    if pure.parts[: len(repo_prefix.parts)] == repo_prefix.parts:
        pure = PurePosixPath(*pure.parts[len(repo_prefix.parts) :])
    require(pure.parts, f"manifest path does not name a file: {name}")

    canonical = pure.as_posix()
    candidate = CAD_ROOT.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise CadCheckError(f"manifest file does not exist: {canonical}") from exc
    try:
        resolved.relative_to(CAD_ROOT.resolve())
    except ValueError as exc:
        raise CadCheckError(f"manifest path escapes CAD root: {name}") from exc
    require(resolved.is_file() and not candidate.is_symlink(), f"manifest path is not a regular file: {canonical}")
    return canonical, resolved


def check_manifest() -> None:
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([0-9A-Fa-f]{64})[ \t]+(.+)", line)
        require(match is not None, f"invalid MANIFEST.sha256 line {line_number}")
        wanted = match.group(1).lower()
        canonical, path = canonical_manifest_path(match.group(2))
        require(canonical != "MANIFEST.sha256", "MANIFEST.sha256 must not hash itself")
        require(canonical not in entries, f"duplicate manifest entry: {canonical}")
        actual = sha256_file(path)
        require(actual == wanted, f"SHA-256 mismatch for {canonical}: {actual}, expected {wanted}")
        entries[canonical] = wanted

    missing = sorted(MANIFEST_ARTIFACTS.difference(entries))
    require(not missing, "manifest omits release artifact(s):\n  " + "\n  ".join(missing))


def check_validation_json() -> None:
    try:
        report = json.loads(VALIDATION.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CadCheckError(f"cannot parse validation JSON: {exc}") from exc
    require(isinstance(report, dict), "validation JSON root must be an object")
    require(report.get("units") == "mm", "validation JSON units must be mm")
    require_pair(report.get("overall_plan_mm"), EXPECTED_PLAN, "overall_plan_mm")

    mounts = report.get("mounts")
    require(isinstance(mounts, list) and len(mounts) == 4, "validation JSON must contain four mounts")
    centers: list[tuple[float, float]] = []
    for index, mount in enumerate(mounts):
        require(isinstance(mount, dict), f"mount {index} must be an object")
        center = mount.get("center_xy_mm")
        require(isinstance(center, list) and len(center) == 2, f"mount {index} center must have x/y")
        require(
            all(finite_number(value) for value in center),
            f"mount {index} center must be finite",
        )
        centers.append((float(center[0]), float(center[1])))
        diameter = mount.get("hole_diameter_mm")
        require(
            finite_number(diameter) and close(float(diameter), EXPECTED_HOLE_DIAMETER),
            f"mount {index} hole diameter must be {EXPECTED_HOLE_DIAMETER} mm",
        )

    xs = sorted({center[0] for center in centers})
    ys = sorted({center[1] for center in centers})
    require(len(xs) == 2 and len(ys) == 2, "mount centers must form a two-by-two pattern")
    require(
        close(xs[1] - xs[0], EXPECTED_MOUNT_SPAN[0])
        and close(ys[1] - ys[0], EXPECTED_MOUNT_SPAN[1]),
        f"mount spans are {(xs[1] - xs[0], ys[1] - ys[0])}, expected {EXPECTED_MOUNT_SPAN}",
    )
    require(set(centers) == {(x, y) for x in xs for y in ys}, "mount centers must contain all four corners")

    mesh = report.get("mesh")
    require(isinstance(mesh, dict), "validation JSON mesh must be an object")
    exact_counters = {
        "vertices": EXPECTED_VERTICES,
        "edges": EXPECTED_POLYGON_EDGES,
        "polygons": EXPECTED_POLYGONS,
        "non_manifold_edges": 0,
        "boundary_edges": 0,
        "connected_face_components": 1,
        "zero_area_faces": 0,
    }
    for key, wanted in exact_counters.items():
        actual = mesh.get(key)
        require(
            type(actual) is int and actual == wanted,
            f"validation mesh.{key} is {actual!r}, expected integer {wanted}",
        )
    require_pair(mesh.get("dimensions_mm")[:2] if isinstance(mesh.get("dimensions_mm"), list) else None, EXPECTED_PLAN, "mesh dimensions plan")
    dimensions = mesh.get("dimensions_mm")
    require(isinstance(dimensions, list) and len(dimensions) == 3, "mesh dimensions_mm must have three values")
    require(
        finite_number(dimensions[2]) and close(float(dimensions[2]), EXPECTED_HEIGHT),
        f"mesh height is {dimensions[2]!r}, expected {EXPECTED_HEIGHT}",
    )

    bbox_min = mesh.get("bbox_min_mm")
    bbox_max = mesh.get("bbox_max_mm")
    require(
        isinstance(bbox_min, list)
        and isinstance(bbox_max, list)
        and len(bbox_min) == len(bbox_max) == 3
        and all(finite_number(value) for value in (*bbox_min, *bbox_max)),
        "validation mesh bounding box must contain finite three-dimensional coordinates",
    )
    require(close(float(bbox_min[0]), 0.0) and close(float(bbox_min[1]), 0.0), "validation bbox plan must start at 0,0")
    require(close(float(bbox_max[0]), 260.0) and close(float(bbox_max[1]), 155.0), "validation bbox plan must end at 260,155")
    require(close(float(bbox_max[2]) - float(bbox_min[2]), EXPECTED_HEIGHT), "validation bbox height is unexpected")


def safe_zip_member(name: str) -> None:
    require(name != "" and "\0" not in name and "\\" not in name, f"unsafe 3MF member name: {name!r}")
    pure = PurePosixPath(name)
    require(not pure.is_absolute(), f"absolute 3MF member path: {name}")
    require(".." not in pure.parts, f"3MF member path traversal: {name}")
    require(not (pure.parts and re.fullmatch(r"[A-Za-z]:", pure.parts[0])), f"drive-qualified 3MF path: {name}")
    require(pure.as_posix() == name, f"non-canonical 3MF member path: {name}")


def parse_safe_xml(data: bytes, label: str) -> ElementTree.Element:
    require(len(data) <= 64 * 1024 * 1024, f"oversized XML part: {label}")
    lowered = data.lower()
    require(b"<!doctype" not in lowered and b"<!entity" not in lowered, f"DTD/entity is forbidden in {label}")
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise CadCheckError(f"invalid XML in {label}: {exc}") from exc


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def relationship_source(member: str) -> str:
    if member == "_rels/.rels":
        return ""
    marker = "/_rels/"
    require(marker in member and member.endswith(".rels"), f"invalid relationship part name: {member}")
    prefix, filename = member.rsplit(marker, 1)
    source_name = filename[: -len(".rels")]
    return f"{prefix}/{source_name}"


def internal_package_target(source: str, target: str) -> str:
    require("\\" not in target and "\0" not in target, f"unsafe 3MF relationship target: {target!r}")
    split = urlsplit(target)
    require(not split.scheme and not split.netloc, f"external 3MF relationship target: {target}")
    require(not split.query and not split.fragment, f"query/fragment is forbidden in 3MF target: {target}")
    decoded_path = unquote(split.path)
    require("\\" not in decoded_path and "\0" not in decoded_path, f"unsafe encoded 3MF target: {target!r}")
    target_parts = PurePosixPath(decoded_path.lstrip("/")).parts
    require(".." not in target_parts, f"3MF relationship path traversal: {target}")
    if decoded_path.startswith("/"):
        combined = decoded_path.lstrip("/")
    else:
        combined = posixpath.join(posixpath.dirname(source), decoded_path)
    normalized = posixpath.normpath(combined)
    safe_zip_member(normalized)
    return normalized


def check_relationships(archive: zipfile.ZipFile, members: set[str]) -> None:
    for member in sorted(name for name in members if name.endswith(".rels")):
        root = parse_safe_xml(archive.read(member), member)
        source = relationship_source(member)
        for relationship in root.iter():
            if local_name(relationship.tag) != "Relationship":
                continue
            mode = relationship.attrib.get("TargetMode", "Internal")
            require(mode.strip().lower() != "external", f"external relationship is forbidden in {member}")
            target = relationship.attrib.get("Target")
            require(target is not None, f"relationship without Target in {member}")
            resolved = internal_package_target(source, target)
            require(resolved in members, f"3MF relationship target is missing: {resolved}")


def vector_cross(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> tuple[float, float, float]:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )


def check_indexed_topology(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    label: str,
) -> None:
    edge_counts: Counter[tuple[int, int]] = Counter()
    directed_counts: Counter[tuple[int, int]] = Counter()
    used_vertices: set[int] = set()
    for triangle_number, triangle in enumerate(triangles):
        require(len(set(triangle)) == 3, f"{label} triangle {triangle_number} repeats a vertex index")
        require(all(0 <= index < len(vertices) for index in triangle), f"{label} triangle {triangle_number} has an invalid index")
        a, b, c = (vertices[index] for index in triangle)
        cross = vector_cross(a, b, c)
        require(sum(value * value for value in cross) > 1e-18, f"{label} triangle {triangle_number} is degenerate")
        used_vertices.update(triangle)
        for start, end in ((triangle[0], triangle[1]), (triangle[1], triangle[2]), (triangle[2], triangle[0])):
            edge_counts[(min(start, end), max(start, end))] += 1
            directed_counts[(start, end)] += 1

    bad_pairing = [edge for edge, count in edge_counts.items() if count != 2]
    require(not bad_pairing, f"{label} has {len(bad_pairing)} edge(s) not shared exactly twice")
    bad_orientation = [
        edge
        for edge in edge_counts
        if directed_counts[(edge[0], edge[1])] != 1 or directed_counts[(edge[1], edge[0])] != 1
    ]
    require(not bad_orientation, f"{label} has {len(bad_orientation)} inconsistently oriented edge(s)")
    require(len(used_vertices) == len(vertices), f"{label} has {len(vertices) - len(used_vertices)} unused vertex/vertices")


def require_expected_bbox(vertices: list[tuple[float, float, float]], label: str) -> None:
    require(vertices, f"{label} has no vertices")
    mins = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
    maxs = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))
    require(close(mins[0], 0.0) and close(mins[1], 0.0), f"{label} bbox minimum is {mins}")
    require(close(maxs[0], 260.0) and close(maxs[1], 155.0), f"{label} bbox maximum is {maxs}")
    require(close(maxs[2] - mins[2], EXPECTED_HEIGHT), f"{label} height is {maxs[2] - mins[2]}")


def check_3mf() -> None:
    try:
        archive = zipfile.ZipFile(THREE_MF)
    except (OSError, zipfile.BadZipFile) as exc:
        raise CadCheckError(f"cannot open 3MF: {exc}") from exc

    with archive:
        infos = archive.infolist()
        require(0 < len(infos) <= 128, f"unexpected 3MF member count: {len(infos)}")
        members: set[str] = set()
        total_size = 0
        for info in infos:
            safe_zip_member(info.filename)
            require(info.filename not in members, f"duplicate 3MF member: {info.filename}")
            members.add(info.filename)
            require(not info.is_dir(), f"directory entry is forbidden in 3MF: {info.filename}")
            require(not (info.flag_bits & 0x1), f"encrypted 3MF member: {info.filename}")
            require(
                info.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
                f"unsupported 3MF compression method: {info.filename}",
            )
            file_type = (info.external_attr >> 16) & 0o170000
            require(file_type != stat.S_IFLNK, f"symlink is forbidden in 3MF: {info.filename}")
            require(info.file_size <= 64 * 1024 * 1024, f"oversized 3MF member: {info.filename}")
            if info.file_size and info.compress_size:
                require(info.file_size / info.compress_size <= 1_000, f"suspicious 3MF compression ratio: {info.filename}")
            total_size += info.file_size
        require(total_size <= 128 * 1024 * 1024, "3MF uncompressed size exceeds 128 MiB")
        require("3D/3dmodel.model" in members, "3MF is missing 3D/3dmodel.model")
        require("[Content_Types].xml" in members and "_rels/.rels" in members, "3MF package metadata is incomplete")

        check_relationships(archive, members)
        content_types = parse_safe_xml(archive.read("[Content_Types].xml"), "[Content_Types].xml")
        require(local_name(content_types.tag) == "Types", "3MF content-types root is not <Types>")
        model_data = archive.read("3D/3dmodel.model")
        model = parse_safe_xml(model_data, "3D/3dmodel.model")
        require(local_name(model.tag) == "model", "3MF model root is not <model>")
        require(model.attrib.get("unit") == "millimeter", "3MF model unit must be millimeter")

        for element in model.iter():
            for attribute, value in element.attrib.items():
                if local_name(attribute).lower() not in {"href", "path", "src"}:
                    continue
                resolved = internal_package_target("3D/3dmodel.model", value)
                require(resolved in members, f"3MF references a missing package part: {resolved}")

        objects = [element for element in model.iter() if local_name(element.tag) == "object"]
        require(len(objects) == 1, f"3MF must contain one object, found {len(objects)}")
        object_id = objects[0].attrib.get("id")
        require(object_id is not None, "3MF object is missing its id")
        require(
            objects[0].attrib.get("name") == EXPECTED_MODEL_NAME,
            f"3MF object name must be {EXPECTED_MODEL_NAME}",
        )
        require(
            not any(local_name(element.tag) == "components" for element in model.iter()),
            "3MF component assemblies are not permitted in this single-mesh release",
        )
        build_items = [element for element in model.iter() if local_name(element.tag) == "item"]
        require(len(build_items) == 1, f"3MF build must contain one item, found {len(build_items)}")
        require(build_items[0].attrib.get("objectid") == object_id, "3MF build item does not reference its mesh object")

        meshes = [element for element in model.iter() if local_name(element.tag) == "mesh"]
        require(len(meshes) == 1, f"3MF must contain one mesh, found {len(meshes)}")
        mesh = meshes[0]

        vertices: list[tuple[float, float, float]] = []
        for vertex in (element for element in mesh.iter() if local_name(element.tag) == "vertex"):
            try:
                point = tuple(float(vertex.attrib[axis]) for axis in ("x", "y", "z"))
            except (KeyError, TypeError, ValueError) as exc:
                raise CadCheckError("3MF contains an invalid vertex") from exc
            require(all(math.isfinite(value) for value in point), "3MF contains a non-finite vertex")
            vertices.append(point)  # type: ignore[arg-type]

        triangles: list[tuple[int, int, int]] = []
        for triangle in (element for element in mesh.iter() if local_name(element.tag) == "triangle"):
            try:
                indices = tuple(int(triangle.attrib[key], 10) for key in ("v1", "v2", "v3"))
            except (KeyError, TypeError, ValueError) as exc:
                raise CadCheckError("3MF contains an invalid triangle") from exc
            triangles.append(indices)  # type: ignore[arg-type]

        require(len(vertices) == EXPECTED_VERTICES, f"3MF vertex count is {len(vertices)}, expected {EXPECTED_VERTICES}")
        require(len(triangles) == EXPECTED_TRIANGLES, f"3MF triangle count is {len(triangles)}, expected {EXPECTED_TRIANGLES}")
        require_expected_bbox(vertices, "3MF")
        check_indexed_topology(vertices, triangles, "3MF")


def check_stl() -> None:
    data = STL.read_bytes()
    require(len(data) >= 84, "STL is too short to be a binary STL")
    expected_header = b"TOKIMI SUPERCAR V3 clean triangulation"
    require(data[: len(expected_header)] == expected_header, "unexpected binary STL header")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    require(triangle_count == EXPECTED_TRIANGLES, f"STL triangle count is {triangle_count}, expected {EXPECTED_TRIANGLES}")
    require(len(data) == 84 + triangle_count * 50, "binary STL length does not match its triangle count")

    vertices_by_value: dict[tuple[float, float, float], int] = {}
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for triangle_number, record in enumerate(struct.iter_unpack("<12fH", data[84:])):
        normal = tuple(float(value) for value in record[0:3])
        points = tuple(
            tuple(float(value) for value in record[offset : offset + 3])
            for offset in (3, 6, 9)
        )
        require(
            all(math.isfinite(value) for value in (*normal, *points[0], *points[1], *points[2])),
            f"STL triangle {triangle_number} contains a non-finite value",
        )
        require(len(set(points)) == 3, f"STL triangle {triangle_number} repeats a vertex")
        cross = vector_cross(points[0], points[1], points[2])
        cross_length_squared = sum(value * value for value in cross)
        require(cross_length_squared > 1e-18, f"STL triangle {triangle_number} is degenerate")
        normal_length_squared = sum(value * value for value in normal)
        require(normal_length_squared > 1e-18, f"STL triangle {triangle_number} has a zero normal")
        require(sum(normal[axis] * cross[axis] for axis in range(3)) > 0.0, f"STL triangle {triangle_number} normal is reversed")
        require(record[12] == 0, f"STL triangle {triangle_number} has an unexpected attribute byte count")

        indices: list[int] = []
        for point in points:
            index = vertices_by_value.get(point)
            if index is None:
                index = len(vertices)
                vertices_by_value[point] = index
                vertices.append(point)
            indices.append(index)
        triangles.append((indices[0], indices[1], indices[2]))

    require(len(vertices) == EXPECTED_VERTICES, f"STL unique vertex count is {len(vertices)}, expected {EXPECTED_VERTICES}")
    require_expected_bbox(vertices, "STL")
    check_indexed_topology(vertices, triangles, "STL")


def check_obj() -> None:
    vertices: list[tuple[float, float, float]] = []
    face_count = 0
    object_names: list[str] = []
    units_notice = False

    for line_number, raw_line in enumerate(OBJ.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if line == "# Units: millimetres":
            units_notice = True
        elif line.startswith("o "):
            object_names.append(line[2:].strip())
        elif line.startswith("v "):
            fields = line.split()
            require(len(fields) == 4, f"OBJ vertex on line {line_number} must have x/y/z")
            try:
                point = tuple(float(value) for value in fields[1:])
            except ValueError as exc:
                raise CadCheckError(f"OBJ contains an invalid vertex on line {line_number}") from exc
            require(all(math.isfinite(value) for value in point), f"OBJ has a non-finite vertex on line {line_number}")
            vertices.append(point)  # type: ignore[arg-type]
        elif line.startswith("f "):
            fields = line.split()[1:]
            require(len(fields) >= 3, f"OBJ face on line {line_number} has fewer than three vertices")
            try:
                indices = [int(field.split("/", 1)[0], 10) for field in fields]
            except ValueError as exc:
                raise CadCheckError(f"OBJ contains an invalid face on line {line_number}") from exc
            require(len(set(indices)) == len(indices), f"OBJ face on line {line_number} repeats a vertex")
            require(all(1 <= index <= len(vertices) for index in indices), f"OBJ face on line {line_number} has an invalid index")
            face_count += 1

    require(units_notice, "OBJ must declare millimetre coordinates")
    require(object_names == [EXPECTED_MODEL_NAME], f"OBJ object name is {object_names!r}, expected {EXPECTED_MODEL_NAME}")
    require(len(vertices) == EXPECTED_VERTICES, f"OBJ vertex count is {len(vertices)}, expected {EXPECTED_VERTICES}")
    require(face_count == EXPECTED_POLYGONS, f"OBJ face count is {face_count}, expected {EXPECTED_POLYGONS}")
    require_expected_bbox(vertices, "OBJ")


def check_pdf() -> None:
    data = PDF.read_bytes()
    require(data.startswith(b"%PDF-1."), "fit-check file is not a PDF 1.x document")
    require(b"%%EOF" in data[-1024:], "fit-check PDF has no trailing %%EOF marker")
    pages = len(re.findall(rb"/Type\s*/Page\b", data))
    require(pages == 1, f"fit-check PDF must contain one page marker, found {pages}")
    require(b"/Encrypt" not in data, "fit-check PDF must not be encrypted")
    require(b"/JavaScript" not in data and b"/JS" not in data, "fit-check PDF must not contain JavaScript")


def main() -> int:
    checks = (
        check_required_files,
        check_no_local_paths,
        check_manifest,
        check_validation_json,
        check_3mf,
        check_obj,
        check_stl,
        check_pdf,
    )
    try:
        for check in checks:
            check()
    except (CadCheckError, OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"CAD release check failed: {exc}", file=sys.stderr)
        return 1

    print("CAD release check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

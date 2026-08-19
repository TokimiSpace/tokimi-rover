"""TOKIMI ROVER top-cover mechanical envelope — build123d / cad-khana.

B-rep source of truth for the locked interface geometry. Styling
(supercar surfacing) stays in the Blender pipeline; this file owns the
mechanical contract and verifies it with assembly-level assertions.

Coordinate frame (matches the Blender pipeline):
    origin = front-left outer bounding-box corner at floor datum
    +X     = rearward
    +Y     = vehicle right
    +Z     = up
    z=0    = chassis floor datum (standoff bases)

Locked dimensions (must match docs and the printed cover):
    260 x 155 plan, M3 centers 195 x 100, 3.5 mm holes,
    front/rear contact planes z = 15 / 55, 2.5 mm shell,
    4.0 mm pad stack, OLED 19 x 36 @ (102, 77.5),
    camera clearance 29 x 78 @ (205, 77.5).
"""

# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

from pathlib import Path

from build123d import Box, Cylinder, Plane, Polyline, Pos, extrude, make_face
from build123d.topology import Part

from cad_khana.mechanism.assembly import Assembly
from cad_khana.mechanism.check import check
from cad_khana.printability.inspect import inspect
from cad_khana.printability.methods import FDM

# ---------------------------------------------------------------------------
# 1. Parameters + derived
# ---------------------------------------------------------------------------
LENGTH = 260.0
WIDTH = 155.0
SHELL_T = 2.5

FRONT_X = 32.5
REAR_X = 227.5
LEFT_Y = 27.5
RIGHT_Y = 127.5
FRONT_CONTACT_Z = 15.0
REAR_CONTACT_Z = 55.0

HOLE_D = 3.5
PAD_R = 8.0
PAD_T = 4.0
FLAT_R = 9.0  # flat contact-plane clamp radius around each mount

OLED_CENTER = (102.0, WIDTH / 2.0)
OLED_XY = (19.0, 36.0)
CAM_CENTER = (205.0, WIDTH / 2.0)
CAM_XY = (29.0, 78.0)

STANDOFF_D = 6.0  # chassis-side M3 standoff stand-in (bought part)

MOUNTS = (
    ("front_left", FRONT_X, LEFT_Y, FRONT_CONTACT_Z),
    ("front_right", FRONT_X, RIGHT_Y, FRONT_CONTACT_Z),
    ("rear_left", REAR_X, LEFT_Y, REAR_CONTACT_Z),
    ("rear_right", REAR_X, RIGHT_Y, REAR_CONTACT_Z),
)

CHECKS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CHECKS_DIR.parent / "generated" / "envelope"


def roof_z(x: float) -> float:
    """Underside of the inclined roof plate (contact-plane datum line)."""
    slope = (REAR_CONTACT_Z - FRONT_CONTACT_Z) / (REAR_X - FRONT_X)
    return FRONT_CONTACT_Z + (x - FRONT_X) * slope


# ---------------------------------------------------------------------------
# 2. Pure part functions
# ---------------------------------------------------------------------------
def cover_envelope() -> Part:
    """Inclined roof plate + pad stacks, minus M3 / OLED / camera openings."""
    profile_pts = [
        (0.0, roof_z(0.0)),
        (LENGTH, roof_z(LENGTH)),
        (LENGTH, roof_z(LENGTH) + SHELL_T),
        (0.0, roof_z(0.0) + SHELL_T),
    ]
    face = make_face(Plane.XZ * Polyline(*profile_pts, close=True))
    plate = extrude(face, amount=WIDTH, dir=(0, 1, 0))

    # Flat contact regions: within FLAT_R of each mount the shell is clamped
    # to the contact plane (mirrors inner_surface_z's mount clamp in the
    # Blender pipeline). Without this the sloped underside dips below the
    # contact plane on the forward side of each standoff.
    part = plate
    for _name, mx, my, contact_z in MOUNTS:
        part = part - Pos(mx, my, 0) * Cylinder(FLAT_R, 400.0)
        part = part + Pos(mx, my, contact_z + SHELL_T / 2.0) * Cylinder(
            FLAT_R, SHELL_T
        )
        pad = Pos(mx, my, contact_z + PAD_T / 2.0) * Cylinder(PAD_R, PAD_T)
        part = part + pad
    for _name, mx, my, _contact_z in MOUNTS:
        part = part - Pos(mx, my, 0) * Cylinder(HOLE_D / 2.0, 300.0)
    part = part - Pos(*OLED_CENTER, 40.0) * Box(*OLED_XY, 160.0)
    part = part - Pos(*CAM_CENTER, 40.0) * Box(*CAM_XY, 160.0)
    return part


def standoff(height: float, d: float = STANDOFF_D) -> Part:
    """Chassis-side standoff stand-in: base at z=0, top at contact plane."""
    return Pos(0, 0, height / 2.0) * Cylinder(d / 2.0, height)


# ---------------------------------------------------------------------------
# 3. Assembly + mechanism assertions
# ---------------------------------------------------------------------------
assembly = Assembly().with_part("cover", cover_envelope())
for name, mx, my, contact_z in MOUNTS:
    assembly = assembly.with_part(
        f"standoff_{name}",
        standoff(contact_z),
        location=Pos(mx, my, 0),
    )
for name, _mx, _my, _contact_z in MOUNTS:
    # Standoff tops are meant to TOUCH the contact planes: tangent contact
    # is zero-volume, so no_interference (not clearance) is the right check.
    assembly = assembly.assert_no_interference("cover", f"standoff_{name}")

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    check(assembly, out=str(OUTPUT_DIR))
    # This diagnostic intentionally uses 89 degrees so a 90-degree region is
    # reported as support-required. It is not a support-free printability
    # claim; wall thickness remains the independent material gate.
    inspect(
        cover_envelope(),
        method=FDM(wall_min_mm=1.5, overhang_max_deg=89.0),
        out=str(OUTPUT_DIR),
        name="cover_envelope",
    )

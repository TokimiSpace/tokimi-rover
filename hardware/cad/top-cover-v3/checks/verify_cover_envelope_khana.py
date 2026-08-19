"""Verify a printed-cover STL against the mechanical envelope with cad-khana.

Off-label but deliberate: khana normally checks B-rep assemblies, here the
Blender-produced tessellated STL is imported as a Solid and probed with
go/no-go gauge parts, so the *actual print geometry* is what gets checked:

  standoffs   (no_interference)  cover never dips below the contact planes
  washers     (assert_interference, +/-0.05 mm) contact faces sit ON them
  clear pins  ⌀3.4 (no_interference)  every M3 hole passes a clearance pin
  fat pin     ⌀3.6 (assert_interference)  a hole must reject the oversize pin
  OLED/camera go blocks (no_interference)  openings pass an undersize block
  OLED/camera no-go blocks (assert_interference)  and reject an oversize one

For supercar_v3, three extra gauges cover the V3 features: a raked
58x85x10 breadboard block through the tower pocket, a 12.4x6.5 USB-C
plug block through the pass-through slot (both no_interference), and a
tail plate at z 28-42 that the 30 mm dropped tail must hit
(assert_interference) — the undropped V2 tail sits ~25 mm above it.

The public release defaults to ``supercar_v3``. Override the input path with
``TOKIMI_CAD_STL`` when checking a newly generated export.
Run: khana check checks/verify_cover_envelope_khana.py
"""

# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

import os
from pathlib import Path

from build123d import Box, Cylinder, Mesher, Pos, Rot, Solid

from cad_khana.mechanism.assembly import Assembly
from cad_khana.mechanism.check import check

COVER = os.environ.get("COVER", "supercar_v3")
PROJECT_DIR = Path(__file__).resolve().parents[1]
STL = os.environ.get(
    "TOKIMI_CAD_STL",
    str(PROJECT_DIR / "exports" / f"tokimi_rover_top_cover_{COVER}_195x100mm.stl"),
)
OUT = str(PROJECT_DIR / "generated" / f"verify_{COVER}")

# Locked envelope (must match docs and the cad/ envelope model)
MOUNTS = (
    ("front_left", 32.5, 27.5, 15.0),
    ("front_right", 32.5, 127.5, 15.0),
    ("rear_left", 227.5, 27.5, 55.0),
    ("rear_right", 227.5, 127.5, 55.0),
)
HOLE_D = 3.5
PIN_GO_D = 3.4
PIN_NOGO_D = 3.6
CONTACT_TOL = 0.05  # washer half-thickness: contact face must sit within this

OLED_CENTER = (102.0, 77.5)
OLED_XY = (19.0, 36.0)
OLED_CORNER_R = 2.5
CAM_CENTER = (205.0, 77.5)
CAM_XY = (29.0, 78.0)
CAM_CORNER_R = 4.5  # supercar's radius (larger of the two variants)

# Go blocks are inset by 2 * corner radius + 0.2 so rounded corners clear;
# no-go blocks are oversize by 0.2 in each dimension.
OLED_GO = (OLED_XY[0] - 2 * OLED_CORNER_R - 0.2, OLED_XY[1] - 2 * OLED_CORNER_R - 0.2)
OLED_NOGO = (OLED_XY[0] + 0.2, OLED_XY[1] + 0.2)
CAM_GO = (CAM_XY[0] - 2 * CAM_CORNER_R - 0.2, CAM_XY[1] - 2 * CAM_CORNER_R - 0.2)
CAM_NOGO = (CAM_XY[0] + 0.2, CAM_XY[1] + 0.2)

shapes = Mesher().read(STL)
cover = shapes[0]
if not isinstance(cover, Solid):
    cover = Solid(cover)

assembly = Assembly().with_part("cover", cover)

for name, mx, my, cz in MOUNTS:
    assembly = (
        assembly
        .with_part(f"standoff_{name}", Cylinder(3.0, cz), location=Pos(mx, my, cz / 2))
        .with_part(
            f"washer_{name}",
            Cylinder(6.0, 2 * CONTACT_TOL),
            location=Pos(mx, my, cz),
        )
        .with_part(
            f"pin_go_{name}",
            Cylinder(PIN_GO_D / 2, 14.0),
            location=Pos(mx, my, cz + 2.0),
        )
        .assert_no_interference("cover", f"standoff_{name}")
        .assert_interference(
            "cover",
            f"washer_{name}",
            reason=(
                f"contact-plane tangency probe: pad face must sit within "
                f"+/-{CONTACT_TOL} mm of z={cz}"
            ),
        )
        .assert_no_interference("cover", f"pin_go_{name}")
    )

# One oversize pin: any hole must reject it (front_left chosen).
assembly = (
    assembly
    .with_part(
        "pin_nogo_front_left",
        Cylinder(PIN_NOGO_D / 2, 14.0),
        location=Pos(32.5, 27.5, 17.0),
    )
    .assert_interference(
        "cover",
        "pin_nogo_front_left",
        reason=f"M3 hole must be smaller than {PIN_NOGO_D} mm",
    )
)

# Openings: go block passes free, no-go block hits the surround.
assembly = (
    assembly
    .with_part("oled_go", Box(*OLED_GO, 60.0), location=Pos(*OLED_CENTER, 60.0))
    .with_part("oled_nogo", Box(*OLED_NOGO, 60.0), location=Pos(*OLED_CENTER, 60.0))
    .with_part("cam_go", Box(*CAM_GO, 40.0), location=Pos(*CAM_CENTER, 65.0))
    .with_part("cam_nogo", Box(*CAM_NOGO, 40.0), location=Pos(*CAM_CENTER, 65.0))
    .assert_no_interference("cover", "oled_go")
    .assert_interference(
        "cover", "oled_nogo", reason="OLED opening must not exceed 19.2x36.2"
    )
    .assert_no_interference("cover", "cam_go")
    .assert_interference(
        "cover", "cam_nogo", reason="camera opening must not exceed 29.2x78.2"
    )
)

# --- V3-only gauges: breadboard pocket, USB-C pass-through, tail drop ---
if COVER == "supercar_v3":
    # Tower frame constants from the V3 validation report:
    # base_z 75.164, foot x 151, rake 0.44 (tilt 23.7495 deg from vertical).
    TOWER_RAKE_DEG = 23.7495
    assembly = (
        assembly
        .with_part(
            "breadboard_gauge",
            Rot(0, TOWER_RAKE_DEG, 0) * Box(10.0, 58.0, 85.0),
            location=Pos(177.15, 77.5, 120.18),
        )
        .assert_no_interference("cover", "breadboard_gauge")
        .with_part(
            "usb_c_gauge",
            Box(6.5, 12.4, 45.0),
            location=Pos(155.0, 77.5, 60.0),
        )
        .assert_no_interference("cover", "usb_c_gauge")
        .with_part(
            "tail_drop_plate",
            Box(7.0, 25.0, 14.0),
            location=Pos(255.5, 77.5, 35.0),
        )
        .assert_interference(
            "cover",
            "tail_drop_plate",
            reason=(
                "30 mm tail drop must bring the rear overhang down into "
                "z 28-42 at x 252-259; the undropped tail sits ~25 mm higher"
            ),
        )
    )

if __name__ == "__main__":
    check(assembly, out=OUT)

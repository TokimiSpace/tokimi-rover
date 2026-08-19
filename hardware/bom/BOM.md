<!--
SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
SPDX-License-Identifier: CERN-OHL-W-2.0
-->

# V0.1 bill of materials

This is a consolidated prototype BOM, not a purchasing specification. Quantities
marked `reported` come from the as-built handoff; exact manufacturer part
numbers and ratings remain required before a reproducible release.

| Subsystem | Item | Qty | Status / missing detail |
|---|---|---:|---|
| Control | ESP32-S3 N16R8 development board | 1 | Reported installed; exact board SKU required |
| Camera | GOOUUU ESP32-S3-CAM V1.5 | 1 | Reported installed |
| Camera | OV3660 sensor | 1 | Reported installed |
| Drive | TB6612FNG breakout | 1 | Reported installed; known thermal shutdown limitation |
| Drive | TT DC gear motor, reported 3–7.2 V | 4 | Exact ratio, vendor, and current required |
| Chassis | Two-layer acrylic 4WD chassis | 1 | Reported installed |
| Display | 1.3-inch SH1106 128×64 I²C OLED | 1 | Reported installed |
| Lighting | WS2812 front strip | 8 pixels | Reported installed |
| Lighting | WS2812 center ring | 16 pixels | Reported installed |
| Lighting | WS2812 rear strip | 8 pixels | Reported installed |
| Power | LM2596 adjustable buck converter | 1 | Verify 5.00 V under load |
| Power | 2S 18650 pack | 1 | Cell model, capacity, rating, matching, and BMS unknown |
| Power | USB power bank | 1 | Exact model/capacity unknown |
| Protection | 1.8 A / 30 V resettable PTC | 1 | Installed position must be verified |
| Lighting | 1000 µF / 16 V electrolytic capacitor | 1 | Across LED 5 V/GND |
| Lighting | 330 Ω, 1/4 W data resistor | 1 | GPIO4 to first pixel DIN |
| Cooling | 5 V fan | 1+ | Exact model and airflow unknown |
| RF | 2.4 GHz U.FL/IPEX FPC antenna | 1 | Physically attached; active RF path unknown |
| Enclosure | Custom curved top cover | 1 | CAD, material, mass, and print settings pending |

See [HARDWARE_AS_BUILT.md](../../HARDWARE_AS_BUILT.md) for the evidence labels
and [KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) before substituting components.

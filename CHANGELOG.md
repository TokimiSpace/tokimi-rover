# Changelog

All notable project changes will be recorded here.

## Unreleased

### Added

- Combined rover-controller and camera-node PlatformIO projects.
- Code-confirmed implementation, pin-map, API, build, safety, and provenance documentation.
- GitHub contribution, security, issue, pull-request, and firmware-build scaffolding.
- Public configuration examples with local credential files excluded from version control.
- Official Apache-2.0, CERN-OHL-W-2.0, and CC-BY-4.0 license texts with an
  explicit path-level scope map and diagram SPDX sidecars.
- CC-BY-4.0 conceptual hero artwork and a source-audited dual-controller
  architecture diagram for the project overview.
- Documentation links to the separately maintained bilingual
  [Tokimi Open Source](https://tokimispace.github.io/) organization page.
- Owner-selected Supercar V3 procedural/editable top-cover source, 3MF/STL/OBJ
  exports, A4 1:1 fit-check template, clean renders, validation data, checksums,
  and a repository CAD integrity checker.

### Changed

- Repository layout aligned with the documented two-controller architecture.
- Public documentation reconciled with the 2026-08-19 read-only audit.
- Rover Espressif32 and library versions are pinned, and its declared maximum
  application size now matches the selected 0x640000 partition slot.
- Camera firmware now uses a repository-owned 16 MB partition table with two
  0x640000 application slots.
- The owner-approved multi-license structure is active; Tokimi trademarks
  remain outside the open-source license grants.

### Known limitations

- V0.1 motor-stop ordering, watchdog latency, direction reversal, and 80% PWM cap require safety work.
- Camera runtime health and restart authorization require hardening.
- Physical power, thermal, antenna, endurance, and battery measurements remain incomplete.
- Published V3 uses 195 × 100 mm mounting centers while the historical physical
  record says approximately 203 × 105 mm; physical reconciliation remains open.

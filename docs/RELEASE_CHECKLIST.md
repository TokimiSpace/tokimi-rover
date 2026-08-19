# V0.1 Release Checklist

> This checklist separates repository packaging from physical validation. A checked documentation item does not certify the assembled rover.

## Audit and public documentation

- [x] Read-only implementation audit completed against both supplied source archives.
- [x] `docs/CURRENT_IMPLEMENTATION.md` records code-confirmed behavior and non-features.
- [x] `docs/CURRENT_PINMAP.md` records both controllers' GPIO assignments.
- [x] `docs/CURRENT_API.md` records exact routes, values, responses, and limitations.
- [x] `docs/BUILD_AND_FLASH.md` provides one canonical build/upload procedure.
- [x] `docs/SAFETY.md` makes drive, battery, power, and STOP limitations prominent.
- [x] `docs/ARCHIVE_PROVENANCE.md` records supplied archive hashes and traceability limits.
- [x] Root README is English-first and links to a zh-TW README.
- [x] Tokimi Open Source site source is separated from the Rover repository.
- [x] Project context, as-built hardware, known issues, roadmap, and agent rules reconciled with the audit.
- [x] Local Markdown link checker passes on the packaged tree.
- [ ] Perform final link and Markdown rendering review on the release commit.

## Source and reproducibility

- [x] Rover dependencies and Espressif32 platform are version-pinned.
- [x] Camera Espressif32 platform is version-pinned.
- [x] Camera uses an explicit 16 MB partition table rather than silently leaving half the nominal flash outside the partition map.
- [x] Real Wi-Fi credentials are removed from tracked source and replaced by ignored local configuration plus safe tracked examples.
- [x] Both firmware projects build successfully from isolated copies of the packaged tree; results are recorded in `docs/BUILD_AND_FLASH.md`.
- [ ] Run a fresh clean build of both firmware projects from the final release commit and attach/log the results.
- [ ] Add automated tests for motor-state transitions, input validation, stop latching/order, watchdog behavior, and API compatibility.
- [ ] Record a test command/result other than the current `TestDirNotExistsError`.
- [ ] Record compiler/platform/library versions in a release manifest.
- [ ] Generate SHA-256 hashes for release artifacts from the tagged commit.
- [ ] Generate third-party license notices or an SBOM for the exact dependency set before distributing firmware binaries.
- [x] The packaged source tree contains no `.pio/`, local configuration, or generated firmware binary.
- [x] Confirm no `.pio/`, local configuration, credentials, private IP assumptions, or private media are staged.

## Safety-critical software

- [ ] Prevent an older in-flight movement request from superseding STOP.
- [ ] Define and implement a hard worst-case motor-stop deadline independent of synchronous HTTP/display/lighting work.
- [ ] Measure and document worst-case stop latency under slow, repeated, malformed, and disconnected-client cases.
- [ ] Implement and test enforced direction-change dead time.
- [ ] Implement and test soft start/ramping, or explicitly approve its omission based on measurements.
- [ ] Replace the current 80% cap with a measured safe envelope; historical 50–60% guidance is not currently enforced.
- [ ] Decide and document whether malformed lighting/expression requests should also stop motion.
- [ ] Add an authenticated control design, or explicitly accept AP-password-only prototype exposure for V0.1.

## Camera software

- [ ] Clear/degrade camera health after repeated runtime capture failures and retry initialization safely.
- [ ] Make `/status.sensor` truthful when the sensor is offline.
- [ ] Implement or remove the ignored snapshot timeout parameter.
- [ ] Protect or remove unauthenticated, side-effecting `GET /restart`.
- [ ] Define snapshot/stream behavior for the one-buffer DRAM fallback.
- [ ] Verify final partition table, flash use, PSRAM reporting, and upload behavior on the actual board.

## Physical hardware and build assets

- [ ] Identify exact 18650 cells, capacity, discharge rating, age, matching, and BMS/protection.
- [ ] Resolve the documented 3–7.2 V motor rating versus up-to-8.4 V 2S supply conflict.
- [ ] Record idle, start, straight, pivot, and peak/stall current using a reviewed safe procedure.
- [ ] Record TB6612 and battery temperature versus run time and ambient temperature.
- [ ] Select/validate a motor driver with adequate continuous and peak margin.
- [ ] Verify LM2596 output unloaded and under accessory load.
- [ ] Photograph and document fuse placement, wire gauges, grounds, polarity, strain relief, and connectors.
- [ ] Remove breadboard/high-current friction connections from the drive path.
- [ ] Verify external camera antenna selection and repeatable range/RSSI.
- [ ] Record final rover mass, payload, top-cover material, print settings, and fit; reconcile the historical 203 × 105 mm record with V3's 195 × 100 mm pattern.
- [ ] Publish a verified BOM with exact part numbers.
- [ ] Publish reviewed wiring diagrams for every power and signal path.
- [x] Publish owner-selected procedural/editable V3 source and software-checked 3MF/STL/OBJ exports; no GLB or final parametric STEP is claimed.
- [x] Publish the A4 1:1 V3 mounting template with a 100 mm calibration line.
- [ ] Physically verify the printed template scale and all four V3 hole centers against the current unpowered chassis.

## Physical acceptance tests

- [ ] Boot with wheels clear and confirm both motor channels and STBY remain stopped.
- [ ] Verify every movement command and physical motor polarity at conservative duty.
- [ ] Verify STOP on release, explicit STOP, page hide/close, AP station loss, watchdog threshold, invalid command, invalid speed, and unknown route.
- [ ] Verify lighting boot diagnostic, zones, current draw, and voltage drop.
- [ ] Verify OLED initialization, expressions, motion faces, and graceful missing-display behavior.
- [ ] Verify camera initialization, capture, single stream, failure paths, recovery, and restart.
- [ ] Run a defined endurance test without thermal shutdown only after current/temperature instrumentation is installed.
- [ ] Document test date, operators, hardware revision, firmware commit, environment, results, and failures.

## Governance and publication

- [x] Owner approved and activated Apache-2.0 software, CERN-OHL-W-2.0 hardware-source, and CC-BY-4.0 documentation licenses; see `LICENSES.md`.
- [x] Trademark/logo boundaries and factual-use/attribution exceptions are documented in `TRADEMARKS.md`.
- [x] Contribution and security policies plus issue and pull-request templates are present.
- [ ] Review personal/contact information intended for publication.
- [x] Create an initial Git commit history with a traceable repository origin.
- [x] Create and verify the canonical public `TokimiSpace/tokimi-rover` remote.
- [x] Verify the separately published `https://tokimispace.github.io/` site and its Rover links.
- [ ] Create and sign/annotate the V0.1 tag as appropriate.
- [ ] Attach build artifacts, hashes, build logs, and test report to the release.
- [ ] Publish field photos/video only with rights and privacy review.

## Release decision

Repository documentation is ready for review, but V0.1 remains a **prototype release candidate**, not a hardware-certified release. The STOP race, non-hard watchdog deadline, motor-driver thermal history, battery uncertainty, and motor-voltage mismatch are explicit release-owner decisions and must not be hidden by checking unrelated packaging tasks.

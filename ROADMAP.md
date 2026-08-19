# Tokimi Rover — Roadmap

> Roadmap items are plans, not current features. Public materials must distinguish implemented, experimental, and proposed work.

> Audit status: reconciled with repository source on 2026-08-19. Documentation checkmarks below mean the named files exist; they do not imply physical hardware validation.

## Release philosophy

- **V0.1:** publish the working prototype honestly.
- **V0.2:** solve reliability and measurement first.
- **V0.3:** extend communication range and field operability.
- **V0.4+:** add sensing and autonomy only after the drive base is trustworthy.

---

## V0.1 — Open-source prototype release

### Goal

Make the current rover reproducible and useful as a reference platform.

### Deliverables

- [x] Codex read-only implementation audit
- [x] code-confirmed GPIO map — `docs/CURRENT_PINMAP.md`
- [x] code-confirmed API documentation — `docs/CURRENT_API.md`
- [x] build/flash guide for rover controller — `docs/BUILD_AND_FLASH.md`
- [x] build/flash guide for camera node — `docs/BUILD_AND_FLASH.md`
- [ ] current BOM with verified part numbers
- [ ] wiring diagrams for power, motor driver, OLED, camera, and lighting
- [ ] editable top-cover source plus STL/GLB/OBJ exports
- [ ] 1:1 mounting-hole template
- [x] known-issues page with TB6612 thermal shutdown highlighted
- [ ] field-demo photos and short video
- [ ] first tagged release
- [x] contribution guide and issue templates
- [x] trademark statement and final license selection
- [x] English-first README and zh-TW README
- [x] Tokimi Open Source site source separated into its dedicated publication repository
- [x] live organization site verified at `https://tokimispace.github.io/`
- [x] safety guide and release checklist
- [x] supplied-archive provenance/hashes documented

### Exit criteria

- another builder can build firmware and understand the wiring;
- every public feature is either code-confirmed or explicitly labeled;
- safety limitations are visible from the README;
- no credentials or private network settings are committed.

Documentation now meets the first three explanatory goals, deployment credentials have been moved to ignored local configuration, and the approved multi-license structure is active. Physical reproduction assets, physical safety validation, and a tagged release remain open; see `docs/RELEASE_CHECKLIST.md`.

---

## V0.2 — Reliability and instrumentation

### Priority 0: deterministic stop semantics

- [ ] prevent an older in-flight movement request from superseding STOP
- [ ] add explicit command sequencing and/or a latched stop state
- [ ] move the motor safety deadline outside synchronous HTTP/display/lighting scheduling
- [ ] define and measure a worst-case stop deadline under slow and malformed traffic
- [ ] test page release/hide/close, station loss, heartbeat loss, unknown routes, and invalid input
- [ ] define authentication requirements for motor commands

### Priority 1: motor subsystem

- [ ] measure one-motor and two-motor-per-channel current
- [ ] record idle, cruise, acceleration, pivot-turn, and stall current
- [ ] select a driver with adequate continuous and peak current margin
- [ ] replace TB6612 or redesign drive distribution
- [ ] validate thermal performance for at least 30 minutes
- [ ] add soft start and enforced direction-change dead time
- [ ] establish a measured safe PWM envelope

Candidate directions to evaluate, not preselect:

- dual-channel 3 A+ driver;
- two higher-current single-channel H-bridges;
- integrated driver with current limiting and fault reporting.

### Priority 2: sensing and safety

- [ ] INA219/INA226 or suitable current/voltage sensing
- [ ] motor-driver temperature sensing
- [ ] battery temperature sensing
- [ ] low-voltage cutoff behavior
- [ ] over-current/stall detection
- [ ] thermal derating and thermal stop
- [ ] audible fault indication
- [ ] structured fault log
- [ ] make OLED camera state truthful or remove it until transport exists
- [ ] add camera runtime health transitions and initialization recovery
- [ ] protect/remove unauthenticated camera restart

### Priority 3: electrical construction

- [ ] eliminate breadboard from high-current paths
- [ ] design a small power-distribution / controller PCB
- [ ] add locking connectors and strain relief
- [ ] document wire gauge and fuse placement
- [ ] verify LM2596 output under load
- [ ] add logic-level buffer for WS2812 if required
- [ ] document grounding and cable routing

### Exit criteria

- no thermal shutdown during the defined endurance test;
- measured current and temperature are logged;
- rover fails safe under disconnect, stall, and low-voltage scenarios;
- moving-platform wiring survives vibration testing.
- STOP cannot be superseded by an older command and its worst-case deadline is measured.

---

## V0.3 — Long-range control and field communications

### Proposed architecture

```text
Phone web UI
    │ Wi-Fi / BLE
    ▼
ESP32 gateway controller
    │ UART
    ▼
LoRa module
    )))))) long-range control link ((((((
LoRa module
    │ UART
    ▼
Rover ESP32-S3
    │
    └── Motor / safety controller

Separate Wi-Fi camera link remains optional.
```

### Work items

- [ ] verify legally appropriate radio frequency and module configuration
- [ ] evaluate AS32-TTL-100 or alternative module
- [ ] define compact command protocol with sequence numbers and checksum
- [ ] implement command acknowledgement and latency reporting
- [ ] implement hard failsafe on lost LoRa heartbeat
- [ ] preserve browser UI through Wi-Fi-to-LoRa gateway
- [ ] add link status to OLED
- [ ] conduct open-field range tests
- [ ] document antenna placement and RF safety

### Exit criteria

- control remains fail-safe when packets are lost;
- measured range and latency are published;
- camera traffic cannot interfere with the primary control channel.

---

## V0.4 — Navigation and perception

Only begin after V0.2 drive reliability is complete.

- [ ] wheel encoders
- [ ] IMU
- [ ] compass where appropriate
- [ ] GPS for outdoor telemetry
- [ ] obstacle sensors
- [ ] camera snapshot and stream API cleanup
- [ ] computer-vision experiments on a separate compute node
- [ ] assisted driving
- [ ] waypoint navigation
- [ ] return-to-home experiments

Do not describe the rover as autonomous until these features are implemented and validated.

---

## V0.5 — Productization

- [ ] custom integrated PCB
- [ ] serviceable wiring harness
- [ ] production enclosure revision
- [ ] thermal and ingress testing
- [ ] repeatable assembly instructions
- [ ] official Tokimi Rover kit
- [ ] education/workshop edition
- [ ] sponsor/component partner edition
- [ ] fleet-management and telemetry backend evaluation

---

## Open-source and commercial program

### Community assets

- [ ] public issue tracker
- [ ] build gallery
- [ ] compatible-component list
- [ ] community enclosure variants
- [ ] translated documentation
- [x] initial zh-TW project README
- [ ] reproducible demo scenarios

### Commercial opportunities

- official assembled rover;
- hardware kits and custom PCB;
- paid integration and prototyping;
- robotics workshops;
- branded demonstration vehicles;
- component sponsorship and partner validation;
- custom camera, LoRa, sensing, and telemetry builds.

### Brand policy

The source may be open while **Tokimi**, its logo, and “Official Tokimi Rover” designation remain controlled trademarks. Third parties may build derivatives according to the selected licenses but may not imply official endorsement without permission.

---

## Immediate next actions

1. Prepare a tag-specific release manifest and CERN-OHL Source Location for the first tagged release.
2. Run clean builds from the final release commit and record versions, sizes, and hashes.
3. Fix and test STOP request ordering plus a hard worst-case stop deadline.
4. Identify the 18650 pack and resolve the 3–7.2 V motor versus 8.4 V supply conflict.
5. Photograph final wiring/enclosure and record current, temperature, weight, runtime, and stop-latency measurements.
6. Publish the V0.1 prototype only with the known issues and verification boundaries visible.

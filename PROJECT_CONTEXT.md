# Tokimi Rover — Project Context

> Document type: product and engineering context<br>
> Status: reconciled with the 2026-08-19 repository audit<br>
> Software source of truth: repository code plus `docs/CURRENT_*.md`<br>
> Hardware boundary: historical reports were not physically re-tested during the audit

## 1. Project summary

Tokimi Rover is an open-source modular rover prototype for browser teleoperation, independent live vision, embedded-systems education, and field-robotics experimentation. Software is licensed under Apache-2.0, identified hardware design source under CERN-OHL-W-2.0, and documentation/original diagrams under CC-BY-4.0; `LICENSES.md` defines the exact scope.

The project was developed rapidly with AI assistance:

- ChatGPT supported electronics learning, wiring and power reasoning, fault isolation, mechanical planning, documentation, and positioning.
- Codex supported firmware and Web-interface implementation and later reconciled the source into public-facing documentation.
- Physical assembly, wiring, earlier testing, field demonstration, and enclosure work were performed on the real rover by the project team.

The 2026-08-19 repository audit independently inspected and built the supplied source. It did not upload firmware or repeat physical tests.

## 2. Product positioning

Recommended public description:

> **Tokimi Rover is a modular ESP32-S3 rover prototype combining browser teleoperation, an independent camera node, addressable lighting, an animated OLED, and a customizable enclosure.**

Appropriate V0.1 contexts:

- robotics and browser-control demonstrations with explicit supervision;
- camera-rover and embedded-Web experimentation;
- embedded-systems education;
- component-integration discussion;
- a reference for future reliability, sensing, and communications work.

Do not position V0.1 as a production vehicle, safety-rated platform, autonomous robot, AI vision system, long-range rover, or verified four-motor reference design.

## 3. Current architecture

```text
Phone / browser
      │ rover-control Wi-Fi AP
      ▼
ESP32-S3 N16R8 — main rover controller
      ├── TB6612FNG, two motor channels
      ├── four TT gear motors, grouped by side
      ├── SH1106 OLED
      ├── 32-pixel WS2812 chain
      ├── motor command/watchdog state
      └── rover HTTP interface

Tablet / browser
      │ separate camera Wi-Fi AP
      ▼
GOOUUU ESP32-S3-CAM V1.5
      └── OV3660 snapshot/MJPEG/status Web service
```

`CODE-CONFIRMED`:

- There is no GPIO, UART, I²C, SPI, HTTP, or other application link between the two controllers.
- Camera processing or restart cannot directly execute motor code.
- The rover has no camera-health input and cannot display truthful live camera status without new transport.
- Two APs separate software roles and client workflows, but do not guarantee radio-frequency isolation.

The historical demonstration used a phone for the rover AP and a tablet for the camera AP.

## 4. Major design decisions

### 4.1 Separate rover and camera controllers

Camera capture and streaming were isolated from motor control to reduce direct resource coupling and keep camera resets out of the motor-controller process. This is a useful failure boundary, but it does not by itself make STOP timing deterministic.

### 4.2 Browser-based control

An embedded Web UI avoids a dedicated phone application. The page sends movement heartbeats every 250 ms while a control is held. The current unsequenced request model has a known STOP-ordering race, and the 750 ms firmware watchdog is not a hard deadline. These are V0.2 safety priorities, not hidden details.

### 4.3 Split power architecture

Historically reported topology:

- motor driver and motors from a 2S 18650 pack;
- rover and camera controllers from USB power bank power;
- LM2596-regulated 5 V accessory rail for WS2812 lighting and fan;
- common rover signal ground where required;
- camera electrically isolated when it communicates only through Wi-Fi.

The reported motor rating is 3–7.2 V while a full 2S pack can reach 8.4 V. That unresolved conflict must be addressed before the power architecture is treated as a reproducible recommendation.

### 4.4 Modular lighting

`CODE-CONFIRMED` chain layout:

- front: pixels 0–7;
- center: pixels 8–23;
- rear: pixels 24–31;
- GPIO4 data, WS2812B/GRB;
- raw FastLED brightness 40/255, approximately 15.7%.

Power is historically documented as parallel distribution; only data is daisy-chained.

### 4.5 Custom enclosure

The original two acrylic chassis plates were retained. A curved printed top cover was reported as built and fitted, with an OLED opening, camera area, lighting integration, ventilation, and M3 mounting to existing standoffs. Exact material, print settings, mass, and final fit measurements remain open.

### 4.6 Open technology and separate brand value

The intended strategy is to make technical work reusable while retaining separate value in:

- Tokimi name, logo, and official-product designation;
- assembled versions and kits;
- custom PCBs and integration;
- workshops, support, consulting, and field prototypes;
- component partnerships and reliability sponsorship.

The approved open-source licenses apply by material type while Tokimi brand rights remain separate; see `LICENSES.md` and `TRADEMARKS.md`.

## 5. Current code-confirmed behavior

### Rover controller

- Eight movement directions plus STOP.
- 20 kHz, 8-bit PWM, 80% physical ceiling, 30% default requested speed.
- Arc inside wheel at 40% of outside duty.
- Boot, explicit, selected malformed-input, station-loss, watchdog, and unknown-route stop paths.
- No soft start or enforced direction-change dead time.
- SH1106 animated face UI and timed expressions; dormant text dashboard has no caller.
- 32-pixel lighting boot diagnostic, default scene, and zone toggles.
- No authentication, TLS, status API, battery telemetry, OTA, LoRa, ROS, or autonomy.

### Camera node

- OV3660 PID validation.
- JPEG HVGA 480×320, quality 18, 20 MHz XCLK, 10 FPS target.
- Two PSRAM frame buffers with latest-frame mode, or one DRAM buffer fallback.
- One MJPEG stream, JPEG capture, JSON status, UI, and remote restart.
- Runtime online state can become stale; initialization is not retried; capture timeout argument is ignored.
- Browser-only contour overlay labelled `ROCKET`; not trained detection.
- No authentication or TLS.

Complete details are in [Current implementation](docs/CURRENT_IMPLEMENTATION.md), [Current API](docs/CURRENT_API.md), and [Current pin map](docs/CURRENT_PINMAP.md).

## 6. Historical demonstrated outcome

`HARDWARE-CONFIRMED` from prior project reporting:

- the rover was assembled and driven through its Wi-Fi interface;
- the OLED and camera subsystem were integrated;
- a custom top cover was printed;
- sustained four-motor use produced a failure consistent with TB6612 overload/thermal shutdown, followed by recovery after cooling.

`AUDIT-NOT-PHYSICALLY-RETESTED`:

- the repository audit did not reproduce any item above;
- it did not measure current, temperature, voltage, latency, RF range, stream performance, or endurance;
- successful firmware builds are not proof of the historical physical behavior.

## 7. Development principles

- Publish an honest prototype, not an implied finished product.
- Put safety limitations in the first-screen README and operating guide.
- Separate code-confirmed, build-confirmed, historically hardware-confirmed, and planned claims.
- Measure drive current and thermal behavior before adding payload or duty cycle.
- Prefer modular replacement of weak subsystems over cosmetic feature expansion.
- Preserve camera independence from motor STOP.
- Keep secrets out of tracked source and bind releases to real commits and hashes.

## 8. Repository structure

```text
tokimi-rover/
├── README.md
├── README.zh-TW.md
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── HARDWARE_AS_BUILT.md
├── KNOWN_ISSUES.md
├── ROADMAP.md
├── firmware/
│   ├── rover-controller/
│   └── camera-node/
├── hardware/
├── docs/
│   ├── CURRENT_IMPLEMENTATION.md
│   ├── CURRENT_PINMAP.md
│   ├── CURRENT_API.md
│   ├── BUILD_AND_FLASH.md
│   ├── SAFETY.md
│   ├── RELEASE_CHECKLIST.md
│   └── ARCHIVE_PROVENANCE.md
└── scripts/
    ├── check_markdown_links.py
    └── check_repository.sh
```

## 9. V0.1 release goals

A public prototype release should let another builder understand:

1. what the current code does and does not do;
2. both controllers' exact pins and routes;
3. how to build and flash without committing credentials;
4. the historically reported power and mechanical construction;
5. the TB6612, STOP, battery, and motor-voltage risks;
6. which claims have build evidence and which still need physical validation;
7. that a tagged release still requires a tag, artifact hashes, and a release manifest tied to an exact commit.

See [Release checklist](docs/RELEASE_CHECKLIST.md) for remaining work.

## 10. Non-goals and prohibited implications for V0.1

Do not imply:

- autonomous navigation or assisted driving;
- AI/trained object detection;
- production-grade drive, thermal, battery, or emergency-stop protection;
- waterproofing or ingress certification;
- kilometer-scale control or LoRa support;
- accurate battery percentage;
- a measured 750 ms maximum stop time;
- verified external-antenna selection;
- regulatory, radio, or safety certification;

## 11. Collaboration and contact

Potential future collaboration includes motor-driver replacement, current/temperature sensing, custom electronics, education builds, enclosure refinement, field prototypes, and—only after drive reliability—communications and perception experiments.

Tokimi / 時見數位科技<br>
`ben@tokimi.space`

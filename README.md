![Tokimi Rover — audited dual-controller ESP32-S3 prototype](media/tokimi-rover-hero.svg)

# Tokimi Rover

A dual-controller ESP32-S3 rover prototype with browser teleoperation, an independent OV3660 camera node, animated OLED faces, and 32-pixel addressable lighting.

[繁體中文](README.zh-TW.md) · [Build & flash](docs/BUILD_AND_FLASH.md) · [API](docs/CURRENT_API.md) · [Pin map](docs/CURRENT_PINMAP.md) · [Safety](docs/SAFETY.md)

![Status: audited prototype](https://img.shields.io/badge/status-audited_prototype-f59e0b?style=flat-square)
![Controllers: 2 × ESP32-S3](https://img.shields.io/badge/controllers-2_%C3%97_ESP32--S3-0ea5e9?style=flat-square)
![Build: PlatformIO confirmed](https://img.shields.io/badge/build-PlatformIO_confirmed-22c55e?style=flat-square)
![License: multi-license](https://img.shields.io/badge/license-multi--license-8b5cf6?style=flat-square)

> [!WARNING]
> **This is a supervised prototype, not a production or safety-certified vehicle.** Lift every driven wheel before first power-on or after firmware changes, and keep a physical motor-power disconnect within reach. The TB6612FNG has a reported overload/thermal-shutdown history; the firmware uses an 80% PWM ceiling but has no current/temperature sensing, soft start, or enforced direction-change dead time.
>
> The browser control also has a known STOP request-ordering race. Its 750 ms watchdog is a main-loop threshold—not a guaranteed maximum stopping time. A fully charged 2S pack can reach 8.4 V while the reported motors are rated to 7.2 V. Read [Safety](docs/SAFETY.md) and [Known issues](KNOWN_ISSUES.md) before powering the drive system.

## At a glance

| | Rover controller | Camera node |
|---|---|---|
| **Board** | ESP32-S3 N16R8 development board | GOOUUU ESP32-S3-CAM V1.5 |
| **Job** | Drive, browser controls, OLED, WS2812 | OV3660 snapshot, MJPEG stream, diagnostics |
| **Network** | Dedicated Wi-Fi AP and HTTP control UI | Separate Wi-Fi AP and HTTP camera UI |
| **Physical outputs** | TB6612FNG, SH1106, 32 × WS2812 | OV3660 camera |
| **Build** | PlatformIO / Espressif32 7.0.1 | PlatformIO / Espressif32 6.12.0 |

### What works today

- Eight-direction browser teleoperation plus STOP.
- Boot STOP, selected invalid-command stops, station-loss stop, and watchdog threshold.
- One 480 × 320 JPEG snapshot endpoint and one MJPEG stream.
- Motion-responsive OLED eyes, timed expressions, SOS, and sleep animation.
- Front 8 + center 16 + rear 8 WS2812 zones.
- Clean isolated builds for both firmware projects.

### What is not being claimed

There is no battery, current, temperature, low-voltage, stall, encoder, IMU, GPS, obstacle, or LoRa sensing. There is no autonomous navigation or trained onboard vision; the camera page's `ROCKET` overlay is only a browser-side contour heuristic. See [Current implementation](docs/CURRENT_IMPLEMENTATION.md) for the complete code-confirmed boundary.

## Two-controller architecture

![Tokimi Rover dual-controller system architecture](docs/images/system-architecture.svg)

The camera controller and rover controller have no GPIO, UART, I²C, SPI, or application-level network link. Camera load or restart cannot directly execute motor code. Separate access points do not guarantee RF isolation, and the rover does not consume camera-health data.

## Firmware-verified rover wiring

[![Tokimi Rover V0.1 rover-controller wiring diagram](hardware/wiring/tokimi-rover-wiring.png)](hardware/wiring/tokimi-rover-wiring.svg)

*Click the diagram for the scalable SVG. It records the firmware-verified GPIO map and intended/reported rover wiring; the camera node is excluded. The assembled vehicle was not physically re-verified wire by wire during this repository audit.*

## Start here

| Step | Guide | Why it matters |
|---:|---|---|
| 1 | [Read the safety guide](docs/SAFETY.md) | Understand motor, battery, STOP, power, and first-boot precautions |
| 2 | [Review the current implementation](docs/CURRENT_IMPLEMENTATION.md) | Separate code-confirmed behavior from plans and historical reports |
| 3 | [Build and flash](docs/BUILD_AND_FLASH.md) | Create ignored local Wi-Fi configuration and build either controller |
| 4 | [Check the pin map](docs/CURRENT_PINMAP.md) | Verify GPIO and board-specific camera assignments before wiring |
| 5 | [Use the HTTP API reference](docs/CURRENT_API.md) | Work with the exact routes, parameters, responses, and limitations |

Real Wi-Fi credentials are never stored in tracked source. Each firmware requires an ignored local configuration copied from its safe example; missing configuration intentionally stops the build with a clear error.

## Build evidence

Both current firmware trees were rebuilt from isolated temporary copies with safe example configuration on 2026-08-19. Compilation does not prove a successful upload or safe physical operation.

| Firmware | Result | RAM | Application flash | Binary |
|---|---|---:|---:|---:|
| Rover controller | Success; one optional FastLED parallel-I²S warning | 47,784 / 327,680 | 812,909 / 6,553,600 | 813,280 bytes |
| Camera node | Success; no compiler warning | 49,352 / 327,680 | 789,081 / 6,553,600 | 789,440 bytes |

No automated firmware tests currently exist. Physical motor polarity, stop latency, camera RF path, current draw, battery behavior, and thermal margin were not re-tested during the repository audit.

## Known V0.1 limitations

- An older in-flight browser movement request can arrive after STOP.
- The 750 ms watchdog is not independent of synchronous main-loop work.
- TB6612FNG thermal margin and the installed 18650 pack remain unmeasured.
- The reported 3–7.2 V motors can receive 8.4 V pulses from a full 2S pack.
- Camera health can become stale, and `GET /restart` has no application authentication.
- The editable enclosure CAD, verified BOM part numbers, and physical acceptance report are still missing.

Track the full list in [Known issues](KNOWN_ISSUES.md) and the evidence-gated work in the [V0.1 release checklist](docs/RELEASE_CHECKLIST.md).

<details>
<summary><strong>Hardware snapshot</strong></summary>

| Subsystem | V0.1 hardware |
|---|---|
| Main controller | ESP32-S3 N16R8 development board |
| Camera | GOOUUU ESP32-S3-CAM V1.5 with OV3660 |
| Drive | 4 × reported 3–7.2 V TT gear motor, grouped left/right |
| Motor driver | TB6612FNG breakout; not production-ready for this load |
| Display | 1.3-inch SH1106 128 × 64 I²C OLED |
| Lighting | 8 + 16 + 8 WS2812 pixels |
| Motor supply | Reported 2S 18650 pack, approximately 7–8.4 V |
| Logic/camera supply | USB power bank |
| 5 V accessories | LM2596 buck converter feeding lighting/fan |

See [Hardware as built](HARDWARE_AS_BUILT.md) and the current prototype [BOM](hardware/bom/BOM.md). Exact cells, part numbers, measurements, and several physical wiring details remain open.

</details>

<details>
<summary><strong>All project documentation</strong></summary>

| Document | Purpose |
|---|---|
| [Build and flash](docs/BUILD_AND_FLASH.md) | Canonical PlatformIO setup, upload, and serial-monitor procedure |
| [Safety](docs/SAFETY.md) | Electrical, battery, motor, and control-link precautions |
| [Current implementation](docs/CURRENT_IMPLEMENTATION.md) | Code-confirmed behavior and explicit non-features |
| [Current pin map](docs/CURRENT_PINMAP.md) | Rover and camera GPIO assignments |
| [Current API](docs/CURRENT_API.md) | Exact HTTP routes, parameters, responses, and limitations |
| [Hardware as built](HARDWARE_AS_BUILT.md) | Historically reported physical configuration and open measurements |
| [Known issues](KNOWN_ISSUES.md) | Safety and reliability limitations |
| [Roadmap](ROADMAP.md) | Planned work, clearly separated from current features |
| [Release checklist](docs/RELEASE_CHECKLIST.md) | Work remaining before a tagged public release |
| [Archive provenance](docs/ARCHIVE_PROVENANCE.md) | Supplied ZIP hashes and traceability limits |
| [Tokimi Open Source](https://tokimispace.github.io/) | Bilingual organization page for current and planned open-source projects |

</details>

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Please open an issue before changing GPIO assignments, power topology, public routes, radio behavior, or motor-safety semantics. Reports about physical behavior should include the hardware revision, power source, safe test setup, and reproducible evidence.

## Licensing and brand

This is a path-specific multi-license repository:

- firmware, software, build configuration, CI, and scripts: **Apache-2.0**;
- identified hardware design/manufacturing source: **CERN-OHL-W-2.0**;
- documentation and original diagrams: **CC-BY-4.0**.

See [LICENSES.md](LICENSES.md) for authoritative scope and official texts. Tokimi, 時見數位科技, project logos, and the “Official Tokimi Rover” designation remain separate brand assets under [TRADEMARKS.md](TRADEMARKS.md).

Tokimi / 時見數位科技 welcomes collaboration on reliability, sensing, education builds, and field-robotics prototypes. Contact: `ben@tokimi.space`

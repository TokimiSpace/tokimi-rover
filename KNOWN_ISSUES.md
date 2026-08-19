# Tokimi Rover — Known Issues

> Reconciled with the 2026-08-19 source audit. Publish measured limitations clearly; do not hide failures that affect safety or reproducibility.

## Severity definitions

- **Critical:** can cause unexpected motion, materially unsafe power behavior, hardware damage, or complete loss of drive control.
- **High:** significantly reduces field reliability or defeats an expected safety/reproducibility property.
- **Medium:** degraded or misleading behavior with a workaround.
- **Low:** cosmetic, documentation, or minor usability limitation.

## Critical and high issues

### KR-001 — TB6612 shutdown under sustained four-motor load

- **Severity:** Critical
- **Status:** Open; historical `HARDWARE-CONFIRMED`, audit not physically retested
- **Evidence:** All four motors reportedly stopped after sustained demonstration use, then operation returned after approximately half an hour of cooling.
- **Likely contributors:** two TT motors per channel, vehicle mass, high duty/pivot load, mechanical drag, wiring loss, and insufficient continuous-current margin.
- **Current software reality:** physical PWM ceiling is **80%**; no current sensor, temperature sensor, fault input, soft start, or enforced reversal dead time exists.
- **Operating guidance, not implemented protection:** use short low-duty tests with wheels clear, avoid prolonged pivots/rapid reversal/payload, monitor externally, and keep a physical disconnect available. Earlier 50–60% guidance is not enforced by current code.
- **Permanent work:** safely measure current and temperature, then select a driver and wiring system with adequate continuous/peak margin.

### KR-002 — Motor current and temperature are not instrumented

- **Severity:** High
- **Status:** Open
- **Impact:** overload, stall, and thermal events are inferred after failure rather than detected or logged.
- **Missing:** current measurement, driver/motor/battery temperature, fault input, current limiting, thermal derating, and thermal stop.
- **Recommended work:** add reviewed sensors and structured logging only after the power branch and measurement method are made safe.

### KR-003 — Moving-platform wiring reliability

- **Severity:** High
- **Status:** Open
- **Problem:** breadboards and friction-fit Dupont connections can loosen under vibration; high-current paths can heat or drop voltage.
- **Impact:** resets, intermittent direction, difficult diagnosis, unexpected stop, or heating.
- **Permanent work:** direct correctly sized motor wiring, locking connectors, strain relief, documented fuse placement, and a reviewed PCB/perfboard distribution design.

### KR-006 — Outdoor thermal margin is not quantified

- **Severity:** High
- **Status:** Open
- **Context:** hot outdoor demonstration around 35°C was part of the design intent.
- **Unknowns:** enclosure material/softening, internal air temperature, battery/driver/regulator temperature, airflow, and payload effect.
- **Required evidence:** measured thermal profile and defined endurance conditions. A fan or heatsink alone does not establish driver adequacy.

### KR-008 — 18650 pack specification and protection are unknown

- **Severity:** Critical
- **Status:** Open
- **Unknown:** cell manufacturer/model/capacity/discharge rating/age/matching and BMS/protection/charger/fuse details.
- **Impact:** uncertain current capability, voltage sag, runtime, charging safety, and fault energy.
- **Required action:** identify and document a matched reputable pack, suitable 2S protection/balancing, safe charger, wiring, and fuse placement before public reproduction.

### KR-011 — Adjustable LM2596 can expose 5 V loads to battery voltage

- **Severity:** Critical
- **Status:** Process control required
- **Risk:** connecting WS2812/fan before measuring can expose them to up to 8.4 V.
- **Required procedure:** disconnect loads, power the regulator, measure OUT+/OUT−, adjust to 5.00 V, verify under load, then connect accessories.

### KR-015 — STOP can be superseded by an older movement request

- **Severity:** Critical
- **Status:** Open; `CODE-CONFIRMED`
- **Cause:** browser movement heartbeats are asynchronous and not sequenced/cancelled. Release sends STOP but cannot cancel an earlier in-flight movement POST.
- **Impact:** a late movement request can re-enable the motors after STOP until another stop path runs.
- **Required fix:** add an explicit ordering/latching protocol and tests; do not rely on browser event order.

### KR-016 — 750 ms watchdog is not a hard stop deadline

- **Severity:** High
- **Status:** Open; `CODE-CONFIRMED`
- **Cause:** timeout is tested as `elapsed > 750` in the main loop after synchronous HTTP handling.
- **Impact:** actual stop can occur later than 750 ms, particularly during slow requests or other loop work.
- **Required fix:** establish a safety-critical deadline independent of HTTP/display/lighting scheduling and measure worst-case behavior on hardware.

### KR-019 — Motor voltage rating conflicts with documented 2S supply

- **Severity:** Critical
- **Status:** Open; documented hardware conflict
- **Evidence:** motors are reported as rated 3–7.2 V; the motor branch is reported as 2S, up to 8.4 V fully charged.
- **Impact:** excess voltage can increase current, heating, brush/gear stress, and driver load. PWM reduces average duty but not pulse amplitude.
- **Required action:** verify exact motor model and adopt an appropriate supply/regulator or explicitly rated motors.

### KR-024 — Published V3 CAD spacing conflicts with the historical cover record

- **Severity:** High
- **Status:** Open; owner-selected artifact, audit not physically retested
- **Conflict:** the historical as-built document records approximately 203 × 105 mm M3 centers, while the published Supercar V3 model and A4 template use 195 × 100 mm.
- **Impact:** assuming either set is correct can waste a print or cause unsafe drilling, forced mounting, cracked parts, or interference with the rover's electronics.
- **Software evidence:** the V3 3MF/STL topology, 260 × 155 mm plan, 195 × 100 mm centers, and Ø3.5 mm holes pass repository checks. This does not prove chassis fit, material choice, support strategy, or print accuracy.
- **Required action:** print the A4 sheet at Actual Size, verify its 100 mm calibration line, measure the current chassis, compare all four centers, and record dated photos/measurements before manufacturing or marking the issue resolved.

## Medium and low issues

### KR-004 — Camera latency, frame rate, and one-buffer contention

- **Severity:** Medium
- **Status:** Open / partially mitigated
- **Current settings:** JPEG HVGA 480×320, quality 18, 20 MHz XCLK, 10 FPS target; two PSRAM/latest buffers or one DRAM/when-empty fallback.
- **Limit:** one MJPEG stream; snapshot availability during a one-buffer stream is not guaranteed. Actual latency/FPS has not been audit-measured.
- **Architecture mitigation:** independent controller/AP prevents camera code from directly consuming rover-controller execution time, but not 2.4 GHz interference.

### KR-005 — External camera antenna path is unverified

- **Severity:** Medium
- **Status:** Open
- **Problem:** a flexible U.FL/IPEX antenna is reportedly attached, but active RF selection is unknown and cannot be inferred by firmware.
- **Safe verification:** repeatable distance/RSSI/stream tests, powering off before antenna connection changes.
- **Do not:** move RF components or recommend solder changes without board-specific documentation.

### KR-007 — OLED visibility in direct sunlight

- **Severity:** Low
- **Status:** Accepted limitation
- **Mitigation:** angled/shaded mounting and detailed status on the client device.

### KR-009 — Battery percentage/runtime cannot be reported

- **Severity:** Medium
- **Status:** Open
- **Code fact:** no battery ADC/divider/calibration path exists.
- **Rule:** do not display voltage or percentage until sensing, calibration, and load-aware interpretation are implemented and tested.

### KR-010 — WS2812 power and logic margin

- **Severity:** Medium
- **Status:** Open / hardware-dependent
- **Configuration:** 32 pixels, external 5 V rail, GPIO4 through reported 330 Ω resistor, reported 1000 µF bulk capacitor, raw brightness 40/255.
- **Risks:** voltage drop, ground bounce, 3.3 V data margin, wiring heat, and transient resets.
- **Mitigation:** verified parallel injection/common ground/short data path and a suitable level shifter if measurement shows it is needed.

### KR-012 — Two-network operation usually needs two client devices

- **Severity:** Low
- **Status:** Accepted for V0.1
- **Impact:** operationally simple but less convenient; separate APs do not guarantee RF isolation.
- **Future options:** reviewed infrastructure/gateway design or independently fail-safe long-range control.

### KR-013 — LoRa is planned but not implemented

- **Severity:** Low
- **Status:** `PLANNED-NOT-IMPLEMENTED`
- **Rule:** do not list LoRa as a current feature until hardware, legal frequency, protocol, authentication, failsafe, latency, and range are verified.

### KR-017 — OLED text dashboard is unreachable and contains stale camera default

- **Severity:** Medium
- **Status:** Open; `CODE-CONFIRMED`
- **Problem:** `drawDashboard()` has no caller. The accepted `dashboard` expression returns to animated eyes. Dormant camera text initializes as `ONLINE` without any camera transport.
- **Impact:** earlier telemetry claims are false; activating the renderer unchanged would create misleading health output.
- **Resolution:** either intentionally remove the dead renderer or add truthful data transport with `UNKNOWN/OFFLINE` defaults and failure handling.

### KR-018 — Camera health/status/restart semantics are weak

- **Severity:** Medium
- **Status:** Open; `CODE-CONFIRMED`
- **Problems:** runtime capture failure does not clear `online`; initialization is not retried; `/status.sensor` is hardcoded; snapshot timeout is ignored; `GET /restart` is unauthenticated and reboots the board.
- **Impact:** stale status, indefinite failure retries, and remote reboot by any AP client.
- **Required work:** explicit health transitions/retry policy, truthful fields, real timeout semantics, and protected side-effecting control.

### KR-020 — No automated safety/API tests

- **Severity:** High
- **Status:** Open
- **Evidence:** both `pio test` commands end with `TestDirNotExistsError` because no test directory exists.
- **Impact:** builds verify compilation only; STOP ordering, state transitions, validation, routes, and timeouts have no regression harness.
- **Required work:** host/unit tests where feasible plus hardware-in-loop tests with dated evidence.

### KR-021 — HTTP APIs have no application authentication or TLS

- **Severity:** High
- **Status:** Open / accepted only as a supervised prototype limitation
- **Scope:** rover commands and camera status/capture/stream/restart are available to any associated AP client.
- **Packaging mitigation:** real Wi-Fi credentials live only in ignored local configuration; this does not provide per-request authorization, encryption against associated peers, or CSRF protection.
- **Required work:** define a threat model and authenticated control protocol before broader deployment.

## Resolved documentation/package issues

### KR-014 — Documentation drifted from code

- **Severity:** High
- **Status:** Resolved for the 2026-08-19 audited snapshot; must be continuously maintained
- **Previously conflicting:** GPIO4 role, PWM cap, watchdog meaning, OLED dashboard, camera settings/routes, and API behavior.
- **Resolution:** `docs/CURRENT_IMPLEMENTATION.md`, `docs/CURRENT_PINMAP.md`, `docs/CURRENT_API.md`, and this file now reflect current code.

### KR-022 — Deployment passwords were tracked in the source archives

- **Severity:** High
- **Status:** Resolved in public-repository packaging; rotate any previously used values
- **Resolution:** each firmware now requires an ignored local configuration copied from a safe tracked example. No deployment password should be committed.
- **Residual risk:** values present in supplied/private archives or previously flashed devices must be treated as compromised and changed; Git history must be reviewed before publication.

### KR-023 — Camera nominal flash was under-partitioned

- **Severity:** Medium
- **Status:** Resolved in public-repository packaging; hardware upload still unverified
- **Previous state:** 16 MB flash declared but generated default partition layout ended at 8 MB; a misleading RAM denominator override was present.
- **Resolution:** an explicit repository 16 MB partition layout provides two 0x640000 application slots and removes the misleading maximum-RAM override.

See [Current implementation](docs/CURRENT_IMPLEMENTATION.md), [Safety](docs/SAFETY.md), and [Release checklist](docs/RELEASE_CHECKLIST.md) for evidence boundaries and required release work.

# Current Implementation

> Audit date: 2026-08-19<br>
> Scope: repository source, PlatformIO configuration, embedded Web pages, and supplied archive metadata<br>
> Hardware boundary: `AUDIT-NOT-PHYSICALLY-RETESTED`

This document records what the V0.1 code implements. It overrides older software descriptions when they conflict. Physical construction history remains in [HARDWARE_AS_BUILT.md](../HARDWARE_AS_BUILT.md).

## Verification summary

| Area | Status | Meaning |
|---|---|---|
| Rover source behavior | `CODE-CONFIRMED` | Reconciled against `firmware/rover-controller/` |
| Camera source behavior | `CODE-CONFIRMED` | Reconciled against `firmware/camera-node/` |
| Rover build | `BUILD-CONFIRMED` | PlatformIO audit build succeeded |
| Camera build | `BUILD-CONFIRMED` | PlatformIO audit build succeeded |
| Automated tests | `UNKNOWN` | No test directories exist; no automated test suite ran |
| Assembled rover behavior | `AUDIT-NOT-PHYSICALLY-RETESTED` | No upload, motor run, camera run, power test, or RF test occurred during the audit |

## System architecture

`CODE-CONFIRMED`:

- The main ESP32-S3 controls both TB6612 channels, the SH1106 OLED, 32 WS2812 pixels, and the rover HTTP server.
- The GOOUUU ESP32-S3-CAM V1.5 controls only OV3660 capture, its own Wi-Fi AP, and its own HTTP server.
- There is no GPIO, UART, I²C, SPI, HTTP, or other application-level control/status path between the two firmwares.
- Camera failure therefore cannot directly block motor code. It also means the rover cannot know whether the camera is healthy.
- Each controller creates a separate Wi-Fi AP. That is operational separation, not guaranteed RF isolation.
- Deployment SSID/password settings are not tracked. Each firmware requires an ignored local configuration copied from its safe example.

## Rover controller

### Drive output

`CODE-CONFIRMED`:

- PWM is 20 kHz, 8-bit, with separate LEDC channels for Motor A and Motor B.
- The configured physical PWM ceiling is **80%**: maximum duty is `204/255`.
- Requested speed defaults to 30%; at that setting the full-speed wheel receives approximately `61/255`, about 24% physical duty.
- Requested speed accepts 0–100 and scales within the 80% ceiling.
- Forward, backward, pivot left, pivot right, forward-left, forward-right, backward-left, and backward-right are implemented.
- For arc commands, the inside channel receives 40% of the outside channel's already-capped duty.
- `driveMotor()` first writes both PWM channels, all direction pins, and STBY to the stopped state, then immediately selects direction and applies the target duty.
- There is **no timed reversal dead time and no PWM ramp/soft start**.
- Left/right physical polarity still depends on how each motor pair is wired.

### Stop behavior and limitations

Every implemented `stopMotor()` path writes both PWM channels to zero, makes all four direction outputs LOW, and makes TB6612 STBY LOW.

Stop paths are invoked for:

- boot;
- explicit `stop` command;
- missing or invalid movement command;
- missing or invalid speed;
- accepted speed value 0;
- no station associated with the rover AP while moving;
- command watchdog threshold exceeded while moving;
- an unhandled HTTP route or method;
- rover AP startup failure.

Important limits:

- The browser emits a movement request immediately and every 250 ms without awaiting or cancelling earlier requests. Releasing the control sends STOP, but an older in-flight movement request can arrive later and resume motion. This is an open ordering race.
- `motorCommandTimeoutMs` is 750 ms, and the comparison is `elapsed > 750`. The check runs only after synchronous HTTP handling and before lighting/display work in the main loop. Therefore 750 ms is a watchdog threshold, **not a hard maximum stopping deadline**.
- AP station count is not the same as control-page liveness. Closing the page while the phone stays associated relies on the heartbeat timeout rather than the station-loss check.
- Missing/invalid lighting and expression requests return 400 but do not stop the motors. Missing/invalid movement or speed requests do stop them.
- An empty speed string is parsed as zero, returns success, and stops the rover rather than being rejected as malformed.
- The HTTP API has no authentication or TLS. Anyone connected to the rover AP can call it.

See [Current API](CURRENT_API.md) for route-level behavior and [Safety](SAFETY.md) before operating the drive base.

### Lighting

`CODE-CONFIRMED`:

- GPIO4 drives one 32-pixel WS2812B chain using FastLED in GRB order.
- Indices 0–7 are front, 8–23 are center, and 24–31 are rear.
- FastLED brightness is raw value 40/255, approximately 15.7%; it is not 40%.
- Boot diagnostic sequence is red, green, blue, white, and off, each for 500 ms.
- Default scene is white front, blue-breathing center, and red rear.
- The public API toggles all/front/center/rear zones.
- Internal `SEARCH`, `RECOVER`, and `ERROR` renderers exist, but no current public route invokes them.
- No legacy ordinary-LED GPIO4 implementation remains.

### OLED

`CODE-CONFIRMED`:

- SH1106 128×64 hardware I²C uses GPIO8 SDA and GPIO3 SCL at 100 kHz.
- Startup scans I²C addresses and accepts the display at 0x3C or 0x3D.
- The visible splash is `TOKIMI / ESP32-S3 / OLED OK` for two seconds.
- Normal output is an animated face: motion-focused eyes while moving, blinking and pupil motion while stopped, and a sleep face after 60 seconds stopped.
- `happy`, `angry`, `sad`, `joy`, `rude`, `tasa-tokimi`, and `tasa-astronaut` last six seconds. `sos` flashes for ten seconds.
- A text dashboard renderer exists for Wi-Fi, RSSI, IP, heap, uptime, motor, camera, and extra status fields, but **nothing calls it**. Sending the accepted `dashboard` expression only returns to the animated default face.
- Dormant dashboard state initializes camera text as `ONLINE`, but there is no camera-status transport. It would not be a truthful health indicator if made visible unchanged.
- No battery, temperature, mission, or camera telemetry is displayed in the current reachable UI.

## Camera node

### Camera capture

`CODE-CONFIRMED`:

- The driver requires the detected PID to match OV3660.
- Capture is JPEG, HVGA 480×320, JPEG quality 18, with 20 MHz XCLK.
- Stream pacing target is 10 FPS; actual FPS depends on capture, client, and Wi-Fi performance.
- With PSRAM, configuration uses two PSRAM buffers and `CAMERA_GRAB_LATEST`.
- Without PSRAM, it falls back to one DRAM buffer and `CAMERA_GRAB_WHEN_EMPTY`.
- The camera is initialized once at boot. Initialization failure leaves the diagnostic/Web process running; camera initialization is not retried.
- Only one MJPEG stream can be active. Snapshot availability while streaming is not guaranteed in the single-buffer DRAM fallback.
- The browser mirrors its displayed image with CSS. Raw `/capture` and `/stream` output is not transformed by the HTTP handlers.

### Network and Web service

`CODE-CONFIRMED`:

- AP name/password/channel/client limit/address/gateway/subnet come from the required ignored `camera_config.h`. The tracked example uses channel 1, `192.168.4.1/24`, and up to four Wi-Fi clients; these are example defaults, not deployment facts.
- The firmware requests 20 MHz bandwidth and 19.5 dBm TX power and disables Wi-Fi power saving.
- The HTTP service permits up to six active client tasks and uses port 80 without TLS or application authentication.
- The UI exposes snapshot, stream, status, and restart actions.
- The `ROCKET` contour box is JavaScript in the browser. It applies grayscale/edge/component heuristics and is not trained detection, verified recognition, or rover autonomy.

### Camera health limitations

- `online` becomes true after the first validated frame but is never cleared after repeated runtime capture failures.
- Runtime capture failures retry indefinitely; `/status` can continue reporting `camera: online` with stale or zero stream metrics.
- `/status` hardcodes sensor text as `OV3660`, even when initialization failed.
- `copyLatestJpeg(output, timeoutMs)` ignores `timeoutMs` and attempts one immediate acquisition.
- `GET /restart` is unauthenticated, changes device state, and reboots after returning its response.
- RSSI is one instantaneous value from the first associated client, not an average.
- The firmware cannot determine whether the physically connected external antenna is the active RF path.

## Not implemented

The following are `PLANNED-NOT-IMPLEMENTED` or absent:

- motor current measurement;
- TB6612 or motor temperature measurement;
- battery-voltage measurement or calibrated state of charge;
- low-voltage cutoff, stall detection, current limiting, or thermal derating;
- wheel encoders, IMU, compass, GPS, or obstacle sensors;
- LoRa hardware/protocol support;
- camera-to-rover status or command transport;
- autonomous navigation, assisted driving, or onboard trained computer vision;
- OTA updates, MQTT, ROS, cloud control, API authentication, or TLS.

## Build evidence

The read-only audit produced these successful builds before documentation packaging:

| Firmware | Platform/framework | Audit result |
|---|---|---|
| Rover | PlatformIO 6.1.19; Espressif32 7.0.1; Arduino-ESP32 2.0.17 | `BUILD-CONFIRMED`; RAM 47,784/327,680; flash 812,741/6,553,600; binary 813,104 bytes |
| Camera | PlatformIO 6.1.19; Espressif32 6.12.0; Arduino-ESP32 2.0.17 | `BUILD-CONFIRMED`; app 788,593/3,342,336; binary 788,960 bytes |

The rover audit build emitted FastLED's optional parallel clockless-I²S backend warning because `esp_memory_utils.h` was unavailable; it did not emit a rover-source compiler warning. The camera build emitted no compiler warnings.

Both `pio test` attempts failed with `TestDirNotExistsError` because no test directories exist. No upload or hardware behavior was verified by those builds. Follow [Build and flash](BUILD_AND_FLASH.md) to reproduce the current compile process.

Public-repository packaging pinned the rover platform to the audited 7.0.1 resolution, moved both deployments' network settings to ignored local configuration, and added an explicit camera 16 MB partition table with two 0x640000 application slots. The table above preserves the input-archive audit sizes; a final release must attach a clean build log from its exact commit.

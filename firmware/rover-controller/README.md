# Tokimi Rover controller firmware

PlatformIO firmware for the Tokimi Rover's main ESP32-S3 N16R8 controller. It
runs a Wi-Fi access point and browser controller, drives two TB6612FNG channels,
updates a SH1106 OLED, and controls a 32-pixel WS2812 chain.

This directory contains the rover controller only. The camera is an independent
ESP32-S3 node and does not exchange commands or status with this firmware.

## Safety status

This is prototype firmware, not a production-ready vehicle controller. Test
with the wheels raised and keep a physical way to disconnect motor power within
reach.

- The configured PWM ceiling is currently **80%** (`204/255`), not the
  50–60% temporary ceiling recommended for unmeasured hardware. A web speed of
  100% therefore produces up to 80% physical PWM duty; the default requested
  speed is 30% (about 24% physical duty).
- The installed TB6612FNG has reportedly shut down under sustained four-motor
  load. Motor current and driver temperature are not measured by this firmware.
- The 750 ms command watchdog is a threshold checked by the main loop, not a
  guaranteed worst-case stopping deadline.
- Direction changes stop the PWM outputs first, but there is no enforced
  reversal dead time or soft-start ramp.
- Browser movement requests can overlap. A delayed movement request may arrive
  after a STOP request and resume movement until another stop or watchdog event.
- Loss of all Wi-Fi station associations stops an active drive command. Closing
  the browser while its device remains associated relies on the command
  watchdog instead.
- Invalid or missing drive and speed values stop both motor channels. Invalid
  lighting or expression values return HTTP 400 without an added motor stop.
  Unknown routes return HTTP 404 and stop the motors.

These are known, unresolved V0.1 limitations. This packaging change deliberately
does not alter motor direction behavior, the PWM cap, the watchdog, the public
HTTP API, or the embedded web UI. Review the repository's
[known issues](../../KNOWN_ISSUES.md) and
[as-built hardware notes](../../HARDWARE_AS_BUILT.md) before powering motors.

## Build configuration

The `esp32-s3-n16r8` environment uses:

- PlatformIO's `espressif32@7.0.1` platform;
- Arduino framework on `esp32-s3-devkitc-1`;
- 16 MB flash with the `default_16MB.csv` partition table;
- QIO flash and OPI PSRAM settings;
- C++17;
- U8g2 2.36.18 and FastLED 3.10.3.

Install [PlatformIO](https://platformio.org/), then create the ignored local
configuration before building:

```sh
cd firmware/rover-controller
cp include/local_config.example.h include/local_config.h
```

Edit `include/local_config.h` and replace both example strings with a unique AP
SSID and an 8–63 byte WPA2 password. The real file is ignored by Git. A build
without it fails with an explicit instruction instead of embedding tracked or
fallback credentials.

Build, upload, and open the 115200-baud serial monitor with:

```sh
pio run -e esp32-s3-n16r8
pio run -e esp32-s3-n16r8 -t upload
pio device monitor -b 115200
```

After boot, connect a client to the configured AP and open the IP printed in the
serial log (normally the ESP32 SoftAP address). The HTTP server has no
application authentication or TLS; the WPA2 AP password is its only access
boundary.

## Code-confirmed GPIO map

| GPIO | Function |
| ---: | --- |
| 3 | SH1106 OLED SCL |
| 4 | WS2812 data, 32 pixels in GRB order |
| 5 | TB6612 PWMA, LEDC channel 0 |
| 6 | TB6612 AIN1 |
| 7 | TB6612 AIN2 |
| 8 | SH1106 OLED SDA |
| 15 | TB6612 STBY |
| 16 | TB6612 PWMB, LEDC channel 1 |
| 17 | TB6612 BIN1 |
| 18 | TB6612 BIN2 |
| 19, 20 | Not used by application code; reserved for native USB |

Motor PWM is 20 kHz at 8-bit resolution. Lighting indices are front 0–7,
center 8–23, and rear 24–31. FastLED global brightness is 40/255.

## HTTP interface

The server listens on port 80. Query parameters and accepted values are
case-sensitive.

| Method and path | Query value | Current behavior |
| --- | --- | --- |
| `GET /` | — | Serves the embedded browser controller. |
| `POST /api/command` | `value=forward`, `backward`, `left`, `right`, `forward-left`, `forward-right`, `backward-left`, `backward-right`, or `stop` | Updates both motor channels or stops them. The browser repeats held movement commands every 250 ms. |
| `POST /api/speed` | `value=0..100` | Sets requested speed; the 80% physical PWM ceiling still applies. Zero stops the motors. |
| `POST /api/led` | `state=toggle-all`, `toggle-front`, `toggle-center`, or `toggle-rear` | Toggles the corresponding WS2812 zone state. |
| `POST /api/expression` | `value=sos`, `happy`, `angry`, `sad`, `joy`, `rude`, `tasa-tokimi`, `tasa-astronaut`, or `dashboard` | Selects a temporary OLED expression or returns to the default face. |

There is no status, telemetry, battery, camera, JSON, OTA, MQTT, LoRa, ROS,
TLS, or application-authentication endpoint in this firmware.

## Hardware test checklist

Compilation does not verify wiring or safe current capacity. Before driving:

1. Keep the motor supply disconnected and confirm the configured AP, web UI,
   OLED, and lighting behavior.
2. Raise all wheels, provide a reachable motor-power disconnect, and verify that
   boot, explicit STOP, invalid drive/speed input, loss of all associated Wi-Fi
   clients, and command timeout leave both PWM channels at zero and STBY low.
3. Verify actual motor polarity for every direction; two motors are wired in
   parallel on each driver channel.
4. Measure motor current, supply voltage, wiring temperature, and TB6612
   temperature under load. Do not use the present 80% ceiling as evidence that
   the hardware is safe.
5. Confirm the 2S battery, protection/BMS, regulator output, fusing, wire gauge,
   and common-ground arrangement against the physical rover.

## Repository documentation

- [Repository overview](../../README.md)
- [Project context](../../PROJECT_CONTEXT.md)
- [Hardware as built](../../HARDWARE_AS_BUILT.md)
- [Known issues](../../KNOWN_ISSUES.md)
- [Roadmap](../../ROADMAP.md)

Roadmap items are not implemented features. Licensing and Tokimi trademark
terms are defined at the repository root.

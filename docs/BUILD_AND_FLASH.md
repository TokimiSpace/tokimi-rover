# Build and Flash

> Canonical V0.1 procedure<br>
> Firmware builds are `BUILD-CONFIRMED`; flashing and operation are `AUDIT-NOT-PHYSICALLY-RETESTED`.

## Before you begin

Read [Safety](SAFETY.md). For any first boot or motor-related change:

1. disconnect motor-battery power while configuring and flashing;
2. support the chassis so every driven wheel is clear;
3. keep a physical motor-power disconnect within reach;
4. verify wiring against [Current pin map](CURRENT_PINMAP.md);
5. do not connect 2S battery voltage to 5 V accessories.

You need:

- Python 3 supported by PlatformIO;
- PlatformIO Core (the audit used 6.1.19);
- a data-capable USB cable;
- the appropriate serial-device permissions for your operating system.

All commands below run from the repository root.

## Local Wi-Fi configuration

Both firmware projects deliberately require local configuration files that are ignored by Git. The tracked templates contain only safe example values.

### Rover controller

```sh
cp firmware/rover-controller/include/local_config.example.h \
  firmware/rover-controller/include/local_config.h
```

Edit `firmware/rover-controller/include/local_config.h` and replace both example values:

- `TOKIMI_ROVER_AP_SSID`: 1–32 bytes;
- `TOKIMI_ROVER_AP_PASSWORD`: 8–63 bytes.

### Camera node

```sh
cp firmware/camera-node/include/camera_config.h.example \
  firmware/camera-node/include/camera_config.h
```

Edit `firmware/camera-node/include/camera_config.h` and replace the example AP name and password. The same file also owns the AP channel, client limit, IPv4 address, gateway, and subnet. Keep the password at 8–63 bytes and use a unique value.

Never commit either local file. Check staged changes before every push. A missing file intentionally causes a clear compile-time error rather than silently shipping a shared password.

## Build

### Rover controller

```sh
pio run --project-dir firmware/rover-controller
```

Configured environment: `esp32-s3-n16r8`.

- board: `esp32-s3-devkitc-1`;
- Espressif32 platform: pinned to 7.0.1;
- framework: Arduino;
- C++17;
- 16 MB flash and `default_16MB.csv`;
- two 0x640000 application slots, with maximum application size 6,553,600 bytes;
- QIO flash / OPI PSRAM configuration;
- native USB CDC enabled;
- U8g2 2.36.18;
- FastLED 3.10.3.

### Camera node

```sh
pio run --project-dir firmware/camera-node
```

Configured environment: `goouuu-esp32-s3-cam`.

- board: `esp32-s3-devkitc-1` with the board-specific camera GPIO map in source;
- Espressif32 platform: pinned to 6.12.0;
- framework: Arduino;
- 16 MB flash;
- DIO flash / OPI PSRAM configuration;
- native USB CDC enabled;
- repository partition file `partitions_16mb.csv`, with two 0x640000 application slots;
- maximum application size 6,553,600 bytes.

Do not substitute the AI Thinker ESP32-CAM board definition or pin map.

## Find the serial port

Connect only the controller you intend to flash, then list detected devices:

```sh
pio device list
```

Record the explicit port path shown for the board. Avoid choosing a port by guesswork when both ESP32-S3 boards are connected.

## Upload

Keep the rover's motor battery disconnected during upload.

### Rover controller

```sh
pio run --project-dir firmware/rover-controller \
  --target upload \
  --upload-port <ROVER_SERIAL_PORT>
```

### Camera node

```sh
pio run --project-dir firmware/camera-node \
  --target upload \
  --upload-port <CAMERA_SERIAL_PORT>
```

If automatic reset does not enter the bootloader, follow the exact boot/reset procedure for the installed board revision. Do not assume the two boards use identical buttons or timing.

## Serial monitor

Both firmwares use 115200 baud.

```sh
pio device monitor --port <SERIAL_PORT> --baud 115200
```

Expected rover evidence includes:

- `drive=stopped reason=boot`;
- pin/PWM summary;
- access-point startup result;
- Web UI address;
- `motor ready; waiting in STOP`.

Expected camera evidence includes:

- reset/chip/memory diagnostics;
- detected OV3660 PID;
- validated first JPEG, or an explicit camera initialization error;
- access-point and HTTP-listener state;
- snapshot, stream, and status addresses.

A successful compile or boot log does not prove safe motor polarity, acceptable current, reliable stopping latency, camera RF path, or thermal margin.

## First functional check

Perform checks in this order:

1. Boot the rover with motor battery disconnected and confirm STBY and both PWM outputs remain stopped in the log.
2. Confirm the OLED and lighting boot behavior without relying on either for safety.
3. Join the rover AP and load the root page.
4. With wheels still clear, connect motor power and issue STOP before any movement command.
5. Test one short, low-requested-speed movement at a time and verify physical polarity.
6. Release the control and verify stopping; also test page hide, browser close, and Wi-Fi loss while ready to disconnect power.
7. Treat results as experimental because the STOP ordering race and non-hard watchdog deadline remain open.
8. Test the camera separately, then verify `/capture`, one `/stream`, and `/status`.

Do not perform a stall test with the present unknown 18650 pack and uninstrumented TB6612 installation.

## Recorded audit build

The source archives compiled successfully during the 2026-08-19 read-only audit:

| Firmware | Result | Size evidence |
|---|---|---|
| Rover | Success | RAM 47,784/327,680; flash 812,741/6,553,600; binary 813,104 bytes |
| Camera | Success | app 788,593 bytes; binary 788,960 bytes |

The camera's audited input archive used a smaller generated default application partition. Repository packaging subsequently added the explicit 16 MB partition table described above; the binary content size remains well below the configured slot size. Release artifacts should record a fresh build log from the final tagged commit.

The rover build reported a FastLED optional-backend warning about unavailable `esp_memory_utils.h`; the normal clockless output path still built. No automated tests exist: invoking `pio test` currently fails with `TestDirNotExistsError`. This must not be represented as a passing test suite.

## Packaged-tree verification build

The reorganized repository tree was independently rebuilt on 2026-08-19 from fresh temporary project copies. Each copy used its tracked example configuration as the ignored local configuration; no `.pio/`, credential file, or binary was created in the repository.

| Firmware | Platform | Result | Size evidence |
|---|---|---|---|
| Rover | PlatformIO 6.1.19; Espressif32 7.0.1; Arduino-ESP32 2.0.17 package `3.20017.241212` | Success; one FastLED optional parallel-I²S warning | RAM 47,784/327,680; flash 812,909/6,553,600; binary 813,280 bytes |
| Camera | PlatformIO 6.1.19; Espressif32 6.12.0; Arduino-ESP32 2.0.17 package `3.20017.241212` | Success; no compiler warning | RAM 49,352/327,680; flash 789,081/6,553,600; binary 789,440 bytes |

These results verify compilation of the current uncommitted packaging tree, not a tagged release. Release hashes and logs must be regenerated from the exact public commit after the initial commit.

## Clean rebuild and release evidence

For a release candidate, delete only each project's generated `.pio/` directory, recreate local configuration from the templates, rebuild both environments, and retain:

- commit ID and tag;
- PlatformIO version;
- resolved platform/framework versions;
- build logs and size reports;
- SHA-256 hashes of distributable artifacts;
- separate physical test records.

Do not commit `.pio/`, private configuration, or firmware binaries unless a release process explicitly requires signed/hash-published artifacts.

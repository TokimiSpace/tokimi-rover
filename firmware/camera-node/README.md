# Tokimi Ground Support Rover — Camera Firmware

Standalone firmware for the **GOOUUU ESP32-S3-CAM V1.5** camera board with an
**OV3660** sensor. It creates a local Wi-Fi access point and exposes only a
camera Web UI, a JPEG snapshot, an MJPEG stream, JSON status, and a manual
restart action.

This project intentionally contains no rover firmware, motor/TB6612 support,
OLED support, WS2812 support, dashboard integration, face detection, QR, AI,
or trained object-recognition model. The Web UI includes a lightweight,
client-side geometric contour detector for elongated rectangular shapes. This
browser-only overlay displays only the highest-scoring `ROCKET` candidate and
never sends rover or motor commands.

## Verified hardware target

The target is the GOOUUU ESP32-S3-CAM family board, not the AI Thinker
ESP32-CAM. PlatformIO does not provide a dedicated GOOUUU board ID, so the
project uses `esp32-s3-devkitc-1` with the GOOUUU N16R8 memory overrides:
16 MB flash, 8 MB octal PSRAM, and `dio_opi` memory mode.

The GPIO mapping was cross-checked against the
[GOOUUU board repository and schematic](https://github.com/zhuhai-esp/ESP32-S3-Goouuu-Cam)
and the independently published
[ESP32-S3-CAM schematic/pin table](https://github.com/nulllaborg/esp32s3-cam).
Both sources give the same DVP routing:

| OV3660 signal | ESP32-S3 GPIO |
|---|---:|
| SCCB SDA | 4 |
| SCCB SCL | 5 |
| VSYNC | 6 |
| HREF | 7 |
| D0 / Y2 | 11 |
| D1 / Y3 | 9 |
| D2 / Y4 | 8 |
| D3 / Y5 | 10 |
| D4 / Y6 | 12 |
| D5 / Y7 | 18 |
| D6 / Y8 | 17 |
| D7 / Y9 | 16 |
| XCLK | 15 |
| PCLK | 13 |
| PWDN | not connected (`-1`) |
| RESET | not connected (`-1`) |

The firmware also reads the sensor PID and refuses to report the camera online
unless it is exactly `OV3660_PID`. A camera initialization failure is logged by
name and hexadecimal error code; it does not trigger a reboot loop. The AP and
diagnostic status page still start when the camera is offline.

### External antenna

Firmware cannot detect which physical RF path is active. A public
ESP32-S3-CAM board-family reference describes a physical 0 Ω antenna selector,
but that information has not been conclusively matched to this exact GOOUUU
V1.5 PCB revision. The presence of a connected U.FL/IPEX antenna therefore
does not prove that it is active. Use the measurement procedure in
[`ANTENNA_TEST.md`](ANTENNA_TEST.md); do not modify the PCB based on this
repository alone.

## Camera and network configuration

Deployment credentials are not stored in tracked source. Create the required
local configuration before building:

```sh
cp include/camera_config.h.example include/camera_config.h
```

Edit `include/camera_config.h` and replace the example SSID and password with
deployment-specific values. The local file is ignored by Git. A checkout that
does not contain it stops at compile time with a message explaining the copy
step. The password must be 8-63 bytes; the SSID, channel, and client limit are
also checked at compile time.

The same local header contains the fixed AP address, gateway, subnet, channel,
and maximum associated-client count. The example uses channel 1 and
`192.168.4.1/24`, but those are examples rather than deployment credentials.

| Setting | Value |
|---|---|
| Pixel format | JPEG |
| Resolution | 480 × 320 (`FRAMESIZE_HVGA`) |
| JPEG quality | 18 |
| Capture/stream target | 10 FPS |
| Network write timeout | 300 ms |
| Frame buffers | 2 in PSRAM; 1 in DRAM fallback |
| Grab mode | latest frame when PSRAM is available |
| Wi-Fi mode | 2.4 GHz access point |
| SSID and password | Required ignored local configuration |
| Channel and IPv4 settings | Ignored local configuration; safe example provided |
| Wi-Fi bandwidth | 20 MHz |
| Maximum TX power setting | 19.5 dBm |
| Wi-Fi power save | explicitly disabled |

One MJPEG stream is accepted at a time. The server can accept status and
snapshot connections while that stream is running. With the normal two-buffer
PSRAM configuration, the snapshot path is intended to remain usable. In the
one-buffer DRAM fallback, `/capture` competes with the stream for the only
driver frame buffer and is not guaranteed to complete promptly. The current
snapshot wrapper also ignores its `timeoutMs` argument.

The HTTP path borrows JPEG buffers directly from the camera driver and returns
them immediately after socket delivery, avoiding per-frame allocation and
copying. The Web preview is horizontally mirrored for the installed camera
orientation; the raw JPEG and MJPEG endpoints are unchanged.

## HTTP endpoints

| Request | Result |
|---|---|
| `GET /` | Camera Web UI |
| `GET /stream` | MJPEG stream |
| `GET /capture` | One JPEG image |
| `GET /status` | JSON status |
| `GET /restart` | Return JSON, then restart the board |

All endpoints use unauthenticated plain HTTP. In particular, `GET /restart` is
a state-changing, unauthenticated request: any client able to reach the AP can
reboot the camera board. The AP password controls network association only; it
is not per-request authorization. Do not bridge this HTTP service to an
untrusted network without adding a separate security layer.

`/status` returns camera, stream, memory, and Wi-Fi diagnostics. Uptime is in
milliseconds. Each `rssi` value is one instantaneous reading for the first
associated station returned by the ESP-IDF station list. It is not an average,
and it does not summarize multiple clients. RSSI is `-127` when no client is
connected. Calculate averages externally from multiple `/status` responses or
three-second Serial diagnostic samples.

```json
{
  "camera": "online",
  "sensor": "OV3660",
  "resolution": "480x320",
  "fps": 10,
  "actual_fps": 9.8,
  "avg_frame_ms": 24.1,
  "avg_capture_ms": 18.4,
  "avg_jpeg_bytes": 12345,
  "heap": 123456,
  "psram": true,
  "psram_free": 8300000,
  "uptime": 12345,
  "rssi": -52,
  "channel": 1,
  "phy": "11n",
  "protocol": "11b/g/n",
  "bandwidth_mhz": 20,
  "tx_power_dbm": 19.5,
  "power_save": false,
  "ip": "192.168.4.1",
  "ap": "your-configured-ssid"
}
```

The health fields have deliberate current limitations. `camera` records
whether initialization succeeded; it is not a continuous sensor-health check.
After initialization, repeated capture failures do not clear the online flag
or trigger camera reinitialization, so camera state and stream metrics can
become stale. The `sensor` field is currently emitted as `OV3660` even when
initialization failed. Treat `/status` as diagnostics, not a safety or liveness
guarantee.

The AP state is checked every five seconds. If AP mode stops, firmware attempts
to restore the configured AP and HTTP listener without rebooting. Serial prints
RSSI, channel, PHY, TX power, memory, FPS, average frame time, and average JPEG
size every three seconds.

## Source layout

- `platformio.ini` — ESP32-S3, flash, OPI PSRAM, native USB CDC settings
- `partitions_16mb.csv` — explicit 16 MB flash layout
- `include/camera_config.h.example` — safe local network configuration template
- `src/main.cpp` — boot diagnostics and top-level lifecycle
- `src/camera.cpp`, `src/camera.h` — verified GPIO mapping and OV3660 setup
- `src/web.cpp`, `src/web.h` — AP/stream recovery, zero-copy MJPEG,
  diagnostics, Web UI
- `ANTENNA_TEST.md` — controlled antenna-distance test and report template

## Build, upload, and monitor

Install PlatformIO Core, connect a data-capable USB-C cable to the board's
native USB/OTG programming port, then run from this directory. The first
command is required for every fresh checkout:

```sh
cp include/camera_config.h.example include/camera_config.h
# Edit include/camera_config.h and set unique deployment credentials.
pio run
pio run -t upload
pio device monitor
```

The environment pins `espressif32@6.12.0` and uses Arduino-ESP32 2.0.17 from
that platform package. The repository-owned partition CSV spans the full 16 MB
flash and provides two `0x640000` (6,553,600-byte) application slots; the
PlatformIO maximum application size matches one slot. No OTA HTTP endpoint is
implemented. The normal PlatformIO RAM percentage covers internal SRAM rather
than treating external PSRAM as statically linkable RAM.

The serial monitor runs at 115200 baud. If automatic download mode does not
start, hold **BOOT**, tap **RST**, release **RST**, then release **BOOT** and run
the upload command again. Press **RST** once after an upload if the new USB CDC
monitor port has not appeared. `pio device list` can be used to find an explicit
port; pass it as `--upload-port /dev/...` or `--port /dev/...` when needed.

`pio run` verifies compilation and the partition fit only. It does not verify
the physical camera, PSRAM, antenna selection, Wi-Fi range, USB power quality,
or runtime endpoint behavior.

## Manual test checklist

Perform the electrical checks with USB power disconnected.

- [ ] Confirm the PCB says GOOUUU ESP32-S3-CAM V1.5 and the module is the
      N16R8 variant expected by `platformio.ini`.
- [ ] Confirm the OV3660 FFC is fully seated, correctly oriented, and latched.
- [ ] Record the installed antenna arrangement without assuming which RF path
      is active.
- [ ] Copy the configuration example, choose a unique SSID and password, and
      confirm `include/camera_config.h` remains ignored by Git.
- [ ] Build with `pio run`; expect `SUCCESS` with no compiler warnings.
- [ ] Upload over USB-C with `pio run -t upload`.
- [ ] Start `pio device monitor`; reset once and verify boot reason, detected
      flash size, heap, and approximately 8 MB PSRAM are logged.
- [ ] Verify the log reports sensor PID `0x3660`, first JPEG size, `480x320`,
      quality 18, target 10 FPS, the configured AP channel, and the configured
      camera URL.
- [ ] Join the configured SSID using the local password; confirm the client
      receives an address in the configured subnet and can reach the camera.
- [ ] Open the configured camera URL; verify live video, Capture JPEG, Restart
      camera, Heap, PSRAM, and Resolution are visible.
- [ ] Place a high-contrast elongated rectangle in view; verify the browser
      draws a mirrored-coordinate `ROCKET` box and updates `Rocket Scan` without
      reducing the camera stream target.
- [ ] Leave the stream open for at least 10 minutes. Serial should approach
      10 FPS without steadily falling heap/PSRAM or repeated disconnects.
- [ ] With PSRAM detected and two buffers active, press Capture JPEG while
      streaming. Verify a valid 480 × 320 JPEG opens and the stream continues.
      Record one-buffer fallback results separately; success is not guaranteed.
- [ ] Set `CAMERA_IP` to the configured address, then run
      `curl -o tokimi-test.jpg "http://${CAMERA_IP}/capture"`; verify the file
      is recognized as JPEG and is 480 × 320.
- [ ] Run `curl -s "http://${CAMERA_IP}/status"`; verify camera, stream,
      memory, and Wi-Fi diagnostic fields, `fps: 10`, and `psram: true`.
- [ ] Disconnect and reconnect the phone/laptop from the AP; verify the Web UI
      is reachable again and logs show both Wi-Fi events.
- [ ] Interrupt and restore the link; verify the page retries the stream first
      and automatically reloads only after three failed stream recoveries.
- [ ] From a trusted client, press Restart camera once. Verify exactly one
      reboot occurs and the AP and camera return; remember this GET action has
      no application-level authentication.
- [ ] Failure test: power off, disconnect the camera FFC, and boot. Verify the
      precise camera initialization error is printed, the board does not reboot
      repeatedly, the AP remains available, and `/status` says camera offline.
      Power off before reconnecting the FFC.
- [ ] Power from the intended USB-C power bank and repeat the stream test to
      check for brownout messages or power-related frame failures.

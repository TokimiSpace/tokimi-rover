# GOOUUU ESP32-S3-CAM V1.5 Antenna Measurement Report

## Current conclusion

- Estimated antenna status: **Cannot determine**
- Confidence in this classification: **95%**

### Measured facts

- The firmware can take one instantaneous RSSI reading for the first associated
  client returned by the ESP-IDF station list.
- The firmware can read the active AP channel, enabled Wi-Fi protocols,
  bandwidth, configured maximum TX power, and power-save mode.
- The external 2.4 GHz FPC antenna is physically connected to U.FL/IPEX
  (reported hardware observation).
- No antenna-selection control is implemented in firmware.

### Unverified observations

- The supplied PCB photographs reportedly show no obvious RF selector jumper.
- The exact RF routing of this physical V1.5 board has not been established
  from measurements or an exact revision-matched schematic.

### Hypotheses

- The PCB antenna may still be selected even though an FPC antenna is attached.
- The external FPC antenna may be selected by a fixed trace or an RF component
  that is not visually identifiable in the available photographs.

Firmware cannot distinguish these hypotheses. The presence of a U.FL antenna,
RSSI from one location, or long range by itself does not prove which path is
active.

One public ESP32-S3-CAM board-family reference describes a 0 ohm RF selector
near IPEX and a default PCB-antenna position:
https://github.com/nulllaborg/esp32s3-cam

This is not treated as conclusive proof for the specific GOOUUU V1.5 PCB in
this test. No PCB modification is recommended by this report.

## Controlled test setup

Keep these conditions unchanged for the complete test:

- Use an open, line-of-sight path where possible.
- Keep the rover camera board, external FPC antenna, and phone at the same
  height and orientation at every point.
- Do not touch or reposition the antenna between readings.
- Keep the camera stream open continuously.
- Keep Wi-Fi channel and firmware unchanged.
- Wait at least 15 seconds at each distance and record at least five diagnostic
  samples (one instantaneous first-client sample every 3 seconds).
- Calculate minimum, average, and maximum RSSI externally from those recorded
  samples. The firmware does not calculate RSSI averages.
- Repeat the full test twice, once walking away and once walking back, to expose
  environmental variation.

## Procedure

1. Boot the camera and open the Serial monitor at 115200 baud.
2. Connect the phone to the SSID configured in the ignored local
   `include/camera_config.h` file.
3. Open the camera address configured in that file and confirm live streaming.
4. At each distance, wait 15 seconds before recording results.
5. Record RSSI minimum/average/maximum, FPS, observed latency, and packet loss.
6. Test 1 m, 5 m, 10 m, 15 m, 20 m, and 30 m.
7. Repeat the measurements while walking back toward the rover.

## Results

| Distance | RSSI min | RSSI avg | RSSI max | FPS avg | Latency | Packet loss | Notes |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 m  |  |  |  |  |  |  |  |
| 5 m  |  |  |  |  |  |  |  |
| 10 m |  |  |  |  |  |  |  |
| 15 m |  |  |  |  |  |  |  |
| 20 m |  |  |  |  |  |  |  |
| 30 m |  |  |  |  |  |  |  |

### Packet-loss measurement

When a laptop is connected to the camera AP, run:

```sh
CAMERA_IP=192.168.4.1  # Replace if the local configuration uses another IP.
ping -c 50 -i 0.2 "${CAMERA_IP}"
```

Record the packet-loss percentage. If only an iPad or iPhone is available and
no ping utility is installed, record packet loss as `not measured`; do not
infer it from video appearance.

### Latency measurement

For a repeatable measurement, place a blinking light in the camera view and
record both the physical light and the phone display in the same slow-motion
video. Count the frames between the physical transition and the transition on
the display. Latency is:

```text
latency_ms = frame_difference / recording_fps * 1000
```

## Interpretation rules

Treat RSSI and FPS trends as evidence about link performance, not direct proof
of antenna routing.

- A repeatable improvement of roughly 6 dB or more over a separately verified
  PCB-antenna reference, across several distances in the same environment,
  would support **Very likely external antenna**.
- Results matching a separately verified PCB-antenna reference, with no
  repeatable improvement at longer distances, would support **Very likely PCB
  antenna**.
- Without a verified comparison state or revision-matched RF schematic, select
  **Cannot determine**, even if the absolute range is good.
- Sudden FPS loss with strong RSSI can indicate 2.4 GHz interference rather
  than antenna selection.
- Weak RSSI alone does not prove that the external antenna is inactive; antenna
  orientation, polarization, obstruction, interference, and the phone radio
  can produce the same result.

## Final assessment after measurements

- Estimated antenna status: **Cannot determine / Very likely PCB antenna /
  Very likely external antenna**
- Confidence: **___%**
- Evidence supporting the assessment:
  -
  -
- Conflicting or missing evidence:
  -
  -

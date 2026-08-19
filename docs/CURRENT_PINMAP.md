# Current Pin Map

> Audit date: 2026-08-19<br>
> GPIO assignments are `CODE-CONFIRMED`. Connection to the reported physical devices is `HARDWARE-CONFIRMED` from prior development history but `AUDIT-NOT-PHYSICALLY-RETESTED` in this repository audit.

The rover controller and camera node are separate ESP32-S3 devices. Reuse of a GPIO number across the two tables is not a conflict.

## Rover controller — ESP32-S3 N16R8

| GPIO | Firmware role | Direction/peripheral | Code evidence and notes |
|---:|---|---|---|
| 3 | SH1106 SCL | I²C clock | `display.cpp`; bus starts at 100 kHz |
| 4 | WS2812B data | FastLED output | 32 pixels, GRB order; no legacy single-LED path |
| 5 | TB6612 PWMA | LEDC channel 0 | 20 kHz, 8-bit |
| 6 | TB6612 AIN1 | Digital output | LOW in stopped state |
| 7 | TB6612 AIN2 | Digital output | LOW in stopped state |
| 8 | SH1106 SDA | I²C data | `display.cpp` |
| 15 | TB6612 STBY | Digital output | LOW in stopped state; HIGH only for drive output |
| 16 | TB6612 PWMB | LEDC channel 1 | 20 kHz, 8-bit |
| 17 | TB6612 BIN1 | Digital output | LOW in stopped state |
| 18 | TB6612 BIN2 | Digital output | LOW in stopped state |
| 19 | Native USB D− | Reserved | Not referenced by application code; native USB build flags enabled |
| 20 | Native USB D+ | Reserved | Not referenced by application code; native USB build flags enabled |

### Rover peripheral mapping

Reported physical motor grouping:

```text
Left-front + left-rear motors   → TB6612 AO1/AO2, channel A
Right-front + right-rear motors → TB6612 BO1/BO2, channel B
```

The application treats A and B as left and right sides when generating arcs and pivots. Actual forward polarity depends on the physical motor leads and was not rechecked during the audit.

Reported physical connections:

| Rover signal | Physical connection | Verification boundary |
|---|---|---|
| GPIO3/GPIO8 | SH1106 SCL/SDA | Historical `HARDWARE-CONFIRMED`; audit not physically retested |
| GPIO4 | 330 Ω series resistor, then first WS2812 DI | Historical `HARDWARE-CONFIRMED`; audit not physically retested |
| GPIO5/6/7/15/16/17/18 | TB6612 PWMA/AIN1/AIN2/STBY/PWMB/BIN1/BIN2 | Historical `HARDWARE-CONFIRMED`; audit not physically retested |
| 3V3 | TB6612 VCC and SH1106 power | Historical `HARDWARE-CONFIRMED`; audit not physically retested |
| GND | TB6612, motor-battery negative, LM2596 OUT−, and WS2812 common reference | Required by documented topology; exact present wiring must be inspected before power-on |

Do not repurpose GPIO19 or GPIO20 without a complete native-USB/board conflict review. Do not change any listed GPIO solely to make a different board variant compile.

## Camera node — GOOUUU ESP32-S3-CAM V1.5

The mapping below is explicitly configured in `firmware/camera-node/src/camera.cpp`; it is not the AI Thinker ESP32-CAM map.

| Camera signal | GPIO | Notes |
|---|---:|---|
| SCCB SDA / SIOD | 4 | Sensor control data |
| SCCB SCL / SIOC | 5 | Sensor control clock |
| VSYNC | 6 | Frame synchronization |
| HREF | 7 | Line/reference synchronization |
| D0 / Y2 | 11 | Parallel pixel data bit 0 |
| D1 / Y3 | 9 | Parallel pixel data bit 1 |
| D2 / Y4 | 8 | Parallel pixel data bit 2 |
| D3 / Y5 | 10 | Parallel pixel data bit 3 |
| D4 / Y6 | 12 | Parallel pixel data bit 4 |
| D5 / Y7 | 18 | Parallel pixel data bit 5 |
| D6 / Y8 | 17 | Parallel pixel data bit 6 |
| D7 / Y9 | 16 | Parallel pixel data bit 7 |
| XCLK | 15 | 20 MHz sensor clock |
| PCLK | 13 | Pixel clock |
| PWDN | −1 | Not controlled by a GPIO |
| RESET | −1 | Not controlled by a GPIO |

The firmware verifies the sensor PID as OV3660 before declaring initialization successful. This source-level check does not verify connector orientation, cable condition, antenna selection, or power integrity.

## Lighting indices

| Physical zone | Pixel indices | Count | Default scene |
|---|---:|---:|---|
| Front | 0–7 | 8 | White |
| Center | 8–23 | 16 | Blue breathing |
| Rear | 24–31 | 8 | Red |

All three zones share one data chain. Their 5 V power is documented as parallel distribution from the LM2596, not a thin series/daisy-chain power path.

## Power is not a GPIO assignment

- Never feed the reported 2S battery voltage directly into WS2812 pixels, a 5 V fan, or a controller 5 V input.
- Measure LM2596 output before connecting loads; the documented target is 5.00 V.
- The camera can remain electrically isolated because it communicates only through Wi-Fi and has its own USB supply.
- The reported 3–7.2 V motors are documented on a 2S branch that can reach 8.4 V. Resolve that voltage mismatch before treating the design as reproducible or safe.

See [Safety](SAFETY.md) and [Hardware as built](../HARDWARE_AS_BUILT.md) for the complete power boundary.

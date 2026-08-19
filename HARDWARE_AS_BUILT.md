# Tokimi Rover — Hardware As Built

> Status: historical physical configuration, reconciled with the 2026-08-19 source audit<br>
> Verification rule: **HARDWARE-CONFIRMED** means directly reported, measured, photographed, or demonstrated during prior development. The repository audit did **not** physically re-test those items. **CODE-CONFIRMED** describes firmware assignments only. **DOCUMENTED-NOT-VERIFIED** still requires inspection or measurement.

## 1. System overview

| Subsystem | Hardware | Qty | Status | Notes |
|---|---|---:|---|---|
| Main controller | ESP32-S3 N16R8 development board | 1 | HARDWARE-CONFIRMED | Main rover controller; native USB; product documentation states no 5 V output pin |
| Camera controller | GOOUUU ESP32-S3-CAM V1.5 | 1 | HARDWARE-CONFIRMED | Separate node; USB-C; OV3660 |
| Camera sensor | OV3660 | 1 | HARDWARE-CONFIRMED | Used for live MJPEG-style video testing |
| Motor driver | TB6612FNG breakout | 1 | HARDWARE-CONFIRMED | Drives left and right motor groups; known thermal shutdown behavior |
| Motors | TT DC gear motor, rated 3–7.2 V | 4 | HARDWARE-CONFIRMED | Two motors per side, normally paired on one H-bridge channel |
| Chassis | Two-layer transparent acrylic 4WD smart-car chassis | 1 | HARDWARE-CONFIRMED | Original two acrylic plates retained |
| Display | 1.3-inch SH1106, 128×64, I²C, white OLED | 1 | HARDWARE-CONFIRMED | Integrated into rover controller |
| Front lighting | WS2812 strip/module, 8 pixels | 1 | HARDWARE-CONFIRMED | Intended first segment of data chain |
| Center lighting | WS2812 ring, 16 pixels | 1 | HARDWARE-CONFIRMED | Mounted around center/bottom region |
| Rear lighting | WS2812 strip/module, 8 pixels | 1 | HARDWARE-CONFIRMED | Intended last segment of data chain |
| Accessory regulator | LM2596 adjustable buck converter | 1 | HARDWARE-CONFIRMED | Motor-battery input; adjusted to 5.0 V for lighting/fan |
| Bulk capacitor | 1000 µF / 16 V electrolytic | 1 | HARDWARE-CONFIRMED | Parallel across LED 5 V/GND near first lighting segment |
| Data resistor | 330 Ω, 1/4 W | 1 | HARDWARE-CONFIRMED | In series with GPIO4 → first WS2812 DI |
| Cooling fan | 5 V fan | 1+ | HARDWARE-CONFIRMED | Powered from regulated 5 V rail; exhaust/airflow placement discussed |
| Motor battery | 2 × 18650 in series | 1 pack | HARDWARE-CONFIRMED | Approximately 7–8.4 V; exact cell brand/capacity/BMS unknown |
| Logic/camera supply | USB power bank | 1 | HARDWARE-CONFIRMED | Powers ESP32 boards through USB |
| Protection | PTC resettable fuse, 1.8 A / 30 V | 1 | HARDWARE-CONFIRMED | Intended for protected power branch; exact installed position must be checked |
| External antenna | 2.4 GHz FPC antenna, seller-claimed 6 dBi, U.FL/IPEX | 1 | HARDWARE-CONFIRMED | Physically attached to camera board; active RF path unverified |
| Top cover | Custom 3D-printed curved enclosure | 1 | HARDWARE-CONFIRMED | Printed and fitted; exact filament material/finish must be confirmed |

## 2. Rover-controller GPIO allocation

The repository audit confirmed the assignments below in the current rover source. This confirms configured software use, not continuity or connector placement on the assembled vehicle.

| GPIO | Current use | Type | Verification |
|---:|---|---|---|
| 3 | OLED SCL | I²C clock | CODE-CONFIRMED; physical connection not audit-retested |
| 4 | WS2812B data, 32-pixel GRB chain | FastLED output | CODE-CONFIRMED; no legacy ordinary-LED path |
| 5 | Motor A PWMA | LEDC channel 0 | CODE-CONFIRMED; 20 kHz, 8-bit |
| 6 | Motor A AIN1 | Digital output | CODE-CONFIRMED |
| 7 | Motor A AIN2 | Digital output | CODE-CONFIRMED |
| 8 | OLED SDA | I²C data | CODE-CONFIRMED |
| 15 | TB6612 STBY | Digital output | CODE-CONFIRMED; LOW when stopped |
| 16 | Motor B PWMB | LEDC channel 1 | CODE-CONFIRMED; 20 kHz, 8-bit |
| 17 | Motor B BIN1 | Digital output | CODE-CONFIRMED |
| 18 | Motor B BIN2 | Digital output | CODE-CONFIRMED |
| 19 | Native USB D− | Reserved system pin | Not referenced by application code; native USB enabled |
| 20 | Native USB D+ | Reserved system pin | Not referenced by application code; native USB enabled |

The full rover and camera tables are maintained in [`docs/CURRENT_PINMAP.md`](docs/CURRENT_PINMAP.md).

## 3. Motor wiring

Reported topology:

```text
Left-front motor  ─┐
                   ├── TB6612 Motor A: AO1 / AO2
Left-rear motor   ─┘

Right-front motor ─┐
                   ├── TB6612 Motor B: BO1 / BO2
Right-rear motor  ─┘
```

Each side is expected to contain two TT motors connected in parallel. Confirm actual polarity and connector order on the physical rover.

Reported motor-driver logic wiring:

```text
ESP32 3V3  ── TB6612 VCC
ESP32 GND  ── TB6612 GND
GPIO5      ── PWMA
GPIO6      ── AIN1
GPIO7      ── AIN2
GPIO15     ── STBY
GPIO16     ── PWMB
GPIO17     ── BIN1
GPIO18     ── BIN2
```

Motor supply:

```text
2S 18650 positive ── TB6612 VM
2S 18650 negative ── TB6612 GND
ESP32 GND          ── same common ground
```

The left/right grouping and polarity are historical physical reports. The audit confirmed how code drives channels A/B but did not probe which motor leads are attached to AO1/AO2 or BO1/BO2.

## 4. Power distribution

### 4.1 Current architecture

```text
2S 18650 pack, approximately 7–8.4 V
        │
        ├── TB6612 VM ── four TT motors
        │
        └── LM2596 IN
                │
                └── regulated 5.0 V
                       ├── WS2812 lighting
                       └── 5 V cooling fan

USB power bank
        ├── Main ESP32-S3 through USB
        └── ESP32-S3-CAM through USB

Main ESP32-S3 3V3
        ├── TB6612 VCC
        └── SH1106 OLED VCC
```

### 4.2 Grounding

Signal grounds must share a common reference:

```text
ESP32 GND = TB6612 GND = motor-battery negative = LM2596 OUT− = WS2812 GND
```

The camera node may remain electrically isolated if it communicates only over Wi-Fi and is independently powered through USB.

### 4.3 Important power rules

- Never connect 2S 18650 voltage directly to WS2812 or a 5 V fan.
- Measure LM2596 output before connecting accessories; target 5.00 V.
- The 1000 µF capacitor is connected **in parallel**, not in series:
  - capacitor positive → 5 V;
  - capacitor negative → GND.
- The main ESP32-S3 board is documented as having no usable 5 V output pin.
- Exact fuse placement and wire gauge should be photographed and documented before release.
- **Voltage conflict:** the reported motors are rated 3–7.2 V, while a fully charged 2S pack can reach 8.4 V. PWM does not lower pulse amplitude. Verify the motor model and use an appropriate motor supply/regulator before treating this topology as a safe reproduction guide.

## 5. OLED

Display module:

- controller: SH1106;
- size: 1.3 inch;
- resolution: 128×64;
- interface: I²C;
- visible area used in top-cover design: approximately 35 × 18 mm;
- reported pins: GPIO3 SCL, GPIO8 SDA;
- power: 3.3 V from main ESP32-S3.

`CODE-CONFIRMED` reachable output is a two-second `TOKIMI / ESP32-S3 / OLED OK` splash followed by animated eyes. Motion changes the face; a stopped rover blinks and moves pupils, then enters a sleep animation after 60 seconds. Timed expressions and a flashing SOS are available from the rover API.

A textual renderer for Wi-Fi, RSSI, IP, heap, uptime, motor, camera, and extra status exists in source but has no caller. The accepted `dashboard` command returns to the animated face. Its dormant camera value initializes as `ONLINE` even though no camera-status transport exists. Battery, temperature, mission, and truthful camera telemetry are not currently displayed.

## 6. Lighting

Physical layout:

| Segment | Pixel count | Intended index range |
|---|---:|---:|
| Front strip | 8 | 0–7 |
| Center ring | 16 | 8–23 |
| Rear strip | 8 | 24–31 |
| Total | 32 | 0–31 |

Data chain:

```text
ESP32 GPIO4
    │
   330 Ω
    │
Front DI → Front DO → Center DI → Center DO → Rear DI
```

Power distribution is parallel, not daisy-chained as a single thin power path:

```text
LM2596 5 V ─┬── front +5 V
             ├── center +5 V
             └── rear +5 V

LM2596 GND ─┬── front GND
             ├── center GND
             ├── rear GND
             └── ESP32 GND
```

A 1000 µF / 16 V capacitor is placed near the first LED segment across 5 V and GND.

`CODE-CONFIRMED` implementation:

- FastLED 3.10.3, WS2812B, GRB order;
- raw brightness 40/255, approximately 15.7%, not 40%;
- boot diagnostic red → green → blue → white → off, 500 ms each;
- default white front, blue-breathing center, red rear;
- public all/front/center/rear toggles;
- internal search/recover/error scenes with no public route;
- no legacy ordinary-LED GPIO4 path.

## 7. Camera node

Hardware:

- board: GOOUUU ESP32-S3-CAM V1.5;
- image sensor: OV3660;
- power: USB-C from power bank;
- network: separate camera AP during demonstration;
- video: live stream tested;
- external flexible U.FL antenna physically connected.

Important uncertainty:

- no external RF jumper was visible in photographs;
- automatic antenna switching was not confirmed;
- firmware cannot reliably identify which physical antenna path is active;
- do not recommend RF solder modifications without board documentation.

`CODE-CONFIRMED` camera configuration is OV3660-required JPEG at HVGA 480×320, quality 18, 20 MHz XCLK, and a 10 FPS stream target. PSRAM uses two latest-frame buffers; the fallback is one when-empty DRAM buffer. Only one MJPEG stream is allowed. Camera initialization is attempted only at boot, runtime `online` state can become stale after capture failures, and the snapshot timeout argument is ignored. `/restart` is an unauthenticated state-changing GET. These are software facts, not proof of physical frame rate, latency, RF range, or sensor reliability.

## 8. 3D-printed top cover

Retained base:

- two transparent acrylic smart-car chassis plates.

Historical physical record (the printed part was not remeasured during this
audit):

| Item | Dimension |
|---|---:|
| Overall top-cover envelope | 260 × 155 mm |
| Front-to-rear M3 hole-center spacing | 203 mm |
| Left-to-right M3 hole-center spacing | 105 mm |
| Front standoff height | 15 mm |
| Rear standoff height | 55 mm |
| Height difference | 40 mm |
| Approximate roof incline | 11.15° |
| M3 clearance hole recommendation | Ø3.5 mm |
| OLED visible opening | 35 × 18 mm nominal |
| Camera module envelope | 28 × 77 mm nominal |
| Front/rear light module length | 54 mm |

The project owner also designated a separate
[Supercar V3 CAD package](hardware/cad/top-cover-v3/README.md) as the final
version to publish. Its software-checked design contract is:

| Item | Published V3 value |
|---|---:|
| Overall plan | 260 × 155 mm |
| Front-to-rear M3 hole-center spacing | 195 mm |
| Left-to-right M3 hole-center spacing | 100 mm |
| Front / rear flat contact planes | z = 15 / 55 mm |
| Nominal roof incline | 11.5922° |
| M3 clearance holes | Ø3.5 mm |
| Nominal shell thickness | 2.5 mm |
| OLED opening | 19 × 36 mm |
| Camera roof clearance | 29 × 78 mm |
| Breadboard target | 85 × 58 × 10 mm |
| Tail drop | 30 mm over the rear 32.5 mm |

The 203 × 105 mm historical record and 195 × 100 mm V3 contract conflict.
Owner correspondence identifies the V3 3MF and matching A4 1:1 sheet as the
publication pair, but it is not independent proof of physical fit. Do not
silently substitute one set of dimensions for the other: first verify the
printed 100 mm calibration line, then compare all four V3 hole centers with the
unpowered chassis.

The historical cover was described as curved with high/low roof geometry,
camera section, OLED opening, lighting integration, and ventilation. Exact
printed material, wall thickness, mass, paint, current chassis hole pattern,
and the identity/fit of the historical part versus V3 should be entered after
physical measurement.

## 9. Construction and connectors

Reported materials and practices include:

- M3 standoffs and screws;
- Dupont crimp terminals / 5016 terminals;
- JST-XH connectors discussed for locking connections;
- heat-shrink tubing;
- Kafuter K-704 or equivalent flexible silicone adhesive considered for PCB strain relief;
- breadboard and Dupont connections remain a reliability concern for a moving platform.

## 10. Measurements still required

Before publishing a definitive BOM or build guide, record:

- exact 18650 manufacturer, model, capacity, maximum discharge current, and protection/BMS status;
- actual idle, cruise, acceleration, turn, and stall current;
- LM2596 output voltage under load;
- TB6612 surface temperature versus run time;
- final rover mass;
- actual top-cover filament material and print settings;
- current chassis hole centers and physical fit of the published V3
  195 × 100 mm pattern versus the historical 203 × 105 mm record;
- camera stream resolution, FPS, and latency;
- Wi-Fi range and RSSI;
- whether the external camera antenna is actually active;
- actual wire gauges and fuse position;
- current firmware commit hash and build environment;
- observed worst-case motor-stop latency under request reordering, slow HTTP, page close, and Wi-Fi loss;
- whether the 3–7.2 V motors are being exposed to an 8.4 V full-charge supply and the approved resolution;
- whether current wiring still matches every code-confirmed GPIO assignment.

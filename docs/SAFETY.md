# Safety

> **Prototype warning:** Tokimi Rover V0.1 is not a certified product, safety controller, or production vehicle. The current repository was compiled and audited, but the assembled hardware was not physically re-tested during that audit.

## Non-negotiable operating rules

1. Lift all driven wheels before first power-on, after rewiring, and after any motor-control change.
2. Keep an immediate **physical motor-power disconnect** within reach. A browser button is not an emergency-stop device.
3. Do not operate unattended, near people, animals, traffic, edges, flammable material, or anything that unexpected movement could damage.
4. Disconnect the motor battery before flashing, rewiring, or touching the drive electronics.
5. Do not perform intentional stall tests with the current uninstrumented motor branch and undocumented battery pack.
6. Stop immediately if there is heat, odor, swelling, discoloration, intermittent drive, unusual sound, or repeated reset behavior.

## Control and STOP limitations

The implemented stop output sets both PWM channels to zero, all direction inputs LOW, and TB6612 STBY LOW. That output is used at boot and by several software fault paths, but the end-to-end control system has unresolved limitations:

- The browser sends movement requests without serializing or cancelling earlier requests. A movement request already in flight can arrive after STOP and re-enable motion.
- The command watchdog uses a 750 ms threshold checked by the main loop after synchronous HTTP handling. It is not a guaranteed maximum stopping time.
- Closing the control page does not necessarily disassociate the phone from the AP. If a station remains associated, the rover relies on the heartbeat timeout rather than immediate station-loss STOP.
- Missing/invalid movement and speed inputs stop the rover; missing/invalid lighting or expression inputs do not.
- Unknown HTTP routes stop the rover, but this is not a substitute for a dedicated, independently tested safety channel.
- The rover AP and HTTP API have no application authentication or TLS. Anyone with network access can issue commands.

Treat the physical power disconnect as the only current emergency action that does not depend on browser, Wi-Fi, HTTP scheduling, or firmware execution.

Before any free-running test, verify each stop path with the wheels clear and record observed worst-case latency. Do not claim a 750 ms guaranteed stop until an independent hard deadline is implemented and measured under slow/malformed HTTP traffic and maximum UI/display/lighting load.

## Motor driver and motor supply

The present TB6612FNG has a field history consistent with overload or thermal shutdown under sustained four-motor load: propulsion stopped and later returned after cooling. No current, driver-temperature, or FAULT signal is available to the firmware.

Current code facts:

- PWM ceiling: **80%**, or maximum duty `204/255`;
- default requested speed: 30%, approximately 24% physical duty;
- no soft start;
- no enforced direction-change dead time;
- no stall detection, current limiting, or thermal derating.

Earlier project guidance proposed a temporary 50–60% physical ceiling and reversal dead time. Those mitigations are **not implemented** in V0.1. Do not mistake a recommendation for an active protection mechanism.

Avoid prolonged pivot turns, rapid reversals, added payload, blocked wheels, carpet/high-drag surfaces, and long continuous runs. Cooling airflow and a heatsink cannot compensate for an undersized driver or unknown stall current. The permanent path is to measure real current and choose a driver with adequate continuous and peak margin.

The reported TT motors are rated 3–7.2 V, while the documented 2S pack can reach 8.4 V. PWM reduces average delivered energy but does not reduce the amplitude of each supply pulse. Verify the actual motor model and use an appropriate motor supply or regulator before calling this power design reproducible.

## 18650 battery safety

The current records do not identify the cells' manufacturer, model, capacity, discharge rating, age, matching, or BMS/protection status. Treat the pack as an unresolved critical risk.

- Use matched, reputable cells appropriate for the measured load.
- Confirm a suitable 2S protection/balancing arrangement and safe charging procedure.
- Never mix cells of different type, capacity, age, or state of charge.
- Inspect holders, insulation, polarity, wiring, and fuse placement before use.
- Keep the pack away from sharp printed parts, motor heat, loose hardware, and crush points.
- Do not charge inside the rover or leave charging/powered batteries unattended until the pack and charging system are fully documented and reviewed.
- If a cell is damaged, swollen, leaking, unusually hot, or mechanically compromised, isolate it safely and follow local hazardous-battery guidance.

## Power domains

Documented topology:

```text
2S battery ─┬─ TB6612 VM → motors
            └─ LM2596 → regulated 5 V → WS2812 + fan

USB power bank ─┬─ rover ESP32-S3
                └─ camera ESP32-S3-CAM
```

Rules:

- Never connect raw 2S voltage directly to WS2812 pixels, a 5 V fan, or a 5 V controller input.
- With accessory loads disconnected, measure LM2596 OUT+/OUT−, adjust to 5.00 V, and verify again under load before connecting accessories.
- Connect the 1000 µF capacitor in parallel across the LED 5 V/GND rail with correct polarity, never in series.
- The rover ESP32, TB6612 logic, motor-battery negative, LM2596 output ground, and WS2812 ground need the documented common signal reference.
- The Wi-Fi-only camera may remain electrically isolated on its own USB supply.
- Verify wire gauge and fuse location. Do not carry motor current through breadboard power rails or marginal friction contacts.
- Power off before connecting or disconnecting the external camera antenna.

## Moving-platform wiring

Breadboards and loose Dupont connections are prototype-only on a vibrating vehicle. A loose high-current path can heat, drop voltage, reset the controller, reverse apparent polarity, or create intermittent motion.

Use suitable direct wiring for motor current, locking connectors where practical, insulation, strain relief, and secure mounting. Photograph final routing and label connector polarity before public reproduction instructions are considered complete.

## Lighting

The 32 WS2812 pixels use an externally regulated 5 V rail, a documented 330 Ω series data resistor, and a 1000 µF bulk capacitor near the first segment. Current firmware sets raw global brightness to 40/255, but that is not a power fuse or current limiter.

Check voltage drop, connector temperature, ground integrity, and 3.3 V data-level margin. Add a suitable logic-level buffer if behavior is unstable; do not “fix” data problems by raising the 5 V rail.

## Camera and radio

- Camera and rover networks are independent, but can still interfere in the same 2.4 GHz spectrum.
- The camera's external antenna is physically reported as connected, but the active RF path is unverified.
- Do not move RF components or solder antenna-selection parts without board-specific documentation.
- The camera API is unauthenticated, and `GET /restart` remotely reboots the camera.
- Camera `online` status can remain stale after runtime capture failure. Never use it as a safety interlock.
- Camera failure must remain unable to delay or block motor stop.

## Missing protections

V0.1 has no confirmed:

- battery-voltage or state-of-charge measurement;
- motor-current measurement;
- driver, motor, battery, enclosure, or regulator temperature measurement;
- over-current, stall, thermal, or low-voltage automatic stop;
- obstacle/person detection;
- safety-rated radio link or emergency-stop circuit;
- waterproofing or ingress rating;
- regulatory or radio certification for the assembled rover.

Do not infer any of these protections from the OLED, camera UI, diagnostic logs, or planned roadmap.

## Minimum pre-drive record

Before allowing the rover to run on the ground, record at least:

- exact battery cells, BMS/protection, charger, and fuse position;
- no-load and loaded LM2596 voltage;
- motor polarity for each side;
- idle, start, straight-drive, pivot, and peak current using an appropriate safe method;
- TB6612 and battery temperature versus time;
- observed stop latency for release, browser hide/close, Wi-Fi loss, malformed command, and slow-request conditions;
- wiring photographs and actual wire gauges;
- tested firmware commit and local configuration revision;
- test surface, rover mass, payload, ambient temperature, and duration.

Until those measurements exist, all free-running operation remains experimental.

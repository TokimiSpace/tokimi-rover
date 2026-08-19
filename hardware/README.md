# Tokimi Rover hardware

This directory separates currently available artifacts from planned release
assets. Repository diagrams document the intended/currently reported wiring;
they are not a substitute for checking the physical rover before power-up.

## Available now

- [Wiring diagram (SVG)](wiring/tokimi-rover-wiring.svg)
- [Wiring preview (PNG)](wiring/tokimi-rover-wiring.png)
- [V0.1 BOM](bom/BOM.md)
- [As-built report](../HARDWARE_AS_BUILT.md)
- [Safety notes](../docs/SAFETY.md)

## Still required

- editable top-cover CAD and verified print exports;
- final photos of every connector, fuse, regulator, and ground path;
- exact cell, BMS, wire-gauge, connector, motor, fan, and fuse part numbers;
- measured current, voltage, temperature, mass, runtime, and motor-driver endurance data.

Do not infer that a wire shown in a diagram was physically verified. In
particular, confirm motor voltage suitability, the LM2596 output, fuse placement,
cell protection, and common-ground routing before use.

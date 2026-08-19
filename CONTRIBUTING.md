# Contributing

Tokimi Rover is a physical machine with safety-relevant motor control. Start by
reading [AGENTS.md](AGENTS.md), [docs/SAFETY.md](docs/SAFETY.md), and the current
implementation documents under `docs/CURRENT_*.md`.

## Before opening a pull request

1. Open or reference an issue for GPIO, public API, radio, power, or motor-safety changes.
2. Keep the rover controller and camera node independent.
3. Never commit the local `include/local_config.h` or `include/camera_config.h`, credentials, private network settings, build artifacts, or private media.
4. Build every affected PlatformIO environment.
5. Describe hardware tests separately from compilation; never label an untested hardware result as verified.
6. Preserve motor STOP behavior and document any timing or compatibility change.
7. Update the current implementation, pin-map, API, and safety documents when public behavior changes.

## Pull-request evidence

Include:

- the affected controller and hardware revision;
- build command and complete result;
- tests performed, including whether wheels were lifted;
- before/after API or GPIO behavior;
- remaining uncertainty and rollback instructions.

Small, reviewable changes are preferred. Do not combine enclosure, power,
network, UI, and motor-control changes unless they are inseparable.

## Licensing contributions

By intentionally submitting a contribution for inclusion, you agree to license
it under the license that `LICENSES.md` assigns to that path and material type:
Apache-2.0 for software, CERN-OHL-W-2.0 for identified hardware source, or
CC-BY-4.0 for documentation and original diagrams. You must have the right to
make that grant, preserve applicable third-party notices, and identify any
material that is not your original work. Do not submit assets with unknown or
incompatible rights.

# Licensing

The project owner approved this multi-license structure on 2026-08-19. The
repository is open source, but it is not licensed as one indivisible work under
one license. Use the path-specific rules below.

## License map

| Material | SPDX identifier | Full license text |
|---|---|---|
| Firmware, software, build configuration, CI, and scripts | `Apache-2.0` | [Apache License 2.0](LICENSE) |
| Hardware design source and manufacturing source explicitly identified below | `CERN-OHL-W-2.0` | [CERN Open Hardware Licence Version 2 — Weakly Reciprocal](LICENSES/CERN-OHL-W-2.0.txt) |
| Documentation and original diagrams | `CC-BY-4.0` | [Creative Commons Attribution 4.0 International](LICENSES/CC-BY-4.0.txt) |

The root [LICENSE](LICENSE) is an unmodified copy of Apache License 2.0 so
GitHub and software tooling can identify the primary software license. Copies
of all three official texts are retained under `LICENSES/`.

### Apache-2.0 software scope

Apache-2.0 applies to:

- source and header files under `firmware/**/src/` and
  `firmware/**/include/`;
- both `platformio.ini` files and the camera partition CSV;
- executable and support files under `scripts/`;
- repository automation and templates under `.github/`;
- `.editorconfig`, `.gitattributes`, `.gitignore`, and future software/build
  configuration not carrying a different notice.

Markdown documentation inside a firmware project is a documentation exception
and uses CC-BY-4.0; the directory-level `firmware/LICENSE.md` notice itself is
part of the Apache-2.0 software distribution metadata.

### CERN-OHL-W-2.0 hardware scope

CERN-OHL-W-2.0, exact version 2.0 only, applies to:

- `hardware/bom/BOM.md` as hardware design/manufacturing source;
- the design/generator/check source, editable BLEND, 3MF/STL/OBJ exports, A4
  fit-check template, validation data, renders, requirements, and checksum
  manifest under `hardware/cad/top-cover-v3/`, except its explanatory
  `README.md` and `NOTICE.md`;
- future editable CAD, schematic, PCB, mechanical, fabrication, and
  manufacturing source placed under `hardware/cad/` or explicitly marked with
  `SPDX-License-Identifier: CERN-OHL-W-2.0`.

`hardware/cad/README.md` and `hardware/cad/top-cover-v3/{README,NOTICE}.md` are
explanatory-documentation exceptions licensed under CC-BY-4.0. The
CERN-OHL-W-2.0 Source Location for currently published Covered Source is
[`https://github.com/TokimiSpace/tokimi-rover/tree/main/hardware`](https://github.com/TokimiSpace/tokimi-rover/tree/main/hardware).
A tagged release should use a tag-specific Source Location in its release
manifest.

### CC-BY-4.0 documentation scope

CC-BY-4.0 applies to:

- original Markdown documentation at the repository root;
- project-authored documentation and archival metadata under `docs/`, including
  the retained JSON manifest;
- firmware README and test-procedure Markdown files;
- `hardware/README.md`, `hardware/cad/README.md`,
  `hardware/cad/top-cover-v3/{README,NOTICE}.md`, and other explanatory hardware
  documentation except the hardware source noted above;
- both versions of the original Tokimi Rover wiring diagram under
  `hardware/wiring/`;
- project-authored explanatory text under `media/`.

For CC-BY-4.0 attribution, identify the work or file, credit **Tokimi Rover
contributors**, link to the source repository when reasonably practical, link
to CC-BY-4.0, and indicate modifications. Attribution does not imply Tokimi
endorsement or official-product status.

## File notices and priority

A file-level SPDX or third-party notice takes priority over the path defaults
above. License texts themselves retain their licensors' stated copyright and
license status. Each contributor licenses only rights they are authorized to
grant; existing third-party copyright, patent, trademark, and attribution
notices must be preserved.

PlatformIO, Arduino-ESP32, U8g2, FastLED, toolchains, and other downloaded
dependencies are not vendored by this repository and retain their own
licenses. A binary release must include the third-party notices required by the
exact resolved dependency set.

## Trademarks

The licenses above do not grant trademark rights in Tokimi, 時見數位科技,
Tokimi logos, or the “Official Tokimi Rover” designation. Necessary
attribution, faithful reproduction of licensed material, and factual reference
to the project's origin remain permitted as described in
[TRADEMARKS.md](TRADEMARKS.md).

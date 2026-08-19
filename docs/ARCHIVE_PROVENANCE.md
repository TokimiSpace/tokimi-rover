# Archive Provenance

> Evidence date: 2026-08-19<br>
> Purpose: preserve the identity of the supplied handoff/source archives without claiming a Git history that did not exist.

## Supplied archives

The repository audit began from three ZIP archives located together in the working folder. Their SHA-256 hashes were recorded before documentation restructuring:

| Archive | SHA-256 |
|---|---|
| `tokimi-camera-2026-08-19.zip` | `bccca5dc7191854ed6301620f07fc5f667e9746466954fd657268fdbca8826a7` |
| `tokimi-rover-handoff-v0.1.zip` | `f7c32b418531ecec4f898941bca9af54bdd2a1d5464bee0f491c2d8bba8972d4` |
| `tokimi-rover-source-2026-08-19.zip` | `befe38d8761f93fa875f6373f64f517a84553d058161a7cfd6dde882e17202be` |

These hashes identify the ZIP byte streams only. They do not establish authorship, licensing, release approval, or a relationship to a future Git commit unless a signed release manifest explicitly makes that connection.

## Repository assembly

The supplied materials did not include usable Git metadata, a source commit ID, a signed tag, a dependency lockfile, or a signed manifest binding documentation to both firmware archives. The combined GitHub-oriented tree was therefore assembled as a new working repository from:

- rover controller source;
- camera node source;
- handoff project/context documents;
- existing hardware notes/assets;
- the 2026-08-19 read-only implementation audit;
- subsequent public-repository hygiene and documentation changes.

`docs/archive/HANDOFF_MANIFEST.json` is retained as historical input metadata. Its `pre-audit` status describes the original handoff, not the current documentation. `docs/archive/ROVER_CONTROLLER_ORIGINAL_CONTEXT.md` is likewise historical and must not override current source or `docs/CURRENT_*.md`.

## Audit handling

During the read-only audit:

- source archives were extracted and built only in temporary working locations;
- no firmware was uploaded;
- no source ZIP or handoff ZIP was modified;
- no motors, display, lighting, camera, battery, power rail, antenna, thermal behavior, or Wi-Fi range were physically tested;
- both PlatformIO firmware builds succeeded;
- test commands found no test directories and ended with `TestDirNotExistsError`.

Public-repository packaging after the audit changes the working tree and is not covered by the original ZIP hashes.
The public Git history begins with commit `0fba3b5`; it is a packaging origin,
not evidence that the supplied archives had an earlier verified Git history.

## Supercar V3 CAD import

The top-cover package was not present in the three ZIP archives above. It was
curated separately on 2026-08-19 from the project owner's local design
repository at commit
`832607fa7774f4a0d7127bf7e1cfed78f55e4ddf`; that local repository had no
configured remote. The owner identified the following files as the final pair:

| Owner-selected artifact | Original SHA-256 |
|---|---|
| `tokimi_rover_top_cover_supercar_v3_195x100mm.3mf` | `63705ecb922497ba21377872e016b9f1f347514e83f36552bd44460a31844ad6` |
| `tokimi_rover_top_cover_supercar_v3_m3_fitcheck_195x100mm_A4_1to1.pdf` | `7d6b6a89d0019a412369d6b36be1a25f1878ef68775be773c293c518a9887687` |

The public package preserves those two byte streams and their hashes. It also
includes the minimum V3 procedural source chain, checked mesh exports, a
self-contained editable Blender scene, sanitized validation data, and preview
renders. Publication changes replaced machine-specific paths, removed preview
metadata, localized Blender's bundled node-group dependency, and added SPDX
notices and documentation. The source geometry was rebuilt with Blender 5.2.0
LTS and its canonical triangle set was compared with the checked release mesh.

The original CAD Git history, unrelated variants, temporary files, private
correspondence screenshot, and unselected design outputs were not imported.
The screenshot identifies the owner's selection but is neither redistributed
nor treated as independent proof of physical fit. The historical as-built
record says approximately 203 × 105 mm hole centers while published V3 uses
195 × 100 mm; this unresolved physical conflict is recorded in
`KNOWN_ISSUES.md`.

## Creating release provenance

Before publishing a tagged release:

1. identify the exact release commit in the canonical public repository;
2. review every staged file, including binary assets and history-preservation files;
3. make a clean build from the exact release commit with local secrets excluded;
4. record the commit ID, tag, PlatformIO/platform/framework versions, and build sizes;
5. hash each distributed source archive and firmware artifact;
6. record physical test hardware revision and results separately from build evidence;
7. create a release manifest that binds the tag/commit, artifacts, hashes, licenses, and test record;
8. sign the tag/manifest if the project adopts a signing policy.

Until those steps are complete, describe this tree as derived from the listed archives, not as a continuation of a verified upstream Git history.

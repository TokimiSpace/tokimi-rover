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

## Creating release provenance

Before publishing a tagged release:

1. create the repository in the intended owner/organization account;
2. review every staged file, including binary assets and history-preservation files;
3. make a clean build from the exact release commit with local secrets excluded;
4. record the commit ID, tag, PlatformIO/platform/framework versions, and build sizes;
5. hash each distributed source archive and firmware artifact;
6. record physical test hardware revision and results separately from build evidence;
7. create a release manifest that binds the tag/commit, artifacts, hashes, licenses, and test record;
8. sign the tag/manifest if the project adopts a signing policy.

Until those steps are complete, describe this tree as derived from the listed archives, not as a continuation of a verified upstream Git history.

#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: Apache-2.0

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"

required_files="
README.md
README.zh-TW.md
AGENTS.md
CONTRIBUTING.md
SECURITY.md
LICENSES.md
LICENSE
LICENSES/Apache-2.0.txt
LICENSES/CERN-OHL-W-2.0.txt
LICENSES/CC-BY-4.0.txt
firmware/LICENSE.md
docs/LICENSE.md
hardware/LICENSE.md
scripts/LICENSE.md
.github/LICENSE.md
docs/CURRENT_IMPLEMENTATION.md
docs/CURRENT_PINMAP.md
docs/CURRENT_API.md
docs/BUILD_AND_FLASH.md
docs/SAFETY.md
firmware/rover-controller/platformio.ini
firmware/rover-controller/include/local_config.example.h
firmware/camera-node/platformio.ini
firmware/camera-node/include/camera_config.h.example
"

for required_file in $required_files; do
  if [ ! -f "$required_file" ]; then
    echo "missing required file: $required_file" >&2
    exit 1
  fi
done

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  tracked_secrets=$(git ls-files \
    'firmware/rover-controller/include/local_config.h' \
    'firmware/camera-node/include/camera_config.h')
  if [ -n "$tracked_secrets" ]; then
    echo "tracked local credential file(s):" >&2
    echo "$tracked_secrets" >&2
    exit 1
  fi
fi

python3 - <<'PY'
from hashlib import sha256
from pathlib import Path

expected = {
    "LICENSE": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    "LICENSES/Apache-2.0.txt": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    "LICENSES/CERN-OHL-W-2.0.txt": "9682f98d4fe43f33e618a14da9b324f7b4c170fdc811ea261041898e4e0744ce",
    "LICENSES/CC-BY-4.0.txt": "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
}

for name, wanted in expected.items():
    actual = sha256(Path(name).read_bytes()).hexdigest()
    if actual != wanted:
        raise SystemExit(f"modified or unexpected official license text: {name}")
PY

echo "repository structure check passed"

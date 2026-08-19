#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: Apache-2.0

"""Check local Markdown links without making network requests."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")


def target_path(markdown: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0]
    if not target or target.startswith(SKIP_PREFIXES):
        return None
    target = unquote(target)
    if target.startswith("/"):
        return ROOT / target.lstrip("/")
    return markdown.parent / target


def main() -> int:
    failures: list[str] = []
    for markdown in sorted(ROOT.rglob("*.md")):
        if any(part in {".git", ".pio"} for part in markdown.parts):
            continue
        text = markdown.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = target_path(markdown, match.group(1))
            if target is not None and not target.exists():
                relative_source = markdown.relative_to(ROOT)
                failures.append(f"{relative_source}: missing {match.group(1)}")

    if failures:
        print("local Markdown link check failed:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    print("local Markdown link check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

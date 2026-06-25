#!/usr/bin/env python3
"""Validate Neo Remix game folders against manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEO = ROOT / "neo-remix"
MANIFEST = NEO / "manifests" / "games.json"


def main() -> int:
    if not MANIFEST.exists():
        print("ERROR: manifests/games.json missing — run build_manifest.py")
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    for gid, game in manifest["games"].items():
        game_root = NEO / "games" / gid
        py_files = list(game_root.glob("*.py"))
        if not py_files:
            errors.append(f"{gid}: missing entry .py in {game_root}")

        for entry in game["images"]:
            path = NEO / entry["neo_path"]
            if not path.exists():
                errors.append(f"{gid}: missing image {path.relative_to(NEO)}")
            elif entry.get("neo_status") == "pending":
                warnings.append(f"{gid}: image pending {entry['id']}")

        for bucket in ("sounds", "music"):
            for entry in game[bucket]:
                path = NEO / entry["neo_path"]
                if not path.exists():
                    errors.append(f"{gid}: missing {bucket} {path.relative_to(NEO)}")

    print(f"Validated {len(manifest['games'])} games")
    print(f"  errors:   {len(errors)}")
    print(f"  warnings: {len(warnings)}")

    for msg in errors[:20]:
        print(f"  ERROR: {msg}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

    for msg in warnings[:10]:
        print(f"  WARN:  {msg}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

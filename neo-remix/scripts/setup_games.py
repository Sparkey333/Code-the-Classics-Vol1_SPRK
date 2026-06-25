#!/usr/bin/env python3
"""Copy classic game sources into neo-remix/games/ with Neo branding."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEO = ROOT / "neo-remix"
MANIFEST = NEO / "manifests" / "games.json"

TITLE_MAP = {
    "Boing!": "Neo Boing",
    "Infinite Bunner": "Neo Bunner",
    "Cavern": "Neo Cavern",
    "Myriapod": "Neo Myriapod",
    "Substitute Soccer": "Neo Soccer",
}


def patch_source(text: str, neo_title: str) -> str:
    text = re.sub(
        r'(TITLE\s*=\s*["\'])([^"\']+)(["\'])',
        rf"\g<1>{neo_title}\g<3>",
        text,
        count=1,
    )
    banner = (
        "# Neo Remix edition — assets in images/, sounds/, music/\n"
        "# Style guide: neo-remix/STYLE_GUIDE.md\n"
    )
    if "Neo Remix edition" not in text:
        text = banner + text
    return text


def main() -> None:
    if not MANIFEST.exists():
        raise SystemExit("Run build_manifest.py first")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for gid, game in manifest["games"].items():
        src_dir = ROOT / game["source_dir"]
        dst_dir = NEO / "games" / gid
        dst_dir.mkdir(parents=True, exist_ok=True)

        py_src = next(src_dir.glob("*.py"))
        py_dst = dst_dir / py_src.name
        patched = patch_source(py_src.read_text(encoding="utf-8"), game["neo_title"])
        py_dst.write_text(patched, encoding="utf-8")
        print(f"  {gid}: {py_dst.relative_to(ROOT)}")

    print("Game sources staged under neo-remix/games/")


if __name__ == "__main__":
    main()

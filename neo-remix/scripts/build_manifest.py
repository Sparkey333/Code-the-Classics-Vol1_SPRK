#!/usr/bin/env python3
"""Build machine-readable asset manifests for the Neo Remix collection."""

from __future__ import annotations

import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASSICS = ROOT
NEO = ROOT / "neo-remix"
MANIFEST_DIR = NEO / "manifests"

GAME_DIRS = {
    "boing": "boing-master",
    "bunner": "bunner-master",
    "cavern": "cavern-master",
    "myriapod": "myriapod-master",
    "soccer": "soccer-master",
}

NEO_TITLES = {
    "boing": "Neo Boing",
    "bunner": "Neo Bunner",
    "cavern": "Neo Cavern",
    "myriapod": "Neo Myriapod",
    "soccer": "Neo Soccer",
}

ACCENT_COLORS = {
    "boing": "#00F5FF",
    "bunner": "#7CFF6B",
    "cavern": "#FF2E97",
    "myriapod": "#FFD447",
    "soccer": "#6BFF8A",
}

AUDIO_EXTS = {".ogg", ".wav", ".mp3"}


def png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            return None
        f.read(8)
        return struct.unpack(">II", f.read(8))


def parse_title(py_path: Path) -> str:
    text = py_path.read_text(encoding="utf-8")
    match = re.search(r'TITLE\s*=\s*["\']([^"\']+)', text)
    return match.group(1) if match else py_path.stem


def parse_resolution(py_path: Path) -> dict[str, int]:
    text = py_path.read_text(encoding="utf-8")
    width = re.search(r"WIDTH\s*=\s*(\d+)", text)
    height = re.search(r"HEIGHT\s*=\s*(\d+)", text)
    return {
        "width": int(width.group(1)) if width else 0,
        "height": int(height.group(1)) if height else 0,
    }


def collect_game(game_id: str, source_dir: str) -> dict:
    src = CLASSICS / source_dir
    py_files = sorted(src.glob("*.py"))
    if not py_files:
        raise FileNotFoundError(f"No Python entry point in {src}")
    py = py_files[0]

    images = []
    for img in sorted((src / "images").glob("*.png")):
        size = png_size(img)
        images.append(
            {
                "id": img.stem,
                "source": f"{source_dir}/images/{img.name}",
                "neo_path": f"games/{game_id}/images/{img.name}",
                "width": size[0] if size else None,
                "height": size[1] if size else None,
                "neo_status": "pending",
            }
        )

    sounds = []
    music = []
    for folder, bucket in (("sounds", sounds), ("music", music)):
        d = src / folder
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in AUDIO_EXTS:
                continue
            bucket.append(
                {
                    "id": f.stem,
                    "source": f"{source_dir}/{folder}/{f.name}",
                    "neo_path": f"games/{game_id}/{folder}/{f.name}",
                    "format": f.suffix.lstrip(".").lower(),
                    "neo_status": "pending",
                }
            )

    return {
        "id": game_id,
        "original_title": parse_title(py),
        "neo_title": NEO_TITLES[game_id],
        "accent_color": ACCENT_COLORS[game_id],
        "source_dir": source_dir,
        "entry_point": f"games/{game_id}/{py.name}",
        "resolution": parse_resolution(py),
        "counts": {
            "images": len(images),
            "sounds": len(sounds),
            "music": len(music),
        },
        "images": images,
        "sounds": sounds,
        "music": music,
    }


def main() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    games = {gid: collect_game(gid, folder) for gid, folder in GAME_DIRS.items()}
    total_images = sum(g["counts"]["images"] for g in games.values())
    total_sounds = sum(g["counts"]["sounds"] for g in games.values())
    total_music = sum(g["counts"]["music"] for g in games.values())

    catalog = {
        "collection": "neo-remix",
        "version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_book": "Code the Classics Vol I (2nd ed.)",
        "totals": {
            "games": len(games),
            "images": total_images,
            "sounds": total_sounds,
            "music": total_music,
        },
        "games": games,
    }

    (MANIFEST_DIR / "games.json").write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
    )

    # Per-game slim manifests for artists
    for gid, game in games.items():
        slim = {k: game[k] for k in game if k != "images"}
        slim["image_ids"] = [i["id"] for i in game["images"]]
        slim["sound_ids"] = [s["id"] for s in game["sounds"]]
        slim["music_ids"] = [m["id"] for m in game["music"]]
        (MANIFEST_DIR / f"{gid}.json").write_text(
            json.dumps(slim, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Wrote manifests for {len(games)} games")
    print(f"  images: {total_images}")
    print(f"  sounds: {total_sounds}")
    print(f"  music:  {total_music}")


if __name__ == "__main__":
    main()

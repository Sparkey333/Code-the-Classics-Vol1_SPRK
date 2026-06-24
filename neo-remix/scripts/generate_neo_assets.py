#!/usr/bin/env python3
"""Apply Neo Remix visual treatment to classic sprites (procedural pass v1)."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
NEO = ROOT / "neo-remix"
MANIFEST = NEO / "manifests" / "games.json"
SHARED = NEO / "shared"

PALETTE = {
    "void": (11, 14, 23, 255),
    "deep": (21, 27, 46, 255),
    "cyan": (0, 245, 255, 255),
    "magenta": (255, 46, 151, 255),
    "gold": (255, 212, 71, 255),
    "white": (232, 238, 255, 255),
    "violet": (107, 76, 255, 255),
}

ACCENT_RGB = {
    "boing": PALETTE["cyan"][:3],
    "bunner": (124, 255, 107),
    "cavern": PALETTE["magenta"][:3],
    "myriapod": PALETTE["gold"][:3],
    "soccer": (107, 255, 138),
}


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise SystemExit("Run build_manifest.py first")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def recolor_flat(img: Image.Image, accent: tuple[int, int, int]) -> Image.Image:
    """Map non-transparent pixels to a neo flat + rim look."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            lum = (r * 299 + g * 587 + b * 114) / 1000
            if lum > 200:
                fill = PALETTE["white"][:3]
            elif lum > 120:
                fill = accent
            elif lum > 60:
                fill = tuple(max(0, c - 40) for c in accent)
            else:
                fill = PALETTE["deep"][:3]
            opx[x, y] = (*fill, a)

    # Neon rim via edge detect on alpha
    alpha = out.split()[-1]
    edge = alpha.filter(ImageFilter.FIND_EDGES)
    glow = Image.new("RGBA", (w, h), (*accent, 0))
    glow.putalpha(edge)
    glow = glow.filter(ImageFilter.GaussianBlur(1))
    return Image.alpha_composite(glow, out)


def make_digit(img: Image.Image, accent: tuple[int, int, int]) -> Image.Image:
    """Seven-segment style digit from classic glyph."""
    img = img.convert("RGBA")
    w, h = img.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    # Bounding box of opaque pixels
    bbox = img.getbbox()
    if not bbox:
        return canvas
    bx0, by0, bx1, by1 = bbox
    cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2
    draw.rounded_rectangle(
        [bx0 - 1, by0 - 1, bx1 + 1, by1 + 1],
        radius=2,
        outline=(*accent, 255),
        width=1,
        fill=(*PALETTE["deep"][:3], 200),
    )
    # Stamp simplified bright core
    core = img.point(lambda p: min(255, p + 40) if p > 0 else 0)
    canvas = Image.alpha_composite(canvas, core)
    return canvas


def process_image(src: Path, dst: Path, game_id: str, asset_id: str) -> None:
    accent = ACCENT_RGB.get(game_id, PALETTE["cyan"][:3])
    img = Image.open(src)
    if asset_id.startswith("digit"):
        out = make_digit(img, accent)
    elif asset_id == "blank":
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    else:
        out = recolor_flat(img, accent)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, optimize=True)


def copy_audio(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def generate_shared_digits(manifest: dict) -> None:
    """Build one shared neon digit set from Boing (smallest digit set)."""
    digits_dir = SHARED / "images"
    digits_dir.mkdir(parents=True, exist_ok=True)
    boing_images = {
        i["id"]: ROOT / i["source"] for i in manifest["games"]["boing"]["images"]
    }
    for i in range(30):
        key = f"digit{i:02d}"
        if key not in boing_images:
            continue
        process_image(boing_images[key], digits_dir / f"{key}.png", "boing", key)


def generate_hub_art() -> None:
    hub_images = NEO / "images"
    hub_images.mkdir(parents=True, exist_ok=True)
    shared_images = SHARED / "images"
    shared_images.mkdir(parents=True, exist_ok=True)

    # Logo plate
    logo = Image.new("RGBA", (800, 200), PALETTE["void"])
    draw = ImageDraw.Draw(logo)
    draw.rounded_rectangle([20, 20, 780, 180], radius=16, fill=PALETTE["deep"], outline=PALETTE["cyan"], width=2)
    draw.text((60, 70), "NEO REMIX", fill=PALETTE["cyan"])
    draw.text((60, 110), "Classics, recharged.", fill=PALETTE["white"])
    logo.save(hub_images / "hub_logo.png")
    logo.save(shared_images / "hub_logo.png")

    # Card template
    card = Image.new("RGBA", (360, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([0, 0, 359, 219], radius=12, fill=PALETTE["deep"], outline=PALETTE["violet"], width=2)
    card.save(shared_images / "hub_card.png")

    # Palette swatch sheet for artists
    swatch = Image.new("RGBA", (320, 64), PALETTE["void"])
    draw = ImageDraw.Draw(swatch)
    colors = ["void", "deep", "cyan", "magenta", "gold", "white", "violet"]
    for i, name in enumerate(colors):
        x = i * 44 + 8
        draw.rectangle([x, 12, x + 36, 52], fill=PALETTE[name][:3])
    swatch.save(shared_images / "palette_swatch.png")


def process_game(manifest: dict, game_id: str, audio_only: bool = False) -> tuple[int, int]:
    game = manifest["games"][game_id]
    img_count = snd_count = 0

    if not audio_only:
        for entry in game["images"]:
            src = ROOT / entry["source"]
            dst = ROOT / "neo-remix" / entry["neo_path"]
            process_image(src, dst, game_id, entry["id"])
            entry["neo_status"] = "generated_v1"
            img_count += 1

    for bucket in ("sounds", "music"):
        for entry in game[bucket]:
            src = ROOT / entry["source"]
            dst = ROOT / "neo-remix" / entry["neo_path"]
            copy_audio(src, dst)
            entry["neo_status"] = "placeholder_copy"
            snd_count += 1

    return img_count, snd_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=list(ACCENT_RGB) + ["all"], default="all")
    parser.add_argument("--audio-only", action="store_true")
    parser.add_argument("--skip-shared", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest()
    games = list(ACCENT_RGB) if args.game == "all" else [args.game]

    if not args.skip_shared and not args.audio_only:
        generate_shared_digits(manifest)
        generate_hub_art()

    totals = {"images": 0, "audio": 0}
    for gid in games:
        ic, sc = process_game(manifest, gid, audio_only=args.audio_only)
        totals["images"] += ic
        totals["audio"] += sc
        print(f"{gid}: {ic} images, {sc} audio files")

    manifest["asset_pass"] = "neo_generated_v1"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Done — {totals['images']} images, {totals['audio']} audio (placeholder copy)")


if __name__ == "__main__":
    main()

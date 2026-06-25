#!/usr/bin/env python3
"""Generate Neo Remix sprites via linked AI APIs with variation + best-pick scoring."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow `from lib.*` when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.api_config import KEY_ENV, load_settings, mask_key
from lib.providers import get_provider
from lib.sprite_post import fit_to_canvas, quantize_neo
from lib.sprite_prompts import build_prompt, variation_seeds
from lib.sprite_score import load_image_bytes, pick_best

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NEO = ROOT / "neo-remix"
MANIFEST = NEO / "manifests" / "games.json"
AI_LOG = NEO / "manifests" / "ai_generation_log.jsonl"
VARIATIONS_DIR = NEO / "variations"


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise SystemExit("Run build_manifest.py first")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(manifest: dict) -> None:
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def log_generation(record: dict) -> None:
    AI_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AI_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def should_skip(entry: dict, force: bool) -> bool:
    if force:
        return False
    status = entry.get("neo_status", "")
    return status in ("ai_ready", "ready")


def process_asset(
    game_id: str,
    game: dict,
    entry: dict,
    settings,
    provider_name: str,
    variations: int,
    dry_run: bool,
    save_variants: bool,
    force: bool,
) -> str | None:
    if should_skip(entry, force):
        return "skipped"

    asset_id = entry["id"]
    if asset_id == "blank":
        return "blank"

    src = ROOT / entry["source"]
    dst = NEO / entry["neo_path"]
    tw, th = entry["width"], entry["height"]
    prompt = build_prompt(game_id, asset_id, game["accent_color"], randomize=settings.randomize)
    base_seed = random.randint(0, 2**31 - 1) if settings.randomize else hash(asset_id) % (2**31)
    seeds = variation_seeds(base_seed, variations)

    if dry_run:
        print(f"  [dry-run] {asset_id} ({tw}x{th}) provider={provider_name} n={variations}")
        print(f"            prompt: {prompt[:120]}...")
        return "dry_run"

    provider = get_provider(provider_name, settings) if provider_name != "local" else None
    if provider_name == "local":
        from lib.local_provider import LocalProvider

        provider = LocalProvider()
    reference = Image.open(src).convert("RGBA")
    raw_variants = provider.generate_variations(src, prompt, variations, base_seed, (tw, th))

    candidates = []
    for raw in raw_variants:
        img = load_image_bytes(raw)
        img = fit_to_canvas(img, tw, th)
        img = quantize_neo(img)
        candidates.append(img)

    if save_variants:
        var_dir = VARIATIONS_DIR / game_id / asset_id
        var_dir.mkdir(parents=True, exist_ok=True)
        for i, cand in enumerate(candidates):
            cand.save(var_dir / f"variant_{i:02d}.png")

    best_idx, best, scores = pick_best(reference, candidates, (tw, th))
    dst.parent.mkdir(parents=True, exist_ok=True)
    best.save(dst, optimize=True)

    entry["neo_status"] = "ai_ready"
    entry["ai_meta"] = {
        "provider": provider_name,
        "prompt": prompt,
        "seed": base_seed,
        "variations": variations,
        "picked_variant": best_idx,
        "scores": scores,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    log_generation(
        {
            "game": game_id,
            "asset": asset_id,
            "provider": provider_name,
            "picked_variant": best_idx,
            "scores": scores,
            "prompt": prompt,
        }
    )
    return f"ok (variant {best_idx}, score {scores['total']:.3f})"


def cmd_status(settings) -> None:
    print("Neo Remix AI providers")
    print("-" * 40)
    for p in ("openai", "replicate", "fal", "stability"):
        import os

        key = os.environ.get(KEY_ENV[p], "")
        status = "linked" if key.strip() else "missing"
        print(f"  {p:12} {status:8}  {mask_key(key)}")
    print()
    print(f"Available: {', '.join(settings.available_providers) or 'none'}")
    print(f"Default provider: {settings.pick_provider() if settings.available_providers else 'n/a'}")
    print(f"Variations per sprite: {settings.variations}")
    print(f"Randomize prompts: {settings.randomize}")
    if not settings.available_providers:
        print()
        print("Set keys in neo-remix/.env (copy from config/api_keys.example.env)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=["boing", "bunner", "cavern", "myriapod", "soccer", "all"], default="all")
    parser.add_argument("--asset", help="Single asset id (e.g. ball, bat00)")
    parser.add_argument("--provider", choices=["auto", "openai", "replicate", "fal", "stability", "local"], default=None)
    parser.add_argument("--variations", type=int, default=None, help="Candidates per sprite (default from .env)")
    parser.add_argument("--limit", type=int, default=0, help="Max assets to process (0 = all)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if ai_ready/ready")
    parser.add_argument("--save-variants", action="store_true", help="Keep all variations under neo-remix/variations/")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without API calls")
    parser.add_argument("--status", action="store_true", help="Show linked API key status")
    args = parser.parse_args()

    settings = load_settings()

    if args.status:
        cmd_status(settings)
        return 0

    try:
        provider_name = settings.pick_provider(args.provider)
    except RuntimeError as e:
        if args.dry_run:
            provider_name = "openai"
            print(f"Note: {e}")
            print("Continuing dry-run with placeholder provider label.\n")
        elif args.provider == "local":
            provider_name = "local"
        else:
            print(f"ERROR: {e}", file=sys.stderr)
            print("Tip: use --provider local to test scoring pipeline without API keys.", file=sys.stderr)
            return 1

    if args.provider == "local":
        provider_name = "local"

    variations = args.variations or settings.variations
    manifest = load_manifest()
    games = list(manifest["games"].keys()) if args.game == "all" else [args.game]

    processed = 0
    for gid in games:
        game = manifest["games"][gid]
        images = game["images"]
        if args.asset:
            images = [e for e in images if e["id"] == args.asset]
            if not images:
                print(f"Asset '{args.asset}' not found in {gid}")
                return 1

        print(f"\n=== {game['neo_title']} ({provider_name}, {variations} variations) ===")
        for entry in images:
            if args.limit and processed >= args.limit:
                break
            try:
                result = process_asset(
                    gid,
                    game,
                    entry,
                    settings,
                    provider_name,
                    variations,
                    args.dry_run,
                    args.save_variants,
                    args.force,
                )
                if result and result not in ("skipped", "blank"):
                    processed += 1
                    print(f"  {entry['id']}: {result}")
                elif result == "skipped":
                    print(f"  {entry['id']}: skip (already {entry.get('neo_status')})")
            except Exception as exc:
                print(f"  {entry['id']}: ERROR — {exc}", file=sys.stderr)
                if not args.dry_run:
                    return 1
            if args.limit and processed >= args.limit:
                break

    if not args.dry_run:
        manifest["asset_pass"] = "ai_generated"
        save_manifest(manifest)

    print(f"\nDone — processed {processed} assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

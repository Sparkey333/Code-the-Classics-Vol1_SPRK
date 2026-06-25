#!/usr/bin/env python3
"""Verify API key linkage for Neo Remix AI sprite pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.api_config import KEY_ENV, load_settings, mask_key

PROVIDER_ORDER = ("openai", "replicate", "fal", "stability")


def main() -> int:
    settings = load_settings()
    print("Neo Remix API Key Linkage\n")

    any_linked = False
    for p in PROVIDER_ORDER:
        import os

        raw = os.environ.get(KEY_ENV[p], "")
        linked = bool(raw.strip())
        any_linked = any_linked or linked
        icon = "✓" if linked else "✗"
        print(f"  [{icon}] {p:12} {mask_key(raw)}")

    print()
    if any_linked:
        print(f"Active provider (auto): {settings.pick_provider()}")
        print(f"Variations: {settings.variations}  |  Randomize: {settings.randomize}")
        print("\nReady. Example:")
        print("  python3 neo-remix/scripts/generate_ai_sprites.py --game boing --asset ball --save-variants")
        return 0

    print("No keys linked yet.")
    print("\nSetup:")
    print("  cp neo-remix/config/api_keys.example.env neo-remix/.env")
    print("  # Edit neo-remix/.env and add at least one API key")
    print("  python3 neo-remix/scripts/link_api_keys.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

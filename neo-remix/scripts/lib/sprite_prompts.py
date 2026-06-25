"""Neo Remix sprite prompt builder with randomized style modifiers."""

from __future__ import annotations

import random
import re
from typing import Iterable

GAME_CONTEXT = {
    "boing": "neon arcade pong paddle and ball arena",
    "bunner": "endless hopper rabbit crossing roads and rivers",
    "cavern": "cave platformer with orbs traps and explorers",
    "myriapod": "vertical shooter with segmented centipede enemies",
    "soccer": "top-down substitute soccer match",
}

ACCENT_NAMES = {
    "boing": "neon cyan",
    "bunner": "electric green",
    "cavern": "hot magenta",
    "myriapod": "solar gold",
    "soccer": "pitch green",
}

STYLE_CORE = (
    "Neo Remix game sprite, late-80s arcade pixel art with synthwave neon finish, "
    "flat shading max 3 tones, 1px neon rim glow, transparent background, "
    "crisp readable silhouette, no text, no watermark, no blur"
)

RANDOM_MODIFIERS: list[str] = [
    "subtle scanline texture",
    "slightly bolder outline",
    "extra punchy highlight",
    "soft inner glow",
    "high contrast arcade pop",
    "minimal detail clean shape",
    "retro CRT phosphor tint",
    "tighter pixel clusters",
    "vivid accent bloom",
    "matte fill with neon edge",
]

CATEGORY_HINTS: list[tuple[str, str]] = [
    (r"^digit", "seven-segment HUD digit, monospace neon display glyph"),
    (r"^blank$", "fully transparent empty sprite"),
    (r"impact|effect|exp|vanish|splash|splat", "short impact VFX frame, burst particles"),
    (r"menu|title|over|gameover", "UI title panel element, bold neo chrome"),
    (r"ball|orb", "round game object with neon rim"),
    (r"bat|player|car|bunny|bunner|rabbit|ship", "playable character or paddle sprite"),
    (r"grass|dirt|road|sidewalk|table|pitch|tile|trap|rock|wall|block", "environment tile or terrain"),
    (r"enemy|meanie|segment|eagle|goalie", "enemy or hazard entity"),
]


def categorize(asset_id: str) -> str:
    for pattern, hint in CATEGORY_HINTS:
        if re.search(pattern, asset_id, re.I):
            return hint
    return "arcade game sprite element"


def build_prompt(
    game_id: str,
    asset_id: str,
    accent_hex: str,
    *,
    randomize: bool = True,
    rng: random.Random | None = None,
) -> str:
    if asset_id == "blank":
        return "fully transparent 1x1 empty sprite"

    rng = rng or random.Random()
    accent = ACCENT_NAMES.get(game_id, "neon cyan")
    context = GAME_CONTEXT.get(game_id, "retro arcade game")
    category = categorize(asset_id)

    parts = [
        STYLE_CORE,
        f"Game: {context}.",
        f"Asset: {asset_id.replace('_', ' ')} — {category}.",
        f"Accent color {accent} ({accent_hex}).",
        "Preserve exact pose and silhouette from reference image.",
        "Output single centered sprite on transparent background.",
    ]

    if randomize:
        picks = rng.sample(RANDOM_MODIFIERS, k=min(2, len(RANDOM_MODIFIERS)))
        parts.append("Style accents: " + ", ".join(picks) + ".")

    return " ".join(parts)


def variation_seeds(base_seed: int, count: int) -> list[int]:
    rng = random.Random(base_seed)
    return [rng.randint(0, 2**31 - 1) for _ in range(count)]

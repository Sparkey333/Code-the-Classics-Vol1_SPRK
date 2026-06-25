"""Local procedural provider for pipeline testing without API keys."""

from __future__ import annotations

import random
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from lib.sprite_post import fit_to_canvas


class LocalProvider:
    name = "local"

    def generate_variations(
        self,
        reference: Path,
        prompt: str,
        count: int,
        seed: int,
        target_size: tuple[int, int],
    ) -> list[bytes]:
        rng = random.Random(seed)
        ref = Image.open(reference).convert("RGBA")
        results: list[bytes] = []
        accents = [(0, 245, 255), (255, 46, 151), (255, 212, 71), (107, 255, 138)]

        for i in range(count):
            img = ref.copy()
            accent = accents[i % len(accents)]
            # Tint non-transparent pixels toward accent
            px = img.load()
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = px[x, y]
                    if a < 32:
                        continue
                    mix = 0.25 + rng.random() * 0.35
                    px[x, y] = (
                        int(r * (1 - mix) + accent[0] * mix),
                        int(g * (1 - mix) + accent[1] * mix),
                        int(b * (1 - mix) + accent[2] * mix),
                        a,
                    )
            if rng.random() > 0.5:
                img = img.filter(ImageFilter.EDGE_ENHANCE)
            img = ImageEnhance.Contrast(img).enhance(1.0 + rng.random() * 0.4)
            img = fit_to_canvas(img, target_size[0], target_size[1])
            buf = BytesIO()
            img.save(buf, format="PNG")
            results.append(buf.getvalue())
        return results

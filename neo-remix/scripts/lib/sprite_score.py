"""Score AI sprite candidates and pick the best variation."""

from __future__ import annotations

import math
from io import BytesIO

from PIL import Image, ImageChops, ImageFilter

NEO_PALETTE_RGB = [
    (11, 14, 23),
    (21, 27, 46),
    (0, 245, 255),
    (255, 46, 151),
    (255, 212, 71),
    (232, 238, 255),
    (107, 76, 255),
]


def _alpha_mask(img: Image.Image) -> Image.Image:
    return img.convert("RGBA").split()[-1].point(lambda a: 255 if a > 32 else 0)


def _resize_mask(mask: Image.Image, size: tuple[int, int]) -> Image.Image:
    return mask.resize(size, Image.Resampling.NEAREST)


def silhouette_iou(reference: Image.Image, candidate: Image.Image) -> float:
    ref = _alpha_mask(reference)
    cand = _alpha_mask(candidate)
    if ref.size != cand.size:
        cand = _resize_mask(cand, ref.size)
    ref_px = ref.load()
    cand_px = cand.load()
    inter = union = 0
    for y in range(ref.size[1]):
        for x in range(ref.size[0]):
            r = ref_px[x, y] > 0
            c = cand_px[x, y] > 0
            if r and c:
                inter += 1
            if r or c:
                union += 1
    return inter / union if union else 0.0


def palette_score(img: Image.Image) -> float:
    rgba = img.convert("RGBA")
    px = rgba.load()
    hits = total = 0
    for y in range(rgba.size[1]):
        for x in range(rgba.size[0]):
            r, g, b, a = px[x, y]
            if a < 32:
                continue
            total += 1
            best = min(
                math.sqrt((r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2)
                for pr, pg, pb in NEO_PALETTE_RGB
            )
            if best < 72:
                hits += 1
    return hits / total if total else 0.0


def sharpness_score(img: Image.Image) -> float:
    gray = img.convert("RGBA").split()[-1].filter(ImageFilter.FIND_EDGES)
    hist = gray.histogram()
    edge_pixels = sum(hist[64:])
    total = sum(hist)
    return min(1.0, (edge_pixels / total) * 8) if total else 0.0


def dimension_penalty(candidate: Image.Image, target: tuple[int, int]) -> float:
    w, h = candidate.size
    tw, th = target
    if (w, h) == (tw, th):
        return 1.0
    ratio = min(w / tw, h / th, tw / w, th / h)
    return max(0.0, ratio)


def score_candidate(
    reference: Image.Image,
    candidate: Image.Image,
    target_size: tuple[int, int],
) -> dict[str, float]:
    sil = silhouette_iou(reference, candidate)
    pal = palette_score(candidate)
    sharp = sharpness_score(candidate)
    dim = dimension_penalty(candidate, target_size)
    total = 0.45 * sil + 0.30 * pal + 0.15 * sharp + 0.10 * dim
    return {
        "total": round(total, 4),
        "silhouette": round(sil, 4),
        "palette": round(pal, 4),
        "sharpness": round(sharp, 4),
        "dimension": round(dim, 4),
    }


def pick_best(
    reference: Image.Image,
    candidates: list[Image.Image],
    target_size: tuple[int, int],
) -> tuple[int, Image.Image, dict[str, float]]:
    best_idx = 0
    best_score: dict[str, float] = {"total": -1.0}
    best_img = candidates[0]
    for i, cand in enumerate(candidates):
        s = score_candidate(reference, cand, target_size)
        if s["total"] > best_score["total"]:
            best_idx, best_img, best_score = i, cand, s
    return best_idx, best_img, best_score


def load_image_bytes(data: bytes) -> Image.Image:
    return Image.open(BytesIO(data)).convert("RGBA")

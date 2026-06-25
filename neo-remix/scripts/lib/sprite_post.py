"""Post-process AI output to exact game sprite dimensions."""

from __future__ import annotations

from PIL import Image


def fit_to_canvas(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale content to fit inside target box, center on transparent canvas."""
    img = img.convert("RGBA")
    if img.size == (target_w, target_h):
        return img

    bbox = img.getbbox()
    if not bbox:
        return Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

    cropped = img.crop(bbox)
    cw, ch = cropped.size
    scale = min(target_w / cw, target_h / ch, 1.0)
    nw = max(1, int(cw * scale))
    nh = max(1, int(ch * scale))
    resized = cropped.resize((nw, nh), Image.Resampling.NEAREST)

    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    ox = (target_w - nw) // 2
    oy = (target_h - nh) // 2
    canvas.paste(resized, (ox, oy), resized)
    return canvas


def quantize_neo(img: Image.Image, colors: int = 16) -> Image.Image:
    """Snap to limited palette while keeping alpha."""
    img = img.convert("RGBA")
    alpha = img.split()[-1]
    rgb = img.convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out

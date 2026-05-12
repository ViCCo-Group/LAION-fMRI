#!/usr/bin/env python3
"""Generate a 1200x630 Open Graph image for LAION-fMRI.

Composes the photorealistic-earth icon, the "LAION-fMRI" wordmark, a
short tagline, and a Get-Started CTA onto a 1200x630 dark canvas. The
same palette as the rendered Furo theme so the social card visually
matches the site.

Usage:
    uv run python docs/scripts/make_og_image.py
Output:
    docs/source/_static/og-image.png
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "source" / "_static"
BRAND = ROOT / "_brand"

W, H = 1200, 630

# Palette from conf.py dark theme.
BG = (10, 14, 26)
BG_GRADIENT = (17, 23, 41)
CYAN = (0, 212, 255)
CORAL = (255, 107, 74)
FG = (232, 234, 240)
FG_MUTED = (160, 168, 192)


def _find_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        base.putpixel((0, y), (r, g, b))
    return base.resize((w, h))


def _radial_glow(size: tuple[int, int], center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int = 90) -> Image.Image:
    w, h = size
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    cx, cy = center
    px = glow.load()
    for y in range(max(0, cy - radius), min(h, cy + radius)):
        for x in range(max(0, cx - radius), min(w, cx + radius)):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d < radius:
                t = 1 - d / radius
                a = int(alpha * (t ** 2))
                px[x, y] = (*color, a)
    return glow


def _circular_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    return mask


def _load_earth() -> Image.Image | None:
    """Use the high-res photorealistic-earth source if available; fall back
    to the 192px favicon that ships with the docs."""
    source = BRAND / "favicon_source.png"
    if source.exists():
        img = Image.open(source).convert("RGBA")
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        return img.crop((left, top, left + side, top + side))
    favicon_png = STATIC / "favicon-192.png"
    if favicon_png.exists():
        return Image.open(favicon_png).convert("RGBA")
    return None


def main() -> int:
    out = STATIC / "og-image.png"

    img = _vertical_gradient((W, H), BG, BG_GRADIENT).convert("RGBA")
    img.alpha_composite(_radial_glow((W, H), center=(W - 180, 160), radius=420, color=CYAN, alpha=80))
    img.alpha_composite(_radial_glow((W, H), center=(180, H - 140), radius=420, color=CORAL, alpha=50))

    draw = ImageDraw.Draw(img)

    # Top accent bar.
    draw.rectangle([0, 0, W, 4], fill=CYAN)

    # Fonts.
    f_brand = _find_font([
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ], 104)
    f_tag = _find_font([
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "DejaVuSans.ttf",
    ], 36)
    f_meta = _find_font([
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "DejaVuSans.ttf",
    ], 26)
    f_footer = _find_font([
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "DejaVuSans.ttf",
    ], 24)
    f_cta = _find_font([
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "DejaVuSans-Bold.ttf",
    ], 26)

    # Logo (earth) inline with the wordmark — same horizontal centerline.
    brand_text = "LAION-fMRI"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=f_brand)
    brand_w = brand_bbox[2] - brand_bbox[0]
    brand_h = brand_bbox[3] - brand_bbox[1]
    brand_visual_top = brand_bbox[1]

    logo_size = 180
    gap = 28
    block_left = 80
    center_y = 260
    logo_x = block_left
    logo_y = center_y - logo_size // 2

    earth = _load_earth()
    if earth is not None:
        earth = earth.resize((logo_size, logo_size), Image.LANCZOS)
        circle = Image.new("RGBA", (logo_size, logo_size), (0, 0, 0, 0))
        circle.paste(earth, (0, 0), _circular_mask(logo_size))
        img.alpha_composite(circle, dest=(logo_x, logo_y))

    # Wordmark.
    x = logo_x + logo_size + gap
    y = center_y - brand_h // 2 - brand_visual_top
    draw.text((x, y), brand_text, font=f_brand, fill=FG)

    # Tagline + meta line below.
    tagline_y = max(logo_y + logo_size, y + brand_h) + 28
    draw.text((block_left, tagline_y), "A 7T fMRI dataset of human vision", font=f_tag, fill=FG)
    draw.text(
        (block_left, tagline_y + 50),
        "5 subjects  ·  25,000+ natural images  ·  165 sessions  ·  open access",
        font=f_meta,
        fill=FG_MUTED,
    )

    # CTA pill (bottom-right): cyan-tinted background, white bold label + drawn arrow.
    cta_left = "Get started"
    cta_right = "laion-fmri docs"
    gap_arrow = 22
    left_bbox = draw.textbbox((0, 0), cta_left, font=f_cta)
    right_bbox = draw.textbbox((0, 0), cta_right, font=f_cta)
    left_w = left_bbox[2] - left_bbox[0]
    right_w = right_bbox[2] - right_bbox[0]
    text_h = max(left_bbox[3] - left_bbox[1], right_bbox[3] - right_bbox[1])
    arrow_w = 20
    arrow_h = 18

    cta_text_w = left_w + gap_arrow + arrow_w + gap_arrow + right_w
    pad_x, pad_y = 30, 16
    pill_w = cta_text_w + pad_x * 2
    pill_h = text_h + pad_y * 2
    pill_right = W - 80
    pill_bottom = H - 50
    pill_left = pill_right - pill_w
    pill_top = pill_bottom - pill_h
    radius = pill_h // 2
    draw.rounded_rectangle(
        [pill_left, pill_top, pill_right, pill_bottom],
        radius=radius,
        fill=CYAN,
    )

    cursor_x = pill_left + pad_x
    text_y = pill_top + (pill_h - text_h) // 2 - left_bbox[1]
    label_color = (10, 14, 26)  # navy text on cyan pill for contrast
    draw.text((cursor_x, text_y), cta_left, font=f_cta, fill=label_color)
    cursor_x += left_w + gap_arrow

    # Arrow rendered as a polygon (font-independent).
    cy = pill_top + pill_h // 2
    stem_y0, stem_y1 = cy - 2, cy + 2
    stem_x0 = cursor_x
    stem_x1 = cursor_x + arrow_w - arrow_h // 2 - 2
    draw.rectangle([stem_x0, stem_y0, stem_x1, stem_y1], fill=label_color)
    tip_x = cursor_x + arrow_w
    draw.polygon(
        [
            (stem_x1, cy - arrow_h // 2),
            (tip_x, cy),
            (stem_x1, cy + arrow_h // 2),
        ],
        fill=label_color,
    )
    cursor_x += arrow_w + gap_arrow
    draw.text((cursor_x, text_y), cta_right, font=f_cta, fill=label_color)

    # Bottom-left URL (cyan), vertically centered to the CTA pill.
    url_text = "laion-fmri.hebartlab.com"
    url_bbox = draw.textbbox((0, 0), url_text, font=f_footer)
    url_h = url_bbox[3] - url_bbox[1]
    url_y = pill_top + (pill_h - url_h) // 2 - url_bbox[1]
    draw.text((80, url_y), url_text, font=f_footer, fill=CYAN)

    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Wrote {out} ({W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

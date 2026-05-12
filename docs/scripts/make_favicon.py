#!/usr/bin/env python3
"""Regenerate the LAION-fMRI favicon at sizes Google accepts in search.

Google requires the favicon to be a multiple of 48px (>=48 square).
Sphinx ships a single ``favicon.ico``; we rebuild that .ico to hold
16, 32, 48, 96, 192 entries so it works in browser tabs AND in
Google search results.

Source image: a high-res render of the "photorealistic earth" mosaic
(same look as the wordmark fill). Place a 1024px+ source PNG at
``docs/_brand/favicon_source.png`` and re-run this script. The source
lives outside ``_static`` so it doesn't ship with the built site.

Output:
    docs/source/_static/favicon.ico         (multi-size ICO)
    docs/source/_static/favicon-192.png     (referenced as a PNG icon)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "source" / "_static"
BRAND = ROOT / "_brand"

# Sizes Google + browsers + Apple use.
SIZES = [16, 32, 48, 96, 192]


def _circular_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    return mask


def _render(base: Image.Image, size: int) -> Image.Image:
    """Return a circular, transparent-background icon at the given size."""
    icon = base.resize((size, size), Image.LANCZOS).convert("RGBA")
    transparent = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    transparent.paste(icon, (0, 0), _circular_mask(size))
    return transparent


def _load_source() -> Image.Image:
    """Locate the favicon source image.

    Prefers ``_brand/favicon_source.png`` (high-res master, not shipped).
    Falls back to cropping the wordmark mosaic so the script still runs
    in clones where the brand asset isn't present.
    """
    candidate = BRAND / "favicon_source.png"
    if candidate.exists():
        img = Image.open(candidate).convert("RGBA")
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        return img.crop((left, top, left + side, top + side)).resize(
            (512, 512), Image.LANCZOS,
        )

    mosaic = STATIC / "laion_fmri_logo_mosaic.png"
    if not mosaic.exists():
        raise SystemExit(
            "No favicon_source.png in _static and no fallback mosaic found.",
        )
    img = Image.open(mosaic).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize(
        (512, 512), Image.LANCZOS,
    )


def main() -> int:
    base = _load_source()
    icons = {s: _render(base, s) for s in SIZES}

    # Pillow's ICO writer needs every variant baked in via append_images
    # AND the largest size as the primary image, otherwise it silently
    # writes only the first entry.
    ico_path = STATIC / "favicon.ico"
    largest = icons[max(SIZES)]
    others = [icons[s] for s in SIZES if s != max(SIZES)]
    largest.save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=others,
    )
    print(f"Wrote {ico_path} with sizes {SIZES}")

    png192 = STATIC / "favicon-192.png"
    icons[192].save(png192, "PNG", optimize=True)
    print(f"Wrote {png192} (192x192)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

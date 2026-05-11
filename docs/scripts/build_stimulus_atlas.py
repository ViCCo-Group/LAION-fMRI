#!/usr/bin/env python3
"""Pack stimulus thumbnails into a single texture atlas for the homepage hero.

The hero shows the brain mesh as ~2000 image sprites, each sampling one
tile from this atlas. Tiles are square center-crops of the natural-image
stimuli that subjects viewed in the scanner — the brain is literally
made of what it saw.

Run once and commit the output PNG. Re-run only when the stimulus set
changes.

Usage:
    uv run python docs/scripts/build_stimulus_atlas.py \
        --stimuli-root ~/Downloads/LAION-fMRI-stimuli \
        --tile-count 1024 --tile-size 32
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("atlas")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "source" / "_static" / "hero"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_stimuli(root: Path) -> list[Path]:
    files = [p for p in root.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    log.info("Found %d source images under %s", len(files), root)
    return files


def square_thumbnail(path: Path, tile_size: int) -> Image.Image:
    """Center-crop to a square then resize to tile_size."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        im = im.crop((left, top, left + side, top + side))
        return im.resize((tile_size, tile_size), Image.LANCZOS)


def build_atlas(
    sources: list[Path],
    tile_count: int,
    tile_size: int,
    out_png: Path,
    out_manifest: Path,
    seed: int,
) -> None:
    rng = random.Random(seed)
    if len(sources) > tile_count:
        chosen = rng.sample(sources, tile_count)
    else:
        chosen = list(sources)
        log.warning(
            "Only %d source images available, requested %d. "
            "Atlas will be padded with repeats.",
            len(chosen), tile_count,
        )
        while len(chosen) < tile_count:
            chosen.append(rng.choice(sources))

    grid = 1
    while grid * grid < tile_count:
        grid += 1
    atlas_size = grid * tile_size
    log.info(
        "Packing %d tiles into %dx%d grid -> %dx%d atlas",
        tile_count, grid, grid, atlas_size, atlas_size,
    )

    atlas = Image.new("RGB", (atlas_size, atlas_size), (0, 0, 0))
    used: list[str] = []
    for idx, src in enumerate(chosen):
        try:
            tile = square_thumbnail(src, tile_size)
        except Exception as exc:
            log.warning("Skipping %s: %s", src.name, exc)
            tile = Image.new("RGB", (tile_size, tile_size), (16, 23, 41))
        col = idx % grid
        row = idx // grid
        atlas.paste(tile, (col * tile_size, row * tile_size))
        used.append(src.name)
        if (idx + 1) % 200 == 0:
            log.info("  %d/%d", idx + 1, tile_count)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(out_png, format="JPEG", quality=80, optimize=True, progressive=True)
    log.info("Wrote atlas: %s (%.1f KB)", out_png, out_png.stat().st_size / 1024)

    manifest = {
        "tile_count": tile_count,
        "tile_size": tile_size,
        "grid": grid,
        "atlas_size": atlas_size,
        "seed": seed,
        "tiles": used,
    }
    out_manifest.write_text(json.dumps(manifest, indent=2))
    log.info("Wrote manifest: %s", out_manifest)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stimuli-root", type=Path, required=True,
        help="Directory containing stimulus images (recursively scanned).",
    )
    ap.add_argument(
        "--tile-count", type=int, default=1024,
        help="Number of tiles in the atlas (default: 1024 -> 32x32 grid).",
    )
    ap.add_argument(
        "--tile-size", type=int, default=32,
        help="Pixel side length per tile (default: 32). Sprites render at ~25-40px "
             "on screen, so 32px keeps file size low without visible loss.",
    )
    ap.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR,
        help="Output directory for atlas PNG and manifest JSON.",
    )
    ap.add_argument("--seed", type=int, default=20260511)
    args = ap.parse_args()

    stim_root = args.stimuli_root.expanduser().resolve()
    if not stim_root.is_dir():
        ap.error(f"--stimuli-root not found: {stim_root}")

    sources = collect_stimuli(stim_root)
    if not sources:
        ap.error("No images found under stimuli root.")

    out_png = args.out_dir / "stimuli_atlas.jpg"
    out_manifest = args.out_dir / "stimuli_atlas.json"
    build_atlas(
        sources=sources,
        tile_count=args.tile_count,
        tile_size=args.tile_size,
        out_png=out_png,
        out_manifest=out_manifest,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

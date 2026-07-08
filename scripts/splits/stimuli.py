"""Stimulus metadata and split-pool helpers."""

from __future__ import annotations

import csv
from pathlib import Path


STIMULI_METADATA = "task-images_metadata.csv"
STIMULI_H5 = "task-images_stimuli.h5"

POOLS = ("shared", "sub-01", "sub-03", "sub-05", "sub-06", "sub-07")

# Historical filename suffixes can differ from public BIDS subject IDs.
# Prefer the metadata participant column; use this only when that column is
# absent or empty.
FILENAME_SUFFIX_TO_POOL = {
    "p01": "sub-01",
    "p02": "sub-06",
    "p03": "sub-05",
    "p04": "sub-03",
    "p05": "sub-07",
}

POOL_TO_FEATURE_LABEL = {
    "sub-01": "sub-01",
    "sub-03": "sub-04",
    "sub-05": "sub-03",
    "sub-06": "sub-02",
    "sub-07": "sub-05",
}


def add_stimuli_arg(parser) -> None:
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        required=True,
        help=(
            "Directory containing task-images_metadata.csv and, when feature "
            "extraction is needed, task-images_stimuli.h5."
        ),
    )


def require_stimuli_dir(stimuli_dir: Path) -> Path:
    stimuli_dir = Path(stimuli_dir)
    metadata_path = stimuli_dir / STIMULI_METADATA
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing stimulus metadata: {metadata_path}. Download stimuli "
            "with `laion-fmri download-stimuli` or pass --stimuli-dir."
        )
    return stimuli_dir


def load_stimulus_metadata(stimuli_dir: Path) -> list[dict[str, str]]:
    metadata_path = stimuli_dir / STIMULI_METADATA
    with metadata_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or "image_name" not in rows[0]:
        raise ValueError(f"{metadata_path} must contain an image_name column")
    return rows


def _as_token(value: str | None) -> str:
    return str(value or "").strip().lower().replace("-", "")


def _participant_suffix(image_name: str) -> str | None:
    stem = Path(image_name).stem
    suffix = stem.rsplit("_", 1)[-1].lower()
    if len(suffix) == 3 and suffix.startswith("p") and suffix[1:].isdigit():
        return suffix
    return None


def _row_pool(row: dict[str, str]) -> str | None:
    token = _as_token(row.get("participant"))
    if token.startswith("sub") and token[3:].isdigit():
        return f"sub-{int(token[3:]):02d}"
    if token.startswith("p") and token[1:].isdigit():
        suffix = f"p{int(token[1:]):02d}"
        return FILENAME_SUFFIX_TO_POOL.get(suffix)
    suffix = _participant_suffix(row["image_name"])
    if suffix is not None:
        return FILENAME_SUFFIX_TO_POOL.get(suffix)
    return None


def is_ood(row: dict[str, str]) -> bool:
    dataset = _as_token(row.get("dataset"))
    image_name = row["image_name"]
    return dataset == "ood" or "_OOD_" in image_name


def is_shared(row: dict[str, str]) -> bool:
    shared = _as_token(row.get("unique_or_shared"))
    return shared == "shared" or row["image_name"].startswith("shared_")


def pool_label(pool: str) -> str:
    if pool == "shared":
        return "LAION non-OOD shared (1121 images)"
    subject_label = POOL_TO_FEATURE_LABEL[pool]
    return f"{subject_label} full pool (unique + LAION non-OOD shared)"


def ood_pool_label(pool: str) -> str:
    if pool == "shared":
        return pool_label(pool)
    return f"{pool} full pool (5833 images)"


def pool_image_ids(rows: list[dict[str, str]], pool: str) -> list[str]:
    """Return the ordered regular image universe for a split pool."""

    if pool not in POOLS:
        raise KeyError(f"unknown pool {pool!r}; expected one of {POOLS}")

    shared_regular = [
        row["image_name"]
        for row in rows
        if is_shared(row) and not is_ood(row)
    ]
    if pool == "shared":
        return sorted(shared_regular)

    unique = [
        row["image_name"]
        for row in rows
        if not is_shared(row)
        and not is_ood(row)
        and _row_pool(row) == pool
    ]
    return sorted(shared_regular + unique)


def ood_image_ids_from_metadata(rows: list[dict[str, str]]) -> list[str]:
    return sorted(row["image_name"] for row in rows if is_shared(row) and is_ood(row))

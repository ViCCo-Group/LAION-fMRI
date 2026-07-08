"""Shared helpers for standalone split method scripts.

The scripts in this directory derive split membership from stimulus metadata
and, for feature-based methods, stimulus embeddings. Method inputs are
stimulus-level data and visual feature arrays.
"""

from __future__ import annotations

import csv
import difflib
import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SPLIT_DIR = REPO_ROOT / "laion_fmri" / "splits" / "data"

STIMULI_METADATA = "task-images_metadata.csv"
STIMULI_H5 = "task-images_stimuli.h5"

POOLS = ("shared", "sub-01", "sub-03", "sub-05", "sub-06", "sub-07")
SUBJECT_POOLS = ("sub-01", "sub-03", "sub-05", "sub-06", "sub-07")
RANDOM_NAMES = tuple(f"random_{i}" for i in range(5))
CLUSTER_K5_NAMES = tuple(f"cluster_k5_{i}" for i in range(5))
SPLIT_NAMES = RANDOM_NAMES + CLUSTER_K5_NAMES + ("tau", "ood")

RANDOM_SPLITTER = "random_kfold"
RANDOM_METHOD = "shuffled_5fold_cv"
RANDOM_SEED = 42
RANDOM_FOLDS = 5

CLUSTER_K5_SPLITTER = "kmeans_cluster_holdout"
CLUSTER_K5_METHOD = "kmeans_clip_k5_holdout"
CLUSTER_K5_FEATURE_SPACE = "CLIP"
CLUSTER_K5_K = 5
CLUSTER_K5_SEED = 2026
CLUSTER_K5_DEFAULT_N_INIT = 10
# The split-construction method used five k-means++ restarts for sub-05
# and ten for the other pools.
CLUSTER_K5_N_INIT_BY_POOL = {"sub-05": 5}

TAU_SPLITTER = "min_nn_stochastic"
TAU_METHOD = "min_nn_filter + stochastic_mmd_swap"

OOD_SPLITTER = "ood_holdout"
OOD_METHOD = "ood_dataset_holdout"

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

OOD_TYPES = (
    "cropped",
    "gabor",
    "gaudy",
    "illusion-classic",
    "illusion-natural",
    "relations",
    "selfmade",
    "shape",
    "unusual",
)


def random_params(
    fold: int,
    *,
    folds: int = RANDOM_FOLDS,
    seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    return {
        "method": RANDOM_METHOD,
        "k": int(folds),
        "seed": int(seed),
        "fold": int(fold),
    }


def cluster_k5_n_init(pool: str) -> int:
    return CLUSTER_K5_N_INIT_BY_POOL.get(pool, CLUSTER_K5_DEFAULT_N_INIT)


def cluster_k5_params(
    held_out_cluster: int,
    *,
    k: int = CLUSTER_K5_K,
    seed: int = CLUSTER_K5_SEED,
    n_init: int = CLUSTER_K5_DEFAULT_N_INIT,
) -> dict[str, Any]:
    return {
        "method": CLUSTER_K5_METHOD,
        "feature_space": CLUSTER_K5_FEATURE_SPACE,
        "n_clusters": int(k),
        "seed": int(seed),
        "n_init": int(n_init),
        "held_out_cluster": int(held_out_cluster),
    }


def ood_params() -> dict[str, Any]:
    return {
        "method": OOD_METHOD,
        "ood_types": list(OOD_TYPES),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2) + "\n"


def split_path(
    pool: str,
    name: str,
    data_dir: Path = PACKAGE_SPLIT_DIR,
) -> Path:
    return data_dir / pool / f"{name}.json"


def load_split(
    pool: str,
    name: str,
    data_dir: Path = PACKAGE_SPLIT_DIR,
) -> dict[str, Any]:
    return load_json(split_path(pool, name, data_dir))


def variant(split: dict[str, Any]) -> dict[str, Any]:
    variants = split.get("variants", [])
    if len(variants) != 1:
        raise ValueError(f"expected a single variant in {split.get('name')}")
    return variants[0]


def train_ids(split: dict[str, Any]) -> list[str]:
    return [str(x) for x in variant(split)["train_ids"]]


def test_ids(split: dict[str, Any]) -> list[str]:
    return [str(x) for x in variant(split)["test_ids"]]


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


def ordered_complement(image_ids: list[str], test: Iterable[str]) -> list[str]:
    test_set = set(str(x) for x in test)
    return [image_id for image_id in image_ids if image_id not in test_set]


def make_single_variant_split(
    *,
    name: str,
    pool_label: str,
    splitter: str,
    params: dict[str, Any],
    train: Iterable[str],
    test: Iterable[str],
) -> dict[str, Any]:
    train_list = [str(x) for x in train]
    test_list = [str(x) for x in test]
    return {
        "name": name,
        "pool": pool_label,
        "splitter": splitter,
        "params": params,
        "n_train": len(train_list),
        "n_test": len(test_list),
        "variants": [
            {
                "variant_id": 0,
                "train_ids": train_list,
                "test_ids": test_list,
            }
        ],
    }


def check_or_write(
    path: Path,
    payload: dict[str, Any],
    *,
    write: bool,
) -> None:
    """Write payload or compare it against a reference JSON object."""

    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_text(payload))
        return

    current = load_json(path)
    if current == payload:
        return

    current_text = json_text(current).splitlines(keepends=True)
    new_text = json_text(payload).splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(
            current_text,
            new_text,
            fromfile=str(path),
            tofile=f"{path} (generated)",
            n=3,
        )
    )
    raise AssertionError(f"{path} differs from generated payload:\n{diff}")


def validate_single_split(split: dict[str, Any]) -> None:
    var = variant(split)
    train = set(str(x) for x in var["train_ids"])
    test = set(str(x) for x in var["test_ids"])
    if train & test:
        raise AssertionError(f"{split['name']}: train/test overlap")
    if split["n_train"] != len(var["train_ids"]):
        raise AssertionError(f"{split['name']}: bad n_train")
    if split["n_test"] != len(var["test_ids"]):
        raise AssertionError(f"{split['name']}: bad n_test")
    if var.get("variant_id") != 0:
        raise AssertionError(f"{split['name']}: expected variant_id=0")


def add_write_check_args(parser) -> None:
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write generated JSON payloads into --data-dir.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Compare generated JSON payloads against --data-dir.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PACKAGE_SPLIT_DIR,
        help="Split data directory to compare or write.",
    )


def should_write(args) -> bool:
    # Default mode is non-mutating check behavior.
    return bool(args.write)

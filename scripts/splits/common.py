"""Shared helpers for split-generation scripts.

These scripts are maintainer tooling for regenerating the JSON files shipped
under ``laion_fmri/splits/data``. They intentionally avoid importing the
public ``laion_fmri`` package so split validation can run in a minimal Python
environment.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SPLIT_DIR = REPO_ROOT / "laion_fmri" / "splits" / "data"
FINALIZED_MIN_NN_DIR = (
    REPO_ROOT / "experiments" / "generalization_split" / "min_nn"
)

POOLS = ("shared", "sub-01", "sub-03", "sub-05", "sub-06", "sub-07")
SUBJECT_POOLS = ("sub-01", "sub-03", "sub-05", "sub-06", "sub-07")
RANDOM_NAMES = tuple(f"random_{i}" for i in range(5))
CLUSTER_K5_NAMES = tuple(f"cluster_k5_{i}" for i in range(5))
SPLIT_NAMES = RANDOM_NAMES + CLUSTER_K5_NAMES + ("tau", "ood")

# Historical full-pool artifacts were generated under acquisition/run pool
# labels. These map those finalized artifact pools back to public BIDS subject
# pool names exposed by laion_fmri.splits.
PUBLIC_TO_FINALIZED_POOL = {
    "shared": "shared",
    "sub-01": "p01_full",
    "sub-03": "p04_full",
    "sub-05": "p03_full",
    "sub-06": "p02_full",
    "sub-07": "p05_full",
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
        raise ValueError(f"expected exactly one variant in {split.get('name')}")
    return variants[0]


def train_ids(split: dict[str, Any]) -> list[str]:
    return [str(x) for x in variant(split)["train_ids"]]


def test_ids(split: dict[str, Any]) -> list[str]:
    return [str(x) for x in variant(split)["test_ids"]]


def regular_pool_ids(
    pool: str,
    data_dir: Path = PACKAGE_SPLIT_DIR,
) -> list[str]:
    """Return the regular, non-OOD image IDs for a pool.

    In packaged splits, ``ood`` is train=regular-pool and test=OOD-shared, so
    the train side is the canonical regular stimulus universe.
    """

    return train_ids(load_split(pool, "ood", data_dir))


def ood_image_ids(data_dir: Path = PACKAGE_SPLIT_DIR) -> list[str]:
    return test_ids(load_split("shared", "ood", data_dir))


def pool_label_from_existing(
    pool: str,
    split_name: str,
    data_dir: Path = PACKAGE_SPLIT_DIR,
) -> str:
    return str(load_split(pool, split_name, data_dir)["pool"])


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
    """Write payload or compare it against the current JSON object."""

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
    raise AssertionError(f"{path} does not match generated payload:\n{diff}")


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


def public_pool_to_finalized(pool: str) -> str:
    try:
        return PUBLIC_TO_FINALIZED_POOL[pool]
    except KeyError as exc:
        raise KeyError(f"unknown public pool {pool!r}") from exc


def finalized_split_path(
    finalized_root: Path,
    pool: str,
    name: str,
) -> Path:
    artifact_pool = public_pool_to_finalized(pool)
    return finalized_root / artifact_pool / "splits" / f"{name}.json"


def add_write_check_args(parser) -> None:
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write generated JSONs into --data-dir.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Check generated JSONs against --data-dir without writing.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PACKAGE_SPLIT_DIR,
        help="Package split data directory to check or write.",
    )


def should_write(args) -> bool:
    # Default to check mode so running a script without flags is non-mutating.
    return bool(args.write)

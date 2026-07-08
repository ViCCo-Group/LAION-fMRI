"""Split JSON I/O helpers."""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SPLIT_DIR = REPO_ROOT / "laion_fmri" / "splits" / "data"


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

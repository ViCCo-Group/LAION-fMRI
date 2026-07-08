"""Validate split JSON files and cross-split invariants."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from split_json import (
    PACKAGE_SPLIT_DIR,
    load_split,
    test_ids,
    train_ids,
    validate_single_split,
)
from create_cluster_k5 import (
    CLUSTER_K5_NAMES,
    CLUSTER_K5_SPLITTER,
    cluster_k5_n_init,
    cluster_k5_params,
)
from create_ood import OOD_SPLITTER, OOD_TYPES, ood_params
from create_random import RANDOM_NAMES, RANDOM_SPLITTER, random_params
from create_tau import TAU_SPLITTER
from stimuli import POOLS


SPLIT_NAMES = RANDOM_NAMES + CLUSTER_K5_NAMES + ("tau", "ood")


def _assert_unique(values: list[str], label: str) -> None:
    counts = Counter(values)
    duplicates = [value for value, count in counts.items() if count > 1]
    if duplicates:
        raise AssertionError(f"{label}: duplicate IDs: {duplicates[:5]}")


def _assert_complement(
    *,
    pool: str,
    name: str,
    universe: list[str],
    train: list[str],
    test: list[str],
) -> None:
    universe_set = set(universe)
    train_set = set(train)
    test_set = set(test)
    if train_set | test_set != universe_set:
        missing = sorted(universe_set - (train_set | test_set))[:5]
        extra = sorted((train_set | test_set) - universe_set)[:5]
        raise AssertionError(
            f"{pool}/{name}: train+test differs from regular universe; "
            f"missing={missing}, extra={extra}"
        )
    if train != [image_id for image_id in universe if image_id not in test_set]:
        raise AssertionError(f"{pool}/{name}: train differs from ordered complement")


def _ood_type(image_id: str) -> str:
    marker = "_OOD_"
    if marker not in image_id:
        raise AssertionError(f"OOD image id lacks {marker!r}: {image_id}")
    return image_id.split(marker, 1)[1].split("_", 1)[0]


def _regular_pool_ids(pool: str, data_dir: Path) -> list[str]:
    return train_ids(load_split(pool, "ood", data_dir))


def validate_pool(pool: str, data_dir: Path) -> None:
    universe = _regular_pool_ids(pool, data_dir)
    _assert_unique(universe, f"{pool}/regular universe")
    universe_set = set(universe)

    for name in SPLIT_NAMES:
        split = load_split(pool, name, data_dir)
        if split["name"] != name:
            raise AssertionError(f"{pool}/{name}: bad split name")
        validate_single_split(split)
        train = train_ids(split)
        test = test_ids(split)
        _assert_unique(train, f"{pool}/{name}/train")
        _assert_unique(test, f"{pool}/{name}/test")
        if name != "ood":
            _assert_complement(
                pool=pool,
                name=name,
                universe=universe,
                train=train,
                test=test,
            )

    random_test_sets = []
    for name in RANDOM_NAMES:
        split = load_split(pool, name, data_dir)
        if split["splitter"] != RANDOM_SPLITTER:
            raise AssertionError(f"{pool}/{name}: expected {RANDOM_SPLITTER}")
        params = split["params"]
        expected_fold = int(name.rsplit("_", 1)[1])
        if params != random_params(expected_fold):
            raise AssertionError(f"{pool}/{name}: unexpected random params")
        random_test_sets.append(set(test_ids(split)))
    if set.union(*random_test_sets) != universe_set:
        raise AssertionError(f"{pool}: random folds leave gaps in universe coverage")
    if sum(len(s) for s in random_test_sets) != len(universe_set):
        raise AssertionError(f"{pool}: random fold test sets overlap")
    random_sizes = [len(s) for s in random_test_sets]
    if max(random_sizes) - min(random_sizes) > 1:
        raise AssertionError(f"{pool}: imbalanced random fold sizes")

    cluster_test_sets = []
    for name in CLUSTER_K5_NAMES:
        split = load_split(pool, name, data_dir)
        if split["splitter"] != CLUSTER_K5_SPLITTER:
            raise AssertionError(
                f"{pool}/{name}: expected {CLUSTER_K5_SPLITTER}"
            )
        expected_cluster = int(name.rsplit("_", 1)[1])
        if split["params"] != cluster_k5_params(
            expected_cluster,
            n_init=cluster_k5_n_init(pool),
        ):
            raise AssertionError(f"{pool}/{name}: unexpected cluster params")
        cluster_test_sets.append(set(test_ids(split)))
    if set.union(*cluster_test_sets) != universe_set:
        raise AssertionError(f"{pool}: cluster folds leave gaps in universe coverage")
    if sum(len(s) for s in cluster_test_sets) != len(universe_set):
        raise AssertionError(f"{pool}: cluster fold test sets overlap")

    tau = load_split(pool, "tau", data_dir)
    if tau["splitter"] != TAU_SPLITTER:
        raise AssertionError(f"{pool}/tau: unexpected splitter")
    expected_tau_n = round(0.20 * len(universe))
    if tau["n_test"] != expected_tau_n:
        raise AssertionError(
            f"{pool}/tau: expected {expected_tau_n} test IDs, "
            f"got {tau['n_test']}"
        )

    ood = load_split(pool, "ood", data_dir)
    if ood["splitter"] != OOD_SPLITTER:
        raise AssertionError(f"{pool}/ood: unexpected splitter")
    if ood["params"] != ood_params():
        raise AssertionError(f"{pool}/ood: unexpected params")
    if set(train_ids(ood)) != universe_set:
        raise AssertionError(f"{pool}/ood: train side differs from regular universe")
    if set(test_ids(ood)) & universe_set:
        raise AssertionError(f"{pool}/ood: OOD test overlaps regular universe")
    seen_types = sorted({_ood_type(image_id) for image_id in test_ids(ood)})
    if seen_types != sorted(OOD_TYPES):
        raise AssertionError(f"{pool}/ood: unexpected OOD types {seen_types}")


def validate_all(data_dir: Path) -> None:
    shared_ood = test_ids(load_split("shared", "ood", data_dir))
    for pool in POOLS:
        validate_pool(pool, data_dir)
        pool_ood = test_ids(load_split(pool, "ood", data_dir))
        if pool_ood != shared_ood:
            raise AssertionError(f"{pool}/ood: test IDs differ from shared")
        print(f"{pool}: validation ok")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PACKAGE_SPLIT_DIR,
        help="Package split data directory to validate.",
    )
    args = parser.parse_args()
    validate_all(args.data_dir)


if __name__ == "__main__":
    main()

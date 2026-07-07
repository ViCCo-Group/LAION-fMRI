"""Regenerate the packaged shuffled 5-fold random splits.

The random split family is a single shuffled K-fold partition of each regular
pool. Every image appears in exactly one validation fold across
``random_0`` ... ``random_4``; each train set is the complement of its test
fold.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from common import (
    PACKAGE_SPLIT_DIR,
    POOLS,
    add_write_check_args,
    check_or_write,
    make_single_variant_split,
    pool_label_from_existing,
    regular_pool_ids,
    should_write,
    split_path,
    validate_single_split,
)


DEFAULT_SEED = 42
DEFAULT_FOLDS = 5


def build_random_splits(
    pool: str,
    *,
    seed: int = DEFAULT_SEED,
    folds: int = DEFAULT_FOLDS,
    source_data_dir: Path,
) -> list[tuple[str, dict]]:
    """Return ``random_*`` split payloads for one pool."""

    image_ids = regular_pool_ids(pool, source_data_dir)
    pool_label = pool_label_from_existing(pool, "random_0", source_data_dir)

    shuffled = np.array(image_ids, dtype=object)
    np.random.default_rng(seed).shuffle(shuffled)

    payloads = []
    for fold, test_arr in enumerate(np.array_split(shuffled, folds)):
        name = f"random_{fold}"
        test = [str(x) for x in test_arr.tolist()]
        test_set = set(test)
        train = [image_id for image_id in image_ids if image_id not in test_set]
        payload = make_single_variant_split(
            name=name,
            pool_label=pool_label,
            splitter="random_kfold",
            params={
                "method": "shuffled_5fold_cv",
                "k": folds,
                "seed": seed,
                "fold": fold,
            },
            train=train,
            test=test,
        )
        validate_single_split(payload)
        payloads.append((name, payload))

    return payloads


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_write_check_args(parser)
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Shuffle seed used for the K-fold partition.",
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=DEFAULT_FOLDS,
        help="Number of shuffled CV folds to generate.",
    )
    parser.add_argument(
        "--source-data-dir",
        type=Path,
        default=PACKAGE_SPLIT_DIR,
        help="Split data directory that supplies the regular pool universes.",
    )
    args = parser.parse_args()

    write = should_write(args)
    for pool in POOLS:
        for name, payload in build_random_splits(
            pool,
            seed=args.seed,
            folds=args.folds,
            source_data_dir=args.source_data_dir,
        ):
            check_or_write(
                split_path(pool, name, args.data_dir),
                payload,
                write=write,
            )
        print(f"{pool}: random_0..random_{args.folds - 1} ok")


if __name__ == "__main__":
    main()

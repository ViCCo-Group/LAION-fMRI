"""Create shuffled 5-fold random split payloads from stimuli.

The random split family is a single shuffled K-fold partition of each regular
pool. Pool membership comes from ``task-images_metadata.csv``.
"""

from __future__ import annotations

import argparse

import numpy as np

from split_json import (
    add_write_check_args,
    check_or_write,
    make_single_variant_split,
    ordered_complement,
    should_write,
    split_path,
    validate_single_split,
)
from stimuli import (
    POOLS,
    add_stimuli_arg,
    load_stimulus_metadata,
    pool_image_ids,
    pool_label,
    require_stimuli_dir,
)


RANDOM_NAMES = tuple(f"random_{i}" for i in range(5))
RANDOM_SPLITTER = "random_kfold"
RANDOM_METHOD = "shuffled_5fold_cv"
RANDOM_SEED = 42
RANDOM_FOLDS = 5


def random_params(fold: int) -> dict[str, object]:
    return {
        "method": RANDOM_METHOD,
        "k": RANDOM_FOLDS,
        "seed": RANDOM_SEED,
        "fold": int(fold),
    }


def build_random_splits(
    pool: str,
    *,
    image_ids: list[str],
) -> list[tuple[str, dict]]:
    """Return ``random_*`` split payloads for one pool."""

    shuffled = np.array(image_ids, dtype=object)
    np.random.default_rng(RANDOM_SEED).shuffle(shuffled)

    payloads = []
    for fold, (name, test_arr) in enumerate(
        zip(RANDOM_NAMES, np.array_split(shuffled, RANDOM_FOLDS)),
    ):
        test = [str(x) for x in test_arr.tolist()]
        payload = make_single_variant_split(
            name=name,
            pool_label=pool_label(pool),
            splitter=RANDOM_SPLITTER,
            params=random_params(fold),
            train=ordered_complement(image_ids, test),
            test=test,
        )
        validate_single_split(payload)
        payloads.append((name, payload))

    return payloads


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_write_check_args(parser)
    add_stimuli_arg(parser)
    args = parser.parse_args()

    stimuli_dir = require_stimuli_dir(args.stimuli_dir)
    rows = load_stimulus_metadata(stimuli_dir)
    write = should_write(args)

    for pool in POOLS:
        image_ids = pool_image_ids(rows, pool)
        for name, payload in build_random_splits(pool, image_ids=image_ids):
            check_or_write(
                split_path(pool, name, args.data_dir),
                payload,
                write=write,
            )
        print(f"{pool}: random_0..random_{RANDOM_FOLDS - 1} ok")


if __name__ == "__main__":
    main()

"""Create shuffled 5-fold random split payloads from stimuli.

The random split family is a single shuffled K-fold partition of each regular
pool. Pool membership comes from ``task-images_metadata.csv``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def random_params(fold: int, pool: str = "shared") -> dict[str, object]:
    params = {
        "method": RANDOM_METHOD,
        "k": RANDOM_FOLDS,
        "seed": RANDOM_SEED,
        "fold": int(fold),
    }
    if pool != "shared":
        params["revision"] = 2
    return params


def build_random_splits(
    pool: str,
    *,
    image_ids: list[str],
) -> list[tuple[str, dict]]:
    """Return ``random_*`` split payloads for one pool."""

    shuffled = np.array(image_ids, dtype=object)
    np.random.default_rng(RANDOM_SEED).shuffle(shuffled)

    folds = [part.tolist() for part in np.array_split(shuffled, RANDOM_FOLDS)]
    changes_path = Path(__file__).parent / "data/random_fold_changes.json"
    changes = json.loads(changes_path.read_text()).get(pool, [])
    assignments = {
        image_id: fold for fold, ids in enumerate(folds) for image_id in ids
    }
    for change in changes:
        image_id = change["image_id"]
        if assignments.get(image_id) != change["old_fold"]:
            raise ValueError(f"{pool}: unexpected original fold for {image_id}")
        assignments[image_id] = change["new_fold"]

    payloads = []
    for fold, (name, original) in enumerate(zip(RANDOM_NAMES, folds)):
        original_set = set(original)
        additions = sorted(
            image_id for image_id, assigned in assignments.items()
            if assigned == fold and image_id not in original_set
        )
        departures = sum(assignments[n] != fold for n in original)
        if len(additions) != departures:
            raise ValueError(f"{pool}/{name}: correction changes fold size")
        incoming = iter(additions)
        # Replace departing images in place, preserving all other ordering.
        test = [
            image_id if assignments[image_id] == fold else next(incoming)
            for image_id in original
        ]
        payload = make_single_variant_split(
            name=name,
            pool_label=pool_label(pool),
            splitter=RANDOM_SPLITTER,
            params=random_params(fold, pool),
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

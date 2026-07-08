"""Create OOD holdout split payloads from stimulus metadata.

The OOD split is defined by the stimuli themselves: train is the pool's regular
non-OOD images, and test is the shared OOD stimulus set.
"""

from __future__ import annotations

import argparse

from common import (
    OOD_SPLITTER,
    POOLS,
    add_stimuli_arg,
    add_write_check_args,
    check_or_write,
    load_stimulus_metadata,
    make_single_variant_split,
    ood_params,
    ood_pool_label,
    ood_image_ids_from_metadata,
    pool_image_ids,
    require_stimuli_dir,
    should_write,
    split_path,
    validate_single_split,
)


def build_ood_split(
    pool: str,
    *,
    image_ids: list[str],
    ood_ids: list[str],
) -> dict:
    payload = make_single_variant_split(
        name="ood",
        pool_label=ood_pool_label(pool),
        splitter=OOD_SPLITTER,
        params=ood_params(),
        train=image_ids,
        test=ood_ids,
    )
    validate_single_split(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_write_check_args(parser)
    add_stimuli_arg(parser)
    args = parser.parse_args()

    stimuli_dir = require_stimuli_dir(args.stimuli_dir)
    rows = load_stimulus_metadata(stimuli_dir)
    ood_ids = ood_image_ids_from_metadata(rows)
    write = should_write(args)

    for pool in POOLS:
        payload = build_ood_split(
            pool,
            image_ids=pool_image_ids(rows, pool),
            ood_ids=ood_ids,
        )
        check_or_write(
            split_path(pool, "ood", args.data_dir),
            payload,
            write=write,
        )
        print(f"{pool}: ood ok")


if __name__ == "__main__":
    main()

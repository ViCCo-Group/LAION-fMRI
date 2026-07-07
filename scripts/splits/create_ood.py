"""Regenerate the packaged OOD holdout split.

The tracked repository currently does not contain a raw all-stimulus manifest
that independently defines each regular pool and the 371 OOD stimuli. This
script therefore rebuilds ``ood.json`` from a source split-data directory:
the source ``ood`` train side defines each regular pool, and the source shared
``ood`` test side defines the common OOD holdout.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    OOD_TYPES,
    PACKAGE_SPLIT_DIR,
    POOLS,
    add_write_check_args,
    check_or_write,
    make_single_variant_split,
    ood_image_ids,
    pool_label_from_existing,
    regular_pool_ids,
    should_write,
    split_path,
    validate_single_split,
)


def build_ood_split(pool: str, *, source_data_dir: Path) -> dict:
    regular_ids = regular_pool_ids(pool, source_data_dir)
    ood_ids = ood_image_ids(source_data_dir)
    pool_label = pool_label_from_existing(pool, "ood", source_data_dir)
    payload = make_single_variant_split(
        name="ood",
        pool_label=pool_label,
        splitter="ood_holdout",
        params={
            "method": "ood_dataset_holdout",
            "ood_types": list(OOD_TYPES),
        },
        train=regular_ids,
        test=ood_ids,
    )
    validate_single_split(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_write_check_args(parser)
    parser.add_argument(
        "--source-data-dir",
        type=Path,
        default=PACKAGE_SPLIT_DIR,
        help=(
            "Split data directory that supplies the regular pool universes "
            "and shared OOD image list."
        ),
    )
    args = parser.parse_args()

    write = should_write(args)
    for pool in POOLS:
        payload = build_ood_split(pool, source_data_dir=args.source_data_dir)
        check_or_write(
            split_path(pool, "ood", args.data_dir),
            payload,
            write=write,
        )
        print(f"{pool}: ood ok")


if __name__ == "__main__":
    main()

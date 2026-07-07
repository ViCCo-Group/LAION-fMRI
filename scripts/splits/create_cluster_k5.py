"""Package the finalized CLIP k-means cluster holdout splits.

The cluster splits were selected upstream in the min-NN generalization
pipeline and exported as finalized per-pool split JSON files. This script
normalizes those finalized artifacts into ``laion_fmri/splits/data`` and
checks that they reproduce the packaged ``cluster_k5_*`` splits.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    CLUSTER_K5_NAMES,
    FINALIZED_MIN_NN_DIR,
    POOLS,
    check_or_write,
    finalized_split_path,
    load_json,
    make_single_variant_split,
    should_write,
    split_path,
    validate_single_split,
    variant,
    add_write_check_args,
)


def _load_finalized_cluster(
    pool: str,
    name: str,
    *,
    finalized_root: Path,
) -> dict:
    source_path = finalized_split_path(finalized_root, pool, name)
    if not source_path.exists():
        raise FileNotFoundError(
            f"missing finalized cluster split artifact: {source_path}"
        )
    source = load_json(source_path)
    source_variant = variant(source)
    payload = make_single_variant_split(
        name=name,
        pool_label=str(source["pool"]),
        splitter=str(source["splitter"]),
        params=dict(source["params"]),
        train=source_variant["train_ids"],
        test=source_variant["test_ids"],
    )
    validate_single_split(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_write_check_args(parser)
    parser.add_argument(
        "--finalized-root",
        type=Path,
        default=FINALIZED_MIN_NN_DIR,
        help="Root containing finalized min-NN split artifacts.",
    )
    args = parser.parse_args()

    write = should_write(args)
    for pool in POOLS:
        for name in CLUSTER_K5_NAMES:
            payload = _load_finalized_cluster(
                pool,
                name,
                finalized_root=args.finalized_root,
            )
            check_or_write(
                split_path(pool, name, args.data_dir),
                payload,
                write=write,
            )
        print(f"{pool}: cluster_k5_0..cluster_k5_4 ok")


if __name__ == "__main__":
    main()

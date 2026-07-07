"""Package the finalized adaptive tau split.

The shipped ``tau`` split is the balanced adaptive stochastic min-NN split
selected by the upstream min-NN generalization pipeline. This script reads the
finalized tau artifact for each pool, renames it to the public split name
``tau``, and checks or writes the packaged JSON.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    FINALIZED_MIN_NN_DIR,
    POOLS,
    add_write_check_args,
    check_or_write,
    finalized_split_path,
    load_json,
    make_single_variant_split,
    should_write,
    split_path,
    validate_single_split,
    variant,
)


TAU_TIERS = ("permissive", "balanced", "tight")


def build_tau_split(
    pool: str,
    *,
    tier: str,
    finalized_root: Path,
    output_name: str,
) -> dict:
    source_name = f"tau_{tier}_adaptive_stochastic"
    source_path = finalized_split_path(finalized_root, pool, source_name)
    if not source_path.exists():
        raise FileNotFoundError(
            f"missing finalized tau split artifact: {source_path}"
        )
    source = load_json(source_path)
    source_variant = variant(source)
    payload = make_single_variant_split(
        name=output_name,
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
    parser.add_argument(
        "--tier",
        choices=TAU_TIERS,
        default="balanced",
        help="Adaptive tau tier to package.",
    )
    parser.add_argument(
        "--output-name",
        default="tau",
        help="Public split name to write/check.",
    )
    args = parser.parse_args()

    write = should_write(args)
    for pool in POOLS:
        payload = build_tau_split(
            pool,
            tier=args.tier,
            finalized_root=args.finalized_root,
            output_name=args.output_name,
        )
        check_or_write(
            split_path(pool, args.output_name, args.data_dir),
            payload,
            write=write,
        )
        print(f"{pool}: {args.output_name} ok")


if __name__ == "__main__":
    main()

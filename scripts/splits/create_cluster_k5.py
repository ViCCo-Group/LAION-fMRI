"""Demonstrate CLIP k-means K=5 cluster holdout construction."""

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
from features import (
    add_feature_runtime_args,
    feature_runtime_kwargs,
    load_feature_mats,
)
from stimuli import (
    POOLS,
    add_stimuli_arg,
    load_stimulus_metadata,
    pool_image_ids,
    pool_label,
    require_stimuli_dir,
)


CLUSTER_K5_NAMES = tuple(f"cluster_k5_{i}" for i in range(5))
CLUSTER_K5_SPLITTER = "kmeans_cluster_holdout"
CLUSTER_K5_METHOD = "kmeans_clip_k5_holdout"
CLUSTER_K5_FEATURE_SPACE = "CLIP"
CLUSTER_K5_K = 5
CLUSTER_K5_SEED = 2026
CLUSTER_K5_DEFAULT_N_INIT = 10
# The split-construction method used five k-means++ restarts for sub-05
# and ten for the other pools.
CLUSTER_K5_N_INIT_BY_POOL = {"sub-05": 5}


def cluster_k5_n_init(pool: str) -> int:
    return CLUSTER_K5_N_INIT_BY_POOL.get(pool, CLUSTER_K5_DEFAULT_N_INIT)


def cluster_k5_params(
    held_out_cluster: int,
    *,
    n_init: int,
) -> dict[str, object]:
    return {
        "method": CLUSTER_K5_METHOD,
        "feature_space": CLUSTER_K5_FEATURE_SPACE,
        "n_clusters": CLUSTER_K5_K,
        "seed": CLUSTER_K5_SEED,
        "n_init": int(n_init),
        "held_out_cluster": int(held_out_cluster),
    }


def build_cluster_splits(
    pool: str,
    *,
    image_ids: list[str],
    clip_features: np.ndarray,
) -> list[tuple[str, dict]]:
    try:
        from sklearn.cluster import KMeans
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "cluster split generation requires scikit-learn"
        ) from exc

    n_init = cluster_k5_n_init(pool)
    km = KMeans(
        n_clusters=CLUSTER_K5_K,
        random_state=CLUSTER_K5_SEED,
        n_init=n_init,
    ).fit(clip_features)
    labels = km.labels_

    payloads = []
    for cluster_id, name in enumerate(CLUSTER_K5_NAMES):
        test = [
            image_id
            for image_id, label in zip(image_ids, labels)
            if int(label) == cluster_id
        ]
        payload = make_single_variant_split(
            name=name,
            pool_label=pool_label(pool),
            splitter=CLUSTER_K5_SPLITTER,
            params=cluster_k5_params(
                cluster_id,
                n_init=n_init,
            ),
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
    add_feature_runtime_args(
        parser,
        extract_help=(
            "Extract missing CLIP features from task-images_stimuli.h5."
        ),
    )
    args = parser.parse_args()

    stimuli_dir = require_stimuli_dir(args.stimuli_dir)
    rows = load_stimulus_metadata(stimuli_dir)
    write = should_write(args)

    for pool in POOLS:
        image_ids = pool_image_ids(rows, pool)
        mats = load_feature_mats(
            spaces=[CLUSTER_K5_FEATURE_SPACE],
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            **feature_runtime_kwargs(args),
        )
        for name, payload in build_cluster_splits(
            pool,
            image_ids=image_ids,
            clip_features=mats["clip"],
        ):
            check_or_write(
                split_path(pool, name, args.data_dir),
                payload,
                write=write,
            )
        print(f"{pool}: cluster_k5_0..cluster_k5_4 ok")


if __name__ == "__main__":
    main()

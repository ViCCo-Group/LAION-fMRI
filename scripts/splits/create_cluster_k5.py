"""Demonstrate CLIP k-means K=5 cluster holdout construction."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from common import (
    CLUSTER_K5_DEFAULT_N_INIT,
    CLUSTER_K5_FEATURE_SPACE,
    CLUSTER_K5_K,
    CLUSTER_K5_NAMES,
    CLUSTER_K5_SEED,
    CLUSTER_K5_SPLITTER,
    POOLS,
    add_stimuli_arg,
    add_write_check_args,
    check_or_write,
    cluster_k5_n_init,
    cluster_k5_params,
    load_stimulus_metadata,
    make_single_variant_split,
    ordered_complement,
    pool_image_ids,
    pool_label,
    require_stimuli_dir,
    should_write,
    split_path,
    validate_single_split,
)
from features import load_feature_mats


def build_cluster_splits(
    pool: str,
    *,
    image_ids: list[str],
    clip_features: np.ndarray,
    seed: int = CLUSTER_K5_SEED,
    k: int = CLUSTER_K5_K,
    n_init: int = CLUSTER_K5_DEFAULT_N_INIT,
) -> list[tuple[str, dict]]:
    try:
        from sklearn.cluster import KMeans
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "cluster split generation requires scikit-learn"
        ) from exc

    km = KMeans(
        n_clusters=k,
        random_state=seed,
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
                k=k,
                seed=seed,
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
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("temp/split_feature_cache"),
        help="Feature cache directory.",
    )
    parser.add_argument(
        "--extract-missing",
        action="store_true",
        help="Extract missing CLIP features from task-images_stimuli.h5.",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--clip-model", default="ViT-L-14-CLIPA")
    parser.add_argument("--clip-pretrained", default="datacomp1b")
    parser.add_argument("--seed", type=int, default=CLUSTER_K5_SEED)
    parser.add_argument(
        "--n-init",
        type=int,
        default=None,
        help=(
            "KMeans n_init override. Defaults to the original per-pool values "
            "used by the split-construction method."
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
            cache_dir=args.cache_dir,
            extract_missing=args.extract_missing,
            batch_size=args.batch_size,
            device=args.device,
            clip_model=args.clip_model,
            clip_pretrained=args.clip_pretrained,
            dinov2_model="dinov2_vitl14",
            use_release_embeddings=False,
        )
        for name, payload in build_cluster_splits(
            pool,
            image_ids=image_ids,
            clip_features=mats["clip"],
            seed=args.seed,
            n_init=(
                args.n_init
                if args.n_init is not None
                else cluster_k5_n_init(pool)
            ),
        ):
            check_or_write(
                split_path(pool, name, args.data_dir),
                payload,
                write=write,
            )
        print(f"{pool}: cluster_k5_0..cluster_k5_4 ok")


if __name__ == "__main__":
    main()

"""Create tau and cluster splits over the combined regular image pool."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from create_tau import select_tau_indices
from features import (
    add_feature_runtime_args, feature_runtime_kwargs, load_feature_mats,
)
from split_json import (
    add_write_check_args, check_or_write, make_single_variant_split,
    ordered_complement, should_write, split_path, validate_single_split,
)
from stimuli import (
    add_stimuli_arg, load_stimulus_metadata, pool_image_ids, pool_label,
    require_stimuli_dir,
)

GROUPS_PATH = Path(__file__).parent / "data/pooled_duplicate_groups.json"
IMAGE_GROUPS_PATH = Path(__file__).parent / "data/pooled_image_groups.json"
POOLED_NAMES = ("tau",) + tuple(f"cluster_k5_{k}" for k in range(5))


def image_groups(image_ids: list[str], groups=None) -> list[list[int]]:
    """Return supplied groups and singleton images as index lists."""
    if groups is None:
        groups = json.loads(GROUPS_PATH.read_text())
    lookup = {name: i for i, name in enumerate(image_ids)}
    groups = [
        [lookup[name] for name in group]
        for group in groups
    ]
    used = {i for group in groups for i in group}
    if sum(map(len, groups)) != len(used):
        raise ValueError("Image groups overlap")
    groups.extend([i] for i in range(len(image_ids)) if i not in used)
    return sorted(groups, key=lambda group: min(group))


def cluster_labels(x: np.ndarray, groups: list[list[int]]) -> np.ndarray:
    """Fit five clusters, assigning each image group as one unit."""
    from sklearn.cluster import KMeans

    means = np.stack([x[group].mean(0) for group in groups])
    sizes = np.array([len(group) for group in groups])
    model = KMeans(n_clusters=5, random_state=2026, n_init=10)
    labels = model.fit_predict(means, sample_weight=sizes)
    per_image = np.empty(len(x), dtype=np.int64)
    for group, label in zip(groups, labels):
        per_image[group] = label
    return per_image


def payload(name, image_ids, indices, splitter, params):
    test = [image_ids[int(i)] for i in indices]
    out = make_single_variant_split(
        name=name, pool_label=pool_label("pooled"), splitter=splitter,
        params=params, train=ordered_complement(image_ids, test), test=test,
    )
    validate_single_split(out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_stimuli_arg(parser)
    add_write_check_args(parser)
    add_feature_runtime_args(parser, extract_help="Extract missing features.")
    parser.add_argument("--diagnostics", type=Path)
    args = parser.parse_args()
    stimuli_dir = require_stimuli_dir(args.stimuli_dir)
    rows = load_stimulus_metadata(stimuli_dir)
    ids = pool_image_ids(rows, "pooled")
    mats = load_feature_mats(
        spaces=("clip", "dreamsim", "dinov2"), rows=rows,
        stimuli_dir=stimuli_dir, image_ids=ids, **feature_runtime_kwargs(args),
    )
    duplicate_groups = image_groups(ids)
    groups_hash = hashlib.sha256(GROUPS_PATH.read_bytes()).hexdigest()
    group_spec = json.loads(IMAGE_GROUPS_PATH.read_text())
    groups = image_groups(ids, group_spec["groups"])
    labels = cluster_labels(mats["clip"], groups)
    labels = np.asarray(group_spec["cluster_label_order"])[labels]
    for k in range(5):
        name = f"cluster_k5_{k}"
        out = payload(name, ids, np.where(labels == k)[0],
                      "kmeans_cluster_holdout", {
                          "method": "kmeans_clip_k5_holdout",
                          "feature_space": "CLIP", "n_clusters": 5,
                          "seed": 2026, "n_init": 10,
                          "held_out_cluster": k,
                          "duplicate_groups_sha256": groups_hash,
                          "image_groups_sha256": hashlib.sha256(
                              IMAGE_GROUPS_PATH.read_bytes()
                          ).hexdigest(),
                          "cosine_distance_cutoffs": group_spec[
                              "cosine_distance_cutoffs"
                          ],
                      })
        check_or_write(split_path("pooled", name, args.data_dir), out,
                       write=should_write(args))
        print(f"pooled/{name}: {out['n_train']} / {out['n_test']}", flush=True)

    # Isolated test images are selected from images without known duplicates.
    # All copies remain in training, so no duplicate group can cross sides.
    eligible = np.ones(len(ids), dtype=bool)
    for group in duplicate_groups:
        if len(group) > 1:
            eligible[group] = False
    sweep = []

    def progress(row):
        sweep.append(row)
        print(f"tau percentile {row['percentile']:.0f}: "
              f"MMD/random {row['ratio_to_random']:.4f}", flush=True)
        if args.diagnostics:
            args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
            args.diagnostics.write_text(json.dumps(sweep, indent=2) + "\n")

    indices, selection = select_tau_indices(
        mats, eligible=eligible, progress=progress,
    )
    out = payload("tau", ids, indices, "min_nn_stochastic", {
        "method": "min_nn_filter + stochastic_mmd_swap",
        "adaptive_selection": selection,
        "duplicate_images_in_training": int((~eligible).sum()),
        "duplicate_groups_sha256": groups_hash,
    })
    check_or_write(split_path("pooled", "tau", args.data_dir), out,
                   write=should_write(args))
    print(f"pooled/tau: {out['n_train']} / {out['n_test']}; {selection}",
          flush=True)


if __name__ == "__main__":
    main()

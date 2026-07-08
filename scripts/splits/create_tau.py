"""Demonstrate adaptive tau split construction from stimulus embeddings.

This implements the min-NN + stochastic MMD-swap procedure from stimulus
metadata and feature spaces.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from common import (
    POOLS,
    add_stimuli_arg,
    add_write_check_args,
    check_or_write,
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


TARGET_RATIOS = {
    "permissive": 0.40,
    "balanced": 1.00,
    "tight": 1.80,
}
TAU_CRITERION = {
    "permissive": "MMD-matched (≤ 0.5× random)",
    "balanced": "MMD-matched (≤ 1.0× random)",
    "tight": "MMD-matched (≤ 2.0× random)",
}
ADAPTIVE_PERCENTILES = sorted(set(
    [p for p in range(5, 50, 5)]
    + [p for p in range(50, 86, 1)]
    + [p for p in range(86, 93, 2)]
))


def _mmd2(x: np.ndarray, mask: np.ndarray) -> float:
    diff = x[mask].mean(0) - x[~mask].mean(0)
    return float((diff * diff).sum())


def _lonely_worst_percentile(mats: dict[str, np.ndarray]) -> np.ndarray:
    pct_per_space = []
    for x in mats.values():
        dist = 1.0 - x @ x.T
        np.fill_diagonal(dist, np.inf)
        dist = dist.astype(np.float32)
        lonely = dist.min(axis=1)
        order = np.argsort(lonely)
        ranks = np.empty_like(order)
        ranks[order] = np.arange(len(lonely))
        pct = ranks.astype(np.float64) / max(len(lonely) - 1, 1)
        pct_per_space.append(pct.astype(np.float32))
    return np.stack(pct_per_space).min(axis=0).astype(np.float32)


def _random_baseline(
    mats: dict[str, np.ndarray],
    *,
    n_test: int,
    seed: int,
    n_draws: int,
) -> tuple[dict[str, float], float]:
    rng = np.random.default_rng(seed)
    n = next(iter(mats.values())).shape[0]
    values = {space: [] for space in mats}
    for _ in range(n_draws):
        mask = np.zeros(n, dtype=bool)
        mask[rng.choice(n, n_test, replace=False)] = True
        for space, x in mats.items():
            values[space].append(_mmd2(x, mask))
    per_space = {space: float(np.mean(v)) for space, v in values.items()}
    return per_space, float(np.mean(list(per_space.values())))


def _best_of_n_seed(
    mats: dict[str, np.ndarray],
    feasible: np.ndarray,
    n_test: int,
    n_samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    n = next(iter(mats.values())).shape[0]
    n_feasible = len(feasible)
    if n_test >= n_feasible:
        return feasible

    u = rng.random((n_samples, n_feasible), dtype=np.float32)
    pick_local = np.argpartition(u, n_test, axis=1)[:, :n_test]
    pick_abs = feasible[pick_local]
    n_train = n - n_test

    masks = np.zeros((n_samples, n), dtype=bool)
    masks[np.repeat(np.arange(n_samples), n_test), pick_abs.ravel()] = True
    masks_f = masks.astype(np.float32)
    total = np.zeros(n_samples, dtype=np.float64)
    for x in mats.values():
        sum_test = masks_f @ x
        sum_all = x.sum(0, keepdims=True)
        sum_train = sum_all - sum_test
        diff = sum_test / n_test - sum_train / n_train
        total += (diff * diff).sum(1).astype(np.float64)
    return pick_abs[int(np.argmin(total))]


def _refine_mmd_stochastic(
    mats: dict[str, np.ndarray],
    feasible: np.ndarray,
    test_idx: np.ndarray,
    *,
    n_steps: int,
    seed: int,
    t0: float | None = None,
    tf: float = 1e-10,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = next(iter(mats.values())).shape[0]
    space_mats = list(mats.values())
    test_idx = np.asarray(test_idx, dtype=np.int64).copy()
    feasible = np.asarray(feasible, dtype=np.int64)
    n_test = len(test_idx)
    n_train = n - n_test
    if n_test == 0 or n_train == 0:
        return test_idx
    coeff = 1.0 / n_test + 1.0 / n_train

    sum_all = [x.sum(0) for x in space_mats]
    sum_test = [x[test_idx].sum(0) for x in space_mats]
    vec = [coeff * s - s_all / n_train
           for s, s_all in zip(sum_test, sum_all)]

    is_test = np.zeros(n, dtype=bool)
    is_test[test_idx] = True
    non_test_feasible = feasible[~is_test[feasible]].tolist()
    if not non_test_feasible:
        return test_idx

    def delta_mmd(i_out: int, j_in: int) -> float:
        delta_sum = 0.0
        for i, x in enumerate(space_mats):
            d = x[j_in] - x[i_out]
            delta_sum += (
                2.0 * coeff * float(vec[i] @ d)
                + (coeff * coeff) * float(d @ d)
            )
        return delta_sum

    cur_mmd = float(sum(v @ v for v in vec))
    best_mmd = cur_mmd
    best_test_idx = test_idx.copy()

    if t0 is None:
        samples = []
        for _ in range(100):
            a = int(rng.integers(0, n_test))
            i_out = int(test_idx[a])
            j_in = non_test_feasible[
                int(rng.integers(0, len(non_test_feasible)))
            ]
            samples.append(abs(delta_mmd(i_out, j_in)))
        t0 = max(float(np.median(samples)), 1e-10)

    log_ratio = np.log(max(tf, 1e-30) / max(t0, 1e-30))
    for step in range(n_steps):
        temp = t0 * np.exp(log_ratio * step / n_steps)
        a = int(rng.integers(0, n_test))
        i_out = int(test_idx[a])
        jb = int(rng.integers(0, len(non_test_feasible)))
        j_in = int(non_test_feasible[jb])
        delta = delta_mmd(i_out, j_in)
        accept = (
            delta < 0
            or rng.random() < np.exp(-delta / max(temp, 1e-30))
        )
        if accept:
            for i, x in enumerate(space_mats):
                diff = x[j_in] - x[i_out]
                sum_test[i] = sum_test[i] + diff
                vec[i] = vec[i] + coeff * diff
            test_idx[a] = j_in
            is_test[i_out] = False
            is_test[j_in] = True
            non_test_feasible[jb] = i_out
            cur_mmd += delta
            if cur_mmd < best_mmd:
                best_mmd = cur_mmd
                best_test_idx = test_idx.copy()
    return best_test_idx


def _log_distance(ratio: float, target: float) -> float:
    return abs(np.log(max(ratio, 1e-12)) - np.log(target))


def select_tau_indices(
    mats: dict[str, np.ndarray],
    *,
    tier: str,
    target_frac: float,
    target_ratio: float,
    baseline_draws: int,
    n_seed_samples: int,
    anneal_steps: int,
    seed: int,
) -> tuple[np.ndarray, dict[str, float]]:
    n = next(iter(mats.values())).shape[0]
    n_test = int(round(target_frac * n))
    lonely_worst = _lonely_worst_percentile(mats)
    baseline_per_space, baseline_mean = _random_baseline(
        mats,
        n_test=n_test,
        seed=seed,
        n_draws=baseline_draws,
    )

    rng = np.random.default_rng(seed)
    sweep = []
    for percentile in ADAPTIVE_PERCENTILES:
        tau = float(np.quantile(lonely_worst, percentile / 100.0))
        feasible = np.where(lonely_worst > tau)[0].astype(np.int64)
        if len(feasible) < n_test:
            continue
        seed_test = _best_of_n_seed(
            mats,
            feasible,
            n_test,
            n_seed_samples,
            rng,
        )
        refined = _refine_mmd_stochastic(
            mats,
            feasible,
            seed_test,
            n_steps=anneal_steps,
            seed=seed,
        )
        mask = np.zeros(n, dtype=bool)
        mask[refined] = True
        mmd_per_space = {space: _mmd2(x, mask) for space, x in mats.items()}
        mmd_mean = float(np.mean(list(mmd_per_space.values())))
        sweep.append({
            "tau": tau,
            "percentile": float(percentile),
            "n_feasible": int(len(feasible)),
            "test_idx": refined,
            "mmd2_mean": mmd_mean,
            "ratio_to_random": mmd_mean / baseline_mean,
            "random_baseline_mmd2": baseline_per_space,
            "random_baseline_mmd2_mean": baseline_mean,
        })

    if not sweep:
        raise RuntimeError("feasible tau candidate set is empty")

    chosen = min(
        sweep,
        key=lambda row: _log_distance(row["ratio_to_random"], target_ratio),
    )
    refined = np.asarray(chosen["test_idx"], dtype=np.int64)
    mask = np.zeros(n, dtype=bool)
    mask[refined] = True
    mmd_per_space = {space: _mmd2(x, mask) for space, x in mats.items()}
    mmd_mean = float(np.mean(list(mmd_per_space.values())))
    selection = {
        "criterion": "mmd_matched_log_closest",
        "tier": tier,
        "target_ratio_x_random": float(target_ratio),
        "tau": float(chosen["tau"]),
        "percentile": float(chosen["percentile"]),
        "mmd2_mean": mmd_mean,
        "ratio_to_random": mmd_mean / baseline_mean,
    }
    return np.where(mask)[0].astype(np.int64), selection


def build_tau_split(
    pool: str,
    *,
    image_ids: list[str],
    mats: dict[str, np.ndarray],
    tier: str,
    target_frac: float,
    baseline_draws: int,
    n_seed_samples: int,
    anneal_steps: int,
    seed: int,
    output_name: str,
) -> dict:
    target_ratio = TARGET_RATIOS[tier]
    test_idx, selection = select_tau_indices(
        mats,
        tier=tier,
        target_frac=target_frac,
        target_ratio=target_ratio,
        baseline_draws=baseline_draws,
        n_seed_samples=n_seed_samples,
        anneal_steps=anneal_steps,
        seed=seed,
    )
    test = [image_ids[int(i)] for i in test_idx]
    payload = make_single_variant_split(
        name=output_name,
        pool_label=pool_label(pool),
        splitter="min_nn_stochastic",
        params={
            "method": "min_nn_filter + stochastic_mmd_swap",
            "criterion": TAU_CRITERION[tier],
            "adaptive_selection": selection,
        },
        train=ordered_complement(image_ids, test),
        test=test,
    )
    validate_single_split(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_write_check_args(parser)
    add_stimuli_arg(parser)
    parser.add_argument(
        "--spaces",
        default="CLIP,DreamSim,DINOv2",
        help="Comma-separated feature spaces used for tau isolation/MMD.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("temp/split_feature_cache"),
        help="Feature cache directory.",
    )
    parser.add_argument(
        "--extract-missing",
        action="store_true",
        help="Extract missing features from task-images_stimuli.h5.",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--clip-model", default="ViT-L-14-CLIPA")
    parser.add_argument("--clip-pretrained", default="datacomp1b")
    parser.add_argument("--dinov2-model", default="vit_base_patch14_dinov2.lvd142m")
    parser.add_argument("--tier", choices=tuple(TARGET_RATIOS), default="balanced")
    parser.add_argument("--output-name", default="tau")
    parser.add_argument("--target-frac", type=float, default=0.20)
    parser.add_argument("--baseline-draws", type=int, default=50)
    parser.add_argument("--n-seed-samples", type=int, default=1500)
    parser.add_argument("--anneal-steps", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    stimuli_dir = require_stimuli_dir(args.stimuli_dir)
    rows = load_stimulus_metadata(stimuli_dir)
    spaces = [x.strip() for x in args.spaces.split(",") if x.strip()]
    write = should_write(args)

    for pool in POOLS:
        image_ids = pool_image_ids(rows, pool)
        mats = load_feature_mats(
            spaces=spaces,
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            cache_dir=args.cache_dir,
            extract_missing=args.extract_missing,
            batch_size=args.batch_size,
            device=args.device,
            clip_model=args.clip_model,
            clip_pretrained=args.clip_pretrained,
            dinov2_model=args.dinov2_model,
            use_release_embeddings=False,
        )
        payload = build_tau_split(
            pool,
            image_ids=image_ids,
            mats=mats,
            tier=args.tier,
            target_frac=args.target_frac,
            baseline_draws=args.baseline_draws,
            n_seed_samples=args.n_seed_samples,
            anneal_steps=args.anneal_steps,
            seed=args.seed,
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

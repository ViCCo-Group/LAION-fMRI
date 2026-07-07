# Split Generation Scripts

This directory contains maintainer scripts for reproducing the JSON split
files shipped in `laion_fmri/splits/data`.

Run scripts without `--write` to check the generated payloads against the
current package data:

```bash
python scripts/splits/create_ood.py --check
python scripts/splits/create_random.py --check
python scripts/splits/create_cluster_k5.py --check
python scripts/splits/create_tau.py --check
python scripts/splits/validate.py
```

Use `--write` to rewrite the target `--data-dir`.

## Sources

- `create_ood.py` rebuilds `ood.json` from a source split-data directory. The
  tracked repository currently has no independent raw all-stimulus manifest, so
  the source `ood` train side defines each regular pool and the shared source
  `ood` test side defines the common 371-image OOD holdout.
- `create_random.py` rebuilds `random_0` ... `random_4` as one shuffled
  5-fold CV partition of each regular pool, using `seed=42`.
- `create_cluster_k5.py` packages the finalized CLIP k-means holdout artifacts
  from `experiments/generalization_split/min_nn/<pool>/splits`.
- `create_tau.py` packages the finalized adaptive tau artifact. By default it
  reads `tau_balanced_adaptive_stochastic.json` and writes/checks the public
  `tau.json` split.
- `validate.py` checks schema-level invariants plus cross-split invariants:
  random and cluster test folds are disjoint full partitions, every train side
  is the ordered complement of its test side, OOD tests are identical across
  pools, and tau is a 20% holdout of the regular pool.

The public subject-pool names and historical finalized artifact names differ.
The mapping is centralized in `common.py` so the package continues to reproduce
the existing split IDs and labels exactly.

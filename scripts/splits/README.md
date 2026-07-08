# Split Method Scripts

This directory contains standalone scripts demonstrating how the split families
are constructed from stimulus metadata and visual embeddings.

The scripts derive split membership from released stimulus inputs:

- `task-images_metadata.csv` defines shared, OOD, and participant-unique image
  pools.
- `task-images_stimuli.h5` is used when image embeddings need to be extracted.
- Feature caches under `--cache-dir` are used when present. Pass
  `--extract-missing` to compute embeddings from `task-images_stimuli.h5`.
- Method inputs are stimulus metadata, stimulus images, and visual embeddings.

Pass `--stimuli-dir /path/to/stimuli` to every method script.

## Commands

Run deterministic split checks and invariants:

```bash
python scripts/splits/create_ood.py --check --stimuli-dir /path/to/stimuli
python scripts/splits/create_random.py --check --stimuli-dir /path/to/stimuli
python scripts/splits/validate.py
```

Generate feature-based method payloads:

```bash
python scripts/splits/create_cluster_k5.py --write --stimuli-dir /path/to/stimuli
python scripts/splits/create_tau.py --write --stimuli-dir /path/to/stimuli
```

Use `--data-dir` to choose where JSON payloads are compared or written.

## Feature Splits

`create_cluster_k5.py` uses `open_clip` `ViT-L-14-CLIPA` with
`pretrained="datacomp1b"` and reruns K-means with `random_state=2026`.
It uses the per-pool `n_init` values from the split-construction method.

`create_tau.py` uses CLIPA, DreamSim, and `timm`
`vit_base_patch14_dinov2.lvd142m` by default. It recomputes nearest-neighbor
isolation, sweeps adaptive tau percentiles, seeds candidates by best-of-N MMD,
and runs stochastic MMD-swap refinement as a method demonstration.

Feature-based scripts need a compatible feature cache or `--extract-missing`.
Optional extraction dependencies:

```bash
pip install torch torchvision open_clip_torch timm scikit-learn dreamsim h5py
```

Feature arrays are cached under `temp/split_feature_cache` by default; override
with `--cache-dir`.

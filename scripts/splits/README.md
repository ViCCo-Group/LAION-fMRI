# Split Generation Scripts

This directory contains standalone maintainer scripts for regenerating the JSON
split files shipped in `laion_fmri/splits/data`.

The scripts derive split membership from the released stimuli:

- `task-images_metadata.csv` defines shared, OOD, and participant-unique image
  pools.
- `task-images_stimuli.h5` is used when image embeddings need to be extracted.
- Feature caches under `--cache-dir` are used when present. Otherwise,
  feature-based scripts require `--extract-missing` so they can compute the
  exact embeddings from `task-images_stimuli.h5`.
- No script reads `experiments/` artifacts or existing split JSONs as its
  generation source.

By default, scripts discover stimuli via `LAION_FMRI_STIMULI_DIR`,
`LAION_FMRI_DATA/stimuli`, or the configured `laion-fmri` data directory.
You can also pass `--stimuli-dir /path/to/stimuli`.

## Commands

Check generated JSONs against the package data:

```bash
python scripts/splits/create_ood.py --check --stimuli-dir /path/to/stimuli
python scripts/splits/create_random.py --check --stimuli-dir /path/to/stimuli
python scripts/splits/create_cluster_k5.py --check --stimuli-dir /path/to/stimuli
python scripts/splits/create_tau.py --check --stimuli-dir /path/to/stimuli
python scripts/splits/validate.py
```

Use `--write` to rewrite the target `--data-dir`.

## Feature Splits

`create_cluster_k5.py` uses `open_clip` `ViT-L-14-CLIPA` with
`pretrained="datacomp1b"` and reruns K-means with `random_state=2026`.
It uses the original per-pool `n_init` values from the packaged split
generation.

`create_tau.py` uses CLIPA, DreamSim, and `timm`
`vit_base_patch14_dinov2.lvd142m` by default. It recomputes nearest-neighbor
isolation, sweeps adaptive tau percentiles, seeds candidates by best-of-N MMD,
and runs stochastic MMD-swap refinement.

Feature-based scripts need an exact feature cache or `--extract-missing`.
Optional extraction dependencies:

```bash
pip install torch torchvision open_clip_torch timm scikit-learn dreamsim h5py
```

Feature arrays are cached under `temp/split_feature_cache` by default; override
with `--cache-dir`.

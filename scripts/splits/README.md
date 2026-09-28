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

## Random split correction

The random generator applies `data/random_fold_changes.json` after the
seeded shuffle. This records the 66 reviewed assignment changes while
preserving fold sizes and the ordering of unaffected images. The validator
checks `data/duplicate_groups.json` to ensure identified duplicate images
stay in one fold. The original files are in `archive/splits/random-v1.zip`.

## Across-subject splits

Generate the pooled tau and cluster splits with:

```bash
python scripts/splits/create_pooled.py --write --stimuli-dir /path/to/stimuli --cache-dir /path/to/cache
```

The combined pool contains each image ID once. Use the same pooled split
for every subject. Features are centered over the combined pool.

The cluster generator reads `data/pooled_image_groups.json` and fits
five clusters to group-average CLIPA features, weighted by group size
(`KMeans`, seed 2026, `n_init=10`). The file also records the fold-label
ordering and grouping thresholds. Split metadata includes its SHA-256.
Singleton images remain individual samples.

Groups are connected components: join an image pair if its cosine distance
is below **any** of CLIPA 0.25, DreamSim 0.30, DINOv2 0.25 or SSCD 0.60,
and join all identified duplicate groups. CLIPA, DreamSim and DINOv2 use
the models listed above, with mean centering and L2 normalization over
all 24,681 images. SSCD uses the 512-dimensional `sscd_disc_mixup`
TorchScript model: RGB images resized to a 288-pixel shorter side with
aspect ratio retained, ImageNet input normalization, and L2-normalized
output without mean centering. The saved components contain 11,781 images
in 2,131 groups; the largest contains 163 images. These are similarity
constraints, not additional duplicate annotations. Their transitive
closure can include images that are not directly similar.

Tau uses the existing selection procedure, with identified duplicate
images kept in training. Its input is `data/pooled_duplicate_groups.json`,
which includes duplicates across subjects; the broader cluster groups do
not restrict tau selection. Pass `--extract-missing` to compute missing
split features and `--diagnostics /path/to/tau_sweep.json` to save the sweep.

`data/pooled_cluster_diagnostics.csv` records the numerical comparison
underlying the figure linked from the split documentation. Before and
after refer to pooled CLIPA clustering without and with the additional
similarity constraints. Distance quantiles cover one held-out observation
per image across five folds. MMD² is the squared difference of feature
means, averaged equally across folds. Its random reference is the exact
expectation at each fold's test size; the distance reference is one
seeded shuffle (2026) matching the final fold sizes. Tau is shown for its
4,936 test images only. These checks use the same features as construction;
they do not establish that every visually similar pair was detected.

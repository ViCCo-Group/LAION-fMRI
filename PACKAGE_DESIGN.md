# `laion_fmri` Python Package — Design Specification

> Design document for the LAION-fMRI data loading package.
> Status: Draft (2026-02-17)

---

## Overview

`laion-fmri` is a Python package that makes it easy to download and load the LAION-fMRI dataset. It provides:

1. **Explicit download management** with interactive terms-of-use acceptance for stimuli
2. **Simple, high-level API** for the common case (load betas, images, ROI masks)
3. **Full BIDS access** for advanced users via pybids integration
4. **PyTorch Dataset** integration for ML workflows

The package is **data-only** — no analysis code, no RSA, no encoding models. Just downloading and loading.

### Install & quickstart

```python
pip install laion-fmri
```

```python
import laion_fmri

# First time: configure where data lives
laion_fmri.set_data_dir("/data/laion_fmri")

# Download a subject (betas + atlases + metadata)
laion_fmri.download(subject="sub-01")

# Download with stimuli (interactive ToU prompt on first time)
laion_fmri.download(subject="sub-01", include_stimuli=True)

# Load and use
sub = laion_fmri.load_subject("sub-01")
betas = sub.get_betas(roi="hlvis")           # (n_stimuli, n_voxels_hlvis)
images = sub.get_images()                     # list[PIL.Image]
mask = sub.get_roi_mask("hlvis")              # (n_all_voxels,) bool
```

---

## Package metadata

| Field | Value |
|-------|-------|
| **pip name** | `laion-fmri` |
| **import name** | `laion_fmri` |
| **Python** | >= 3.10 |
| **License** | MIT (package code); data has separate terms |
| **Repository** | Lives inside the `LAION-fMRI` repo |

### Dependencies

**Required**: `numpy`, `h5py`, `nibabel`, `pandas`, `requests` (or `pooch`)

**Optional**:
- `torch` — for `to_torch_dataset()` and `format="torch"` image loading
- `pybids` — for `get_bids_layout()`
- `Pillow` — for image loading (likely required in practice)

---

## Configuration & download

### Data directory

The data directory must be set explicitly before any data access. There is no implicit default.

```python
import laion_fmri

# Set programmatically
laion_fmri.set_data_dir("/data/laion_fmri")

# Read back
laion_fmri.get_data_dir()  # "/data/laion_fmri"
```

The setting is persisted to a config file (e.g., `~/.config/laion_fmri/config.json`) so it only needs to be set once. If `data_dir` is not set and the user tries to load data, raise a clear error with instructions.

### Download

Downloads are always explicit — the package never silently downloads data.

```python
# Download betas + atlases + metadata for one subject
laion_fmri.download(subject="sub-01")

# Download including stimulus images (triggers ToU on first time)
laion_fmri.download(subject="sub-01", include_stimuli=True)

# Download all subjects
laion_fmri.download(subject="all")
laion_fmri.download(subject="all", include_stimuli=True)
```

If data has not been downloaded and the user tries to load it, raise a clear error (not a silent download):

```
DataNotDownloadedError: Data for sub-01 not found.
Run `laion_fmri.download(subject="sub-01")` or `laion-fmri download --subject sub-01` first.
```

### Terms of use for stimuli

The stimuli include images sourced from the internet. A terms-of-use agreement is required that excludes commercial use.

- On first stimulus download, an **interactive prompt** is displayed (cannot be bypassed programmatically)
- The user must type explicit confirmation (e.g., type "I AGREE" or similar)
- Once accepted, a marker file is written to the data directory
- Subsequent downloads skip the prompt

```
=== LAION-fMRI Stimulus Terms of Use ===

The LAION-fMRI stimulus images include content sourced from the internet.
These images are provided for non-commercial research use only.

By downloading, you agree to:
  1. Use the stimuli only for non-commercial research purposes
  2. Not redistribute the stimuli outside your research group
  3. [Additional terms TBD]

Full terms: https://laion-fmri.github.io/terms

Type "I AGREE" to accept: _
```

### CLI

```bash
# Set data directory (interactive prompt if not provided)
laion-fmri config --data-dir /data/laion_fmri

# Download data
laion-fmri download --subject sub-01
laion-fmri download --subject sub-01 --include-stimuli
laion-fmri download --subject all --include-stimuli

# Dataset info
laion-fmri info
laion-fmri info --subject sub-01
```

On first `download` invocation, if no data directory has been configured, the CLI prompts the user to set one interactively.

---

## Data organization on disk

Downloaded data is stored in **full BIDS format**. The betas, atlases, and metadata are all part of the BIDS derivatives structure.

```
{data_dir}/
├── .laion_fmri/                          # Package metadata
│   ├── config.json                       # data_dir, version, etc.
│   ├── stimuli_terms_accepted            # ToU marker file
│   └── pybids_cache/                     # Cached pybids layout database
├── dataset_description.json
├── participants.tsv
├── stimuli/                              # Shared stimulus images + metadata
│   ├── images/                           # Extracted image files
│   ├── stimuli.tsv                       # Stimulus metadata
│   └── stimuli.json                      # Stimulus set description
├── sub-01/
│   └── ...                               # Raw data (OpenNeuro full download only)
├── derivatives/
│   ├── glmsingle/
│   │   └── sub-01/
│   │       └── ses-01/
│   │           ├── sub-01_ses-01_betas.h5
│   │           └── sub-01_ses-01_trialinfo.tsv
│   └── atlases/
│       ├── sub-01/
│       │   ├── brain_mask.nii.gz
│       │   ├── noise_ceiling.nii.gz
│       │   └── rois/
│       │       ├── hlvis.nii.gz
│       │       └── visual.nii.gz
│       └── ...
```

> **Note**: The exact BIDS structure is preliminary and will be finalized as the dataset publication progresses. The package API should be decoupled from the on-disk layout so that file organization can change without breaking the public interface.

---

## Discovery API

Top-level functions for exploring what's available.

```python
import laion_fmri

# What subjects exist / are downloaded?
laion_fmri.get_subjects()               # ["sub-01", "sub-03", "sub-05", "sub-06", "sub-07"]
laion_fmri.get_downloaded_subjects()    # ["sub-01", "sub-03"]  (what's on disk)

# What ROIs are available?
laion_fmri.get_rois()                   # ["visual", "hlvis", ...]

# Human-readable summary
laion_fmri.describe()
```

`describe()` prints something like:

```
LAION-fMRI Dataset (v1.0)
  Subjects: 5 (sub-01, sub-03, sub-05, sub-06, sub-07)
  Stimuli:  X shared + Y unique per subject
  Sessions: ~30 per subject
  Trials:   ~1,100 per session (~12 repetitions per stimulus)
  ROIs:     visual, hlvis

  Downloaded: sub-01, sub-03
  Stimuli:    downloaded (ToU accepted)
  Data dir:   /data/laion_fmri
```

---

## Subject API

### Loading a subject

```python
sub = laion_fmri.load_subject("sub-01")

# Also accepts integer (1-based participant index)
sub = laion_fmri.load_subject(1)     # → sub-01
sub = laion_fmri.load_subject(2)     # → sub-03
sub = laion_fmri.load_subject(3)     # → sub-05
# etc.
```

The integer mapping must be clearly documented. Both forms are always accepted.

### Subject discovery methods

```python
sub.get_available_rois()             # ["visual", "hlvis", ...]
sub.get_n_stimuli()                  # total stimuli for this subject
sub.get_n_stimuli(stimuli="shared")  # shared stimuli count
sub.get_n_voxels()                   # total brain mask voxels
sub.get_sessions()                   # ["ses-01", "ses-02", ...]
```

### Betas

**Averaged betas** (default): one response vector per stimulus, averaged across trial repetitions.

```python
# All stimuli, all brain mask voxels
betas = sub.get_betas()                              # (n_stimuli, n_voxels)

# Filter by ROI — returns only voxels in that ROI
betas = sub.get_betas(roi="hlvis")                   # (n_stimuli, n_voxels_hlvis)

# Multiple ROIs — union of masks
betas = sub.get_betas(roi=["V1", "V2"])              # (n_stimuli, n_voxels_v1_union_v2)

# Custom mask — any boolean array over all voxels
custom_mask = sub.get_roi_mask("hlvis") & (sub.get_noise_ceiling() > 0.3)
betas = sub.get_betas(mask=custom_mask)              # (n_stimuli, n_voxels_custom)

# Noise ceiling threshold — only voxels above threshold
betas = sub.get_betas(nc_threshold=0.2)              # (n_stimuli, n_voxels_above_nc)

# Combine ROI and noise ceiling
betas = sub.get_betas(roi="hlvis", nc_threshold=0.3) # intersection

# Filter by stimulus type
betas = sub.get_betas(stimuli="shared")              # (n_shared, n_voxels)
betas = sub.get_betas(stimuli="unique")              # (n_unique, n_voxels)

# Memory-mapped (for low-RAM scenarios)
betas = sub.get_betas(memmap=True)
```

**Trial-level betas**: one response vector per trial (before averaging across repetitions).

```python
betas = sub.get_betas(level="trial")                 # (n_trials, n_voxels)
betas = sub.get_betas(level="trial", roi="hlvis")    # (n_trials, n_voxels_hlvis)

# Single session
betas = sub.get_betas(level="trial", session="ses-01")  # (n_trials_ses01, n_voxels)
```

**Parameter summary for `get_betas()`**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | `"stimulus" \| "trial"` | `"stimulus"` | Averaged or trial-level |
| `roi` | `str \| list[str] \| None` | `None` | Named ROI(s) to select voxels (union if list) |
| `mask` | `np.ndarray[bool] \| None` | `None` | Custom boolean mask over all brain voxels |
| `nc_threshold` | `float \| None` | `None` | Minimum noise ceiling for voxel inclusion |
| `stimuli` | `"shared" \| "unique" \| None` | `None` | Filter by stimulus type (`None` = all) |
| `session` | `str \| None` | `None` | Specific session (forces `level="trial"`) |
| `memmap` | `bool` | `False` | Return memory-mapped array |

`roi` and `mask` are mutually exclusive — passing both raises `ValueError`.

### Trial info

When using trial-level betas, a DataFrame describes each trial.

```python
trial_info = sub.get_trial_info()
# DataFrame columns:
#   trial_idx    — global trial index (rows align with get_betas(level="trial"))
#   session      — e.g. "ses-01"
#   run          — run within session
#   stimulus_id  — which stimulus was shown
#   rep_index    — which repetition of that stimulus (0-based)

# Also available filtered by session
trial_info = sub.get_trial_info(session="ses-01")
```

### ROI masks

ROI masks are boolean arrays over all brain mask voxels.

```python
# Single ROI
mask = sub.get_roi_mask("hlvis")                # (n_all_voxels,) bool

# Multiple ROIs (returns dict)
masks = sub.get_roi_masks(["V1", "V2", "hlvis"])
# {"V1": (n_all_voxels,) bool, "V2": ..., "hlvis": ...}

# List available ROIs
sub.get_available_rois()                        # ["visual", "hlvis", ...]
```

### Noise ceiling

Per-voxel noise ceiling values.

```python
nc = sub.get_noise_ceiling()                    # (n_all_voxels,)
nc = sub.get_noise_ceiling(roi="hlvis")         # (n_voxels_hlvis,)
nc = sub.get_noise_ceiling(mask=custom_mask)    # (n_voxels_custom,)
```

### Stimulus images

```python
# PIL Images (default) — one per unique stimulus
images = sub.get_images()                       # list[PIL.Image]
images = sub.get_images(stimuli="shared")       # shared stimuli only

# Alternative formats
images = sub.get_images(format="numpy")         # (n_stimuli, H, W, 3) uint8
images = sub.get_images(format="torch")         # (n_stimuli, 3, H, W) float32 [0, 1]

# Single image by index
img = sub.get_image(idx=0)                      # PIL.Image

# Stimulus metadata
stim_meta = sub.get_stimulus_metadata()
# DataFrame: stimulus_id | shared (bool) | dataset | category | ...
```

### Trial-to-stimulus mapping convenience

```python
# Get stimulus indices for each trial (for indexing into stimulus-level arrays)
stim_indices = sub.get_trial_stimulus_indices()  # (n_trials,) int
# Usage: trial_images = [images[i] for i in stim_indices]
```

### Brain space mapping

```python
# Map voxel values back to a NIfTI volume
# `values` shape must match the voxel set implied by roi=/mask=
sub.to_nifti(values, "output.nii.gz")                       # all brain mask voxels
sub.to_nifti(values, "output.nii.gz", roi="hlvis")          # hlvis voxels
sub.to_nifti(values, "output.nii.gz", mask=custom_mask)     # custom mask voxels

# Get voxel coordinates (MNI space)
coords = sub.get_voxel_coordinates()            # (n_all_voxels, 3)
coords = sub.get_voxel_coordinates(roi="hlvis") # (n_voxels_hlvis, 3)
```

---

## Multi-subject / group API

A lightweight wrapper for cross-subject analyses on shared stimuli.

```python
# Load multiple subjects
group = laion_fmri.load_subjects(["sub-01", "sub-03", "sub-05"])
group = laion_fmri.load_subjects("all")

# Shared betas — guaranteed identical stimulus ordering across subjects
shared_betas = group.get_shared_betas()
# dict: {"sub-01": (n_shared, n_voxels_sub01), "sub-03": ..., ...}

shared_betas = group.get_shared_betas(roi="hlvis")
# dict: {"sub-01": (n_shared, n_voxels_hlvis_sub01), ...}

# Shared stimulus metadata (same for all subjects)
stim_meta = group.get_shared_stimulus_metadata()  # DataFrame

# Shared images (identical across subjects)
images = group.get_shared_images()                # list[PIL.Image]

# Access individual subjects
sub01 = group["sub-01"]                           # returns Subject object
sub01 = group[0]                                  # by index

# Iterate
for sub_id, sub in group:
    betas = sub.get_betas(stimuli="shared", roi="hlvis")
    # ...
```

**Critical guarantee**: In `get_shared_betas()`, row `i` corresponds to the same stimulus across all subjects. The ordering is canonical and defined by the dataset (not by per-subject trial order).

The Group object is intentionally lightweight — it's essentially a dict of Subject objects with convenience methods for the shared-stimuli use case. It does not load all data into memory at construction time.

---

## PyTorch Dataset integration

Optional integration with PyTorch's `DataLoader` ecosystem. Requires `torch` as an optional dependency.

```python
# Stimulus-level dataset
torch_ds = sub.to_torch_dataset(roi="hlvis")
# len(torch_ds) == n_stimuli
# torch_ds[i] → {
#     "betas": Tensor (n_voxels_hlvis,),
#     "image": Tensor (3, H, W),         # float32, [0, 1]
#     "stimulus_id": str,
# }

# Trial-level dataset
torch_ds = sub.to_torch_dataset(roi="hlvis", level="trial")
# len(torch_ds) == n_trials
# torch_ds[i] → {
#     "betas": Tensor (n_voxels_hlvis,),
#     "image": Tensor (3, H, W),
#     "stimulus_id": str,
#     "session": str,
#     "rep_index": int,
# }

# With transforms
from torchvision import transforms
transform = transforms.Compose([transforms.Resize(224), transforms.Normalize(...)])
torch_ds = sub.to_torch_dataset(roi="hlvis", image_transform=transform)

# Standard DataLoader usage
from torch.utils.data import DataLoader
loader = DataLoader(torch_ds, batch_size=32, shuffle=True, num_workers=4)
for batch in loader:
    betas = batch["betas"]    # (32, n_voxels_hlvis)
    images = batch["image"]   # (32, 3, H, W)
```

If `torch` is not installed, calling `to_torch_dataset()` raises:

```
ImportError: PyTorch is required for to_torch_dataset().
Install it with: pip install laion-fmri[torch]
```

---

## Advanced: pybids access

For users who want to query the BIDS structure directly.

```python
layout = laion_fmri.get_bids_layout()  # pybids BIDSLayout

# Standard pybids queries
betas_files = layout.get(subject="01", suffix="betas", extension=".h5")
```

The pybids layout database is **pre-cached** and shipped as part of the download, so `get_bids_layout()` returns instantly without needing to index the filesystem.

Requires `pybids` as an optional dependency.

---

## Data hosting strategy

The data is hosted in two locations:

| Host | Content | Use case |
|------|---------|----------|
| **AWS S3** | Derivatives (betas, atlases, ROIs) + stimuli | Default download source. Fast, simple files. |
| **OpenNeuro** | Full BIDS dataset (raw + derivatives) | Archival, reproducibility, full provenance. |

The package downloads from AWS by default. A future option could allow downloading the full dataset from OpenNeuro:

```python
# Future: full BIDS download from OpenNeuro
laion_fmri.download(subject="sub-01", source="openneuro")  # raw + derivatives
```

> **Status**: AWS bucket is not yet set up. URLs and download logic are TBD.

---

## Package structure

```
LAION-fMRI/                              # Existing repo
├── docs/                                # Sphinx documentation (existing)
├── src/laion_fmri/                      # Package source
│   ├── __init__.py                      # Top-level API: download, set_data_dir, etc.
│   ├── _config.py                       # Config management (data_dir persistence)
│   ├── _constants.py                    # Subject mapping, ROI names, URLs
│   ├── _download.py                     # Download logic, ToU handling
│   ├── _io.py                           # Low-level file loading (npy, hdf5, nifti)
│   ├── subject.py                       # Subject class
│   ├── group.py                         # Group class (lightweight multi-subject)
│   ├── brain.py                         # to_nifti, voxel coordinate mapping
│   └── torch.py                         # PyTorch Dataset (optional dependency)
├── tests/
│   ├── test_subject.py
│   ├── test_group.py
│   ├── test_download.py
│   └── ...
├── pyproject.toml
├── PACKAGE_DESIGN.md                    # This document
└── README.md
```

### CLI entry point

Defined in `pyproject.toml`:

```toml
[project.scripts]
laion-fmri = "laion_fmri._cli:main"
```

---

## Subject ID mapping

The dataset uses BIDS subject IDs that are non-contiguous. Integer shorthand is supported for convenience.

| Integer | BIDS ID | Participant label |
|---------|---------|-------------------|
| 1 | sub-01 | p01 |
| 2 | sub-03 | p02 |
| 3 | sub-05 | p03 |
| 4 | sub-06 | p04 |
| 5 | sub-07 | p05 |

Both `load_subject(1)` and `load_subject("sub-01")` are valid and equivalent. This mapping is documented in the package and in `describe()` output.

---

## Shared vs unique stimuli

Each subject sees two types of stimuli:

- **Shared**: Shown to all subjects (same images, ~12 repetitions each). These enable cross-subject analyses.
- **Unique**: Shown to only one subject. These provide additional per-subject data.

The `stimuli` parameter controls which stimuli are included:

```python
betas = sub.get_betas()                      # all stimuli (shared + unique)
betas = sub.get_betas(stimuli="shared")      # shared only
betas = sub.get_betas(stimuli="unique")      # unique only

stim_meta = sub.get_stimulus_metadata()      # has "shared" column (bool)
```

For multi-subject analyses, the Group API operates only on shared stimuli and guarantees consistent stimulus ordering.

---

## Design principles

1. **Explicit over implicit.** No silent downloads. No hidden defaults. Configuration is required before use.

2. **Plain numpy returns.** `get_betas()` returns `np.ndarray`, not custom wrapper classes. Users know how to work with numpy.

3. **Consistent `roi=` / `mask=` pattern.** The same voxel-selection parameters appear on `get_betas()`, `get_noise_ceiling()`, `to_nifti()`, `get_voxel_coordinates()`. They always mean the same thing.

4. **BIDS on disk, convenience in code.** Data is stored in standard BIDS format for interoperability. The Python API provides a convenient layer on top, not a replacement.

5. **Flexible for future ROIs.** ROIs are not hardcoded in the API — they're discovered from the data on disk. Adding a new ROI is just adding a NIfTI mask file; no code changes needed.

6. **Decouple API from file layout.** The public interface (`get_betas`, `get_roi_mask`, etc.) does not expose file paths or BIDS conventions. The on-disk structure can change between versions without breaking user code.

7. **Optional heavy dependencies.** `torch` and `pybids` are optional. Core functionality works with just numpy/h5py/nibabel/pandas.

---

## Open items / TBD

- [ ] Exact BIDS file naming conventions for published derivatives
- [ ] AWS bucket setup and URL scheme
- [ ] OpenNeuro dataset ID and access pattern
- [ ] Complete list of ROIs to ship with v1.0
- [ ] Stimulus metadata schema (what columns beyond stimulus_id and shared?)
- [ ] Terms of use exact wording
- [ ] Versioning strategy for data updates
- [ ] Whether to support partial downloads (e.g., only specific sessions)
- [ ] Image resolution/format standardization for published stimuli
- [ ] Noise ceiling definition to expose (voxel-wise SNR? split-half?)
- [ ] Z-scoring convention: is it applied during loading or stored pre-applied?

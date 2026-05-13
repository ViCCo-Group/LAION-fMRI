"""
Loading Data
=============

Load single-trial betas, noise-ceiling maps, ROI masks, and stimulus
images.

Every accessor maps to one file in the bucket: it returns the raw
contents of the file you pick. Combining sessions, averaging
across trials, or rebinning is the caller's responsibility.

The "brain mask" is **derived on the fly** from the subject-level
mean-R^2 map (``..._stat-rsquare_desc-R2mean_statmap.nii.gz``):
voxels with any non-zero GLMsingle fit are considered "in brain".
The bucket does not ship a separate brain-mask file.

.. note::

   Run :doc:`plot_01 <plot_01_quickstart>` first so at least one
   subject is downloaded into the shared quickstart directory. A
   single session of full-brain betas is ``~1000 trials × ~270k
   voxels × 4 bytes ≈ 1 GB``; pass an ``roi=`` filter to keep
   per-call memory in the tens of MB.
"""

# %%
# Bind the quickstart's data directory
# -------------------------------------

import os

from laion_fmri.config import dataset_initialize, get_data_dir

data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)

# %%
# Load a subject and pick a session
# ----------------------------------

from laion_fmri.subject import load_subject

subject_id = "sub-01"
session = "ses-01"
roi = "FFA1"

sub = load_subject(subject_id)
print(f"Subject: {subject_id} | session: {session}")
print(f"Voxels in brain mask: {sub.get_n_voxels()}")

available_rois = sub.get_available_rois()
print(f"Primary ROI: {roi}")

# %%
# Single-trial betas for one session
# ------------------------------------
#
# Returns ``(n_trials, n_voxels)``. **Always pass an ROI filter
# unless you really want the full brain-masked array** -- the
# ``roi=`` form drops memory by 1-2 orders of magnitude.

if roi is not None:
    betas_roi = sub.get_betas(session=session, roi=roi)
    print(f"{roi} ROI:           {betas_roi.shape}")

betas_nc = sub.get_betas(session=session, nc_threshold=0.2)
print(f"NC > 0.2:            {betas_nc.shape}")

if roi is not None:
    betas_both = sub.get_betas(
        session=session, roi=roi, nc_threshold=0.3,
    )
    print(f"ROI + NC > 0.3:      {betas_both.shape}")

# %%
# Visualize the first trial with ROI contour overlays
# -----------------------------------------------------
#
# Overlaying the canonical face / body / place ROIs on a
# single trial's response lets you check whether your regions
# of interest sit where the activity actually is. Single
# trials are noisy and stimulus-dependent, so don't expect
# every ROI to show a hotspot for every trial -- you should
# at least see plausible signal somewhere near the contours
# rather than uniform noise. The betas are rendered in
# greyscale so the colored contours stay visually dominant.

import warnings

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from nilearn import plotting

from laion_fmri._paths import r2mean_path

# Nilearn warns about NaN / inf voxels from GLMsingle non-fits;
# they're outside the brain mask and don't affect the rendering.
warnings.filterwarnings(
    "ignore",
    message="Non-finite values detected",
    category=UserWarning,
)

bg_img = str(r2mean_path(get_data_dir(), subject_id))
stat_cmap = "gray"
overlay_rois = ("FFA1", "OFA", "PPA", "EBA", "FBA", "MT")
roi_colors = dict(
    zip(overlay_rois, sns.color_palette("colorblind")),
)

first_beta = sub.get_betas(session=session)[0]
beta_path = f"/tmp/{subject_id}_{session}_trial0_full.nii.gz"
sub.to_nifti(first_beta, beta_path)

roi_paths = {}
for r in overlay_rois:
    p = f"/tmp/{subject_id}_roi_{r}.nii.gz"
    sub.to_nifti(sub.get_roi_mask(r).astype("float32"), p)
    roi_paths[r] = p

vmax = float(np.percentile(np.abs(first_beta), 99))
cuts = [-17, -5, 8]

fig = plt.figure(figsize=(16, 4.7))
gs = fig.add_gridspec(
    3, 1, height_ratios=[0.10, 1, 0.05], hspace=0.1,
)
legend_ax = fig.add_subplot(gs[0])
legend_ax.axis("off")
strip_gs = gs[1].subgridspec(1, 3, wspace=0.05)
axes = [fig.add_subplot(strip_gs[0, i]) for i in range(3)]
cbar_ax = fig.add_subplot(gs[2])

for ax, z in zip(axes, cuts):
    display = plotting.plot_stat_map(
        beta_path, bg_img=bg_img, axes=ax,
        display_mode="z", cut_coords=[z],
        cmap=stat_cmap, vmax=vmax, colorbar=False,
        black_bg=False, threshold=0.5,
    )
    for roi, color in roi_colors.items():
        display.add_contours(
            roi_paths[roi], levels=[0.5],
            colors=[color], linewidths=1.5,
        )

proxies = [
    Line2D([0], [0], color=c, lw=2.0, label=r)
    for r, c in roi_colors.items()
]
legend_ax.legend(
    handles=proxies, loc="center", ncol=len(overlay_rois),
    frameon=False, handlelength=1.2,
)

sm = plt.cm.ScalarMappable(
    cmap=stat_cmap, norm=Normalize(vmin=-vmax, vmax=vmax),
)
fig.colorbar(
    sm, cax=cbar_ax, orientation="horizontal",
    label=f"{session} trial 0 β",
)
plt.show()

# %%
# Single-trial filtering by stimulus type
# -----------------------------------------
#
# Restrict to trials whose stimulus is in the shared / unique
# subset (relies on the dataset-level stimulus metadata, which
# the bucket doesn't yet expose).

if roi is not None and sub.has_stimuli():
    betas_shared = sub.get_betas(
        session=session, roi=roi, stimuli="shared",
    )
    print(f"Shared trials:       {betas_shared.shape}")
else:
    print(
        "Skipped: stimulus subset filter needs stimuli/stimuli.tsv."
    )

# %%
# Custom voxel mask
# ------------------
#
# Combine the ROI mask and the noise-ceiling map yourself, then
# pass the result back in via ``mask=``.

if roi is not None:
    roi_mask = sub.get_roi_mask(roi)
    nc = sub.get_noise_ceiling(session=session)
    custom_mask = roi_mask & (nc > 0.25)
    print(f"Custom mask voxels: {custom_mask.sum()}")

    betas_custom = sub.get_betas(session=session, mask=custom_mask)
    print(f"Custom betas:       {betas_custom.shape}")

# %%
# ROI masks (multi-level query)
# ------------------------------
#
# ``get_roi_mask`` accepts a specific ROI name, a category, or
# ``"all"``. Pass a list to combine several at once -- overlapping
# voxels appear only once in the resulting mask.

if available_rois:
    if roi is not None:
        single = sub.get_roi_mask(roi)
        print(f"  {roi}: {single.sum()} voxels")
    categories = sub.get_available_categories()
    if categories:
        first_cat = categories[0]
        cat_mask = sub.get_roi_mask(first_cat)
        print(f"  {first_cat} (category): {cat_mask.sum()} voxels")
    union = sub.get_roi_mask("all")
    print(f"  all: {union.sum()} voxels")

# %%
# Visualize every face-category ROI
# ----------------------------------
#
# Inspecting every face-category ROI in one row surfaces
# things you'd miss looking at one at a time: which ROIs are
# present for this subject (some are absent for some
# subjects), how the various face areas spatially relate to
# each other, and whether any region looks unexpectedly small
# or empty -- a sign that the localizer underperformed there
# and that ROI may not be reliable to analyse with.

import nibabel as nib
from nilearn.plotting import find_xyz_cut_coords

face_rois = sub.get_available_rois(category="face")
if not face_rois:
    print("No face-category ROIs on disk for this subject.")
else:
    palette = sns.color_palette("colorblind")
    n = len(face_rois)
    fig, axes = plt.subplots(1, n, figsize=(5.3 * n, 3.7))
    axes = [axes] if n == 1 else list(axes)

    for ax, roi, color in zip(axes, face_rois, palette):
        roi_path = f"/tmp/{subject_id}_roi_{roi}.nii.gz"
        sub.to_nifti(
            sub.get_roi_mask(roi).astype("float32"), roi_path,
        )
        _, _, z = find_xyz_cut_coords(nib.load(roi_path))
        display = plotting.plot_anat(
            bg_img, axes=ax,
            display_mode="z", cut_coords=[z],
            black_bg=False, threshold=0.1, colorbar=False,
        )
        display.add_contours(
            roi_path, levels=[0.5],
            colors=[color], linewidths=1.5,
        )
        ax.set_title(roi)
    plt.show()

# %%
# Noise ceiling
# --------------
#
# Use the per-session map when you're analysing data within one
# session (e.g. selecting reliable voxels for a single-session
# decoder). For cross-session work, pick one of the subject-level
# aggregates -- ``Noiseceiling4rep`` and ``Noiseceiling12rep`` are
# computed only over stimuli that have at least 4 / 12 repetitions
# in the dataset; ``NoiseceilingAllrep`` uses every repetition.
# More repetitions tighten the estimate but include fewer stimuli,
# so the right variant depends on whether you'd rather have a
# stable ceiling or full coverage.

nc_session = sub.get_noise_ceiling(session=session)
print(
    "Per-session NC: "
    f"shape={nc_session.shape}, "
    f"range=[{nc_session.min():.3f}, {nc_session.max():.3f}]"
)

# Switch to a subject-level aggregate by passing ``desc=`` instead
# of ``session=``. The line below is commented out to avoid an
# extra download for the example, but the call is identical:
#
#     nc_subj = sub.get_noise_ceiling(desc="Noiseceiling12rep")

# %%
# Trial info and stimulus metadata
# ----------------------------------

trial_info = sub.get_trial_info(session=session)
print(f"Trials in {session}: {len(trial_info)}")
print(trial_info.head())

if sub.has_stimuli():
    # The subject's full trial table -- one row per trial across all
    # sessions, with the image_name already joined in.
    trials = sub.metadata
    print(f"Trial table rows: {len(trials)} (across all sessions)")
    print(trials[
        ["session", "session_trial", "image_name", "unique_or_shared"]
    ].head())
else:
    print("Stimulus metadata not yet uploaded to the bucket.")

# %%
# Stimulus images
# ----------------
#
# Subjects expose images on a per-trial basis via the ``sub.images``
# namespace. The trial index is global (rows of ``sub.metadata``).
# Skipped automatically when the bucket's ``stimuli/`` prefix is
# not yet populated.

if sub.has_stimuli():
    # Iterate one session's images:
    n_session = (sub.metadata["session"] == session).sum()
    print(f"{session} has {n_session} trial-image pairs")

    # Single image for the first trial:
    single_img = sub.images.get(0)
    print(f"First trial image: {single_img.size}")
else:
    print("No stimulus images on disk yet.")

# %%
# Brain-space mapping: save derived results as NIfTI
# ----------------------------------------------------
#
# ``Subject.to_nifti`` is the inverse of "load + brain-mask": it
# scatters a 1-D per-voxel array (length = ``n_brain_voxels``)
# back into a 3-D ``(X, Y, Z)`` NIfTI on the subject's image
# grid, with zeros outside the brain mask. That makes any
# per-voxel statistic you computed in masked space round-trip
# back to disk for downstream tools (``fslview``, ``nilearn``,
# ``mricron``, ...).
#
# Example: trial-mean betas as a 3-D map.

mean_betas = sub.get_betas(session=session).mean(axis=0)
print(f"per-voxel mean shape: {mean_betas.shape}")

mean_path = f"/tmp/{subject_id}_{session}_mean_betas.nii.gz"
sub.to_nifti(mean_betas, mean_path)
print(f"Saved {mean_path}")

# ``to_nifti`` also knows about ROI / mask filters, so an
# ROI-restricted result lands in the right voxels:
ffa1 = sub.get_betas(session=session, roi="FFA1").mean(axis=0)
sub.to_nifti(
    ffa1, f"/tmp/{subject_id}_{session}_FFA1_mean.nii.gz", roi="FFA1",
)

# If you also need the (i, j, k) location of each voxel --
# for example to build a custom voxel selection by spatial
# proximity, or to overlay results outside ``to_nifti``'s
# round-trip -- ``get_voxel_coordinates`` returns them in the
# same order as the 1-D arrays from ``get_betas`` and
# ``get_noise_ceiling``, so they line up index-for-index.
coords = sub.get_voxel_coordinates()
print(f"Voxel coordinates: {coords.shape}")

# %%
# Multi-subject group loading
# -----------------------------
#
# ``Group`` holds several ``Subject`` instances and exposes
# cross-subject loaders that delegate to each one.

from laion_fmri._paths import glmsingle_subject_dir
from laion_fmri.group import load_subjects

# Group loading reads each subject's local files. List the
# subjects you want explicitly; we keep the on-disk filter so the
# example doesn't blow up if only some have been downloaded.
group_subjects = ["sub-01", "sub-03"]
on_disk = [
    s for s in group_subjects
    if glmsingle_subject_dir(get_data_dir(), s).is_dir()
]
group = load_subjects(on_disk)
print(f"Group size: {len(group)}")

# Shared-stimulus betas need stimulus metadata.
if roi is not None and sub.has_stimuli():
    shared = group.get_shared_betas(session=session, roi=roi)
    for sub_id, arr in shared.items():
        print(f"  {sub_id}: {arr.shape}")
else:
    print(
        "Skipped: shared-stimulus betas need stimuli/stimuli.tsv."
    )

# %%
# PyTorch dataset integration
# ----------------------------
#
# When you want to feed betas straight into a PyTorch training
# loop, ``to_torch_dataset`` wraps one session as a
# ``torch.utils.data.Dataset`` whose items pair each trial's betas
# with the matching stimulus image (plus a few bookkeeping fields).
# The PyTorch dependencies are optional -- install them with the
# ``[torch]`` add-on if you want this integration:
#
# .. code-block:: bash
#
#     uv pip install "laion-fmri[torch]"

# The PyTorch dataset pairs each beta with a stimulus image, so it
# requires the stimuli/ prefix to be populated.
if sub.has_stimuli():
    from torch.utils.data import DataLoader

    dataset = sub.to_torch_dataset(session=session, roi=roi)
    print(f"Dataset length: {len(dataset)}")

    sample = dataset[0]
    print(f"betas: {sample['betas'].shape}")
    print(f"image: {sample['image'].shape}")

    loader = DataLoader(dataset, batch_size=16, shuffle=True)
    for batch in loader:
        print(f"Batch betas: {batch['betas'].shape}")
        print(f"Batch image: {batch['image'].shape}")
        break
else:
    print(
        "PyTorch dataset needs stimulus images; skipping until "
        "the bucket's stimuli/ is populated."
    )

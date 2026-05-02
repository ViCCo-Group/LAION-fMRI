"""
Loading Data
=============

Load single-trial betas, noise-ceiling maps, ROI masks, and stimulus
images.

Every accessor maps to one file in the bucket. The loader does no
math (no averaging across sessions, no rebinning) -- it returns the
raw contents of the file you pick.

.. note::

   Run :doc:`plot_01 <plot_01_quickstart>` first so at least one
   subject is downloaded into the shared quickstart directory.
"""

# %%
# Bind the quickstart's data directory
# -------------------------------------
#
# Loading reads files off disk, so we point at the same data
# directory the quickstart populated. Run that example first if
# you haven't already.

import os

from laion_fmri.config import dataset_initialize

data_dir = os.path.join(os.getcwd(), "laion_fmri_quickstart")
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)

# %%
# Load a subject and pick a session
# ----------------------------------
#
# ``get_betas``, ``get_trial_info``, and per-session
# ``get_noise_ceiling`` all require a session, since the bucket
# stores them per-session.

from laion_fmri.discovery import get_subjects
from laion_fmri.subject import load_subject

subject_id = get_subjects()[0]
sub = load_subject(subject_id)

session = sub.get_sessions()[0]
print(f"Subject: {subject_id} | session: {session}")

available_rois = sub.get_available_rois()
roi = available_rois[0] if available_rois else None
if roi is not None:
    print(f"Primary ROI: {roi}")

# %%
# Single-trial betas for one session
# ------------------------------------
#
# Returns a ``(n_trials, n_voxels)`` array. Voxels can be filtered
# by ROI, custom boolean mask, or noise-ceiling threshold.

betas = sub.get_betas(session=session)
print(f"All voxels:          {betas.shape}")

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
# Single-trial filtering by stimulus type
# -----------------------------------------
#
# Restrict to trials whose stimulus is in the shared / unique
# subset (relies on the dataset-level stimulus metadata, which
# the bucket doesn't yet expose).

if sub.has_stimuli():
    betas_shared = sub.get_betas(session=session, stimuli="shared")
    print(f"Shared trials:       {betas_shared.shape}")
else:
    print(
        "Stimulus subsets need stimuli/stimuli.tsv; skipping "
        "until the bucket's stimuli/ is populated."
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
# ROI masks
# ----------

if available_rois:
    all_masks = sub.get_roi_masks(available_rois)
    for name, m in all_masks.items():
        print(f"  {name}: {m.sum()} voxels")

# %%
# Noise ceiling
# --------------
#
# Either pick a session NIfTI or one of the subject-level aggregate
# variants identified by its ``desc-...`` token.

nc_session = sub.get_noise_ceiling(session=session)
print(
    "Per-session NC: "
    f"shape={nc_session.shape}, "
    f"range=[{nc_session.min():.3f}, {nc_session.max():.3f}]"
)

# Subject-level aggregate (uncomment with a desc that exists in the
# bucket, e.g. "Noiseceiling12rep" / "Noiseceiling4rep" /
# "NoiseceilingAllrep"):
#
#     nc_subj = sub.get_noise_ceiling(desc="Noiseceiling12rep")

# %%
# Trial info and stimulus metadata
# ----------------------------------

trial_info = sub.get_trial_info(session=session)
print(f"Trials in {session}: {len(trial_info)}")
print(trial_info.head())

if sub.has_stimuli():
    stim_meta = sub.get_stimulus_metadata()
    print(f"Stimulus metadata rows: {len(stim_meta)}")
else:
    print("Stimulus metadata not yet uploaded to the bucket.")

# %%
# Stimulus images
# ----------------
#
# Skipped automatically when the bucket's ``stimuli/`` prefix is
# not yet populated.

if sub.has_stimuli():
    images = sub.get_images()
    print(f"Images:          {len(images)} PIL items")

    single_img = sub.get_image(idx=0)
    print(f"First image:     {single_img.size}")
else:
    print("No stimulus images on disk yet.")

# %%
# Brain-space mapping
# --------------------
#
# Project a per-voxel array back into a 3-D NIfTI volume.

import numpy as np

per_voxel = np.zeros(sub.get_n_voxels(), dtype=np.float32)
sub.to_nifti(per_voxel, "/tmp/per_voxel.nii.gz")
print("Saved /tmp/per_voxel.nii.gz")

coords = sub.get_voxel_coordinates()
print(f"Voxel coordinates: {coords.shape}")

# %%
# Multi-subject group loading
# -----------------------------
#
# ``Group`` holds several ``Subject`` instances and exposes
# cross-subject loaders that delegate to each one.

from laion_fmri.group import load_subjects

group = load_subjects(get_subjects()[:2])
print(f"Group size: {len(group)}")

# Shared-stimulus betas need the dataset-level stimulus metadata
# to know which trials are "shared" -- skipped until the bucket's
# stimuli/ is populated.
if roi is not None and sub.has_stimuli():
    shared = group.get_shared_betas(session=session, roi=roi)
    for sub_id, arr in shared.items():
        print(f"  {sub_id}: {arr.shape}")
else:
    print(
        "Skipping shared-stimulus betas: needs stimuli/stimuli.tsv."
    )

# %%
# PyTorch dataset integration
# ----------------------------
#
# Wraps one session of a subject as a ``torch.utils.data.Dataset``
# yielding ``{betas, image, stimulus_id, session, rep_index}``.
#
# Requires the ``torch`` extra:
#
# .. code-block:: bash
#
#     uv pip install "laion-fmri[torch]"

from torch.utils.data import DataLoader

# The PyTorch dataset pairs each beta with a stimulus image, so it
# also requires the stimuli/ prefix to be populated.
if sub.has_stimuli():
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

"""
Loading Data
=============

Load single-trial betas, noise-ceiling maps, ROI masks, and stimulus
images.

Every accessor maps to one file in the bucket. The loader does no
math (no averaging across sessions, no rebinning) -- it returns the
raw contents of the file you pick.

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

from laion_fmri.discovery import get_subjects
from laion_fmri.subject import load_subject

subject_id = get_subjects()[0]
sub = load_subject(subject_id)

session = sub.get_sessions()[0]
print(f"Subject: {subject_id} | session: {session}")
print(f"Voxels in brain mask: {sub.get_n_voxels()}")

available_rois = sub.get_available_rois()
roi = available_rois[0] if available_rois else None
if roi is not None:
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
# ``"all"``. Lists union and de-dup.

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

from laion_fmri._paths import glmsingle_subject_dir
from laion_fmri.group import load_subjects

# Group loading reads each subject's local files, so we restrict to
# subjects whose data is actually on disk.
on_disk = [
    s for s in get_subjects()
    if glmsingle_subject_dir(get_data_dir(), s).is_dir()
]
group = load_subjects(on_disk[:2])
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
# Wraps one session of a subject as a ``torch.utils.data.Dataset``
# yielding ``{betas, image, stimulus_id, session, rep_index}``.
#
# Requires the ``torch`` extra:
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

"""
Quick Start
===========

End-to-end walkthrough: initialize, query, download, and load
data.

This example touches every step of a typical LAION-fMRI workflow:

1. Initialize a local data directory
2. Query what is available in the dataset
3. Download data for a single subject
4. Load and inspect the data

For deeper dives into each step, see the focused examples on
:doc:`initialization <plot_02_initialization>`,
:doc:`querying <plot_03_querying>`, and
:doc:`loading <plot_04_loading>`.
"""

# %%
# Initialize the data directory
# ------------------------------
#
# Examples 1, 2, and 4 share one data directory so the licenses
# accepted here, and the data downloaded below, are reused by the
# other examples without re-prompting or re-downloading.

import os

from laion_fmri.config import dataset_initialize, get_data_dir

data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)
print(f"Data directory: {get_data_dir()}")

# %%
# Query the dataset
# ------------------
#
# The bucket is public, so no AWS credentials are needed.
# Discovery functions read directly from the S3 bucket, so you
# can see what is available before downloading anything.

from laion_fmri.discovery import describe, get_subjects

print(f"Available subjects: {get_subjects()}")
describe()

# %%
# Download one subject -- but just one session, in parallel
# ----------------------------------------------------------
#
# A full subject is several tens of GB. ``download`` accepts BIDS
# entities (``ses``, ``task``, ``space``, ``desc``, ``stat``,
# ``suffix``, ``extension``) as filters, so you can grab just the
# slice you need.
#
# **About** ``ses``: when set to a session ID, only that session's
# files are pulled -- subject-level aggregate maps (the per-subject
# noise-ceiling variants, the mean-R^2 summaries, etc.) are
# *excluded*. To pull only those aggregates, use the special value
# ``ses="averages"``; combine with a list to pull both. The brain
# mask is the one exception -- it's automatically included with any
# ``ses`` filter, since the loader needs it to mask voxels.
#
# ``n_jobs`` runs that many ``aws s3 cp`` workers in parallel. The
# call is also idempotent -- re-running after an interrupted
# transfer skips files that already match the bucket size, so you
# only fetch what's missing.
#
# The neuroimaging data and the stimuli are covered by two separate
# licenses. On the first download you will be prompted **twice** --
# once for each -- and you must type ``I AGREE`` each time:
#
# 1. **Neuroimaging data** (CC0 1.0) -- unrestricted use.
# 2. **Stimuli** (closed, research-only) -- no redistribution, no
#    commercial or AI/ML-training use.
#
# The acceptances are persisted, so the prompts only appear on the
# first download into a given data directory.

from laion_fmri.download import download

subject_id = get_subjects()[0]
session_id = "ses-01"
print(f"Downloading {subject_id} / {session_id}")
download(
    subject=subject_id,
    ses=session_id,
    include_stimuli=True,
    n_jobs=4,
)

# %%
# Load the subject
# -----------------
#
# Once data is on disk, load a :class:`~laion_fmri.subject.Subject`
# and inspect its sessions and available ROIs. The brain mask is
# derived on the fly from the subject-level mean-R^2 file
# (``..._stat-rsquare_desc-R2mean_statmap.nii.gz``) -- voxels with
# any non-zero GLMsingle fit are considered "in brain".

from laion_fmri.subject import load_subject

sub = load_subject(subject_id)
print(f"Subject:   {sub.subject_id}")
print(f"Sessions:  {sub.get_sessions()}")
print(f"Voxels:    {sub.get_n_voxels()}")
print(f"ROIs:      {sub.get_available_rois()}")

# %%
# Single-trial betas
# -------------------
#
# ``get_betas`` returns ``(n_trials, n_voxels)`` within the brain
# mask. **For real subjects the brain-mask voxel count is ~270k**;
# multiplied by ~1000 trials per session, that's ~1 GB per call.
# In practice you should always pass an ``roi=`` filter to keep the
# array small (face-area ROI, e.g. ~1000 voxels, drops the call to
# a few MB).

session = sub.get_sessions()[0]

# Without ROI: heavy but works.
betas_all = sub.get_betas(session=session)
print(f"{session} betas (full mask): {betas_all.shape}")

# Recommended: use an ROI filter.
rois_face = sub.get_available_rois(category="face")
if rois_face:
    betas_face = sub.get_betas(session=session, roi="face")
    print(f"{session} betas (face union): {betas_face.shape}")

# %%
# Per-session noise ceiling
# --------------------------

nc = sub.get_noise_ceiling(session=session)
print(
    f"NC: shape={nc.shape}, "
    f"range=[{nc.min():.3f}, {nc.max():.3f}]"
)

# %%
# Stimulus images (when uploaded)
# --------------------------------
#
# Stimuli are forward-compatible: the API is in place but the
# images themselves arrive in the bucket later. Until then, the
# call below will raise ``StimuliNotDownloadedError`` -- that's
# the intended signal.

# images = sub.get_images()
# print(f"Images: {len(images)}")

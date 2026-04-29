"""
Quick Start
===========

End-to-end walkthrough: initialize, authenticate, query, download,
and load data.

This example touches every step of a typical LAION-fMRI workflow:

1. Initialize a local data directory
2. Provide AWS credentials (only required while the bucket is private)
3. Query what is available in the dataset
4. Download data for a single subject
5. Load and inspect the data

For deeper dives into each step, see the focused examples on
:doc:`initialization <plot_02_initialization>`,
:doc:`querying <plot_03_querying>`, and
:doc:`loading <plot_04_loading>`.
"""

# %%
# Initialize the data directory
# ------------------------------
#
# Each example uses its own data directory so they don't step on
# each other when re-run. The quickstart's directory is also
# reused by :doc:`querying <plot_03_querying>` and
# :doc:`loading <plot_04_loading>`, since those examples need
# the data this one downloads.

import os

from laion_fmri.config import dataset_initialize, get_data_dir

data_dir = os.path.join(os.getcwd(), "laion_fmri_quickstart")
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)
print(f"Data directory: {get_data_dir()}")

# %%
# Provide AWS credentials (pre-release only)
# -------------------------------------------
#
# The LAION-fMRI bucket is private during development, so the
# package needs AWS credentials to list and download data. The
# easiest way is :func:`laion_fmri.config.set_aws_credentials`,
# which sets the right environment variables for the current
# Python process. Nothing is written to disk.
#
# Once the bucket is made public this step becomes optional --
# requests fall back to anonymous access automatically.
#
# .. code-block:: python
#
#     from laion_fmri.config import set_aws_credentials
#     set_aws_credentials(
#         access_key_id="AKIA...",
#         secret_access_key="...",
#     )
#
# Sanity check that the AWS CLI sees credentials:

from laion_fmri._s3_engine import has_aws_credentials

if has_aws_credentials():
    print("AWS credentials detected -- signed requests.")
else:
    print(
        "No credentials detected -- only public buckets will work."
    )

# %%
# Query the dataset
# ------------------
#
# Discovery functions read directly from the S3 bucket, so you can
# see what is available before downloading anything.

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
# **About ``ses``:** when set to a session ID, only that session's
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
# and inspect its sessions, voxel count, and available ROIs.

from laion_fmri.subject import load_subject

sub = load_subject(subject_id)
print(f"Subject:   {sub.subject_id}")
print(f"Sessions:  {sub.get_sessions()}")
print(f"Voxels:    {sub.get_n_voxels()}")
print(f"ROIs:      {sub.get_available_rois()}")

# %%
# Load single-trial betas for one session
# -----------------------------------------
#
# Single-trial betas live per session in the bucket, so
# ``session`` is required. ``get_betas`` returns a
# ``(n_trials, n_voxels)`` array within the brain mask.

session = sub.get_sessions()[0]
betas = sub.get_betas(session=session)
print(f"{session} betas: {betas.shape}")

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

"""
Querying the Dataset
=====================

Explore subjects, sessions, runs, ROIs, stimuli, and trial metadata.

This example covers two layers of discovery:

* **Dataset-wide** queries (``get_subjects``, ``get_rois``,
  ``describe``) read directly from the S3 bucket. They work
  immediately after :doc:`initialization <plot_02_initialization>`,
  with no subject downloaded yet.
* **Per-subject** queries (``sub.get_sessions``, ``sub.get_trial_info``,
  ...) operate on local files and require that the subject has
  been downloaded by :doc:`plot_01 <plot_01_quickstart>`.
"""

# %%
# Bind the quickstart's data directory
# -------------------------------------
#
# This example shares the data directory the quickstart populated
# so per-subject queries find data on disk. Run the quickstart
# first if you haven't already.

import os

from laion_fmri.config import dataset_initialize

data_dir = os.path.join(os.getcwd(), "laion_fmri_quickstart")
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)

# %%
# Dataset-wide discovery
# -----------------------
#
# The discovery API queries the S3 bucket directly -- it always
# reflects the dataset, independent of what is downloaded locally.

from laion_fmri.discovery import describe, get_rois, get_subjects

print(f"Subjects:       {get_subjects()}")
print(f"Available ROIs: {get_rois()}")

describe()

# %%
# Participants table
# -------------------
#
# The BIDS ``participants.tsv`` lives at the dataset root and can be
# read with pandas.

import pandas as pd

from laion_fmri.config import get_data_dir

participants = pd.read_csv(
    f"{get_data_dir()}/participants.tsv", sep="\t"
)
print(participants)

# %%
# Per-subject discovery
# ----------------------
#
# Each :class:`~laion_fmri.subject.Subject` exposes query methods for
# sessions, voxels, ROIs, and stimulus counts. We pick the first
# subject available in the bucket so the example adapts to whatever
# is actually downloaded.

from laion_fmri.subject import load_subject

sub = load_subject(get_subjects()[0])

print(f"Subject:        {sub.subject_id}")
print(f"Sessions:       {sub.get_sessions()}")
print(f"Voxels:         {sub.get_n_voxels()}")
print(f"ROIs:           {sub.get_available_rois()}")

# Stimulus counts depend on the dataset-wide ``stimuli/`` prefix,
# which is forward-compat -- not yet populated in the bucket.
if sub.has_stimuli():
    print(f"Stimuli total:  {sub.get_n_stimuli()}")
    print(f"  shared:       {sub.get_n_stimuli(stimuli='shared')}")
    print(f"  unique:       {sub.get_n_stimuli(stimuli='unique')}")
else:
    print("Stimuli:        not yet uploaded to the bucket")

# %%
# Trial information: runs, repetitions, stimulus IDs
# ----------------------------------------------------
#
# Trial information lives per session in a GLMsingle ``events.tsv``.
# The ``session`` argument is required; pick one of the available
# sessions on the subject.

session = sub.get_sessions()[0]
trial_info = sub.get_trial_info(session=session)
print(f"Session: {session}")
print(f"Columns: {list(trial_info.columns)}")
print(f"Trials in this session: {len(trial_info)}")
print(trial_info.head())

# %%
# Stimulus metadata
# ------------------
#
# ``stimuli.tsv`` catalogues every image: its ID, whether it is part
# of the shared subset, its filename, and a category label. The
# ``stimuli/`` prefix is forward-compat -- once it lands in the
# bucket, the cell below will print the full table.

if sub.has_stimuli():
    stim_meta = sub.get_stimulus_metadata()
    print(f"Columns: {list(stim_meta.columns)}")
    print(f"Total stimuli: {len(stim_meta)}")
    print(stim_meta.head())

    print(f"\nShared: {stim_meta['shared'].sum()}")
    print(f"Unique: {(~stim_meta['shared']).sum()}")
    print("\nCategories:")
    print(stim_meta["category"].value_counts())
else:
    print("Stimulus metadata not yet uploaded to the bucket.")

# %%
# Trial-to-stimulus mapping
# --------------------------
#
# For one session, ``get_trial_stimulus_indices`` returns the
# stimulus-metadata row index that each trial points at. Like the
# stimulus metadata itself, this depends on ``stimuli/`` being
# populated.

if sub.has_stimuli():
    stim_indices = sub.get_trial_stimulus_indices(session=session)
    print(f"Mapping shape: {stim_indices.shape}")
    print(f"First 10 trial -> stim idx: {stim_indices[:10]}")
else:
    print(
        "Trial-to-stimulus mapping needs stimuli metadata; "
        "skipping until the bucket's stimuli/ is populated."
    )

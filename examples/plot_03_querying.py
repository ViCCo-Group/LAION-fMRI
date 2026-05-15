"""
Querying the Dataset
=====================

Discover what is in the dataset without downloading anything.

Most cells in this example query the S3 bucket directly
(``laion_fmri.discovery``) or read bundled metadata that ships with
the package (``laion_fmri.splits``) -- no subject data is fetched.
The stimulus-metadata cell below is the one exception: it reads
``Subject.metadata`` from a subject already on disk (the quickstart
example downloads ``sub-01 / ses-01`` into a shared data
directory). For other Subject-API calls the corresponding
``download(...)`` invocations are shown **commented out**, so you
can copy them without this script triggering a download.

Pick the subject you want to look at on the line below:
"""

SUBJECT = "sub-01"

# %%
# Initialize a data directory
# ----------------------------
#
# Discovery and split listings don't need data on disk, but
# ``dataset_initialize`` is still required so that any subsequent
# (commented-out) ``download(...)`` would have a destination.

import os

from laion_fmri.config import dataset_initialize

data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)

from laion_fmri.discovery import (
    describe,
    get_rois,
    get_subjects,
    inspect_bucket,
)

# %%
# Top-level summary
# ------------------
#
# ``describe()`` prints a one-screen overview: bucket name, subject
# count, and the first subject's ROI list. Run it first to confirm
# the bucket is reachable.

describe()

# %%
# Subjects in the bucket
# -----------------------
#
# ``get_subjects`` lists every subject the bucket exposes,
# including ones whose data is only partially uploaded -- so the
# count matches the dataset's published size, not just the
# subjects with complete data.

print(f"All subjects: {get_subjects()}")
print(f"Querying subject: {SUBJECT}")

# %%
# ROI queries: specific / category / all
# ---------------------------------------
#
# ROIs ship in eight categories on the bucket. Use the
# ``category=`` filter when you want to scope a query to one
# functional family (e.g. just the face-area ROIs); call
# ``get_rois`` without a filter when you want the full inventory.

ROI_CATEGORIES = (
    "body", "character", "face", "laion",
    "motion", "object", "place", "retinotopy",
)

print(f"All ROIs ({len(get_rois(SUBJECT))}):")
print(get_rois(SUBJECT))
print()
for cat in ROI_CATEGORIES:
    rois = get_rois(SUBJECT, category=cat)
    print(f"{cat}: {rois}")

# %%
# Bucket diagnostic listing
# --------------------------
#
# ``inspect_bucket`` prints the immediate top-level prefixes plus a
# count of subject directories under each derivative tree -- useful
# when discovery returns surprises.

inspect_bucket()

# %%
# Bundled train/test splits (no download required)
# -------------------------------------------------
#
# ``laion_fmri.splits`` ships predefined train/test partitions of
# the stimulus set so callers can compare against the published
# baselines without re-running any clustering or sampling.

from laion_fmri.splits import (
    get_train_test_ids,
    list_ood_types,
    list_pools,
    list_splits,
    load_split,
)

print(f"Pools:     {list_pools()}")
print(f"Splits:    {list_splits()}")
print(f"OOD types: {list_ood_types()}")

# %%
# Inspect one split
# ------------------
#
# ``load_split(name, pool=...)`` returns a ``Split`` describing the
# split's sizes and family. ``get_train_test_ids`` is the
# convenience wrapper that gives you the actual ID lists in one
# call.

split = load_split("random_0", pool="shared")
print(f"Split:    {split.name}")
print(f"Pool:     {split.pool}")
print(f"Family:   {split.split_family}")
print(f"n_train:  {split.n_train}")
print(f"n_test:   {split.n_test}")

train_ids, test_ids = get_train_test_ids("random_0", pool="shared")
print(f"Loaded:   {len(train_ids)} train / {len(test_ids)} test ids")

# %%
# OOD splits with a type filter
# ------------------------------
#
# The ``ood`` split partitions held-out stimuli by category; the
# ``ood_types=`` argument restricts which categories are kept in the
# test set.

_, test_shape = get_train_test_ids(
    "ood", pool="shared", ood_types=["shape"],
)
print(f"OOD shape only:  test ids = {len(test_shape)}")

# %%
# Per-subject queries that need local data
# -----------------------------------------
#
# Discovery covers what is *available*; once you commit to working
# with a specific subject, the per-subject API on
# :class:`~laion_fmri.subject.Subject` is what you reach for. Those
# methods read on-disk files, so they presuppose a download. The
# block below is **commented out** to keep this example offline --
# copy the lines you need into your own script after running
# ``download(...)`` for the subject and session you care about.
#
# .. code-block:: python
#
#     from laion_fmri.download import download
#     # one session for one subject (~few hundred MB):
#     download(subject="sub-01", ses="ses-01")
#
#     from laion_fmri.subject import load_subject
#     sub = load_subject("sub-01")
#
#     # Sessions present on disk
#     print(sub.get_sessions())                      # ['ses-01', ...]
#
#     # Trial info: runs, repetitions, stimulus labels
#     trials = sub.get_trial_info(session="ses-01")
#     # columns: session, run, beta_index, label
#     print(trials.columns.tolist())
#     print(trials["run"].unique())                  # runs in this session
#     print(len(trials))                             # trial count
#
#     # Single-trial betas with the multi-level ROI grammar
#     betas_one  = sub.get_betas(session="ses-01", roi="FFA1")
#     betas_face = sub.get_betas(session="ses-01", roi="face")
#     betas_all  = sub.get_betas(session="ses-01", roi="all")
#
#     # Multi-format ROI loading
#     roi = sub.get_roi_data("FFA1", format="all", hemi="all")
#     # roi["FFA1"] is a nested dict:
#     # {
#     #   "volume": <1-D bool>,
#     #   "gii": {"hemi-L": {"func.gii": ..., "label": ...},
#     #           "hemi-R": {...}},
#     # }

# %%
# Cross-subject discovery
# ------------------------
#
# Loop ``get_subjects()`` to ask the same questions of every subject
# in the bucket. ROI counts can differ across subjects (some ROIs
# don't exist for everyone).

for sub_id in get_subjects():
    n_face = len(get_rois(sub_id, category="face"))
    n_total = len(get_rois(sub_id))
    print(f"  {sub_id}: {n_total:>3} ROIs total, {n_face} face")

# %%
# Stimulus metadata
# ------------------
#
# Trial-level stimulus metadata is exposed as a
# ``pandas.DataFrame`` via the ``Subject.metadata`` property --
# one row per single-trial beta, indexed by global trial index
# (``0 .. n_total_trials-1``). Columns combine the per-session
# events TSV with derived fields like ``image_name``, ``session``,
# ``session_trial``, ``stim_idx``, and ``unique_or_shared``. The
# same table is what :doc:`plot_04_loading` uses to align betas
# with images.
#
# This reads ``sub-01`` from the shared data directory that
# :doc:`plot_01_quickstart` populates; if you're running plot_03
# in isolation, run plot_01 first (or call ``download(...)``
# yourself).

from laion_fmri.subject import load_subject

sub = load_subject(SUBJECT)
df = sub.metadata
print(df.head())
print(f"Total trials: {len(df)}")
shared = (df["unique_or_shared"] == "shared").sum()
print(f"Shared:       {shared}")
print(f"Per session:  {df['session'].value_counts().to_dict()}")

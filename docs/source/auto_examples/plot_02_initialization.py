"""
Dataset Initialization
=======================

One-time setup before working with the LAION-fMRI dataset.

This example walks through the steps a new user takes the first
time they use the package:

1. Configure the local data directory.
2. Read the licenses you'll be asked to accept on first download.
3. Confirm you can reach the bucket and see what it contains.

Downloads themselves are covered by the
:doc:`quick start <plot_01_quickstart>`.
"""

# %%
# Initialize the data directory
# ------------------------------
#
# Pick a location with enough disk space. The choice is persisted
# so subsequent sessions pick it up automatically -- you don't need
# to call ``dataset_initialize`` again from the same machine.

import os

from laion_fmri.config import dataset_initialize, get_data_dir

# If you already accepted the licenses in another example, the
# following cells just confirm the configuration -- you won't be
# re-prompted.
data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)
print(f"Configured: {get_data_dir()}")

# %%
# Inspect the license texts
# --------------------------
#
# Two licenses apply:
#
# * The **dataset license** (CC0 1.0) covers the brain and
#   participant data.
# * The **stimulus license** (closed, research-only) covers the
#   stimulus images.
#
# Below we print the body of each so you can read the terms in
# advance. The actual ``Type "I AGREE"`` prompt happens in the
# next cell.

from laion_fmri._constants import (
    LICENSE_AGREEMENT_BODY,
    STIMULI_LICENSE_BODY,
)

print(LICENSE_AGREEMENT_BODY)
print("---")
print(STIMULI_LICENSE_BODY)

# %%
# Accept the licenses
# --------------------
#
# This is the same prompt-and-write-marker flow that
# :func:`laion_fmri.download.download` triggers internally on its
# first call. ``accept_licenses(include_stimuli=True)`` prompts
# you to type ``I AGREE`` for both the dataset license and the
# stimulus license, then records your acceptance under
# ``{data_dir}/.laion_fmri/`` so future ``download(...)`` calls
# don't ask again.
#
# If you decline either prompt, the helper raises -- the exception
# is the signal that you opted out and that downstream
# ``download(...)`` calls would refuse to run for the
# corresponding data.

from laion_fmri.download import accept_licenses

accept_licenses(include_stimuli=True)

# %%
# Confirm bucket access
# ----------------------
#
# The bucket is public, so discovery works without any
# credential setup. The functions below query the bucket
# directly and tell you what is available in the dataset
# regardless of what you have downloaded -- a quick way to
# confirm that initialization is complete and the bucket is
# reachable from your network.

from laion_fmri.discovery import describe, get_subjects

print(f"Subjects in bucket: {get_subjects()}")
describe()

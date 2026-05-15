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
# Inspect the license text
# -------------------------
#
# Two licenses apply, handled differently:
#
# * The **dataset license** (CC0 1.0) covers the brain and
#   participant data. It is accepted locally on first
#   ``download(...)`` call and the acceptance is persisted under
#   ``{data_dir}/.laion_fmri/``.
# * The **stimulus license** covers the stimulus images and is
#   gated by an external access service. The full terms are read
#   and accepted on the service's web form, not locally; approved
#   requests then unlock per-trial image downloads via the
#   dataloader.
#
# The dataset-license body prints below; the stimulus terms are
# available at the access-service URL.

from laion_fmri._constants import (
    ACCESS_SERVICE_URL,
    LICENSE_AGREEMENT_BODY,
)

print(LICENSE_AGREEMENT_BODY)
print("---")
print(f"Stimulus terms: {ACCESS_SERVICE_URL}/terms")

# %%
# Accept the dataset license
# ---------------------------
#
# This is the same prompt-and-write-marker flow that
# :func:`laion_fmri.download.download` triggers internally on its
# first call. ``accept_license()`` shows the CC0 text, prompts you
# to type ``I AGREE``, and records the acceptance under
# ``{data_dir}/.laion_fmri/`` so future ``download(...)`` calls
# don't ask again. If you decline, the helper raises -- the
# exception is the signal that downstream ``download(...)`` calls
# would refuse to run.
#
# Stimulus access is requested separately: run
# ``laion-fmri request-access`` from the shell, or call
# :func:`laion_fmri.download.request_stimulus_access` from Python.
# The access service approves requests asynchronously.

from laion_fmri.download import accept_license

accept_license()

# %%
# Request stimulus access
# ------------------------
#
# Stimulus images are gated by a Data Use Agreement that lives on
# an external access service. There are two equivalent entry
# points for submitting a request:
#
# * **CLI (recommended for first use):** ``laion-fmri request-access``
#   walks an interactive form (full name, institutional email,
#   institution, optional PI, research purpose, signed DUA
#   confirmation) and caches the resulting ``request_id`` under
#   ``{data_dir}/.laion_fmri/`` once approved.
# * **Python:**
#   :func:`laion_fmri.download.request_stimulus_access` runs the
#   same form from a script or notebook.
#
# Approval is asynchronous: you submit the request, the service
# vets it, and your cached ``request_id`` then unlocks signed URLs
# the dataloader requests on demand. Two related helpers are worth
# knowing:
#
# * :func:`laion_fmri._stimulus_access.current_terms_version`
#   reports the ToU version the server currently expects in
#   submissions -- handy if you want to print the version before
#   filling out the form.
# * :class:`laion_fmri._stimulus_access.TermsOutdatedError` is
#   raised when a cached ``request_id`` predates a ToU update;
#   re-run ``request-access`` to refresh.

from laion_fmri._constants import ACCESS_SERVICE_URL
from laion_fmri._stimulus_access import (  # noqa: F401
    current_terms_version,
)

print(
    "Access service: "
    f"{ACCESS_SERVICE_URL}\n"
    "Current ToU version (fetched on demand): "
    "use current_terms_version() to print before submitting."
)
# Uncomment to fetch the live ToU version:
# print(f"Current ToU: {current_terms_version()}")

# Uncomment to run the interactive form (this prints prompts and
# waits for user input -- skipped here so the gallery build
# stays non-interactive):
# from laion_fmri.download import request_stimulus_access
# request_stimulus_access()

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

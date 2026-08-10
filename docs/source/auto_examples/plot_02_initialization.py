"""
Dataset Initialization
=======================

Before any of the loaders or download helpers can do anything
useful, a small amount of one-time setup is needed. This example
walks through what that setup involves and why each step exists.

The plan is to:

1. Pick a location on disk and tell the package about it.
2. Read the two licenses that govern the dataset, so it is
   clear what is being agreed to before the first download.
3. Accept the dataset license and request stimulus access.
4. Confirm the bucket is reachable.

The :doc:`quick start <plot_01_quickstart>` then picks up from
here and runs an end-to-end download + analysis pass.
"""

# %%
# Initialize the data directory
# -----------------------------
#
# The package needs to know where to keep the data on disk
# before it can download anything. A subject's data adds up to
# several tens of gigabytes, so the location should be chosen
# with that in mind. A fast local SSD is ideal, a shared
# network drive is fine, anything close to full is not.
#
# ``dataset_initialize`` writes the chosen path to a small
# configuration file so subsequent Python sessions pick it up
# automatically. It does not have to be called more than once
# per machine; the loaders read the same config to find data on
# subsequent imports.

import os

from laion_fmri.config import dataset_initialize, get_data_dir

# If the licenses have already been accepted in another example,
# the following cells just confirm the configuration, so no
# re-prompt will occur.

# define and initialize the data directory
data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)
print(f"Configured: {get_data_dir()}")

# %%
# Inspect the license text
# ------------------------
#
# The dataset is shipped under two separate agreements (a
# permissive one for the brain data and a more restrictive one
# for the stimulus images), and they are handled differently,
# which is worth knowing before any download is started.
#
# * The **dataset license** (CC0 1.0) covers the brain and
#   participant data. It is accepted locally on the first
#   ``download(...)`` call and the acceptance is persisted under
#   ``{data_dir}/.laion_fmri/``. CC0 means unrestricted use,
#   no attribution, no clauses on what can be done with the
#   data, no redistribution gate.
# * The **stimulus license** covers the stimulus images and is
#   gated by an external access service. The full terms are
#   read and accepted on the service's web form, not locally;
#   approved requests then unlock per-trial image downloads via
#   the dataloader. The agreement restricts use to research,
#   no redistribution, no commercial or AI/ML-training use.
#
# The dataset-license body is printed below so it can be
# inspected before the next cell accepts it; the stimulus terms
# live behind the access-service URL.

from laion_fmri._constants import (
    ACCESS_SERVICE_URL,
    LICENSE_AGREEMENT_BODY,
)

# print the dataset-license body and the stimulus-terms URL
print(LICENSE_AGREEMENT_BODY)
print("---")
print(f"Stimulus terms: {ACCESS_SERVICE_URL}/terms")

# %%
# Accept the dataset license
# --------------------------
#
# ``accept_license()`` is the explicit version of the prompt
# that :func:`laion_fmri.download.download` would otherwise
# trigger on its first call. It shows the CC0 text, asks for an
# ``I AGREE`` confirmation, and writes a small marker file under
# ``{data_dir}/.laion_fmri/``. Calling it up-front means the
# first real download will skip the prompt, which is useful in
# CI, in notebooks where the input prompt is awkward, or simply
# for making the acceptance step explicit in a script.
#
# If the user declines, the helper raises rather than silently
# moving on. This is the signal that subsequent
# ``download(...)`` calls will refuse to run, so the failure is
# visible immediately rather than later.
#
# Stimulus access is handled separately; it is the subject of
# the next cell.

from laion_fmri.download import accept_license

# accept the CC0 dataset license
accept_license()

# %%
# Request stimulus access
# -----------------------
#
# Unlike the dataset license, the stimulus agreement cannot be
# accepted from a local prompt. Every researcher has to fill in
# a Data Use Agreement on an external access service that vets
# requests by hand. This cell shows how to submit that request;
# everything that needs an actual image (the stimulus loader,
# the segmentation accessors, the captions and embeddings)
# requires this to be approved first.
#
# There are two equivalent entry points for submitting the
# request. The CLI version is usually the easiest the first
# time around because it walks through the form interactively:
#
# * **CLI (recommended for first use):** ``laion-fmri
#   request-access`` walks an interactive form (full name,
#   institutional email, institution, optional PI, research
#   purpose, signed DUA confirmation) and caches the resulting
#   ``request_id`` under ``{data_dir}/.laion_fmri/`` once
#   approved.
# * **Python:**
#   :func:`laion_fmri.download.request_stimulus_access` runs
#   the same form from a script or notebook.
#
# Approval is asynchronous, so the request is submitted, the
# service vets it, and the cached ``request_id`` then unlocks
# signed URLs that the dataloader requests on demand. Two
# helpers around this are worth knowing about:
#
# * :func:`laion_fmri._stimulus_access.current_terms_version`
#   reports the ToU version the server currently expects in
#   submissions, worth printing before filling out the form
#   so the same version ends up in the agreement.
# * :class:`laion_fmri._stimulus_access.TermsOutdatedError` is
#   raised when a cached ``request_id`` predates a ToU update;
#   in that case ``request-access`` has to be re-run to refresh
#   the cached approval.

from laion_fmri._constants import ACCESS_SERVICE_URL
from laion_fmri._stimulus_access import (  # noqa: F401
    current_terms_version,
)

# print the access-service URL and the ToU helper hint
print(
    "Access service: "
    f"{ACCESS_SERVICE_URL}\n"
    "Current ToU version (fetched on demand): "
    "use current_terms_version() to print before submitting."
)
# uncomment to fetch the live ToU version:
# print(f"Current ToU: {current_terms_version()}")

# uncomment to run the interactive form (this prints prompts and
# waits for user input, so it is skipped here so the gallery build
# stays non-interactive):
# from laion_fmri.download import request_stimulus_access
# request_stimulus_access()

# %%
# Confirm bucket access
# ---------------------
#
# With the data directory configured and the dataset license
# accepted, the final sanity check is that the bucket is
# actually reachable. The discovery functions are perfect for
# this. They hit the bucket directly, do not require any AWS
# credentials (the bucket is public for read), and do not pull
# any subject data to disk. If they return without error, the
# network path is clean and the package is ready to use.

from laion_fmri.discovery import describe, get_subjects

# list the subjects in the bucket and print a one-screen overview
print(f"Subjects in bucket: {get_subjects()}")
describe()

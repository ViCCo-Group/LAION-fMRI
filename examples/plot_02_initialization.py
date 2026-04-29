"""
Dataset Initialization
=======================

One-time setup before working with the LAION-fMRI dataset.

This example walks through the steps a new user takes the first
time they use the package:

1. Configure the local data directory.
2. Provide AWS credentials (only needed while the bucket is
   private).
3. Read the licenses you'll be asked to accept on first download.
4. Confirm you can reach the bucket and see what it contains.

Downloads themselves are covered by the
:doc:`quick start <plot_01_quickstart>`.
"""

# %%
# Initialize the data directory
# ------------------------------
#
# Pick a location with enough disk space. The path is persisted in
# ``$XDG_CONFIG_HOME/laion_fmri/config.json`` (or ``~/.config`` by
# default) so subsequent sessions pick it up automatically.

import os

from laion_fmri.config import dataset_initialize, get_data_dir

# Each example uses its own data directory; this one is isolated
# from the quickstart (which downloads) so re-running here does
# not perturb the quickstart's data.
data_dir = os.path.join(os.getcwd(), "laion_fmri_init_demo")
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)
print(f"Configured: {get_data_dir()}")

# %%
# AWS credentials (pre-release only)
# ------------------------------------
#
# The LAION-fMRI S3 bucket is **private during development** and
# **public after release**. The package wraps the official
# ``awscli`` (installed automatically as a dependency) and respects
# its standard credential chain.
#
# During the private phase you need an AWS access key and secret.
# The easiest path is to call
# :func:`laion_fmri.config.set_aws_credentials` at the start of
# your script or notebook. The call only sets environment
# variables for the current Python process; nothing is written to
# disk.

from laion_fmri.config import set_aws_credentials  # noqa: F401

# set_aws_credentials(
#     access_key_id="AKIA...",
#     secret_access_key="...",
# )

# Any AWS CLI-compatible credential source also works:
#
# * Shell env vars (``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``)
# * ``~/.aws/credentials`` (populated by ``aws configure`` or by hand)
# * An IAM role, when running on AWS infrastructure
#
# Once the bucket goes public, all of the above becomes optional
# -- the package will fall back to anonymous S3 access
# automatically.
#
# Sanity-check that the AWS CLI can see your credentials:

from laion_fmri._s3_engine import has_aws_credentials

if has_aws_credentials():
    print("AWS credentials detected -- signed requests.")
else:
    print("No credentials -- unsigned (public bucket only).")

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
# Discovery functions query the bucket directly -- they describe
# what's available in the dataset, regardless of what you have
# downloaded. Running them is a quick smoke test that
# initialization is complete and credentials work.

from laion_fmri.discovery import describe, get_subjects

print(f"Subjects in bucket: {get_subjects()}")
describe()

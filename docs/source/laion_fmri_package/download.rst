========
Download
========

.. code-block:: python

   from laion_fmri.download import download

   download(
       subject,                  # required
       ses=None,                 # str | list, e.g. "01" or ["ses-01", ...]
       task=None,                # str | list, e.g. "images"
       space=None,               # str | list, e.g. "T1w"
       desc=None,                # str | list, e.g. "singletrial"
       stat=None,                # str | list, e.g. "effect"
       suffix=None,              # str | list, e.g. "statmap"
       extension=None,           # str | list, e.g. "nii.gz"
       include_stimuli=False,    # also mirror stimuli/ when populated
       n_jobs=1,                 # parallel `aws s3 cp` workers
   )

Arguments
=========

* ``subject`` accepts the full BIDS form (``"sub-03"``) or just
  the bare value (``"03"``). The special value ``"all"``
  iterates every subject the bucket exposes.
* All other entity filters accept a single string or a list. A
  bare value (``ses="04"``) and the full BIDS token
  (``ses="ses-04"``) are equivalent.

Filter semantics
================

* **Permissive (default for every entity except ``ses``):** a
  file that doesn't carry the entity is *not* excluded by a
  filter on it. This lets subject-level summaries flow through
  alongside files that *do* carry the entity.
* **Strict ``ses``:** specifying a session ID excludes
  per-subject summary files. Use the special value
  ``ses="averages"`` to fetch *only* those summaries; combine
  with session IDs in a list to fetch both:

.. code-block:: python

   download(subject="sub-03", ses="ses-01")                  # session only
   download(subject="sub-03", ses="averages")                # summaries only
   download(subject="sub-03", ses=["ses-01", "averages"])    # both

The **brain mask** at
``derivatives/glmsingle-tedana/{sub}/{sub}_..._desc-meanR2gt15mask_mask.nii.gz``
is *auto-pinned* whenever ``ses`` filters to specific sessions
-- the loader needs it to mask voxels.

Idempotent re-runs
==================

Before each ``aws s3 cp`` the package checks whether the local
file already exists at exactly the bucket size. If yes, the
file is skipped. So:

* re-running ``download(...)`` after a complete fetch is
  effectively free (one ``list-objects-v2`` call per prefix);
* re-running after an interrupted fetch only pulls what was
  missing or partial.

Parallelism
===========

``n_jobs`` runs that many ``aws s3 cp`` workers concurrently.
Each worker is itself a multipart-parallel transfer, so a value
of 4 typically opens ~40 concurrent S3 connections.

Bad inputs (``n_jobs=0``, negative, very large, non-int) are
detected, warn, and fall back to a working value.

Command-line interface
======================

The same download flow is reachable from the shell via the
``laion-fmri`` console script (installed by ``pip``/``uv``):

.. code-block:: bash

   laion-fmri config   --data-dir ./laion_fmri_data
   laion-fmri info
   laion-fmri download --subject sub-03
   laion-fmri download --subject sub-03 --include-stimuli
   laion-fmri download --subject all

The CLI mirrors the Python ``download(...)`` signature: every
BIDS-entity filter the function accepts is exposed as a
flag, each accepting one or more values:

.. code-block:: bash

   # one session of single-trial betas, parallelized
   laion-fmri download \
       --subject sub-03 \
       --ses ses-01 \
       --desc singletrial --stat effect \
       --extension nii.gz \
       --n-jobs 4

   # session plus subject-level summaries, in one call
   laion-fmri download --subject sub-03 --ses ses-01 averages

Run ``laion-fmri --help`` (or ``laion-fmri download --help``)
for the full flag list.

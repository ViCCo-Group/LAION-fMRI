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
       include_stimuli=False,    # also pull the gated stimulus archive
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
* ``include_stimuli=True`` additionally fetches the stimulus
  archive after the fMRI download. Stimuli are dataset-wide (a
  single HDF5 covering all subjects), so this just calls
  :func:`download_stimuli` after the per-subject fetch. See
  :doc:`stimulus_access`.

Filter semantics
================

* **Permissive** (default for every entity except ``ses``): a
  file that doesn't carry the entity is *not* excluded by a
  filter on it. This lets subject-level summaries flow through
  alongside files that *do* carry the entity.
* **Strict** ``ses``: specifying a session ID excludes
  per-subject summary files. Use the special value
  ``ses="averages"`` to fetch *only* those summaries; combine
  with session IDs in a list to fetch both:

.. code-block:: python

   download(subject="sub-03", ses="ses-01")                  # session only
   download(subject="sub-03", ses="averages")                # summaries only
   download(subject="sub-03", ses=["ses-01", "averages"])    # both

The subject-level mean-R^2 file is automatically included
whenever ``ses`` filters to specific sessions -- the loader
needs it to derive the brain mask, so the strict ``ses``
filter doesn't drop it.

Idempotent re-runs
==================

Before each ``aws s3 cp`` the package checks whether the local
fMRI file already exists at exactly the bucket size. If yes, the
file is skipped. So:

* re-running ``download(...)`` after a complete fetch is
  effectively free (one ``list-objects-v2`` call per prefix);
* re-running after an interrupted fetch only pulls what was
  missing or partial.

The stimulus archive is verified by sha256 and supports HTTP ``Range``
resume, so an interrupted stimulus download picks up where it stopped
on the next call.

Parallelism
===========

``n_jobs`` runs that many ``aws s3 cp`` workers concurrently.
Each worker is itself a multipart-parallel transfer, so a value
of 4 typically opens ~40 concurrent S3 connections.

Bad inputs (``n_jobs=0``, negative, very large, non-int) are
detected, warn, and fall back to a working value.

``n_jobs`` does not affect the stimulus archive — it's a single
HDF5 streamed sequentially.

Stimulus-only downloads
=======================

Stimuli are dataset-wide (one HDF5 for all subjects), so when you
want only the stimulus archive — no fMRI files — use the
subject-independent function:

.. code-block:: python

   from laion_fmri.download import download_stimuli
   download_stimuli()

…or from the shell:

.. code-block:: bash

   laion-fmri download-stimuli

The first call walks through the Data Use Agreement form;
subsequent calls re-use the cached access state silently. See
:doc:`stimulus_access` for the full flow.

Command-line interface
======================

The same flows are reachable from the shell via the ``laion-fmri``
console script (installed by ``pip``/``uv``):

.. code-block:: bash

   laion-fmri config   --data-dir ./laion_fmri_data
   laion-fmri info
   laion-fmri download --subject sub-03
   laion-fmri download --subject sub-03 --include-stimuli
   laion-fmri download --subject all
   laion-fmri download-stimuli
   laion-fmri request-access          # standalone DUA form, no download
   laion-fmri login --request-id lfm_...
   laion-fmri logout

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

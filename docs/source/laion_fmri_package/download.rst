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
       include_stimuli=False,    # also pull the stimuli
       include_freesurfer=False, # also pull derivatives/freesurfer/
       include_anatomical=False, # also pull derivatives/anatomical/
       include_raw=False,        # also pull raw BIDS tree (sub-XX/)
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
  stimuli after the fMRI download. Stimuli are dataset-wide (a
  single HDF5 covering all subjects), so this just calls
  :func:`download_stimuli` after the per-subject fetch. See
  :doc:`access`.
* ``include_freesurfer=True`` pulls the per-subject FreeSurfer
  recon under ``derivatives/freesurfer/{subject}/`` (a few
  hundred MB per subject). Required by ``Subject.to_template``;
  see :doc:`template_space`.
* ``include_anatomical=True`` pulls the per-subject anatomical
  derivatives under ``derivatives/anatomical/{subject}/
  ses-PrismaAnat/anat/`` (T1w, T2w, brain mask at two
  resolutions; tens of MB per subject). Unlocks
  ``Subject.get_t1w`` / ``get_t2w`` /
  ``get_anatomical_brain_mask`` and the ``source="anatomical"``
  brain mask on the voxel-axis accessors; see :doc:`load`.
* ``include_raw=True`` pulls the raw BIDS tree under
  ``sub-XX/`` (multi-echo BOLD, sbref, per-run
  ``events.tsv``, fieldmaps, raw MEGRE). Combine with
  ``ses`` / ``run`` / ``echo`` / ``part`` / ``suffix`` /
  ``extension`` filters to narrow the fetch. Use
  :func:`download_raw` when you want the raw tree without
  the default derivative walk.

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

The stimuli is verified by sha256 and supports HTTP ``Range``
resume, so an interrupted stimulus download picks up where it stopped
on the next call.

Parallelism
===========

``n_jobs`` runs that many ``aws s3 cp`` workers concurrently.
Each worker is itself a multipart-parallel transfer, so a value
of 4 typically opens ~40 concurrent S3 connections.

Bad inputs (``n_jobs=0``, negative, very large, non-int) are
detected, warn, and fall back to a working value.

``n_jobs`` does not affect the stimuli — it's a single
HDF5 streamed sequentially.

Raw BIDS downloads
==================

The raw BIDS tree under ``sub-XX/`` holds the multi-echo BOLD
timeseries, single-band references, per-run ``events.tsv``,
fieldmaps, and the raw MEGRE anatomical. Reach it two ways:

* :func:`download` with ``include_raw=True`` -- fetches raw on
  top of the default derivative walk.
* :func:`download_raw` -- fetches raw only, no derivatives.

Both apply the BIDS filters below; raw-specific entities
(``run``, ``echo``, ``part``) are how you narrow to one run,
one echo, or magnitude vs. phase-encoded companion files.

.. code-block:: python

   from laion_fmri.download import download, download_raw

   # additive: derivatives + one run of raw BOLD/events
   download(
       subject="sub-01",
       include_raw=True,
       ses="ses-01",
       run="01",
       suffix=["bold", "events"],
   )

   # raw only: no derivative walk
   download_raw(
       subject="sub-01",
       ses="ses-01",
       run="01",
       echo="1",
       part="mag",
   )

   # all events TSVs for one session (any run)
   download_raw(
       subject="sub-01",
       ses="ses-01",
       suffix="events",
       extension="tsv",
   )

Stimulus-side downloads
=======================

Everything attached to the stimulus images -- the JPEGs themselves,
the pretrained embeddings, the object-segmentation masks, and the
captions -- is dataset-wide (one set of files for all subjects), so
each comes with its own subject-independent download function.

.. list-table::
   :widths: 25 15 12 48
   :header-rows: 1

   * - Function
     - CLI
     - Gated?
     - What it pulls
   * - :func:`download_stimuli`
     - ``download-stimuli``
     - **Yes** (DUA)
     - The stimulus HDF5 + metadata CSV. First call walks the
       Data Use Agreement form; subsequent calls re-use the
       cached request_id. See :doc:`access`.
   * - :func:`download_embeddings`
     - ``download-embeddings``
     - No (CC0)
     - One HDF5 per pretrained model -- CLIP, DINOv2, PEcore,
       SigLIP2 (~50 MB each, ~210 MB total).
   * - :func:`download_segmentations`
     - ``download-segmentations``
     - No (CC0)
     - One HDF5 (~68 MB) + sidecar CSV with object-level
       segmentation masks for the shared stimulus set.
   * - :func:`download_captions`
     - ``download-captions``
     - No (CC0)
     - One CSV with human + AI captions per stimulus.

All four are independent -- you only need ``download_stimuli`` first
if you want to load images themselves. The public auxiliaries
(``download_embeddings``, ``download_segmentations``,
``download_captions``) need no DUA and pull anonymously over public
S3.

Python:

.. code-block:: python

   from laion_fmri.download import (
       download_stimuli,
       download_embeddings,
       download_segmentations,
       download_captions,
   )

   # Gated (Data Use Agreement on first call):
   download_stimuli()

   # Public, no DUA:
   download_embeddings()                      # all four models
   download_embeddings(models=["CLIP"])       # one model
   download_segmentations()                   # ~68 MB
   download_captions()                        # ~few MB

CLI:

.. code-block:: bash

   laion-fmri download-stimuli                # gated
   laion-fmri download-embeddings             # all four models
   laion-fmri download-embeddings --model CLIP DINOv2
   laion-fmri download-segmentations
   laion-fmri download-captions

All download functions are **idempotent**: files whose local size
matches the S3 size are skipped, so re-running an interrupted
transfer only fetches what's missing.

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
   laion-fmri download-embeddings
   laion-fmri download-segmentations
   laion-fmri download-captions
   laion-fmri download-raw --subject sub-03
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

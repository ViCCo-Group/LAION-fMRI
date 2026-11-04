========
Download
========

The two datasets (:doc:`../dataset_at_a_glance`) each have a download
function, and both write into the same local tree:
:func:`download` for the main experiment and
:func:`download_mapping` for precision mapping (see
`Precision-mapping dataset`_ below).

The two overlap. The pRF maps, localizer maps and ROIs are derived from
precision mapping, but they are also what users of the main experiment
combine with the betas, so :func:`download` can fetch them for the five
subjects it covers. The anatomy and FreeSurfer reconstruction are shared by
both datasets. A file reached through both functions lands at the same local
path, and the second call skips it, so nothing is downloaded twice.

.. list-table::
   :widths: 40 30 30
   :header-rows: 1

   * - Files
     - :func:`download`
     - :func:`download_mapping`
   * - Betas
     - always
     - —
   * - Raw main-experiment sessions
     - ``include_raw``, or :func:`download_raw`
     - —
   * - LAION images, embeddings, segmentations, captions
     - with the ``include_*`` flags or their own functions
     - —
   * - ROIs
     - always
     - always
   * - pRF maps, localizer maps
     - ``include_retinotopy``, ``include_localizers``
     - always
   * - Anatomy, FreeSurfer
     - ``include_anatomical``, ``include_freesurfer``
     - ``include_anatomical``, ``include_freesurfer``
   * - Aperture libraries
     - —
     - always
   * - Precision-mapping data, raw and preprocessed
     - —
     - ``include_raw``, ``include_preproc``
   * - ``sub-04``, ``sub-08``
     - —
     - yes

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
       include_embeddings=False, # also pull stimulus embeddings
       include_freesurfer=False, # also pull derivatives/freesurfer/
       include_anatomical=False, # also pull derivatives/anatomical/
       include_raw=False,        # also pull raw BIDS tree (sub-XX/)
       include_localizers=False, # also pull derivatives/localizers/
       include_retinotopy=False, # also pull derivatives/retinotopy/
       n_jobs=1,                 # parallel `aws s3 cp` workers
   )

Arguments
=========

* ``subject`` accepts the full BIDS form (``"sub-03"``) or just
  the bare value (``"03"``). The special value ``"all"``
  iterates the five subjects of the main experiment. ``sub-04``
  and ``sub-08`` have precision-mapping data only. Asking
  :func:`download` for them raises an error pointing to
  :func:`download_mapping`.
* All other entity filters accept a single string or a list. A
  bare value (``ses="04"``) and the full BIDS token
  (``ses="ses-04"``) are equivalent.
* ``include_stimuli=True`` additionally fetches the stimulus
  stimuli after the fMRI download. Stimuli are dataset-wide (a
  single HDF5 covering all subjects), so this just calls
  :func:`download_stimuli` after the per-subject fetch. See
  :doc:`access`.
* ``include_embeddings`` additionally fetches the dataset-wide
  stimulus embeddings after the fMRI download. Pass ``True``
  for every shipped model, or a model label / list of labels
  to narrow (e.g. ``include_embeddings="clip"``). Defaults to
  ``False`` (skip embeddings). Calls
  :func:`download_embeddings` under the hood.
* ``include_freesurfer=True`` pulls the per-subject FreeSurfer
  recon under ``derivatives/freesurfer/{subject}/`` (a few
  hundred MB per subject). Required by ``Subject.to_template``;
  see :doc:`template_space`.
* ``include_anatomical=True`` pulls the per-subject anatomical
  derivatives under ``derivatives/anatomical/{subject}/
  ses-PrismaAnat/anat/`` (T1w, T2w, brain mask and tissue masks
  at three resolutions). Unlocks
  ``Subject.get_t1w`` / ``get_t2w`` /
  ``get_anatomical_brain_mask`` / ``get_anatomical_tissue_mask`` /
  ``get_tissue_mask`` and the ``source="anatomical"`` brain mask on
  the voxel-axis accessors; see :doc:`load`.
* ``include_raw=True`` pulls the raw BIDS tree under
  ``sub-XX/`` (multi-echo BOLD, sbref, per-run
  ``events.tsv``, fieldmaps, raw MEGRE). Combine with
  ``ses`` / ``run`` / ``echo`` / ``part`` / ``suffix`` /
  ``extension`` filters to narrow the fetch. Use
  :func:`download_raw` when you want the raw tree without
  the default derivative walk.
* ``include_localizers=True`` pulls the per-subject localizer
  derivatives under ``derivatives/localizers/{subject}/``: the
  contrast z-maps and per-run effect-size maps of the category,
  object and motion localizers, and each session's
  ``desc-fitted_mask``.
  They are pulled in full; the BIDS filters do not apply. Address
  single maps with the helpers in :mod:`laion_fmri.derivatives`;
  see :doc:`../localizers`.
* ``include_retinotopy=True`` pulls the per-subject pRF parameter maps
  under ``derivatives/retinotopy/{subject}/`` (surface and volumetric
  maps for every paradigm and model stage), in full; the BIDS filters
  do not apply. Address single maps with the helpers in
  :mod:`laion_fmri.derivatives`; see :doc:`../retinotopy`.

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
whenever ``ses`` filters to specific sessions, since the
loader needs it to derive the brain mask. The strict ``ses``
filter therefore doesn't drop it.

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

``n_jobs`` does not affect the stimuli; the stimuli are a
single HDF5 streamed sequentially.

Raw BIDS downloads
==================

The raw BIDS tree under ``sub-XX/`` holds the multi-echo BOLD
timeseries, single-band references, per-run ``events.tsv``,
fieldmaps, and the raw MEGRE anatomical. Reach it two ways:

* :func:`download` with ``include_raw=True`` -- fetches raw on
  top of the default derivative walk.
* :func:`download_raw` -- fetches raw only, no derivatives.

Both fetch the main experiment's numbered sessions and
``ses-PrismaAnat``. The
raw precision-mapping sessions (``ses-Foveal``, ``ses-Corners1``,
…), which sit beside them under ``sub-XX/``, are left out. They
come with ``download_mapping(include_raw=True)``.

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

Precision-mapping dataset
=========================

.. code-block:: python

   from laion_fmri.download import download_mapping

   download_mapping(
       subject,                  # required; "all" = all seven subjects
       ses=None,                 # str | list, e.g. "Foveal"
       task=None,                # str | list, e.g. "floc"
       space=None,               # str | list, e.g. "fsnative"
       include_anatomical=False, # also pull derivatives/anatomical/
       include_freesurfer=False, # also pull derivatives/freesurfer/
       include_preproc=False,    # also pull derivatives/preproc-mapping/
       include_raw=False,        # also pull the raw mapping sessions
       n_jobs=1,
   )

Every call fetches each subject's pRF maps
(``derivatives/retinotopy/``), localizer maps
(``derivatives/localizers/``) and ROIs (``derivatives/rois/``). Once
per call, it also fetches the dataset-wide files of those trees
(e.g. ``dataset_description.json``) and the retinotopy aperture
libraries under ``stimuli/retinotopy/``.

* ``subject="all"`` iterates every subject of the precision-mapping
  dataset: the five of the main experiment plus ``sub-04`` and
  ``sub-08``.
* ``ses`` filters only the files that belong to a session: localizer
  maps, preprocessed data and raw. The pRF maps, ROIs and anatomy
  carry no session, so ``ses`` never filters them out. ``task`` and
  ``space`` apply wherever a file carries the entity.
* ``include_preproc=True`` adds the preprocessed BOLD, the design
  matrices and the frame tables the pRF maps were fitted on.
* ``include_raw=True`` adds the raw precision-mapping sessions and
  ``ses-PrismaAnat``. The main experiment's numbered sessions are not included;
  :func:`download_raw` fetches those.

.. code-block:: python

   download_mapping(subject="all")                     # maps, ROIs, apertures
   download_mapping(subject="sub-04", space="fsnative")
   download_mapping(subject="sub-03", ses="Foveal",
                    include_preproc=True)              # one session's inputs

Stimulus-side downloads
=======================

Everything attached to the stimulus images (the JPEGs themselves,
the pretrained embeddings, the object-segmentation masks, and the
captions) is dataset-wide (one set of files for all subjects), so
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
     - One HDF5 per pretrained model: CLIP, DINOv2, PEcore,
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

All four are independent; you only need ``download_stimuli`` first
if you want to load the images themselves. The public auxiliaries
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
transfer only fetches what's missing. While files transfer, a
progress line on stderr counts the files and bytes of each tree.

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
   laion-fmri download-mapping --subject all
   laion-fmri download-mapping --subject sub-04 --include-preproc
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

====
Load
====

.. code-block:: python

   from laion_fmri.subject import load_subject

   sub = load_subject("sub-03")

A ``Subject`` reads one file per accessor. **Every accessor
maps to exactly one file on disk**, returned as raw arrays;
combining sessions, averaging, or rebinning is the caller's
responsibility.

The "brain mask" is **derived on the fly** from the
subject-level mean-R^2 map
(``..._stat-rsquare_desc-R2mean_statmap.nii.gz``): voxels with
any non-zero GLMsingle fit are considered "in brain". The
bucket does not ship a separate brain-mask file. This is
consistent across sessions for a given subject, so betas
stacked along the trial axis stay aligned on the voxel axis.

Core accessors
==============

.. code-block:: python

   sub.get_sessions()                          # ['ses-01', ...]
   sub.get_brain_mask()                        # bool, (n_total_voxels,)
   sub.get_n_voxels()                          # number of brain-mask voxels

   sub.get_betas(session="ses-01")             # float32, (n_trials, n_voxels)
   sub.get_betas(session=["ses-01", "ses-02"]) # dict[ses, ndarray]

   sub.get_noise_ceiling(session="ses-01")     # float32, (n_voxels,)
   sub.get_noise_ceiling(desc="Noiseceiling12rep")  # subject-level variant

   sub.get_trial_info(session="ses-01")        # pandas DataFrame

Filters on ``get_betas``
========================

* ``roi="..."`` or list -- ROI mask(s); see "ROI queries"
  below for the full grammar.
* ``mask=ndarray[bool]`` -- custom voxel mask.
* ``nc_threshold=0.2`` -- keep voxels whose per-session noise
  ceiling exceeds the threshold.
* ``stimuli="shared"`` / ``"unique"`` -- restrict to trials
  whose stimulus is in the shared/unique subset.
* ``streaming=False`` (default) materializes the full 4-D
  NIfTI in RAM and then masks it. One-shot decompression of
  the ``.nii.gz``, fastest when memory is plentiful, but peak
  RAM is the full file plus the masked output -- roughly
  12 GB for a real session.
* ``streaming=True`` reads the file volume-by-volume and
  applies the combined brain + ROI + NC mask inline. Peak
  RAM stays at one volume (~10-50 MB) plus the masked output.
  Use this on memory-constrained machines like Colab. Works
  on both ``.nii`` and ``.nii.gz``; the compressed path uses
  a custom gzip pipeline that streams without re-decompressing
  on each slice.

ROI queries
===========

ROI inputs accept three forms (or a list mixing them):

* ``"FFA1"``  -- a specific ROI name.
* ``"face"``  -- every ROI in that category (the bucket groups
  ROIs into ``body``, ``character``, ``face``, ``laion``,
  ``motion``, ``object``, ``place``, ``retinotopy``).
* ``"all"``   -- every ROI for the subject.

Categories and ROI names are disjoint, so a single string
disambiguates by lookup. Pass a list to combine several at
once -- overlapping voxels appear only once in the result.

.. code-block:: python

   sub.get_available_rois()                 # flat list of every ROI
   sub.get_available_categories()           # 8 categories
   sub.get_available_rois(category="face")  # face-area ROIs only

   sub.get_roi_mask("FFA1")        # 1-D bool mask
   sub.get_roi_mask("face")        # union of all face ROIs
   sub.get_roi_mask("all")         # union of every ROI on disk
   sub.get_roi_masks(["FFA1", "face"])  # dict keyed by your inputs

ROI queries on ``get_betas`` follow the same grammar:

.. code-block:: python

   sub.get_betas(session="ses-01", roi="FFA1")
   sub.get_betas(session="ses-01", roi="face")
   sub.get_betas(session="ses-01", roi=["face", "place"])

Note that ``get_roi_mask`` / ``get_betas(roi=...)`` are
**volume-only**: they operate on the ``space-T1w_res-1pt8``
NIfTI mask. Surface variants are loaded via ``get_roi_data``.

Multi-format ROI loading
========================

Each ROI ships in three file types: a volumetric ``.nii.gz``
mask, per-hemisphere ``.func.gii`` surface masks, and
per-hemisphere FreeSurfer ``.label`` files. ``get_roi_data``
returns a nested dict keyed by ROI; format and hemi axes
prune the tree:

.. code-block:: python

   sub.get_roi_data("FFA1")  # full nested dict (default = all)
   # {
   #   "FFA1": {
   #     "volume": <1-D bool ndarray>,
   #     "gii": {
   #       "hemi-L": {"func.gii": <bool>, "label": <int idx>},
   #       "hemi-R": {...},
   #     },
   #   },
   # }

   sub.get_roi_data("FFA1", format="volume")          # vol only
   sub.get_roi_data("FFA1", format="gii", hemi="L")   # left surface
   sub.get_roi_data("FFA1", format="func.gii")        # surface masks only
   sub.get_roi_data("face", format="volume")          # one entry per face ROI

``format`` accepts ``"all"``, ``"volume"`` / ``"nii.gz"``
(synonyms), ``"gii"`` (both surface types), ``"func.gii"``,
or ``"label"``. ``hemi`` accepts ``"L"``, ``"R"``, or
``"all"`` (default).

Multi-session results
=====================

Pass a list to any session-keyed accessor and you get a
``dict`` keyed by session ID, never a stacked array. Trial
counts can differ per session, so a regular ndarray would be
unsafe -- you stack yourself only when you know shapes match.

Multi-subject access
====================

.. code-block:: python

   from laion_fmri.group import load_subjects

   group = load_subjects(["sub-03", "sub-05"])
   group.get_shared_betas(session="ses-01")    # dict[sub, ndarray]
   for sub_id, sub in group:
       ...

Brain-space mapping
===================

.. code-block:: python

   sub.to_nifti(per_voxel_array, "/tmp/out.nii.gz")
   sub.get_voxel_coordinates()                 # (n_voxels, 3)

PyTorch integration
===================

.. code-block:: python

   ds = sub.to_torch_dataset(session="ses-01", roi="visual")
   item = ds[0]                                # dict with betas, image, ...

Memory & shape considerations
=============================

Every accessor returns a fresh ndarray; nothing is cached.
**You control how much data you pull into RAM.** A few rules
of thumb:

* **One whole-brain session of betas** is ``n_trials × n_voxels``
  ``float32``. With ~1000 trials and ~270k brain-mask voxels,
  that's roughly 1 GB per call. Doable for one session on a
  laptop; multiplying by 30+ sessions per subject quickly
  reaches many tens of GB. Always pass an ``roi=`` filter when
  you can -- it cuts memory by 1-2 orders of magnitude.
* **ROI filters cut memory dramatically.** ``roi="visual"``
  typically reduces voxel count by an order of magnitude;
  combining with ``nc_threshold`` reduces it further.
* **Avoid loading whole sessions if you only need a slice.**
  Build a ``mask=`` array yourself, or chain ``roi`` +
  ``nc_threshold``, before calling ``get_betas``.
* **Multi-session results are dicts, not stacked arrays.**
  Trial counts vary per session, so passing a list to
  ``get_betas`` returns a ``dict[ses, ndarray]``. All sessions
  share the same brain mask within a subject, so the voxel
  axis matches and ``np.concatenate(list(out.values()),
  axis=0)`` is the right stack -- you just have to align
  trial-level metadata yourself when you do.

PyTorch users: ``to_torch_dataset(...)`` exposes the same
accessors lazily per ``__getitem__`` call, so total RAM stays
proportional to batch size rather than the dataset.

Per-trial stimulus access
=========================

For most analyses you don't want to talk to the stimulus set directly
-- you want, *for the trials this subject saw*, the images,
embeddings, captions, or segmentation masks aligned to the betas. The
``Subject`` exposes those four modalities as namespaces, each keyed by
**global trial index** (a row of :attr:`Subject.metadata`):

.. code-block:: python

   sub = load_subject("sub-03")

   sub.metadata                                # ── the trial table ──
   # One row per single-trial beta, concatenated across sessions.
   # Columns: session, session_trial, image_name, stim_idx,
   #          unique_or_shared, dataset, (+ events.tsv extras).
   # The row index is the "trial index" used everywhere below.

   sub.images.get(42)                          # PIL.Image for trial 42
   sub.images[42]                              # raw JPEG bytes
   sub.images.array(session="ses-01")          # (n, 1000, 1000, 3) uint8 stack
   sub.images.all()                            # iterator, length n_trials

   sub.embeddings.models                       # ['CLIP', 'DINOv2', ...]
   sub.embeddings.get("CLIP", 42)              # (D,) features for trial 42
   sub.embeddings.all("CLIP")                  # (n_trials, D) — ready to regress
   sub.embeddings.all("CLIP", session="ses-01")

   sub.segmentations.nouns(42)                 # ['hand', 'piano', ...]
   sub.segmentations.has_image(42)             # False if unique-image trial
   sub.segmentations.get(42, "hand")           # (1000, 1000) uint8 mask

   sub.captions.list(42)                       # all captions for trial 42's image

The bulk methods (``.all(...)`` / ``.array(...)``) preserve trial order,
so the rows of ``sub.embeddings.all("CLIP")`` line up one-to-one with
the rows of ``sub.get_betas(session=None)`` concatenated across
sessions. That's the regression workflow in one expression.

Single concrete example — fit CLIP features to betas:

.. code-block:: python

   import numpy as np

   sub = load_subject("sub-03")

   # Per-session z-score, then concatenate, for fair scale:
   beta_chunks = []
   for ses in sub.get_sessions():
       b = sub.get_betas(session=ses, roi="visual")
       beta_chunks.append((b - b.mean(0)) / b.std(0))
   y = np.concatenate(beta_chunks, axis=0)   # (n_trials, n_voxels)

   # Trial-aligned CLIP features (same row order as y):
   X = sub.embeddings.all("CLIP")             # (n_trials, 1024)

   # Standard regression from here...

Another typical pattern — pull masks only for shared-image trials,
since masks ship only for the shared set:

.. code-block:: python

   trials = sub.metadata
   shared_trials = trials.index[trials["unique_or_shared"] == "shared"]

   for trial in shared_trials:
       nouns = sub.segmentations.nouns(trial)
       if "face" in nouns:
           face_mask = sub.segmentations.get(trial, "face")
           ...                                # do something with this trial

The ``sub.segmentations`` API is **safe to call on every trial**:
``has_image(trial)`` returns ``False`` and ``nouns(trial)`` returns
``[]`` for unique-image trials, so loops across the full trial table
need no special-casing.

PyTorch users get the same per-trial access lazily via
:meth:`~laion_fmri.subject.Subject.to_torch_dataset`.

Stimuli: images, embeddings, segmentations (dataset-wide)
=========================================================

The same modalities are also reachable through a dataset-wide hub,
:func:`load_stimuli`, keyed by ``image_name`` rather than trial index.
Use this when you want the full stimulus set independent of any
subject's trial ordering -- e.g. computing similarity matrices on all
1,492 shared images, or pulling embeddings for arbitrary names.

.. code-block:: python

   import laion_fmri

   stim = laion_fmri.load_stimuli()
   stim.metadata.head()                       # pandas DataFrame, 25052 rows

   # ── Stimulus images ─────────────────────────────────────────
   img = stim.images.get("shared_12rep_LAION_cluster_1003_i0.jpg")  # PIL
   jpeg = stim.images["shared_12rep_LAION_cluster_1003_i0.jpg"]      # raw bytes
   stim.images.names()[:3]
   for name, raw in stim.images:
       ...

   # ── Embeddings (CLIP, DINOv2, PEcore, SigLIP2) ──────────────
   stim.embeddings.models                     # ['CLIP', 'DINOv2', 'PEcore', 'SigLIP2']
   stim.embeddings["CLIP"].shape              # (25052, 1024) float16
   stim.embeddings.get(
       "CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                          # (1024,) vector

   # ── Object-segmentation masks (shared images only) ──────────
   stim.segmentations.nouns(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                          # ['fingers', 'hand', ...]
   stim.segmentations.get(
       "shared_12rep_LAION_cluster_1003_i0.jpg", "fingers",
   )                                          # (1000, 1000) uint8

   # ── Captions (human for all images; AI for shared non-OOD) ────────
   stim.captions.human(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                          # list[str], length 5 for shared
   stim.captions.ai(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                          # str or None
   stim.captions.get(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                          # pandas DataFrame

Files are opened lazily: touching ``stim.embeddings`` does not open
the embedding HDF5 until you actually look up a vector. The
modality-specific HDF5 files are independent downloads:

.. code-block:: python

   # Stimulus images (gated; Data Use Agreement on first call):
   laion_fmri.download_stimuli()

   # Embeddings (public, CC0):
   laion_fmri.download_embeddings()
   laion_fmri.download_embeddings(models=["CLIP", "DINOv2"])

   # Object segmentations (public, CC0, ~68 MB):
   laion_fmri.download_segmentations()

   # Captions (public, CC0):
   laion_fmri.download_captions()

CLI equivalents: ``laion-fmri download-stimuli``,
``laion-fmri download-embeddings``, ``laion-fmri download-segmentations``,
``laion-fmri download-captions``.

.. note::

   Segmentations cover the **shared** stimulus set only (1,492 images
   viewed by every subject); subject-unique images carry no masks.
   The listing methods (``nouns``, ``for_image``, ``has_image``)
   return empty results -- not errors -- for uncovered images, so
   loops across all trials need no special-casing.

   Captions cover every stimulus image with human captions: shared
   images have five and unique images have three. AI captions are
   provided for shared non-OOD images only, so
   ``stim.captions.ai(name)`` and ``sub.captions.ai(trial)`` return
   ``None`` for unique-image and OOD trials.

See :doc:`/stimulus_data` for the per-model embedding details
(feature dimensions, normalisation, exact model identifiers) and a
deeper tour of the segmentation file layout.

Common workflow: per-session z-scoring + train/test split
=========================================================

A frequent recipe is to load every session for one subject,
z-score betas within each session, then split shared vs. unique
stimuli into test vs. train. This composes from the existing
accessors:

.. code-block:: python

   import numpy as np
   from laion_fmri.subject import load_subject

   sub = load_subject("sub-03")

   train_chunks, test_chunks = [], []
   for ses in sub.get_sessions():
       betas = sub.get_betas(session=ses)             # (n_trials, n_voxels)
       z = (betas - betas.mean(0)) / betas.std(0)     # within-session z-score

       trials = sub.get_trial_info(session=ses)
       is_shared = trials["label"].str.startswith("shared_").to_numpy()

       train_chunks.append(z[~is_shared])
       test_chunks.append(z[is_shared])

   X_train = np.concatenate(train_chunks, axis=0)
   X_test = np.concatenate(test_chunks, axis=0)

The ``stimuli="shared"`` / ``"unique"`` filter on
``get_betas`` does the same trial selection in one call if you
prefer it without the manual ``label`` parse:

.. code-block:: python

   train = sub.get_betas(session=ses, stimuli="unique")
   test = sub.get_betas(session=ses, stimuli="shared")

For ROI-restricted variants, add ``roi="visual"`` (or any
``mask=`` / ``nc_threshold=`` filter) to the same calls --
voxel selection composes naturally and applies before the
z-score.

Bundled train / test splits (re:vision Method 1 / 2 / 3)
========================================================

The :mod:`laion_fmri.splits` subpackage layers on top of the
accessors above without changing them.
:meth:`~laion_fmri.subject.Subject.get_betas` and
:meth:`~laion_fmri.subject.Subject.get_trial_info` stay
one-file-per-call; splits are pure label matches against the
``label`` column of the trial table:

.. code-block:: python

   import numpy as np
   import pandas as pd
   from laion_fmri.splits import get_split_masks

   sessions = sub.get_sessions()
   betas = np.concatenate(list(
       sub.get_betas(session=sessions, roi="visual").values()
   ), axis=0)
   trials = pd.concat(list(
       sub.get_trial_info(session=sessions).values()
   ), ignore_index=True)

   train, test = get_split_masks(trials, "tau", pool="shared")
   X_train, X_test = betas[train], betas[test]

See :doc:`/train_test_splits` for the full split catalogue
(``random_*``, ``cluster_k5_*``, ``tau``, ``ood``) and per-method
worked examples.

Errors you may encounter
========================

The package raises a small, named exception hierarchy from
:mod:`laion_fmri._errors`:

``DataDirNotSetError``
   Raised by ``load_subject`` (and any accessor) when no data
   directory has been configured. Run
   ``laion_fmri.config.dataset_initialize(...)`` first.

``DataNotDownloadedError`` (subclass of ``FileNotFoundError``)
   Raised when a subject's directory exists but the requested
   file is missing on disk. Re-run ``download(...)`` with the
   right ``ses``/``desc``/``stat`` filters.

``StimuliNotDownloadedError`` (subclass of ``FileNotFoundError``)
   Raised by stimulus-side accessors (``Subject.metadata``,
   ``Subject.images``/``embeddings``/``segmentations``,
   ``Subject.to_torch_dataset``, ``load_stimuli``) when the stimuli
   directory has not been mirrored yet. Re-run ``download(...,
   include_stimuli=True)``.

``SubjectNotFoundError`` (subclass of ``ValueError``)
   Raised by ``resolve_subject_id`` for malformed IDs (empty,
   bare ``"sub-"``, non-string).

``LicenseNotAcceptedError`` (subclass of ``RuntimeError``)
   Raised by ``download`` / ``accept_licenses`` when the
   dataset license is declined.

Plain ``ValueError`` covers narrower mistakes -- for example,
asking ``get_betas`` for both ``roi`` and ``mask`` at once,
passing an unknown ROI name, or specifying neither ``session``
nor ``desc`` to ``get_noise_ceiling``.

See :doc:`/auto_examples/plot_04_loading` for a full tour.

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
That keeps the loader predictable, but means **you control
how much you pull into RAM**. A few rules of thumb:

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

Stimulus images
===============

Stimulus images live in a single HDF5 file that covers the whole dataset (one
file for all subjects, indexed by ``image_name``). The package's loader
function mirrors :func:`load_subject`:

.. code-block:: python

   import laion_fmri

   stim = laion_fmri.load_stimuli()           # mirrors load_subject(...)
   stim.metadata.head()                        # pandas DataFrame
   len(stim)                                   # 25052

   # Two equivalent lookups: by integer index or by image_name
   jpeg_bytes = stim[0]
   jpeg_bytes = stim["shared_12rep_LAION_cluster_1003_i0.jpg"]

   # Decoded PIL.Image (requires Pillow)
   img = stim.image(0)

   # Iterate (name, bytes) in metadata order
   for name, jpeg in stim:
       ...

The HDF5 + metadata CSV are downloaded via the gated access service —
run :func:`laion_fmri.download_stimuli` (or
``laion-fmri download-stimuli``) first. See :doc:`access` for
the full flow.

The metadata CSV columns are ``image_name``, ``dataset``,
``participant``, ``unique_or_shared``, ``n_reps``; row order matches the
HDF5 index.

.. note::

   :class:`Subject` has older stimulus methods (``get_images``,
   ``get_image``, ``get_stimulus_metadata``) that expect a per-PNG layout
   (``stimuli/images/*.png`` + ``stimuli/stimuli.tsv``). For the
   access-service HDF5 schema, prefer ``load_stimuli()`` above.

Stimulus embeddings
===================

Four pretrained image embeddings — OpenCLIP H/14, DINOv2 L/14, PE Core
L/14 336, and SigLIP2 SO400M Patch14 384 — are shipped as one HDF5 file
per model, sitting next to the stimulus images. The loader follows the
same ``load_X(...)`` shape:

.. code-block:: python

   import laion_fmri

   # Single model (only that file is opened)
   emb = laion_fmri.load_embeddings("CLIP")
   emb["CLIP"].shape                # (25052, 1024)
   emb.image_ids[:3]                # array of image filenames
   emb.get("CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg")  # (1024,)

   # All four models (handles opened lazily on first access)
   all_emb = laion_fmri.load_embeddings()           # == "all"
   all_emb["SigLIP2"].shape                          # (25052, 1152)

   # Subject-ordered slice (joined against the stimulus metadata)
   sub01_clip = emb.for_subject("sub-01", "CLIP")

Unlike the stimulus images, the embedding files are **public on the
S3 bucket** (CC0, no Data Use Agreement). Pull them with
:func:`laion_fmri.download_embeddings` (or
``laion-fmri download-embeddings``):

.. code-block:: python

   laion_fmri.download_embeddings()                    # all four
   laion_fmri.download_embeddings(models="CLIP")       # one
   laion_fmri.download_embeddings(models=["CLIP", "DINOv2"])

You can also chain it onto a regular subject download with
``download(..., include_embeddings=True)`` (or pass a list to narrow
the models). See :doc:`/stimulus_data` for the full per-model details
(feature dimensions, normalisation, exact model identifiers).

Common workflow: per-session z-scoring + train/test split
=========================================================

A frequent recipe -- load every session for one subject,
z-score betas within each session, then split shared vs.
unique stimuli into test vs. train -- composes from the
existing accessors:

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
   Raised by ``get_images`` / ``get_image`` /
   ``get_stimulus_metadata`` when the stimuli directory has
   not been mirrored yet. Re-run ``download(...,
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

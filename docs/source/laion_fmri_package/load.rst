====
Load
====

.. code-block:: python

   from laion_fmri.subject import load_subject

   sub = load_subject("sub-03")

A ``Subject`` reads one file per accessor. **Every accessor
maps to exactly one file on disk** -- no averaging, no
concatenation, no rebinning. Those operations are left to the
caller, on the returned arrays.

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

* ``roi="..."`` or list -- ROI mask(s) (union when list).
* ``mask=ndarray[bool]`` -- custom voxel mask.
* ``nc_threshold=0.2`` -- keep voxels whose per-session noise
  ceiling exceeds the threshold.
* ``stimuli="shared"`` / ``"unique"`` -- restrict to trials
  whose stimulus is in the shared/unique subset.

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
  ``float32``. With ~750 trials and ~100k brain-mask voxels,
  that's roughly 300 MB per call. Comfortable for one session
  on a laptop; multiplying by 30+ sessions per subject quickly
  reaches many GB.
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

Bundled train / test splits (re:vision Method 1 + Method 2)
===========================================================

The :mod:`laion_fmri.splits` subpackage layers on top of the
accessors above without changing them. ``get_betas`` and
``get_trial_info`` stay one-file-per-call; splits are pure
label matches against the ``trial_info["label"]`` column:

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

See :doc:`/train_test_splits` for the full split catalogue and
the five-fold cluster-holdout (Method 2) loop.

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

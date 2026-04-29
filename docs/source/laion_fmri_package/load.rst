====
Load
====

.. code-block:: python

   from laion_fmri.subject import load_subject

   sub = load_subject("sub-03")

A ``Subject`` is a thin file-loader. **Every accessor maps to
exactly one file** -- no averaging, no concatenation, no
rebinning. If you want those operations, you do them yourself
on the returned arrays.

Core accessors
==============

.. code-block:: python

   sub.get_sessions()                          # ['ses-01', ...]
   sub.get_brain_mask()                        # bool, (n_total_voxels,)
   sub.get_n_voxels()                          # number of brain-mask voxels

   sub.get_betas(session="ses-01")             # float32, (n_trials, n_voxels)
   sub.get_betas(session=["ses-01", "ses-02"]) # dict[ses, ndarray]

   sub.get_noise_ceiling(session="ses-01")     # float32, (n_voxels,)
   sub.get_noise_ceiling(desc="noiseceiling33ses")  # subject-level variant

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

See :doc:`/auto_examples/plot_04_loading` for a full tour.

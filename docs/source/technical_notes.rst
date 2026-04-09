===============
Technical Notes
===============

Important implementation details, conventions, and known issues. Read this
page to avoid common mistakes when working with the LAION-fMRI data.

Coordinate Spaces & Conventions
===============================

.. note::

   Placeholder -- document the following once finalized:

   * Axis ordering convention (e.g., LPI vs RAS) for NIfTI files
   * Origin location and how it relates to MNI coordinates
   * How to transform between native, MNI, and surface spaces
   * Which space the GLMsingle betas are provided in by default

Beta Estimates
==============

.. note::

   Placeholder -- document:

   * Data type and scaling (e.g., int16 with a multiplier, or float32)
   * How to convert stored values to percent signal change (if applicable)
   * The relationship between beta versions (b1, b2, b3) and when to use each
   * How ridge regression in b3 betas biases values toward zero and what that
     means for connectivity analyses

Noise Ceilings
==============

.. note::

   Placeholder -- document:

   * How noise ceilings are computed (formula)
   * How to convert the provided values to percentage variance explained
   * The difference between split-half and repeat-based noise ceilings
   * How to compute a weighted average noise ceiling across voxels

Stimulus-to-Beta Mapping
=========================

.. note::

   Placeholder -- document:

   * Exact mapping between the 4th dimension of the beta volume and stimulus IDs
   * How repeated stimuli are handled (averaged? separate entries?)
   * Whether indexing is 0-based or 1-based
   * How to cross-reference with stimuli.tsv

File Sizes & Memory
====================

.. note::

   Placeholder -- document:

   * Approximate file sizes per subject for each data type
   * Memory requirements for loading full beta volumes
   * Tips for working with data that doesn't fit in RAM (chunked loading,
     memory mapping, ROI extraction before full load)


Common Pitfalls
===============

A list of things that can trip you up. We'll expand this as we learn what
users run into.

.. warning::

   **All items below are placeholders** -- they will be filled in with
   specific, actionable warnings as the dataset is finalized and users begin
   working with the data.

Beta indexing
-------------

(Placeholder) Make sure you are using the correct mapping between beta indices
and stimulus IDs. Off-by-one errors here silently produce garbage results.

NaN values in betas
--------------------

(Placeholder) Some voxels may contain NaN values (e.g., outside the brain mask
or where the GLM did not converge). These propagate silently through numpy
operations like ``np.mean``. Always check for and handle NaNs before analysis.

Noise ceiling misinterpretation
-------------------------------

(Placeholder) The noise ceiling is an upper bound, not a target. A model
explaining 50% of the noise ceiling is not "only 50% accurate" -- it may be
near-optimal given the noise in the data.

Wrong coordinate space
-----------------------

(Placeholder) Mixing data from different spaces (e.g., applying an MNI ROI mask
to native-space betas) produces silently wrong results. Always verify that your
data and masks are in the same space.

Beta version confusion
-----------------------

(Placeholder) The b1, b2, and b3 betas are not interchangeable. Using b1 when
you should use b3 (or vice versa) can substantially affect your results. See
:doc:`glmsingle_betas` for guidance.

Smoothing already-denoised betas
---------------------------------

(Placeholder) The GLMsingle b3 betas have already been denoised via ridge
regression. Applying spatial smoothing on top of this may degrade rather than
improve your results.

Train/test data leakage
------------------------

(Placeholder) If you are using the predefined train/test splits, make sure your
model selection and hyperparameter tuning only use the training set. Repeated
stimuli that appear in both sets (if any) need special handling.

Large file memory issues
-------------------------

(Placeholder) Loading full beta volumes into memory can require significant RAM.
Consider using ``nibabel``'s memory-mapped loading (``nib.load(...).dataobj``)
or extracting ROIs before loading the full volume.

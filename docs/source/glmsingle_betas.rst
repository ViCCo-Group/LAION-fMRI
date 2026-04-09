========================
GLMsingle Beta Estimates
========================

.. todo::

   Introductory narrative (2-3 sentences): What are single-trial betas, why
   does LAION-fMRI provide them, and why should most users start here?
   Mention that this is likely the primary data product for encoding/decoding
   and RSA analyses.

.. todo::

   Add a figure showing example beta maps for a few stimuli (e.g., 3-4
   example images with their corresponding brain activation maps side by
   side).

.. figure:: _static/placeholder_betas_examples.png
   :align: center
   :width: 80%
   :alt: Example single-trial beta maps

   Example single-trial beta maps for selected stimuli. *(placeholder —
   replace with actual figure)*

Overview
========

.. todo::

   Brief description of GLMsingle and what it does (1 paragraph). Cover:

   - What the method estimates (one beta per trial per voxel)
   - Key improvements over a standard GLM (HRF fitting, GLMdenoise, ridge)
   - Reference: Prince et al., 2022
   - Link to GLMsingle GitHub repo

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Method
     - (placeholder)
   * - GLMsingle version
     - (placeholder)
   * - Input data
     - (placeholder — preprocessed BOLD? which space? link to :doc:`preprocessing`)
   * - Output shape
     - (placeholder — e.g. ``(X, Y, Z, N_stimuli)`` per subject)
   * - Available spaces
     - (placeholder)
   * - Beta versions provided
     - (placeholder — which of GLMsingle's output types are shipped?)
   * - Noise ceilings
     - (placeholder — included? per-voxel?)

File Organization
=================

.. todo::

   Paste the actual file tree from a representative subject. Include all
   files shipped (betas, R2 maps, noise ceilings, HRF estimates, etc.).

.. code-block:: text

    derivatives/glmsingle/
    └── sub-XX/
        └── ... (placeholder — fill with actual file listing)

Beta Versions
=============

.. todo::

   Which beta versions are provided? For each version, document:

   - Name / label
   - What processing was applied
   - When a user should choose this version over others
   - Any caveats (e.g., ridge regression bias toward zero)

   Use a table like the one below.

.. list-table::
   :widths: 15 30 55
   :header-rows: 1

   * - Version
     - Name
     - Description
   * - (placeholder)
     - (placeholder)
     - (placeholder)

Noise Ceilings
===============

.. todo::

   Document:

   - Are noise ceilings provided? Per-voxel, per-ROI, or both?
   - How are they computed (split-half, etc.)?
   - What do the values represent (raw correlation, percent variance, etc.)?
   - How should users interpret / use them?
   - Add a figure showing a noise ceiling map on an example subject.

.. figure:: _static/placeholder_noise_ceilings.png
   :align: center
   :width: 70%
   :alt: Noise ceiling map

   Noise ceiling map for an example subject. *(placeholder — replace with
   actual figure)*

Relation to Stimuli
===================

.. todo::

   This is critical — document precisely:

   - How beta indices map to stimulus IDs (is beta index 0 = first row of
     stimuli.tsv? or is there a separate mapping file?)
   - Are repeated stimuli averaged into a single beta, or kept as separate
     betas?
   - Cross-reference :doc:`stimulus_data` for stimulus metadata and
     :doc:`train_test_splits` for train/test partitioning

Loading the Data
================

.. todo::

   Provide a minimal, correct code example for:

   1. Loading betas for one subject
   2. Checking the shape
   3. Mapping beta indices to stimulus IDs

   Only add code once the file paths and mapping are finalized.

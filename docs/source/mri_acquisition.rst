===============
MRI Acquisition
===============

This page documents the MRI acquisition parameters for all LAION-fMRI scans.
For the experimental design and task descriptions, see :doc:`experimental_design`.

Scanner
=======

.. todo::

   Brief narrative: where data were collected, any relevant site details.

.. todo::

   Fill in scanner details.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Manufacturer
     - (placeholder)
   * - Model
     - (placeholder)
   * - Field strength
     - (placeholder)
   * - Head coil
     - (placeholder)
   * - Site
     - (placeholder)

Functional MRI
==============

.. todo::

   Narrative (2-3 sentences): What sequence was used and why? What tradeoffs
   drove the choice of resolution, TR, and multiband factor? Anything unusual
   about the protocol that users should know? Were dummy volumes acquired and
   discarded?

.. todo::

   Fill in all parameter values below.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Sequence
     - (placeholder)
   * - TR
     - (placeholder)
   * - TE
     - (placeholder)
   * - Flip angle
     - (placeholder)
   * - Voxel size
     - (placeholder)
   * - Matrix size
     - (placeholder)
   * - Number of slices
     - (placeholder)
   * - Slice orientation
     - (placeholder)
   * - Phase encoding direction
     - (placeholder)
   * - Multiband factor
     - (placeholder)
   * - GRAPPA
     - (placeholder)
   * - Partial Fourier
     - (placeholder)
   * - Fat suppression
     - (placeholder)
   * - Volumes per run
     - (placeholder)
   * - Dummy volumes discarded
     - (placeholder)

Structural MRI
==============

.. todo::

   Narrative (1-2 sentences): How many T1w scans per subject? Were they
   averaged? Any specific protocol considerations?

T1-weighted
-----------

.. todo::

   Fill in all parameter values below.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Sequence
     - (placeholder)
   * - TR
     - (placeholder)
   * - TE
     - (placeholder)
   * - TI
     - (placeholder)
   * - Flip angle
     - (placeholder)
   * - Voxel size
     - (placeholder)
   * - Matrix size
     - (placeholder)
   * - GRAPPA
     - (placeholder)

Fieldmaps
=========

.. todo::

   Narrative (1-2 sentences): What kind of fieldmaps were collected (spin-echo
   pair, magnitude/phase, none)? This matters for users who want to rerun
   preprocessing.

Retinotopy & Localizers
========================

.. todo::

   Were retinotopy and localizer scans acquired with the same functional
   sequence as above? If yes, just state that. If any parameters differed,
   note what changed and why.

Diffusion MRI
=============

.. todo::

   If DWI data are included: narrative + parameter table (b-values,
   directions, resolution). If not included, remove this section.

   See also :doc:`diffusion`.

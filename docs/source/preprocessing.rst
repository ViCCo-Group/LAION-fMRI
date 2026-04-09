==============
Preprocessing
==============

.. todo::

   Introductory narrative (2-3 sentences): Which pipeline was used and why?
   Emphasize that both raw and preprocessed data are provided so users can
   rerun their own pipeline if desired. Link to the dataset paper.

For raw data acquisition parameters, see :doc:`mri_acquisition`.

Preprocessing Steps
===================

.. todo::

   List the actual preprocessing steps applied, separately for anatomical
   and functional data. Note any non-default settings. Add a brief narrative
   on key decisions (e.g., why a particular SDC method, whether slice timing
   correction was applied, whether smoothing was applied or not).

Parameters
==========

.. todo::

   Fill in all parameter values below. Add or remove rows as needed to
   match the actual pipeline configuration.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Pipeline
     - (placeholder)
   * - Version
     - (placeholder)
   * - Template
     - (placeholder)
   * - Output spaces
     - (placeholder)
   * - Output resolution
     - (placeholder)
   * - Slice timing correction
     - (placeholder — applied or not?)
   * - SDC method
     - (placeholder)
   * - High-pass filter
     - (placeholder)
   * - Smoothing
     - (placeholder)

Output Files
============

See :doc:`fmri_data` for a full description of the preprocessed output files,
including confound regressors.

Quality Control
===============

For quality control details — MRIQC metrics, motion thresholds, exclusion
criteria, and known issues — see :doc:`quality_control`.

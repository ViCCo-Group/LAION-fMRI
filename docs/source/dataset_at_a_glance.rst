====================
Dataset at a Glance
====================

This page gives you a quick overview of everything in LAION-fMRI and helps you
find the files you need.

At a Glance
===========

.. grid:: 2 2 4 4
    :gutter: 2

    .. grid-item-card:: Participants
        :class-card: sd-border-0
        :shadow: sm

        5 deeply-sampled subjects

    .. grid-item-card:: Stimuli
        :class-card: sd-border-0
        :shadow: sm

        25,052 launch-release images; 1,492 shared

    .. grid-item-card:: Sessions
        :class-card: sd-border-0
        :shadow: sm

        165 acquired fMRI sessions; 150 main sessions in launch release

    .. grid-item-card:: Dataset Size
        :class-card: sd-border-0
        :shadow: sm

        Reported with the final release

.. include:: _includes/current_release_stats.inc

What's Included
===============

The dataset contains raw and preprocessed functional MRI data
(:doc:`fmri_data`, :doc:`preprocessing`), anatomical scans and
FreeSurfer reconstructions (:doc:`anatomical_data`), single-trial
GLMsingle beta estimates (:doc:`glmsingle_betas`), the stimulus set
(:doc:`stimulus_data`) and derived stimulus files
(:doc:`stimulus_derivatives`), ROI masks (:doc:`rois`) derived from
retinotopy (:doc:`retinotopy`) and functional localizers
(:doc:`localizers`), and predefined train/test splits
(:doc:`train_test_splits`).

.. only:: live

   *A full BIDS directory tree, the complete list of coordinate spaces,
   and a per-ROI-set summary table will be added with the final
   release.*

.. only:: dev

   Dataset Structure
   =================

   .. todo::

      Paste the actual top-level BIDS directory tree here. This should reflect
      the real file/folder names, task labels, and derivative directories.

   .. code-block:: text

       LAION-fMRI/
       └── ... (placeholder — fill with actual directory tree)

   Available Spaces
   ================

   .. todo::

      List all coordinate spaces the data is provided in, with resolutions.

   .. list-table::
      :widths: 25 50 25
      :header-rows: 1

      * - Space
        - Description
        - Resolution
      * - (placeholder)
        - (placeholder)
        - (placeholder)

   ROIs
   ====

   .. todo::

      Brief summary of available ROI sets. For full details, point to
      :doc:`rois`.

   .. list-table::
      :widths: 25 40 35
      :header-rows: 1

      * - ROI set
        - Description
        - How defined
      * - (placeholder)
        - (placeholder)
        - (placeholder)


What Files Do I Need?
=====================

Not everyone needs the full dataset. Start from your use case below to find the
relevant files and documentation pages.

Encoding / decoding models
--------------------------

This is the most common use case (e.g. Algonauts challenge participants).

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Single-trial beta estimates
     - ``derivatives/glmsingle-tedana/sub-XX/`` — see :doc:`glmsingle_betas`
   * - Stimulus images & metadata
     - ``stimuli/`` — see :doc:`stimulus_data`
   * - Stimulus derivatives
     - Embeddings, captions, and object segmentations — see
       :doc:`stimulus_derivatives`
   * - Train / test splits
     - Predefined splits for model evaluation — see :doc:`train_test_splits`
   * - ROI masks *(optional)*
     - ``derivatives/rois/`` — see :doc:`rois`

RSA / pattern similarity analyses
---------------------------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Single-trial betas
     - ``derivatives/glmsingle-tedana/sub-XX/`` — see :doc:`glmsingle_betas`
   * - Stimulus metadata & categories
     - ``stimuli/task-images_metadata.csv`` — see
       :doc:`stimulus_data`
   * - ROI masks
     - ``derivatives/rois/`` — see :doc:`rois`

Retinotopic or localizer analyses
---------------------------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Retinotopic maps
     - ``derivatives/retinotopy/`` — see :doc:`retinotopy`
   * - Functional localizer contrasts
     - ``derivatives/localizers/`` — see :doc:`localizers`
   * - ROI masks
     - ``derivatives/rois/`` — see :doc:`rois`

Preprocessing from scratch
--------------------------

If you want to run your own preprocessing pipeline instead of using the
fMRIPrep outputs we provide.

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Raw BOLD data
     - ``sub-XX/func/`` — see :doc:`fmri_data`
   * - T1w anatomical scans
     - ``sub-XX/anat/`` — see :doc:`anatomical_data`
   * - Event timing files
     - ``sub-XX/func/*_events.tsv`` — see :doc:`experimental_design`
   * - Diffusion data *(if needed)*
     - ``sub-XX/dwi/`` — see :doc:`diffusion`

.. tip::

   For details on the preprocessing we already ran, see :doc:`preprocessing`.
   For MRI acquisition parameters, see :doc:`mri_acquisition`.

Data Formats
============

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Data type
     - Format
     - Notes
   * - MRI volumes
     - NIfTI (.nii.gz)
     - 3D (anatomical) or 4D (functional/betas)
   * - Metadata
     - JSON (.json)
     - BIDS sidecar files
   * - Events / behavioral
     - TSV (.tsv)
     - Tab-separated, BIDS-compliant
   * - Stimulus images
     - HDF5 (.h5)
     - Single packed file with raw JPEG bytes, indexed by image name. Loaded
       via :func:`laion_fmri.load_stimuli`.
   * - Stimulus metadata
     - CSV
     - ``stimuli/task-images_metadata.csv`` — see
       :doc:`stimulus_data`

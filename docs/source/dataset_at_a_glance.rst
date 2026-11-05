====================
Dataset at a Glance
====================

This page gives you a quick overview of everything in LAION-fMRI and helps you
find the files you need.

LAION-fMRI combines two datasets: the **main experiment**, in which
participants viewed LAION images, and **precision mapping**, which maps
each participant's visual cortex with retinotopy and functional
localizers.

The main experiment covers **5 participants**, **150 image-viewing fMRI
sessions** (30 per participant), **25,052 distinct images**, and
**1,492 images shared by every participant**. In total, **165 fMRI
sessions** were acquired (33 per participant). The supplemental sessions
expand the shared image set to about **2,200 images** and will be released
later. Precision mapping covers **7 participants** with **6 sessions**
each: the five main-experiment participants and two who took part in
precision mapping only (see :ref:`subject-sets`).

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
(:doc:`train_test_splits`). For precision mapping, the preprocessed
timeseries, the per-run design matrices and the stimulus apertures are
released as well, so the pRF models can be refitted or replaced
(:ref:`retinotopy-stimulus-files`).

.. only:: live

   *Detailed BIDS file trees and per-ROI summaries will be added in an
   upcoming documentation update.*

.. only:: dev

   ROIs
   ====

   .. todo::

      Brief summary of available ROI categories. For full details, point to
      :doc:`rois`.

   .. list-table::
      :widths: 25 40 35
      :header-rows: 1

      * - ROI category
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
     - ``derivatives/glmsingle-tedana/sub-XX/`` - see :doc:`glmsingle_betas`
   * - Stimulus images & metadata
     - ``stimuli/`` - see :doc:`stimulus_data`
   * - Stimulus derivatives
     - Embeddings, captions, and object segmentations - see
       :doc:`stimulus_derivatives`
   * - Train / test splits
     - Predefined splits for model evaluation - see :doc:`train_test_splits`
   * - ROI masks *(optional)*
     - ``derivatives/rois/`` - see :doc:`rois`

RSA / pattern similarity analyses
---------------------------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Single-trial betas
     - ``derivatives/glmsingle-tedana/sub-XX/`` - see :doc:`glmsingle_betas`
   * - Stimulus metadata & categories
     - ``stimuli/task-images_metadata.csv`` - see
       :doc:`stimulus_data`
   * - ROI masks
     - ``derivatives/rois/`` - see :doc:`rois`

Retinotopic or localizer analyses
---------------------------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Retinotopic maps
     - ``derivatives/retinotopy/``, all seven participants - see
       :doc:`retinotopy`
   * - Functional localizer contrasts
     - ``derivatives/localizers/`` - see :doc:`localizers`
   * - ROI masks
     - ``derivatives/rois/`` - see :doc:`rois`

Fitting your own pRF models
---------------------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Preprocessed timeseries
     - ``derivatives/preproc-mapping/sub-XX/ses-YY/func/``, the
       ``desc-pscHp`` series the released maps were fitted on - see
       :doc:`fmri_data`
   * - Design matrices and frame timing
     - ``*_desc-apertures_design.h5`` and ``*_desc-frames_design.tsv``
       beside each run - see :ref:`retinotopy-stimulus-files`
   * - Aperture libraries
     - ``stimuli/retinotopy/`` - see :ref:`retinotopy-stimulus-files`
   * - Brain masks and ROIs on the same grid
     - ``res-1pt5`` files in ``derivatives/anatomical/`` and
       ``derivatives/rois/`` - see :ref:`grids`

Preprocessing from scratch
--------------------------

If you want to run your own preprocessing pipeline instead of using the
provided NORDIC/tedana outputs.

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - What you need
     - Details
   * - Raw BOLD data
     - ``sub-XX/func/`` - see :doc:`fmri_data`
   * - T1w anatomical scans
     - ``sub-XX/anat/`` - see :doc:`anatomical_data`
   * - Event timing files
     - ``sub-XX/func/*_events.tsv`` - see :doc:`experimental_design`
   * - Diffusion data *(if needed)*
     - ``sub-XX/dwi/`` - see :doc:`diffusion`

.. tip::

   For details on the preprocessing we already ran, see :doc:`preprocessing`.
   For MRI acquisition parameters, see :doc:`mri_acquisition`.

.. _subject-sets:

Subject Sets
============

Five participants, ``sub-01``, ``sub-03``, ``sub-05``, ``sub-06`` and
``sub-07``, took part in both the main experiment and precision mapping.
``sub-04`` and ``sub-08`` took part in precision mapping only. They have no
main-experiment sessions or betas and are downloaded separately (see
:doc:`laion_fmri_package/download`).

.. _grids:

Grids
=====

The functional products are on the participant's FreeSurfer surface
(``space-fsnative``, one file per hemisphere) or on one of two volume grids
in the participant's ``T1w`` space: ``res-1pt5`` (1.5 mm), on which the
precision-mapping data were fitted, and ``res-1pt8`` (1.778 mm), the grid of
the main-experiment BOLD and betas, whose files carry ``space-T1w`` without
``res-``. ``res-1pt8`` is the default of the :mod:`laion_fmri` accessors.

Arrays combine voxel by voxel only on the same grid. Which product is on
which grid:

.. list-table::
   :widths: 31 23 23 23
   :header-rows: 1

   * - Product
     - ``space-fsnative``
     - ``space-T1w_res-1pt5``
     - ``space-T1w_res-1pt8``
   * - Preprocessed BOLD
     - precision mapping
     - precision mapping
     - main experiment
   * - Single-trial betas
     - —
     - —
     - fitted
   * - pRF maps
     - fitted
     - fitted
     - resampled
   * - Localizer maps
     - fitted
     - fitted
     - resampled
   * - ROIs
     - drawn
     - projected
     - projected
   * - T1w, T2w, brain and tissue masks
     - —
     - resampled
     - resampled

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
   * - Surface data
     - GIFTI (.func.gii), FreeSurfer (.label, .annot)
     - Values per ``fsnative`` vertex, one file per hemisphere
   * - Metadata
     - JSON (.json)
     - BIDS sidecar files
   * - Events / behavioral
     - TSV (.tsv)
     - Tab-separated, BIDS-compliant
   * - Stimulus images
     - HDF5 (.h5)
     - Single packed file with raw encoded JPEG/PNG bytes, row-aligned to
       ``task-images_metadata.csv`` and accessible by image name through
       :func:`laion_fmri.load_stimuli`.
   * - Stimulus metadata
     - CSV
     - ``stimuli/task-images_metadata.csv`` - see
       :doc:`stimulus_data`

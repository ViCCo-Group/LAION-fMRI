===============
Anatomical Data
===============

The anatomical data were acquired in a dedicated 3T Prisma session (``ses-PrismaAnat``),
including five T1w images and three T2w images at 0.8 mm isotropic.
Per subject we provide the averaged T1w and T2w volumes, a brain
mask, and a FreeSurfer surface reconstruction. 


Averaged T1w, T2w, and Brain Mask
=================================

Path: ``derivatives/anatomical/sub-XX/ses-PrismaAnat/anat/``

.. code-block:: text

    derivatives/anatomical/
    ├── dataset_description.json
    └── sub-XX/
        └── ses-PrismaAnat/
            └── anat/
                ├── sub-XX_ses-PrismaAnat_space-T1w_T1w.nii.gz
                ├── sub-XX_ses-PrismaAnat_space-T1w_T2w.nii.gz
                ├── sub-XX_ses-PrismaAnat_space-T1w_desc-brain_mask.nii.gz
                ├── sub-XX_ses-PrismaAnat_space-T1w_res-1pt8_T1w.nii.gz
                ├── sub-XX_ses-PrismaAnat_space-T1w_res-1pt8_T2w.nii.gz
                └── sub-XX_ses-PrismaAnat_space-T1w_res-1pt8_desc-brain_mask.nii.gz
                (+ one .json sidecar per .nii.gz)

Each modality is shipped at two resolutions:

- **0.8 mm isotropic** (``space-T1w_*``) — on the FreeSurfer hires
  conformed grid, acquisition resolution suitable for surface-level work and high-resolution
  visualisation.
- **1.7778 mm isotropic** (``space-T1w_res-1pt8_*``) — on the same grid
  as the preprocessed BOLD data (see :doc:`fmri_data`) and the ROIs
  (see :doc:`rois`), allowing direct overlay without further resampling.

Both versions are in the **T1w space** of the subject and oriented
**LAS**.

FreeSurfer Reconstruction
=========================

Path: ``derivatives/freesurfer/sub-XX/``

FreeSurfer 7.4.1 was run on the averaged T1w with the T2w supplied via
``-T2`` and ``-T2pial``, at the native 0.8 mm resolution (``-hires``).

.. code-block:: text

    derivatives/freesurfer/
    ├── dataset_description.json
    └── sub-XX/
        ├── label/
        ├── mri/
        ├── stats/
        └── surf/

- ``mri/`` — segmentations, normalised volumes, and recon-all
  intermediates.
- ``surf/`` — standard recon-all surfaces plus per-hemisphere manual
  flat patches cut by hand and used to produce flatmaps for
  visualizations.
- ``label/`` — standard FreeSurfer cortical parcellations and exvivo
  labels.
- ``stats/`` — recon-all per-parcellation summary statistics.

Custom ROI labels (retinotopic maps, category-selective regions) are
provided in a dedicated derivative; see :doc:`rois`.

The volumes inside ``derivatives/freesurfer/sub-XX/mri/`` follow
FreeSurfer's internal convention (LIA-oriented conformed space), as
expected by all FreeSurfer tools. The world-space coordinates are
identical to the ``derivatives/anatomical/`` images.

.. only:: dev

   Loading Anatomical Data
   =======================

   .. todo::

      Provide minimal code examples once file paths are finalized.

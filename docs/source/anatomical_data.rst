===============
Anatomical Data
===============

The anatomical data were acquired in a dedicated 3T Prisma session (``ses-PrismaAnat``),
including five T1w images and three T2w images at 0.8 mm isotropic.
Per subject we provide the averaged T1w and T2w volumes, a brain
mask, tissue masks, and a FreeSurfer surface reconstruction.

``sub-04`` was not scanned in that session. Its anatomy comes from a 3T
Connectom scanner and is released under ``ses-ConnectomAnat``, which
replaces ``ses-PrismaAnat`` in every path and file name on this page.
The derivatives have the same 0.8 mm resolution and file types.
The raw data for ``ses-ConnectomAnat`` are not part of the current release.

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
                ├── sub-XX_ses-PrismaAnat_space-T1w_res-1pt8_desc-brain_mask.nii.gz
                ├── sub-XX_ses-PrismaAnat_space-T1w_res-1pt5_T1w.nii.gz
                ├── sub-XX_ses-PrismaAnat_space-T1w_res-1pt5_T2w.nii.gz
                └── sub-XX_ses-PrismaAnat_space-T1w_res-1pt5_desc-brain_mask.nii.gz
                (+ one .json sidecar per .nii.gz)

Each modality is shipped at three resolutions:

- **0.8 mm isotropic** (``space-T1w_*``) — on the FreeSurfer hires
  conformed grid, acquisition resolution suitable for surface-level work and high-resolution
  visualisation.
- **1.7778 mm isotropic** (``space-T1w_res-1pt8_*``) — on the same grid
  as the preprocessed BOLD data (see :doc:`fmri_data`) and the ROIs
  (see :doc:`rois`), allowing direct overlay without further resampling.
  Not provided for ``sub-04`` and ``sub-08``, who have no main-experiment
  data.
- **1.5 mm isotropic** (``space-T1w_res-1pt5_*``) — on the same grid as
  the volumetric pRF maps (see :doc:`retinotopy`) and localizer maps
  (see :doc:`localizers`), so they share voxel indices with those maps.

The T1w and T2w are resampled with cubic interpolation and the brain
mask with nearest-neighbour interpolation. All three versions are in
the **T1w space** of the subject and oriented **LAS**.

Tissue Masks
============

Path: ``derivatives/anatomical/sub-XX/ses-PrismaAnat/anat/``

.. code-block:: text

    sub-XX_ses-PrismaAnat_space-T1w_label-CGM_mask.nii.gz
    sub-XX_ses-PrismaAnat_space-T1w_label-SGM_mask.nii.gz
    sub-XX_ses-PrismaAnat_space-T1w_label-BS_mask.nii.gz
    sub-XX_ses-PrismaAnat_space-T1w_label-CBM_mask.nii.gz
    sub-XX_ses-PrismaAnat_space-T1w_label-WM_mask.nii.gz
    sub-XX_ses-PrismaAnat_space-T1w_label-CSF_mask.nii.gz
    (each also at res-1pt8 and res-1pt5, + one .json sidecar per .nii.gz)

Six binary masks divide the brain into tissue classes, named with BIDS
common labels. They are taken
from the FreeSurfer reconstruction (see below) and resampled onto each
grid with nearest-neighbour interpolation, without dilation.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Label
     - Contents
   * - ``label-CGM``
     - Cortical grey matter, from ``ribbon.mgz`` (labels 3 and 42). A
       voxel belongs to it when its centre lies between the white and
       pial surfaces.
   * - ``label-SGM``
     - Subcortical grey matter, from ``aseg.mgz``: thalamus, ventral
       diencephalon, hippocampus, amygdala, caudate, putamen, pallidum and
       accumbens.
   * - ``label-BS``
     - Brainstem, from ``aseg.mgz``.
   * - ``label-CBM``
     - Cerebellar cortex, from ``aseg.mgz``. Cerebellar white matter is in
       ``label-WM``.
   * - ``label-WM``
     - White matter, from ``aseg.mgz``: cerebral and cerebellar white
       matter, corpus callosum, optic chiasm and white-matter
       hypointensities.
   * - ``label-CSF``
     - Ventricular CSF, from ``aseg.mgz``: the lateral, inferior lateral,
       third, fourth and fifth ventricles and the ``aseg`` CSF label.

The masks are provided on the same three grids as the T1w, T2w and
brain mask, in the **T1w space** of the subject and oriented **LAS**.

.. note::

   The CSF mask covers the ventricles only, because FreeSurfer does not
   segment sulcal or extracerebral CSF.

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

Loading Anatomical Data
=======================

The :mod:`laion_fmri` package downloads the anatomical derivatives with
``download(include_anatomical=True)`` (``include_freesurfer=True`` for the
recon) and returns the path of each file;
``res`` selects the grid (full resolution by default):

.. code-block:: python

   import laion_fmri
   import nibabel as nib

   sub = laion_fmri.load_subject("sub-03")
   t1w = nib.load(sub.get_t1w(res="1pt5"))
   brain = nib.load(sub.get_anatomical_brain_mask(res="1pt8"))
   cgm = nib.load(sub.get_anatomical_tissue_mask("CGM", res="1pt5"))
   fs_dir = sub.get_freesurfer_dir()

See :doc:`laion_fmri_package/load` for the voxel-axis variants.

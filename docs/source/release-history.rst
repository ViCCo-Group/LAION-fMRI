=========
Changelog
=========

Changes to the dataset, derived files, and Python package.

2026-11-04
==========

Precision-mapping-only subjects: sub-04 and sub-08
--------------------------------------------------

Added ``sub-04`` and ``sub-08``, who took part in precision mapping only.
They did not take part in the LAION image-viewing experiment: they have no
main-experiment sessions, no single-trial betas, no ``res-1pt8`` files, no
object localizer, and none of the ROI sets defined by the image-viewing
data (``laion``, ``laionstim``, ``object``). ``sub-04``'s anatomy is
``ses-ConnectomAnat`` instead of ``ses-PrismaAnat``.

.. warning::

   If your code uses ``get_subjects``, upgrade the LAION-fMRI package to
   0.2.0:

   .. code-block:: bash

      python -m pip install --upgrade "laion-fmri @ git+https://github.com/ViCCo-Group/LAION-fMRI.git@main"

   Versions before 0.2.0 list subjects from the bucket, so ``get_subjects``
   now returns ``sub-04`` and ``sub-08`` among the main-experiment subjects.
   Code that loops over that list then requests main-experiment files these
   subjects do not have, and fails with a ``DataNotDownloadedError``. From
   0.2.0, ``get_subjects()`` returns the main experiment's five subjects and
   ``get_subjects("mapping")`` adds ``sub-04`` and ``sub-08``.

Retinotopy timeseries and stimulus apertures
--------------------------------------------

Added everything needed to fit pRF models to the retinotopy data:

- the preprocessed runs of every precision-mapping session under
  ``derivatives/preproc-mapping/``, including the percent-signal-change,
  high-pass filtered ``desc-pscHp`` timeseries the released pRF maps were
  fitted on, on ``res-1pt5`` and ``fsnative`` (see :doc:`fmri_data`)
- per run, the design matrix as fitted (``desc-apertures_design.h5``) and
  the frame table with its timing (``desc-frames_design.tsv``)
- the aperture libraries the designs were built from, under
  ``stimuli/retinotopy/``.

See :ref:`retinotopy-stimulus-files` for the file layout and how to
rebuild or vary a design matrix. The raw BIDS data of the
precision-mapping sessions are added as well.

2026-10-19
==========

Retinotopy (pRF) maps
---------------------

Added population receptive field estimates (see :doc:`retinotopy`) and
``res-1pt5`` masks and segmentations for every published ROI set.

Retinotopic ROIs constrained by LAION image dimensions
------------------------------------------------------

Added the ``laionstim`` ROI set: every retinotopic ROI restricted to the
vertices whose pRF centre lay inside the LAION image, on the surface and
on both volume grids, with its segmentation. See :doc:`rois`.

2026-10-15
==========

Tissue masks and 1.5 mm anatomicals
-----------------------------------

Added cortical grey matter, subcortical grey matter, brainstem,
cerebellar cortex, white matter and ventricular CSF masks to the
anatomical derivatives, at full resolution, ``res-1pt8`` and
``res-1pt5``. Added the T1w, T2w and
brain mask on the ``res-1pt5`` grid of the volumetric pRF and
localizer maps. See :doc:`anatomical_data`.

2026-10-06
==========

ROI corrections
---------------

- ``SPA`` replaces ``SPL`` as the fourth place-selective area. This is an
  intended redraw, not a rename or a correction: ``SPA`` covers more
  posterior vertices from the ``SPL`` it replaces, so results for the two
  are not comparable across versions. The ``seg-place`` segmentations are 
  updated accordingly.
- Withdrew sub-03's ``pSTS-words`` due to being drawn too anteriorly
  compared to the other subjects'. Updated its
  ``seg-character`` segmentation accordingly.
- Removed sub-07's ``aLOC``, ``dLOC`` and ``pLOC`` masks, left over from an
  earlier object vocabulary. No segmentation referenced them.

The previous ``SPL`` and ``pSTS-words`` masks and the segmentations they
appeared in are kept under ``archive/rois/v1/`` on the bucket.

2026-09-28
==========

.. _random-split-correction:

Corrected per-subject random splits
-----------------------------------

Updated the subject-specific ``random_0``–``random_4`` splits to keep
identified duplicate images in the same fold, preserving split names
and fold sizes. Update the Python package to use the corrected splits.
The `previous files <https://github.com/ViCCo-Group/LAION-fMRI/blob/main/archive/splits/random-v1.zip>`__
are archived for reproducing earlier results.

Across-subject train/test splits
--------------------------------

Added ``pool="pooled"`` with tau and five cluster splits for consistent
image assignments across subjects. See
:ref:`across-subject splits <pooled-splits>` for usage and construction.

.. _embedding-transparency-correction:

Corrected stimulus embedding transparency
-----------------------------------------

Updated the CLIP, DINOv2, PEcore, and SigLIP2 embedding files for 116
out-of-distribution stimuli with non-opaque pixels. Their original
embeddings discarded transparency. The corrected embeddings composite
the images onto the experiment's middle-grey background, RGB
``(128, 128, 128)``, before model-specific resizing and cropping.

The remaining 24,936 embedding rows in each file are unchanged, as are
the image IDs, row order, storage dtypes, and file layout. The stimulus
images themselves have not changed.

The corrected files are available at the existing download URLs. To
refresh an existing download, close any open embedding handles and run:

.. code-block:: python

   import laion_fmri

   laion_fmri.download_embeddings("all")

Then reload the embeddings. This also works with older package versions:
the corrected files differ in size from the originals, so the downloader
replaces the cached files. No package upgrade is required for this data
correction.

For reproducibility, the original files are preserved in the archive:

* `Original CLIP embeddings <https://laion-fmri.s3.us-west-2.amazonaws.com/archive/embeddings/v1/task-images_desc-CLIP_embeddings.h5>`__
* `Original DINOv2 embeddings <https://laion-fmri.s3.us-west-2.amazonaws.com/archive/embeddings/v1/task-images_desc-DINOv2_embeddings.h5>`__
* `Original PEcore embeddings <https://laion-fmri.s3.us-west-2.amazonaws.com/archive/embeddings/v1/task-images_desc-PEcore_embeddings.h5>`__
* `Original SigLIP2 embeddings <https://laion-fmri.s3.us-west-2.amazonaws.com/archive/embeddings/v1/task-images_desc-SigLIP2_embeddings.h5>`__

See :doc:`stimulus_derivatives` for the embedding models and file layout.

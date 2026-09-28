=========
Changelog
=========

Changes to the dataset, derived files, and Python package.

2026-09-28
==========

.. _random-split-correction:

Corrected per-subject random splits
------------------------------------

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

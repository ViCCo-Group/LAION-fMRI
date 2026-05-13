====================
Stimulus Derivatives
====================

LAION-fMRI includes dataset-wide files derived from the stimulus images:
pretrained image embeddings, object segmentations, and natural-language
captions. They are stored under ``stimuli/`` and use the same
``image_name`` keys as the stimulus metadata described in
:doc:`stimulus_data`.

.. code-block:: text

   stimuli/
   ├── task-images_desc-CLIP_embeddings.h5
   ├── task-images_desc-DINOv2_embeddings.h5
   ├── task-images_desc-PEcore_embeddings.h5
   ├── task-images_desc-SigLIP2_embeddings.h5
   ├── task-images_desc-segmentations.h5
   ├── task-images_desc-segmentations_metadata.csv
   └── task-images_desc-captions.csv

Download the derived files independently of the packed image HDF5:

.. code-block:: python

   import laion_fmri

   laion_fmri.download_embeddings("CLIP")
   laion_fmri.download_segmentations()
   laion_fmri.download_captions()

Embeddings can be loaded directly with
:func:`~laion_fmri.load_embeddings`. Captions and segmentations can be
opened directly with :class:`~laion_fmri.Captions` and
:class:`~laion_fmri.Segmentations`. If the raw stimulus set is also
installed, the same files are available through the dataset-wide
:class:`~laion_fmri.Stimuli` handle and through trial-aligned
:class:`~laion_fmri.Subject` accessors.

Stimulus Embeddings
===================

For every stimulus image in the dataset (25,052 in total, including the
OOD set), pretrained image embeddings from four widely used vision
models are provided as a convenience for downstream analyses. The
embeddings are stored as four HDF5 files, one per model:

.. code-block:: text

   stimuli/
   ├── task-images_desc-CLIP_embeddings.h5
   ├── task-images_desc-DINOv2_embeddings.h5
   ├── task-images_desc-PEcore_embeddings.h5
   └── task-images_desc-SigLIP2_embeddings.h5

The four models are:

.. list-table::
   :widths: 15 30 15 40
   :header-rows: 1

   * - ``desc-`` label
     - Model
     - Feature dim
     - Notes
   * - ``CLIP``
     - OpenCLIP LAION ViT-H/14
     - 1024
     - L2-normalised
   * - ``DINOv2``
     - DINOv2 ViT-L/14
     - 1024
     - Mean-pooled patch tokens from layer 23; not normalised
   * - ``PEcore``
     - PE Core L/14, 336 px
     - 1024
     - L2-normalised
   * - ``SigLIP2``
     - SigLIP2 SO400M Patch14, 384 px
     - 1152
     - L2-normalised

Each file has the same layout -- a flat HDF5 with three datasets of
length 25,052:

.. code-block:: text

   embedding   # (25052, feature_dim) float16
   image_ids   # (25052,) variable-length strings; image filenames
   valid       # (25052,) bool; True for every image in release-main

Rows in ``embedding`` correspond one-to-one to entries in ``image_ids``,
and all four files share the same ``image_ids`` order. To work with a
specific subject's stimuli, intersect ``image_ids`` with the
``image_name`` column of the stimulus metadata or use the subject-level
accessors below.

Loading embeddings with the standalone loader:

.. code-block:: python

   import laion_fmri

   emb = laion_fmri.load_embeddings("CLIP")
   emb["CLIP"][0]                            # (1024,) float16
   emb.get(
       "CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                         # one vector

If the full stimulus set is installed, embeddings are also reachable
from the :class:`~laion_fmri.Stimuli` handle:

.. code-block:: python

   stim = laion_fmri.load_stimuli()
   stim.embeddings.models                    # ['CLIP', 'DINOv2', 'PEcore', 'SigLIP2']
   stim.embeddings["CLIP"]                   # (25052, 1024) float16 array
   stim.embeddings.get(
       "CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                         # one vector

Object Segmentations
====================

Every **shared** stimulus image carries object-level segmentation
masks: for each noun the detector found in the image, one binary mask
per detected instance (e.g. four ``hand`` masks for an image with four
visible hands). These are useful for asking questions like "did the
subject see a face on this trial?" or for spatially restricting
analyses to image regions.

.. note::

   Segmentations are provided **for the shared stimulus set only**
   (1,492 images viewed by every subject). Subject-unique images do not
   carry masks. The listing methods (``nouns``, ``for_image``) return
   empty results -- not errors -- for uncovered images.

Files on disk:

.. code-block:: text

   stimuli/
   ├── task-images_desc-segmentations.h5            # (24011, 1000, 1000) uint8
   └── task-images_desc-segmentations_metadata.csv  # one row per mask

The HDF5 holds a single ``masks`` dataset, gzip-compressed with the
byte-shuffle filter so the file ships at about 68 MB despite more than
24,000 masks. The sidecar CSV maps each ``mask_row`` to an
``(image_name, noun, instance_id)`` triple, with detection score,
bounding box, and a ``localized`` flag that is ``0`` when the detector
flagged a concept but could not bound it spatially. Those rare rows are
safe to filter out with ``localized == 1``.

Loading segmentations with the standalone reader:

.. code-block:: python

   import laion_fmri

   seg = laion_fmri.Segmentations()

   # What nouns are present in this image?
   seg.nouns(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                         # ['fingers', 'hand', ...]

   # Fetch one mask:
   mask = seg.get(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
       "fingers",
       instance=0,
   )                                         # (1000, 1000) uint8

Stimulus Captions
=================

Each stimulus carries a small set of short *human* captions. Shared
non-OOD stimuli additionally carry one *AI* caption. The target is:

* **shared** images (seen by every participant) get **five** human
  captions and, for non-OOD images, **one** AI caption
* **unique** images (presented to one participant only) get **three**
  human captions and no AI caption
* **OOD** images get their target human captions and no AI caption

The human captions were written by crowdworkers on CloudResearch
Connect -- each shown one image at a time and asked to describe it in a
single sentence. The AI captions were generated by GPT-5.1 and are
included for shared non-OOD images only. Together they give you a small
set of independent natural-language descriptions per image, useful for
caption-conditioned modelling, retrieval, or quick qualitative checks.

See :doc:`metadata_acquisition` for the collection procedure
(CloudResearch Connect batches, quality screening, AI prompt design).

Captions live in a single CSV that sits next to the stimulus images:

.. code-block:: text

   stimuli/
     task-images_desc-captions.csv

The CSV is in long form: one row per caption. A shared non-OOD image
with five human captions and one AI caption contributes six rows; a
shared OOD image contributes five rows; a unique image contributes
three rows.

.. list-table::
   :widths: 22 78
   :header-rows: 1

   * - Column
     - Meaning
   * - ``image_name``
     - Stimulus filename. Join key against
       ``task-images_metadata.csv``.
   * - ``caption_idx``
     - Position within the image. Rank ``1`` is the highest-quality
       human caption; ranks go up to ``3`` for unique images and up to
       ``5`` for shared images. The AI caption (if any) gets ``0``.
   * - ``source``
     - ``"human"`` or ``"ai"``.
   * - ``caption``
     - The caption text.
   * - ``origin_collection``
     - Where the caption came from -- a CloudResearch Connect batch
       label like ``"main3"`` or ``"topup1"`` for humans, the model name
       (e.g. ``"gpt-5.1"``) for AI.
   * - ``participant_id``
     - CloudResearch Connect participant identifier. Empty for AI rows.
   * - ``ai_model``
     - Model name. Empty for human rows.

All images have their target human-caption count (three for unique
images, five for shared images). AI captions are present for shared
non-OOD images only.

Loading captions with the standalone reader:

.. code-block:: python

   import laion_fmri

   caps = laion_fmri.Captions()

   # All human captions for one image (rank-ordered, up to five):
   caps.human("shared_12rep_LAION_cluster_1003_i0.jpg")
   # ['a hand with light pink painted nails with flower designs',
   #  'A hand with finger painted nails with flowers in them',
   #  ...]

   # The AI caption, or None if no AI caption is available:
   caps.ai("shared_12rep_LAION_cluster_1003_i0.jpg")

   # Or grab everything for an image as a DataFrame:
   caps.get("shared_12rep_LAION_cluster_1003_i0.jpg")

   # And the full long-form table:
   caps.metadata.head()

Subject-Level Access
====================

Subject-level accessors provide trial-aligned views of derived stimulus
files once the subject files and the full stimulus set are installed.
Use ``Subject.metadata`` for a concatenated trial table with derived
``image_name``, ``stim_idx``, ``unique_or_shared``, and ``dataset``
columns. The row index of that table is the global trial index accepted
by ``sub.embeddings``, ``sub.segmentations``, and ``sub.captions``. See
:doc:`glmsingle_betas` for the beta-to-stimulus mapping convention.

.. code-block:: python

   import laion_fmri

   sub = laion_fmri.load_subject("sub-01")

   trials = sub.metadata
   trials[[
       "session", "session_trial", "image_name",
       "unique_or_shared", "dataset",
   ]].head()

   trial = 42  # global row index in sub.metadata

   # Pretrained features aligned to the same trial rows:
   x_one = sub.embeddings.get("CLIP", trial)          # (1024,)
   x_all = sub.embeddings.all("CLIP")                 # (n_trials, 1024)
   x_ses = sub.embeddings.all("CLIP", session="ses-01")

   # Object masks for shared-image trials:
   if sub.segmentations.has_image(trial):
       nouns = sub.segmentations.nouns(trial)
       mask = sub.segmentations.get(trial, nouns[0])  # (1000, 1000) uint8

   # Captions for the stimulus shown on this trial:
   human = sub.captions.human(trial)
   ai = sub.captions.ai(trial)  # None for unique-image and OOD trials

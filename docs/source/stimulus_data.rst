==============
Stimulus Data
==============

The LAION-fMRI stimulus set is a deduplicated collection of 25,052
distinct natural images shown across all five participants. The
majority were drawn from LAION-natural — a curated 120-million-image
subset of LAION-2B filtered to natural photographs (Roth & Hebart,
2025) — and were chosen by an effective-dimensionality optimisation
procedure that promotes uniform coverage of CLIP feature space.
Selection was anchored in two established neuroimaging benchmarks by
incorporating images from the Natural Scenes Dataset (NSD;
Allen et al., 2022) and from THINGS / THINGS+ (Hebart et al., 2019;
Stoinski et al., 2024). The shared set is supplemented with a 371-image
out-of-distribution (OOD) test set — visual illusions, Gabor patches,
shape stimuli, cropped textures, and similarly unusual configurations
— intended as a stress test for encoding and decoding models trained
on the natural-image pool.

"Natural images" here means real-world photographs of scenes, objects,
and events — illustrations, graphic designs, images with applied
filters, and not-safe-for-work content were excluded during manual
quality review (see :doc:`stimulus_selection` for the full screening
criteria).

Each participant saw **6,204** unique images across 30 main sessions:
**1,492 shared** images viewed by every participant (used for noise
ceilings and cross-participant comparison) plus **4,712 subject-unique**
images sampled disjointly from the same pools. Repetition counts and
per-session scheduling are documented in :doc:`experimental_design`;
the methodology behind image selection is in :doc:`stimulus_selection`.

Stimulus Sets
=============

The shared set has four sources and the unique sets have three. The
table below names each contribution and how many repeats it receives in
the main experiment; the full selection procedure is in
:doc:`stimulus_selection`.

.. list-table:: Shared set (1,492 images viewed by every participant)
   :widths: 25 18 18 39
   :header-rows: 1

   * - Source
     - Count
     - Repetitions
     - Notes
   * - LAION-natural
     - 641
     - 12
     - Diversity-optimised photographs from the 120M LAION-natural pool
   * - THINGS+
     - 240
     - 12
     - CC0 object photographs from the THINGS+ extension
   * - NSD
     - 240
     - 4
     - Cross-study comparability with the Natural Scenes Dataset
   * - OOD
     - 371
     - 4
     - Visual illusions, Gabor patches, cropped textures, shape stimuli,
       unusual spatial configurations, gaudy patterns

.. list-table:: Subject-unique set (4,712 images per participant, sampled disjointly across the five participants)
   :widths: 25 18 18 39
   :header-rows: 1

   * - Source
     - Count
     - Repetitions
     - Notes
   * - LAION-natural
     - 4,246
     - 4
     - Each participant draws from a non-overlapping LAION pool
   * - THINGS
     - 144
     - 4
     - Object photographs from the original THINGS database
   * - THINGS+
     - 322
     - 4
     - Additional CC0 object photographs from THINGS+

Across all five participants the experiment encompasses **25,052
distinct images** (1,492 shared + 5 × 4,712 unique). For cross-subject
analyses the 1,492 shared images are the natural unit of analysis; for
within-subject encoding or decoding, the full 6,204-image per-participant
set is available.

Image Format
============

All stimuli ship as **square JPEG files at 1000 × 1000 pixels**, RGB
colour. Where the source image was not already square, reviewers chose
the crop manually during quality review (rather than centre-cropping
automatically) to avoid occluding salient image content.

On the projector during scanning, the 1000 × 1000 px stimulus subtended
**roughly 9.2 × 9.2 degrees of visual angle** — see :doc:`experimental_design`
for the full presentation geometry.

OOD Test Set
============

In addition to the natural-image pool, 371 **out-of-distribution (OOD)**
images are shipped as part of the shared set, viewed by every
participant 4 times. The OOD images deliberately fall outside the LAION
distribution and are intended as a held-out test set for measuring how
well encoding and decoding models generalise beyond the training
distribution. The set covers several visually distinct subcategories:

* **Classical visual illusions** — Müller-Lyer, Ebbinghaus,
  Kanizsa-style, and similar geometric/perceptual illusions.
* **Gabor patches** — at different orientations, spatial frequencies,
  and contrasts.
* **Shape stimuli** — simple coloured shapes on plain backgrounds.
* **Cropped textures** — repetitive patterns and material textures
  with no scene context.
* **Unusual spatial configurations** — objects in implausible
  positions, scale violations, etc.
* **Gaudy / high-saturation patterns** — strongly chromatic
  geometric patterns far from the natural-image colour statistics.

.. figure:: _static/oodA_images.png
   :align: center
   :width: 70%
   :alt: Example OOD stimuli from the LAION-fMRI dataset

   A sample of OOD stimuli from the LAION-fMRI shared set.

See :doc:`train_test_splits` for how to use the OOD set as a held-out
test split (Method 3 of the re:vision generalization framework).

File Organization
=================

The stimuli ship as a single HDF5 image file plus a sidecar metadata
CSV under ``stimuli/``, alongside per-model embedding files and the
object-segmentation bundle:

.. code-block:: text

   stimuli/
   ├── task-images_stimuli.h5                    # raw JPEG bytes, indexed by image name
   ├── task-images_metadata.csv                  # per-image metadata, row-aligned to the HDF5
   ├── task-images_desc-CLIP_embeddings.h5
   ├── task-images_desc-DINOv2_embeddings.h5
   ├── task-images_desc-PEcore_embeddings.h5
   ├── task-images_desc-SigLIP2_embeddings.h5
   ├── task-images_desc-segmentations.h5         # object masks for shared images
   ├── task-images_desc-segmentations_metadata.csv
   └── task-images_desc-captions.csv             # human + AI image captions

Per-asset file layout and download flow are documented in the
respective sections below.

Stimulus Metadata
=================

For details on how the metadata was collected and computed (visual properties,
semantic annotations, model-derived features), see
:doc:`metadata_acquisition`.

.. only:: live

   *Full documentation of the* ``stimuli.tsv`` *columns will be added
   with the final release.*

.. only:: dev

   .. todo::

      Document the ``stimuli.tsv`` file:

      - List every column and what it contains
      - Show a few example rows (copy from the actual file)
      - Document the companion ``stimuli.json`` sidecar if one exists

Stimulus Embeddings
===================

For every stimulus image in the dataset (25,052 in total, including the
OOD set), pretrained image embeddings from four widely used vision models
are provided as a convenience for downstream analyses. The embeddings are
stored as four HDF5 files, one per model, sitting next to the stimulus
images themselves:

.. code-block:: text

   stimuli/
   ├── task-images_stimuli.h5          # the images
   ├── task-images_metadata.csv        # image-level metadata
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

Each file has the same layout — a flat HDF5 with three datasets of
length 25,052:

.. code-block:: text

   embedding   # (25052, feature_dim) float16
   image_ids   # (25052,) variable-length strings — image filenames
   valid       # (25052,) bool — True for every image in release-main

Rows in ``embedding`` correspond one-to-one to entries in ``image_ids``,
and all four files share the same ``image_ids`` order. To work with a
specific subject's stimuli, intersect ``image_ids`` with the
``image_name`` column of the stimulus metadata (filtered to that
subject's images).

Loading them with the package:

.. code-block:: python

   import laion_fmri

   stim = laion_fmri.load_stimuli()
   stim.embeddings.models                    # ['CLIP', 'DINOv2', 'PEcore', 'SigLIP2']
   stim.embeddings["CLIP"]                   # (25052, 1024) float16 array
   stim.embeddings.get(
       "CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                         # one vector

   # Trial-aligned access from the subject side:
   sub = laion_fmri.load_subject(1)
   sub01_clip = sub.embeddings.all("CLIP")   # (n_trials, 1024)

Object Segmentations
====================

Every **shared** stimulus image carries object-level segmentation
masks: for each noun the detector found in the image, one binary
mask per detected instance (e.g. four ``hand`` masks for an image
with four visible hands). These are useful for asking questions
like "did the subject see a face on this trial?" or for spatially
restricting analyses to image regions.

.. note::

   Segmentations are provided **for the shared stimulus set only**
   (1,492 images viewed by every subject). Subject-unique images do
   not carry masks. The listing methods (``nouns``, ``for_image``)
   return empty results -- not errors -- for uncovered images.

Files on disk:

.. code-block:: text

   stimuli/
   ├── task-images_desc-segmentations.h5            # (24011, 1000, 1000) uint8
   └── task-images_desc-segmentations_metadata.csv  # one row per mask

The HDF5 holds a single ``masks`` dataset, gzip-compressed with the
byte-shuffle filter so the file ships at ~68 MB despite 24,000+
masks. The sidecar CSV maps each ``mask_row`` to an
``(image_name, noun, instance_id)`` triple, with detection score,
bounding box, and a ``localized`` flag that is ``0`` when the
detector flagged a concept but couldn't bound it spatially
(rare; safe to filter out with ``localized == 1``).

Download and load:

.. code-block:: python

   import laion_fmri

   laion_fmri.download_segmentations()       # ~68 MB, public, no DUA

   stim = laion_fmri.load_stimuli()

   # What nouns are present in this image?
   stim.segmentations.nouns(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                         # ['fingers', 'hand', ...]

   # Fetch one mask:
   mask = stim.segmentations.get(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
       "fingers",
       instance=0,
   )                                         # (1000, 1000) uint8

Subject-level trial access works the same way, with the trial index
in place of the image name:

.. code-block:: python

   sub = laion_fmri.load_subject(1)
   sub.segmentations.nouns(42)               # nouns shown on trial 42
   sub.segmentations.has_image(42)           # False for unique-image trials
   sub.segmentations.get(42, "fingers")      # mask for trial 42

Stimulus Captions
=================

Each stimulus carries a small set of short *human* captions plus, where
available, one *AI* caption. The target is:

* **shared** images (seen by every participant) get **five** human
  captions
* **unique** images (presented to one participant only) get **three**

The human captions were written by crowdworkers on Prolific — each
shown one image at a time and asked to describe it in a single
sentence. The AI captions come from large multimodal models (currently
GPT-5.1 for the shared stimulus set, GPT-4o for the rest). Together
they give you a small set of independent natural-language descriptions
per image, useful for caption-conditioned modelling, retrieval, or
quick qualitative checks.

See :doc:`metadata_acquisition` for the collection procedure (Prolific
batches, quality screening, AI prompt design).

Captions live in a single CSV that sits next to the stimulus images:

.. code-block:: text

   stimuli/
     task-images_stimuli.h5
     task-images_metadata.csv
     task-images_desc-captions.csv

The CSV is in long form: one row per caption. An image with three
human captions and one AI caption contributes four rows.

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
     - Where the caption came from — a Prolific batch label like
       ``"main3"`` or ``"topup1"`` for humans, the model name
       (e.g. ``"gpt-5.1"``) for AI.
   * - ``participant_id``
     - Prolific participant identifier. Empty for AI rows.
   * - ``ai_model``
     - Model name. Empty for human rows.

The target counts (3 unique / 5 shared) aren't always hit yet — some
images still come up short, mostly because some captions were manually
flagged as bad and removed. AI captions are present for a subset only
(mostly shared images). Treat the file as "best available so far".

Loading them with the package:

.. code-block:: python

   import laion_fmri

   stim = laion_fmri.load_stimuli()

   # All human captions for one image (rank-ordered, up to five):
   stim.captions.human("shared_12rep_LAION_cluster_1003_i0.jpg")
   # ['a hand with light pink painted nails with flower designs',
   #  'A hand with finger painted nails with flowers in them',
   #  ...]

   # The AI caption (or ``None`` if no AI caption is available):
   stim.captions.ai("shared_12rep_LAION_cluster_1003_i0.jpg")
   # 'A hand with short, pale pink polished nails features delicate
   #  floral nail art on two fingers.'

   # Or grab everything for an image as a DataFrame:
   stim.captions.get("shared_12rep_LAION_cluster_1003_i0.jpg")

   # And the full long-form table:
   stim.captions.metadata.head()

Distribution of Stimuli
=======================

To visualise where the different source pools sit relative to one
another in image-feature space, every stimulus was projected to two
dimensions with t-SNE applied to its OpenCLIP ViT-H/14 embedding
(perplexity 30, PCA-50 initialisation). LAION-natural fills the space
broadly thanks to the effective-dimensionality selection procedure.
The object-centric NSD, THINGS, and THINGS+ pools concentrate in
sub-regions of the space dominated by isolated-object photographs.
The OOD set scatters across the periphery, reflecting its
deliberately heterogeneous mix of illusions, Gabors, shapes, and
textures.

.. figure:: _static/stimuli_distribution.png
   :align: center
   :width: 75%
   :alt: t-SNE projection of all 25,052 stimuli in CLIP feature space, coloured by source pool

   t-SNE projection of the 25,052 LAION-fMRI stimuli in CLIP feature
   space, coloured by source pool. The plot is reproducible from
   ``docs/scripts/make_stimuli_tsne.py``.

Loading Stimulus Data
=====================

The :mod:`laion_fmri` package wraps each of the stimulus assets above
with a small named loader:

* :func:`laion_fmri.load_stimuli` returns a :class:`~laion_fmri.Stimuli`
  handle for the image HDF5 and metadata CSV — see
  :ref:`Stimulus images <load:Stimulus images>` in the load reference.
* :func:`laion_fmri.load_embeddings` opens one or more embedding files
  and exposes model-keyed access.
* The segmentation masks and captions are reached through the same
  ``Stimuli`` handle (``stim.segmentations``, ``stim.captions``).

To map stimulus IDs to single-trial beta indices, join
``Subject.get_trial_info(...)["label"]`` against the stimulus
metadata's ``image_name`` column — see :doc:`glmsingle_betas` for the
full mapping convention.

See also :doc:`train_test_splits` for how stimuli are partitioned into
training and test sets.


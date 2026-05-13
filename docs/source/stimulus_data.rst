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
Stoinski et al., 2024). The THINGS / THINGS+ images additionally
overlap with the THINGS-data EEG + fMRI release (Hebart et al., 2023),
so analyses on the LAION-fMRI shared set can be compared against
results from that dataset as well. The shared set is supplemented with
a 371-image out-of-distribution (OOD) test set — visual illusions,
Gabor patches, shape stimuli, cropped textures, and similarly unusual
configurations — intended as a stress test for encoding and decoding
models trained on the natural-image pool.

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
     - CC0 object photographs from the THINGS+ extension; the same images
       appear in the THINGS-data EEG + fMRI release
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
     - Object photographs from the original THINGS database; also
       present in the THINGS-data EEG + fMRI release
   * - THINGS+
     - 322
     - 4
     - Additional CC0 object photographs from THINGS+; also present in
       the THINGS-data EEG + fMRI release

Across all five participants the experiment encompasses **25,052
distinct images** (1,492 shared + 5 × 4,712 unique). For cross-subject
analyses the 1,492 shared images are the natural unit of analysis; for
within-subject encoding or decoding, the full 6,204-image per-participant
set is available.

Image Format
============

All stimulus images are **1000 × 1000 px, RGB, JPEG-encoded**. They are
stored as raw JPEG byte arrays inside ``task-images_stimuli.h5``, keyed
by image name; :func:`laion_fmri.load_stimuli` decodes them on access.

Where the source image was not already square, the 1000 × 1000 region
was selected with **DeepGaze** (Kümmerer et al.): for each candidate
square crop the model predicts a fixation-density map, and the crop
maximising total predicted saliency was kept. This preserves the most
visually salient image content rather than risking truncation through a
naïve centre crop.

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
   └── task-images_desc-captions.csv             # human captions + shared non-OOD AI captions

Per-asset file layout and download flow are documented in the
respective sections below.

Stimulus Metadata
=================

Stimulus-level metadata lives in ``stimuli/task-images_metadata.csv``.
Rows are aligned to ``task-images_stimuli.h5`` and use ``image_name``
as the join key for embeddings, captions, segmentations, and events
TSVs.

Core columns include:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Column
     - Meaning
   * - ``image_name``
     - Filename-style stimulus identifier and primary join key.
   * - ``dataset``
     - Source pool, e.g. LAION-natural, NSD, THINGS / THINGS+, or OOD.
   * - ``participant``
     - Participant assignment for subject-unique images; shared images
       are marked accordingly.
   * - ``unique_or_shared``
     - Whether the image belongs to the cross-subject shared set or to
       one participant's unique set.
   * - ``n_reps``
     - Number of planned experiment repetitions for the image.

For details on how the metadata was collected and computed (visual
properties, semantic annotations, model-derived features), see
:doc:`metadata_acquisition`.

Stimulus Embeddings
===================

For every stimulus image in the dataset (25,052 in total, including the
OOD set), pretrained image embeddings from four widely used vision models
are provided as a convenience for downstream analyses. The embeddings are
stored as four HDF5 files, one per model, sitting next to the stimulus
images themselves:

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
   sub = laion_fmri.load_subject("sub-01")
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

   sub = laion_fmri.load_subject("sub-01")
   sub.segmentations.nouns(42)               # nouns shown on trial 42
   sub.segmentations.has_image(42)           # False for unique-image trials
   sub.segmentations.get(42, "fingers")      # mask for trial 42

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
Connect — each shown one image at a time and asked to describe it in a
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
     - Where the caption came from — a CloudResearch Connect batch
       label like ``"main3"`` or ``"topup1"`` for humans, the model name
       (e.g. ``"gpt-5.1"``) for AI.
   * - ``participant_id``
     - CloudResearch Connect participant identifier. Empty for AI rows.
   * - ``ai_model``
     - Model name. Empty for human rows.

All images have their target human-caption count (three for unique
images, five for shared images). AI captions are present for shared
non-OOD images only.

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

   # Trial-aligned access through Subject uses global trial indices:
   sub = laion_fmri.load_subject("sub-03")
   sub.captions.human(42)
   sub.captions.ai(42)  # None for unique-image and OOD trials

Distribution of Stimuli
=======================

To visualise where the different source pools sit relative to one
another in image-feature space, every stimulus was projected to two
dimensions with t-SNE applied to its OpenCLIP ViT-H/14 embedding
(perplexity 30, PCA-50 initialisation).

.. figure:: _static/stimuli_distribution.png
   :align: center
   :width: 75%
   :alt: t-SNE projection of all 25,052 stimuli in CLIP feature space, coloured by source pool

   t-SNE projection of the 25,052 LAION-fMRI stimuli in CLIP feature
   space, coloured by source pool. The plot is reproducible from
   ``docs/scripts/make_stimuli_tsne.py``.

Loading Stimulus Data
=====================

The :mod:`laion_fmri` package separates downloading from loading:

.. code-block:: python

   import laion_fmri

   # Raw stimulus images + task-images_metadata.csv; requires the DUA.
   laion_fmri.download_stimuli()
   stim = laion_fmri.load_stimuli()

   stim.metadata.head()                       # task-images_metadata.csv
   image = stim.images.get(
       "shared_12rep_LAION_cluster_1003_i0.jpg",
   )                                          # PIL.Image

Public stimulus-derived sidecars are downloaded separately:

.. code-block:: python

   laion_fmri.download_embeddings("CLIP")
   emb = laion_fmri.load_embeddings("CLIP")
   emb.get("CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg")

   laion_fmri.download_segmentations()
   laion_fmri.download_captions()

After those files are present, captions and segmentations are also
reachable through the ``Stimuli`` handle as ``stim.captions`` and
``stim.segmentations``.

Subject-level accessors provide trial-aligned views. Use
``Subject.metadata`` for a concatenated trial table with derived
``image_name``, ``stim_idx``, ``unique_or_shared``, and ``dataset``
columns. The row index of that table is the global trial index accepted
by ``sub.images``, ``sub.embeddings``, ``sub.segmentations``, and
``sub.captions``. See :doc:`glmsingle_betas` for the beta-to-stimulus
mapping convention.

.. code-block:: python

   import laion_fmri

   sub = laion_fmri.load_subject("sub-01")

   trials = sub.metadata
   trials[[
       "session", "session_trial", "image_name",
       "unique_or_shared", "dataset",
   ]].head()

   trial = 42  # global row index in sub.metadata

   # Images shown on this subject's trials:
   img = sub.images.get(trial)                # PIL.Image
   raw = sub.images[trial]                    # raw JPEG bytes
   session_imgs = sub.images.array("ses-01")  # (n, 1000, 1000, 3) uint8

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

See also :doc:`train_test_splits` for how stimuli are partitioned into
training and test sets.

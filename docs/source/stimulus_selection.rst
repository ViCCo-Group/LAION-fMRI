===================
Stimulus Selection
===================

LAION-fMRI stimuli were selected to cover a broad range of natural
image content while preserving enough repetitions for reliable
single-trial fMRI estimates. Most images come from `LAION-natural`_,
a curated 120-million-image subset of LAION-2B filtered to natural
photographs (Roth & Hebart, 2025). The set is supplemented with
images from NSD and THINGS / THINGSplus for cross-study comparison,
plus a shared out-of-distribution (OOD) set for generalization tests.

The launch-release stimulus set contains **25,052 distinct images**
across five participants. Each participant saw **6,204 unique
images**: **1,492 shared** images common to all participants and
**4,712 subject-unique** images. Supplemental sessions expand the
shared set to about 2,200 images and will be released later.

.. _LAION-natural: https://huggingface.co/datasets/andropar/relaion2b-natural

Selection Goals
===============

The stimulus set was designed around three goals:

* **Broad coverage** of the natural-image distribution, rather than a
  small hand-picked taxonomy of categories.
* **Cross-study comparability** through overlap with established
  neuroimaging image sets, especially NSD and THINGS / THINGSplus.
* **Evaluation of generalization** through predefined train/test
  splits and a shared OOD image set.

The resulting dataset has no designed semantic category taxonomy.
Coverage is driven by feature-space diversity, and category-like
metadata should be treated as derived annotations rather than as the
sampling frame.

Source Pools
============

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Source
     - Role
     - Notes
   * - LAION-natural
     - Main source pool
     - Natural photographs selected to cover CLIP feature space broadly.
   * - NSD
     - Shared comparison set
     - Supports comparison with the Natural Scenes Dataset.
   * - THINGS / THINGSplus
     - Object-image comparison set
     - Supports comparison with THINGS and THINGS-data EEG + fMRI.
   * - OOD
     - Held-out stress test
     - Visual illusions, Gabor patches, shapes, cropped textures,
       unusual configurations, self-made images, and high-saturation
       patterns.

Selection Procedure
===================

The LAION-derived images were selected in two stages.

First, a large LAION-natural sample was embedded with CLIP, reduced
with PCA, and clustered. Candidate images were then chosen to maximize
the effective dimensionality of the selected set, encouraging broad
coverage of independent axes in visual-semantic feature space.

Second, visually similar alternatives were retrieved around each
selected prototype using approximate nearest-neighbour search. These
candidate pools made it possible to replace rejected images while
preserving the same broad feature-space coverage.

Images assigned to the shared set were the feature-space slots chosen
for repeated measurement in every participant; the remaining accepted
prototype-centred pools supplied the unique set by contributing one
quality-approved, non-overlapping candidate image per participant.

NSD and THINGSplus images were integrated by assigning them to nearby
LAION feature-space slots. When an NSD or THINGSplus image filled a
slot, it replaced the corresponding LAION shared image so that the
shared set size stayed fixed while gaining cross-study overlap.

Manual Screening
================

Candidate images were reviewed in a custom web interface. Reviewers
accepted clear natural photographs and rejected images with applied
filters, illustrations, graphic-design content, severe quality
problems, or not-safe-for-work content. Candidate pools likely to
contain NSFW material were flagged before manual review using an
automated caption-based screen.

If a prototype pool did not have enough accepted images for all
participants, additional neighbours or newly selected LAION-natural
candidates were reviewed and added.

Final Counts
============

.. list-table:: Shared set (1,492 images viewed by every participant)
   :widths: 35 25 40
   :header-rows: 1

   * - Source
     - Count
     - Repetitions
   * - LAION-natural
     - 641
     - 12
   * - THINGSplus
     - 240
     - 12
   * - NSD
     - 240
     - 4
   * - OOD
     - 371
     - 4

Each participant additionally viewed 4,712 subject-unique images:
4,246 from LAION-natural, 144 from THINGS, and 322 from
THINGSplus. Across all five participants, this yields 25,052
distinct launch-release images.

See :doc:`stimulus_data` for file formats, metadata fields, and
loading examples. See :doc:`train_test_splits` for the predefined
evaluation splits.

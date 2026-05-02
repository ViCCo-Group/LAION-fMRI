===================
Stimulus Selection
===================

How the visual stimuli for the LAION-fMRI dataset were selected and curated.

Stimuli for LAION-fMRI were explicitly designed to maximise visual-semantic
diversity and coverage of the natural image space. Rather than drawing from
a single existing dataset, the majority of stimuli were selected from
LAION-natural using an effective-dimensionality optimisation procedure that
promotes uniform coverage of the CLIP feature space, supplemented by images
from NSD and THINGS+ for cross-study comparability. The resulting stimulus
set comprises 25,052 distinct images across the five participants, with
1,492 shared stimuli enabling cross-participant analyses.

Source Pool
===========

The experimental design required two classes of stimuli: a *shared set*
presented identically to all participants — enabling cross-participant
comparison and noise-ceiling estimation through repeated presentations —
and a *unique set* assigned per participant to maximise the total number of
distinct images sampled across the experiment. Both classes needed to broadly
and uniformly cover the space of natural images, depicting scenes, objects,
and events rather than synthetic graphics or other non-photographic content.

The majority of stimuli were drawn from LAION-natural, a curated subset of
approximately 120 million natural photographs filtered from LAION-2B (see
:doc:`stimulus_data`). To anchor the stimulus set in well-characterised
existing datasets and enable cross-study comparisons, we additionally
incorporated images from the Natural Scenes Dataset (NSD; Allen et al., 2022)
and from two related object-image databases: THINGS, a collection of 1,854
object concepts with over 26,000 naturalistic images (Hebart et al., 2019),
and THINGS+, an extension that provides additional metadata and one
copyright-free (CC0) image per concept (Stoinski et al., 2024).

Selection Criteria
==================

Diversity-optimised selection
-----------------------------

From LAION-natural, we drew a random subset of approximately 10 million
images, reduced their CLIP ViT-L/14 visual embeddings to 323 dimensions via
incremental PCA, and applied mini-batch :math:`K`-means
(:math:`k = 1{,}121`) to partition the reduced feature space. The selected
set was initialised with the image nearest each centroid (1,121 seeds) and
then expanded over 4,378 greedy steps to maximise the effective
dimensionality (ED) of the set's feature covariance, defined as the
participation ratio of the eigenspectrum:

.. math::

   \mathrm{ED} = \frac{\left(\sum_i \lambda_i\right)^2}{\sum_i \lambda_i^2},

where :math:`\lambda_i` are the eigenvalues of the covariance matrix over
the PCA-reduced representations. At each step, 10 candidates were drawn per
:math:`K`-means cluster (~11,210 total); candidates within Euclidean
distance 0.1 of any already-selected image in the PCA-reduced space were
discarded to enforce diversity, and the candidate yielding the largest ED
gain (estimated via rank-1 updates to the running mean and covariance) was
appended. This produced a set of 5,499 diversity-optimised images spanning
the feature space as broadly as possible. We refer to each of these 5,499
images as a *prototype* in the following.

Candidate retrieval
-------------------

Because the experimental design required multiple images per region of the
feature space (one shared stimulus plus one unique stimulus per
participant), we next retrieved visually similar alternatives for each
prototype. We built an approximate nearest-neighbour index (Annoy; 50 trees,
Euclidean metric) over up to 100 million LAION-natural images in the
original (non-PCA-reduced) CLIP embedding space, and retrieved the 200
nearest neighbours for each of the 5,499 prototypes. Near-exact duplicates
(pairwise distance ``< 0.01`` in the original embedding space) were removed.
Note that this deduplication threshold is not directly comparable to the
0.1 threshold used during ED selection, as the two operate in different
feature spaces: the former in the original CLIP embedding space, the latter
in PCA-reduced space. From the resulting neighbour lists, up to the 25
closest candidates per prototype were written out as image pools for manual
quality review (see :ref:`stim-screening`); the remaining ~175 neighbours
were held in reserve for later supplementation if needed.

Integrating NSD and THINGS+
---------------------------

To incorporate stimuli from established neuroimaging datasets without
changing the size or overall coverage of the shared set, we treated the
1,121 LAION-derived shared representatives as feature-space "slots".
Specifically, we re-clustered the 5,499 LAION prototypes into 1,121 groups
and took the prototype nearest each group centroid as that group's default
shared representative. We then selected 240 THINGS+ representatives and
240 NSD representatives in the same CLIP embedding space and assigned each
of them to the nearest still-unclaimed LAION group. Whenever an NSD or
THINGS+ image was assigned to a group, it replaced the default LAION shared
image for that slot. To keep the total number of stimuli fixed, one LAION
prototype from that group was removed entirely, preferentially choosing
prototypes that were among the original :math:`K`-means seeds or had been
flagged during quality review, thereby retaining the strongest ED-optimised
LAION candidates wherever possible. The remaining LAION prototypes in those
groups stayed available for participant-specific unique-image selection.
After excluding rejected images and replacing any rejected LAION shared
representatives with the nearest acceptable alternatives, the final non-OOD
shared set comprised 641 LAION images, 240 NSD images, and 240 THINGS+
images (1,121 total; OOD additions are described in
:ref:`stim-final-set`).

Category Structure
==================

The stimulus set has no designed semantic category taxonomy. Coverage is
driven entirely by the diversity-optimisation procedure described above,
which targets uniform spread in CLIP feature space rather than balanced
sampling of pre-defined categories. The only structural partitioning is
between the cross-participant *shared set* and the per-participant *unique
sets* (see :doc:`experimental_design` for repetition counts and
:doc:`train_test_splits` for how stimuli are partitioned for model
training and evaluation). For derived semantic and category-style
metadata, see :doc:`metadata_acquisition`.

.. _stim-screening:

Stimulus Screening
==================

Manual quality review
---------------------

All candidate images (the 25 nearest-neighbour candidates for each of the
5,499 prototype-centred pools, totalling approximately 137,500 images)
underwent manual quality review via a custom web-based labelling
interface. For each pool, reviewers inspected the prototype image
(displayed as the main image) alongside its 24 nearest-neighbour candidates
and made binary accept/reject decisions for each image. Acceptance criteria
required that images were clear and in focus, free of applied filters, and
depicted actual photographs of scenes or objects rather than illustrations
or graphic designs. Images originating from copyright-free hosting sites
(identified by matching source URLs against a curated list) were
highlighted in the interface and preferred where available, though this
was a soft preference rather than a hard constraint. Pre-computed square
crops for each image were also displayed and could be adjusted by the
reviewer to avoid occluding salient content. Pools likely to contain
not-safe-for-work content were pre-screened automatically using the
``qiuhuachuan/NSFW-detector`` text-classification model on candidate
captions; pools with more than 10 flagged captions were presented to
reviewers with a warning.

Supplementation of underfilled pools
------------------------------------

After quality filtering, some of the 4,378 unique-designated prototype
pools had fewer than five surviving candidates. Because each such pool
needed to contribute one image per participant (five participants in
total), these underfilled pools required supplementation. For these pools,
we first retrieved additional candidates from deeper in the existing
nearest-neighbour lists (beyond the initial 25 images per pool used during
quality review, drawing from the remaining ~175 neighbours retrieved in
the earlier Annoy step). We also ran two further rounds of ED optimisation
on fresh LAION-natural samples to add candidate pools in undercovered
regions of the feature space: the first round drew from a new
10-million-image sample and added 1,200 prototypes; the second added 500
more. Each newly selected prototype received its own nearest-neighbour
retrieval (200 neighbours, deduplicated as before), establishing new
candidate pools. These supplementary pools underwent the same quality
review process. After all exclusions and supplementation, the final
LAION-derived set comprised 641 shared LAION prototypes and 4,246 unique
LAION images per participant.

.. _stim-final-set:

Final Stimulus Set
==================

The 1,121 shared prototypes (641 LAION, 240 NSD, 240 THINGS+) each
contributed a single shared stimulus. For the unique set, each of the
remaining LAION prototype pools contributed one image per participant:
from the quality-approved candidates in each pool, five images were
selected (one per participant), prioritising candidates from the original
quality review round over those added during supplementation. Unique
LAION images were assigned as participant-specific, non-overlapping sets.

In addition to the LAION-derived stimuli, each participant received 144
unique THINGS images (from the original THINGS database) and 322 unique
THINGS+ images (from the CC0 extension), assigned as participant-specific,
non-overlapping sets. The shared set was further supplemented with 371
out-of-distribution (OOD) images — including visual illusions, Gabor
patches, unusual spatial configurations, cropped textures, shape stimuli,
and gaudy patterns — which were added independently of the LAION
selection pipeline.

In total, the shared set comprised:

.. list-table::
   :widths: 40 30 30
   :header-rows: 1

   * - Source
     - Count
     - Repetitions
   * - LAION
     - 641
     - 12
   * - THINGS+
     - 240
     - 12
   * - NSD
     - 240
     - 4
   * - OOD
     - 371
     - 4
   * - **Total shared**
     - **1,492**
     -

Each participant additionally viewed 4,712 unique stimuli (4,246 LAION +
144 THINGS + 322 THINGS+), yielding 6,204 stimuli per participant. Across
all five participants, the experiment encompassed 25,052 distinct images.
All images were resized to 1,000 × 1,000 pixels and stored in HDF5 format.

See :doc:`stimulus_data` for the full stimulus set, metadata fields, and
loading examples. See :doc:`train_test_splits` for how images are
partitioned for model training and evaluation.

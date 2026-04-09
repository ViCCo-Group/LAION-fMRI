===================
Stimulus Selection
===================

How the visual stimuli for the LAION-fMRI dataset were selected and curated.

.. todo::

   Introductory narrative (2-3 sentences): What was the high-level goal of
   the stimulus set? Large-scale and naturalistic? Maximally diverse? How many
   images total, and why that number? Link to the dataset paper for full details.

Source Pool
===========

.. todo::

   Where did the candidate images come from (LAION-5B subset, COCO, ImageNet,
   other)? How large was the initial pool before filtering? Were multiple
   sources combined?

Selection Criteria
==================

.. todo::

   What properties were optimized or controlled for? Consider:

   - Semantic diversity (categories, scene types, object counts)
   - Visual properties (resolution, aspect ratio, luminance, contrast)
   - Automated filters (minimum resolution, NSFW filtering, deduplication)
   - Was any embedding-space sampling used (e.g., CLIP-based)?

Category Structure
==================

.. todo::

   Is there a designed category taxonomy, or is the set intentionally
   unconstrained / naturalistic? If there are categories, describe the
   hierarchy and how balanced they are. If not, say so explicitly — users
   will want to know.

Stimulus Screening
==================

.. todo::

   How were stimuli screened? Human inspection, automated checks, or both?
   Were any images removed post-selection (e.g., duplicates, inappropriate
   content, low quality)?

Final Stimulus Set
==================

See :doc:`stimulus_data` for the full stimulus set, metadata fields, and
loading examples. See :doc:`train_test_splits` for how images are partitioned
for model training and evaluation.

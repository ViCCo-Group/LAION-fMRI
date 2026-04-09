===================
Train / Test Splits
===================

.. todo::

   Introductory narrative (2-3 sentences): Why are predefined splits
   provided? What aspects of generalization do they test? How central are
   they to the challenge / benchmark use case?

.. todo::

   Add a visual overview figure showing the split strategy (e.g., a diagram
   illustrating which stimuli go to train vs test for each split type, or
   an embedding-space visualization showing how splits partition the data).

.. figure:: _static/placeholder_splits_overview.png
   :align: center
   :width: 80%
   :alt: Overview of train/test split strategy

   Overview of the train/test split strategy. *(placeholder — replace with
   actual figure)*

Available Splits
================

.. todo::

   For each split, write a brief description (2-3 sentences) covering the
   rationale, how many stimuli in train vs test, and expected use case.
   Use subsections rather than a table — easier to read and allows for
   figures per split.

Split 1: (placeholder)
-----------------------

.. todo::

   Name, description, rationale, train/test counts.

Split 2: (placeholder)
-----------------------

.. todo::

   Same as above. Add more subsections as needed.

Split Definitions
=================

.. todo::

   For each split, document precisely:

   - Where the split assignments live (column in ``stimuli.tsv``? separate
     file?)
   - How stimulus IDs map to train/test labels
   - Any stratification or balancing applied

Shared Stimuli
==============

.. todo::

   Are there stimuli shown to all participants (for cross-subject analyses,
   noise ceiling estimation, etc.)? If so, how many, and how are they
   identified?

Loading Split Information
=========================

.. todo::

   Provide minimal code examples once the split format is finalized.
   Cross-reference :doc:`stimulus_data` for stimulus metadata and
   :doc:`glmsingle_betas` for mapping splits to beta indices.

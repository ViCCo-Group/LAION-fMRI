====================
Metadata Acquisition
====================

.. todo::

   Introductory narrative (2-3 sentences): What metadata was collected or
   computed for the stimuli beyond basic image properties? Why is this
   metadata useful (e.g., for controlling confounds, building feature spaces,
   analyzing category structure)?

Image-level Metadata
====================

.. todo::

   Document all metadata fields that were collected or computed per image.
   For each field or group of fields, describe:

   - What it is and how it was obtained (manual annotation, automated tool,
     model extraction, database lookup)
   - Software / model / API used (with version)
   - Units or value range

   Candidate metadata categories to cover:

Low-level Visual Properties
---------------------------

.. todo::

   E.g., luminance, contrast, spatial frequency, color statistics.
   How were these computed? Which tool or script?

Semantic Annotations
--------------------

.. todo::

   E.g., object categories, scene types, number of objects, animacy.
   Were these human-annotated, from an existing dataset (COCO, ImageNet
   labels), or model-derived?

Model-derived Features
----------------------

.. todo::

   E.g., CLIP embeddings, DNN feature vectors, caption embeddings.
   Which models and layers? How are they stored (separate files, columns in
   stimuli.tsv)?

Other Metadata
--------------

.. todo::

   Any other metadata: image source/provenance, licensing info per image,
   NSFW scores, aesthetic scores, etc.

Metadata File Format
====================

.. todo::

   Where does the metadata live? Is it all in ``stimuli/stimuli.tsv``, or
   are there separate files for different metadata types (e.g., embeddings
   as .npy)? Document file paths and formats.

   Cross-reference :doc:`stimulus_data` for the full stimulus file
   organization.

====
ROIs
====

.. todo::

   Introductory narrative (2-3 sentences): What ROIs are provided and why?
   Are they intended for most users, or only for ROI-based analyses?

.. todo::

   Add an overview figure showing all ROI sets on a brain (e.g., glass brain
   or inflated surface with ROIs color-coded by set).

.. figure:: _static/placeholder_rois_overview.png
   :align: center
   :width: 80%
   :alt: Overview of all ROI sets

   Overview of all available ROI sets on an example subject. *(placeholder —
   replace with actual figure)*

Available ROI Sets
==================

.. todo::

   For each ROI set below, write a short description (2-3 sentences) covering
   what it is, how it was defined, and when a user would use it.
   Add or remove subsections as needed. Cross-reference the source page where
   applicable.

Atlas-based ROIs
----------------

.. todo::

   Which atlas-based ROIs are provided (e.g., Glasser parcellation, DKT,
   Schaefer)? Brief description of each, which regions are included, and a
   figure.

.. figure:: _static/placeholder_atlas_rois.png
   :align: center
   :width: 70%
   :alt: Atlas-based ROI parcellation

   Atlas-based ROI parcellation. *(placeholder — replace with actual figure)*

Retinotopy-derived ROIs
------------------------

.. todo::

   Which visual area ROIs come from retinotopic mapping (V1, V2, V3, ...)?
   Brief description + figure showing them on a flatmap or inflated surface.
   Cross-reference :doc:`retinotopy`.

.. figure:: _static/placeholder_retino_rois.png
   :align: center
   :width: 70%
   :alt: Retinotopy-derived visual area ROIs

   Retinotopy-derived visual area ROIs on an inflated surface.
   *(placeholder — replace with actual figure)*

Localizer-derived ROIs
-----------------------

.. todo::

   Which category-selective ROIs come from localizers (FFA, PPA, EBA, ...)?
   Brief description of how they were defined (individual thresholding, etc.)
   + figure. Cross-reference :doc:`localizers`.

.. figure:: _static/placeholder_localizer_rois.png
   :align: center
   :width: 70%
   :alt: Localizer-derived category-selective ROIs

   Localizer-derived category-selective ROIs. *(placeholder — replace with
   actual figure)*

Available Spaces
================

.. todo::

   Which spaces are the ROI masks provided in? Are all ROI sets available in
   all spaces, or only some?

File Organization
=================

.. todo::

   Paste the actual file tree from ``derivatives/rois/``.

.. code-block:: text

    derivatives/rois/
    └── ... (placeholder — fill with actual file listing)

Loading ROIs
============

.. todo::

   Provide minimal code examples once file paths and naming are finalized.
   Show how to load an ROI mask and apply it to beta estimates
   (cross-ref :doc:`glmsingle_betas`).

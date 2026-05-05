:orphan:

===========
Retinotopy
===========

.. todo::

   Introductory narrative (2-3 sentences): Were retinotopic mapping
   experiments conducted? What is provided — pRF parameter maps, visual area
   definitions, or both?

   For the retinotopy experimental paradigm, see :doc:`experimental_design`.

.. todo::

   Add an overview figure showing example pRF maps (polar angle +
   eccentricity) on a flatmap or inflated surface for one subject.

.. figure:: _static/placeholder_retinotopy_maps.png
   :align: center
   :width: 80%
   :alt: Example retinotopic maps

   Polar angle and eccentricity maps on an example subject. *(placeholder —
   replace with actual figure)*

pRF Modeling
============

.. todo::

   Document:

   - Software and version used for pRF fitting
   - pRF model type (e.g., isotropic Gaussian, CSS)
   - Input data (preprocessed BOLD from which space?)
   - Any non-default parameters or preprocessing specific to retinotopy

pRF Maps
========

.. todo::

   List all pRF output maps provided. For each, briefly describe what it
   represents, its units/range, and what it looks like. Include a figure
   for each map type if possible, or a combined multi-panel figure.

The following maps are provided per subject:

- **Polar angle** — (placeholder)
- **Eccentricity** — (placeholder)
- **pRF size** — (placeholder)
- **R-squared** — (placeholder)
- *(add or remove as needed)*

Visual Area Definitions
========================

.. todo::

   Which visual areas are delineated (V1, V2, V3, ...)?  How were
   boundaries drawn (automatic, manual, threshold-based)?
   Add a figure showing visual area boundaries.

.. figure:: _static/placeholder_visual_areas.png
   :align: center
   :width: 70%
   :alt: Visual area boundary definitions

   Visual area boundaries derived from retinotopic mapping. *(placeholder —
   replace with actual figure)*

These ROI definitions are also available under ``derivatives/rois/`` — see
:doc:`rois`.

File Organization
=================

.. todo::

   Paste the actual file tree from ``derivatives/retinotopy/sub-XX/``.

.. code-block:: text

    derivatives/retinotopy/
    └── sub-XX/
        └── ... (placeholder — fill with actual file listing)

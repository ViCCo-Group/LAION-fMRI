====
ROIs
====

.. only:: live

   *Full ROI documentation will be added with the final release.* In the
   meantime, the :doc:`load API <laion_fmri_package/load>` documents how
   to load ROI masks and apply them to single-trial betas
   (``sub.get_betas(roi="FFA1")``, category filters like ``"face"``,
   surface and FreeSurfer-label loading, etc.).

.. only:: dev

   .. todo::

      Introductory narrative (2-3 sentences): What ROIs are provided and why?
      Are they intended for most users, or only for ROI-based analyses?

   .. todo::

      Add an overview figure showing all ROI sets on a brain (e.g., glass brain
      or inflated surface with ROIs color-coded by set).

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

   Retinotopy-derived ROIs
   ------------------------

   .. todo::

      Which visual area ROIs come from retinotopic mapping (V1, V2, V3, ...)?
      Brief description + figure showing them on a flatmap or inflated surface.
      Cross-reference :doc:`retinotopy`.

   Localizer-derived ROIs
   -----------------------

   .. todo::

      Which category-selective ROIs come from localizers (FFA, PPA, EBA, ...)?
      Brief description of how they were defined (individual thresholding, etc.)
      + figure. Cross-reference :doc:`localizers`.

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

===============
Anatomical Data
===============

.. todo::

   Introductory narrative (1-2 sentences): What structural data is provided
   (raw T1w, FreeSurfer outputs, tissue segmentations)? How many T1w scans
   per subject — were they averaged?

For acquisition parameters, see :doc:`mri_acquisition`.

T1-weighted Images
==================

.. todo::

   Paste the actual file tree for a representative subject's ``anat/``
   directory.

.. code-block:: text

    sub-XX/
    └── anat/
        └── ... (placeholder — fill with actual file listing)

FreeSurfer Reconstructions
==========================

.. todo::

   Document:

   - FreeSurfer version used
   - Which outputs are actually shipped (not every FS output needs to be
     distributed — list what's included)
   - Paste the actual file tree from ``derivatives/freesurfer/sub-XX/``

.. code-block:: text

    derivatives/freesurfer/
    └── sub-XX/
        └── ... (placeholder — fill with actual file listing)

Tissue Segmentations
====================

.. todo::

   Document:

   - What tissue maps are provided (GM, WM, CSF probability maps)?
   - Which spaces are they available in?
   - Are transformation files (e.g., T1w-to-MNI warps) included?
   - Paste the actual file tree from ``derivatives/fmriprep/sub-XX/anat/``

.. code-block:: text

    derivatives/fmriprep/
    └── sub-XX/
        └── anat/
            └── ... (placeholder — fill with actual file listing)

Loading Anatomical Data
=======================

.. todo::

   Provide minimal code examples once file paths are finalized.

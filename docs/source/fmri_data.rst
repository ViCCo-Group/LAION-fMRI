=========
fMRI Data
=========

.. todo::

   Introductory narrative (2-3 sentences): What functional data is provided
   (raw + preprocessed), how many runs/sessions per subject, and what task(s).

For acquisition parameters, see :doc:`mri_acquisition`. For preprocessing
details, see :doc:`preprocessing`.

.. todo::

   Add a figure showing example raw vs preprocessed BOLD data (e.g.,
   a single slice before and after preprocessing, or a carpet plot).

.. figure:: _static/placeholder_bold_example.png
   :align: center
   :width: 80%
   :alt: Example BOLD data

   Example raw and preprocessed BOLD data for one subject. *(placeholder —
   replace with actual figure)*

Raw Functional Data
===================

.. todo::

   Brief narrative: What's in the raw data? How many runs per session, how
   many sessions? Were any runs excluded, and if so, is there a list?

File Organization
-----------------

.. todo::

   Paste the actual file tree for a representative subject. Include all
   task labels, run numbers, and associated files (BOLD, events, JSON
   sidecars).

.. code-block:: text

    sub-XX/
    └── func/
        └── ... (placeholder — fill with actual file listing)

Preprocessed Functional Data
=============================

.. todo::

   Brief narrative: Which pipeline produced these, what's the key output
   users should grab? Cross-ref :doc:`preprocessing` for pipeline details.

File Organization
-----------------

.. todo::

   Paste the actual file tree from ``derivatives/fmriprep/sub-XX/func/``.

.. code-block:: text

    derivatives/fmriprep/
    └── sub-XX/
        └── func/
            └── ... (placeholder — fill with actual file listing)

Available Spaces
----------------

.. todo::

   List the output spaces the preprocessed data is available in and the
   resolution for each.

Confounds
---------

.. todo::

   Document the confound columns available in the confounds TSV. Which
   columns are included? Are there recommended confound strategies, or do
   you leave that to the user?

Loading Functional Data
=======================

.. todo::

   Provide minimal, correct code examples for loading raw and preprocessed
   data. Only add once file paths are finalized.

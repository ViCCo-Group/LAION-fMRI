===========
Data Access
===========

.. todo::

   Introductory narrative (2-3 sentences): Where is the data hosted, what
   are the access options, and is any part restricted?

   **Note:** This page overlaps with :doc:`quickstart`. Consider whether they
   should be merged or clearly differentiated (quickstart = minimal getting
   started, this page = comprehensive reference for all access options).

Access Requirements
===================

.. todo::

   Document:

   - Is there a Data Use Agreement (DUA)? If so, what does it cover?
   - Is any part of the data restricted (e.g., raw anatomical scans)?
   - Where / how do users register for access?
   - What are the terms of use (research only, citation required, etc.)?

Download Methods
================

.. todo::

   Document all supported download methods. For each one:

   - Prerequisites (tools, credentials)
   - Commands to download full dataset, single subject, derivatives only,
     stimuli only
   - How to handle authentication for restricted data

   Candidate methods to document:

   - AWS S3 (with ``aws s3 sync``)
   - Python package (if ``laion-fmri-dataloader`` has a stable API)
   - Direct HTTP / other

Dataset Size
============

.. todo::

   Document:

   - Total dataset size
   - Size per subject (approximate)
   - Size of major components (raw, derivatives, stimuli)
   - Storage recommendations

Data Verification
=================

.. todo::

   Is there a checksum file or verification script? How can users confirm
   their download is complete and uncorrupted?

Software Requirements
=====================

.. todo::

   What software do users need to work with the data? Minimum list:

   - Python version
   - Key packages (nibabel, pandas, etc.)
   - Any dataset-specific package

Citation
========

.. todo::

   Add the full citation once the paper is published. Include BibTeX.

Support
=======

For data access issues or questions:

* `Open an issue on GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`_
* Check the :doc:`faq` for common questions

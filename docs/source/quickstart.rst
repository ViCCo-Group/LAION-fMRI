==========
Quickstart
==========

This guide will help you get started with the LAION-fMRI dataset quickly.

.. todo::

   This page should be written once the data access method and file paths are
   finalized. It should give a user the shortest path from "I have nothing"
   to "I'm looking at data in Python." Keep it under 5 minutes of reading.

   **Avoid duplicating** :doc:`data_access` — this page should be brief and
   link there for details.

Getting the Data
================

.. todo::

   Minimal download instructions — just enough to get one subject's betas
   and stimuli. Point to :doc:`data_access` for full options (all subjects,
   raw data, etc.).

   Decide: is the primary access method AWS S3, a Python package, or
   something else? Show only one method here; put alternatives in
   :doc:`data_access`.

Loading Betas and Stimuli
=========================

.. todo::

   A single, minimal code example that:

   1. Loads single-trial betas for one subject
   2. Loads the stimulus metadata
   3. Shows how they map to each other

   This should use correct file paths and column names — do not add until
   those are finalized.

Next Steps
==========

* :doc:`dataset_at_a_glance` — full dataset overview and "what files do I need"
* :doc:`glmsingle_betas` — details on the beta estimates
* :doc:`stimulus_data` — stimulus images and metadata
* :doc:`train_test_splits` — train/test partitioning
* :doc:`faq` — common questions

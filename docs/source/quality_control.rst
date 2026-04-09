===============
Quality Control
===============

.. todo::

   Introductory narrative (2-3 sentences): What QC was performed on the
   LAION-fMRI dataset, at what stages, and what was the overall goal
   (ensure data quality, identify exclusions, document known issues)?

Raw Data QC (MRIQC)
===================

.. todo::

   Document:

   - MRIQC version used
   - Which image quality metrics were computed (tSNR, FD, SNR, etc.)
   - Where are the per-subject reports stored (``derivatives/mriqc/``)?
   - Add example screenshots or summary figures

.. figure:: _static/placeholder_mriqc_summary.png
   :align: center
   :width: 80%
   :alt: MRIQC summary metrics

   Summary of MRIQC image quality metrics across subjects. *(placeholder —
   replace with actual figure)*

Motion & Exclusion Criteria
===========================

.. todo::

   Document:

   - What thresholds were used for exclusion (FD, DVARS, tSNR, etc.)?
   - Were decisions made per-run, per-session, or per-subject?
   - How many runs/subjects were excluded, and is there a list?
   - Add a figure showing the distribution of motion across subjects/runs

.. figure:: _static/placeholder_motion_distribution.png
   :align: center
   :width: 70%
   :alt: Distribution of framewise displacement

   Distribution of mean framewise displacement across subjects and runs.
   *(placeholder — replace with actual figure)*

Behavioral QC
=============

.. todo::

   Document:

   - Were behavioral performance thresholds applied (e.g., minimum accuracy)?
   - How were non-compliant runs identified (low accuracy, missed responses)?
   - See :doc:`experimental_design` for the behavioral task details

Anatomical QC
=============

.. todo::

   Document:

   - Was manual inspection of T1w scans performed?
   - Were FreeSurfer surface reconstructions visually checked?
   - Were any subjects excluded due to anatomical issues?

Beta Estimate Quality
=====================

.. todo::

   Document:

   - Were GLMsingle noise ceilings or R2 maps used for QC?
   - Any per-voxel or per-subject quality thresholds?
   - Cross-reference :doc:`glmsingle_betas` for noise ceiling details

.. figure:: _static/placeholder_beta_quality.png
   :align: center
   :width: 70%
   :alt: Beta estimate quality summary

   Summary of single-trial beta quality (e.g., noise ceilings, R2) across
   subjects. *(placeholder — replace with actual figure)*

Known Issues
============

.. todo::

   Document any known data quality issues, quirks, or caveats that users
   should be aware of (e.g., specific subjects with partial data, scanner
   artifacts in certain sessions, etc.).

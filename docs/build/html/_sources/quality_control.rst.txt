===============
Quality Control
===============

Quality control procedures for the LAION-fMRI dataset.

Overview
========

Quality control (QC) ensures data integrity and identifies potential issues before analysis. 
All data undergoes both automated and manual QC procedures.

MRIQC
=====



Visual Inspection
=================



QC Reports
==========

Automated Report Generation
----------------------------

QC reports are generated for each subject and run:

.. code-block:: text

    derivatives/mriqc/
    └── sub-01/
        



QC Thresholds
=============

Recommended Exclusion Criteria
-------------------------------

**Motion-based exclusion:**

* Mean FD > 0.5 mm
* Maximum FD > 3.0 mm
* More than 20% of volumes with FD > 0.5 mm

**Signal quality exclusion:**

* Mean tSNR < 50
* Excessive signal dropout (> 5% of volumes)
* Poor anatomical-functional registration

**Behavioral exclusion:**

* Accuracy < 60%
* Miss rate > 20%
* No responses recorded

THIS COULD BE SUPPORTED BY THE PACKAGE.

Group-Level QC
==============

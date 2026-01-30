===============
Structural Data
===============

High-resolution anatomical MRI scans in the LAION-fMRI dataset.

Overview
========

The dataset includes high-resolution structural MRI scans for anatomical reference and 
normalization of functional data.

Anatomical Scans
================

T1-weighted Images
------------------

**Acquisition Parameters:**

* **Sequence**: 3D T1-weighted MPRAGE (Magnetization Prepared Rapid Gradient Echo)
* **Field strength**: 3 Tesla
* **Resolution**: 1mm isotropic (1x1x1 mm³)
* **Matrix size**: 256 x 256 x 176 (or similar)
* **TE (Echo Time)**: ~3.0 ms
* **TR (Repetition Time)**: ~2300 ms
* **TI (Inversion Time)**: ~900 ms
* **Flip angle**: 9°

**Image Characteristics:**

* Excellent gray/white matter contrast
* Full brain coverage
* Suitable for segmentation and surface reconstruction

File Organization
=================

Structural data location:

.. code-block:: text

    sub-01/
    └── anat/
        ├── sub-01_T1w.nii.gz              # T1-weighted anatomical image
        └── sub-01_T1w.json                # Acquisition parameters

Example JSON Metadata
---------------------

.. code-block:: json

    {
        "Modality": "MR",
        "MagneticFieldStrength": 3,
        "Manufacturer": "Siemens",
        "ManufacturersModelName": "Prisma",
        "SequenceName": "MPRAGE",
        "RepetitionTime": 2.3,
        "EchoTime": 0.003,
        "InversionTime": 0.9,
        "FlipAngle": 9,
        "PixelBandwidth": 200,
        "SliceThickness": 1.0,
        "VoxelSize": [1.0, 1.0, 1.0]
    }


Additional Structural Scans
============================

T2-weighted (if available)
---------------------------

Some datasets may include T2-weighted images for additional contrast:

.. code-block:: text

    sub-01/
    └── anat/
        ├── sub-01_T2w.nii.gz
        └── sub-01_T2w.json

FLAIR (if available)
---------------------


.. code-block:: text

    sub-01/
    └── anat/
        ├── sub-01_FLAIR.nii.gz
        └── sub-01_FLAIR.json

Using Structural Data
=====================


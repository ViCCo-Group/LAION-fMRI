===========
Data Access
===========

LAION-fMRI is hosted in an AWS S3 bucket sponsored by the AWS Open Data
program:

* The **fMRI data, derivatives, dataset metadata, and stimulus-derived
  annotations** are released openly under **CC0 1.0** and can be
  downloaded anonymously. These files include stimulus metadata, captions,
  pretrained embeddings, and object segmentations.
* The **raw stimulus image HDF5** comes from third-party web sources and
  requires accepting a short **Data Use Agreement**.

The :doc:`laion_fmri_package/index` Python package handles both
download paths transparently. For a quick orientation see
:doc:`quickstart`; this page is the full reference.


Access Requirements
===================

CC0 fMRI data
-------------

The package shows the CC0 license once on the first ``download(...)`` call and writes a marker file so subsequent calls don't re-prompt.

Stimulus images
---------------------

The stimulus images require accepting a Data Use Agreement that prohibits
redistribution, commercial use, and use for training general-purpose AI
models. You accept it by submitting a short form (terminal or web).

The form asks for your name, institutional email, institution, optional
PI/supervisor, a short research-purpose description, Terms acceptance,
and Privacy-notice acknowledgement.

Download Methods
================

Python package (recommended)
----------------------------

The :mod:`laion_fmri` package handles both the public S3 mirror and the
stimulus service. Until the PyPI package is published, install directly
from GitHub:

.. code-block:: bash

   python -m pip install "laion-fmri @ git+https://github.com/ViCCo-Group/LAION-fMRI.git@main"

Common operations:

.. code-block:: python

   from laion_fmri.download import download, download_stimuli

   # fMRI for one subject
   download(subject="sub-01")

   # one session, parallel transfer
   download(subject="sub-01", ses="ses-04", n_jobs=4)

   # all subjects (whole-dataset mirror)
   download(subject="all")

   # stimuli — dataset-wide, subject-independent, requires accepting the DUA
   download_stimuli()

   # both at once
   download(subject="sub-01", include_stimuli=True)

CLI equivalents:

.. code-block:: bash

   mkdir -p ./laion_fmri_data
   laion-fmri config --data-dir ./laion_fmri_data
   laion-fmri download --subject sub-01
   laion-fmri download-stimuli
   laion-fmri request-access            # standalone DUA form, no download

Direct AWS CLI (public files only)
----------------------------------

You can also use the AWS CLI directly.
The public prefixes are read-accessible without credentials:

.. code-block:: bash

   aws s3 sync --no-sign-request \
       s3://laion-fmri/derivatives/glmsingle-tedana/sub-01/ ./sub-01/

This skips the package's BIDS-entity filtering and idempotency checks,
but is useful if you want raw control over what's transferred.

The raw image archive
``s3://laion-fmri/stimuli/task-images_stimuli.h5`` is **not**
accessible this way. Use the package or the web form for that file.
The public stimulus metadata, captions, embeddings, and segmentations
can be fetched anonymously.

Web form (no Python required)
-----------------------------

For browser users who'd rather not install the Python package, the same
DUA form is available at:

  https://laion-fmri.hebartlab.com/request

The confirmation page shows the presigned download URLs directly; fetch
them with ``curl`` / ``wget`` or by clicking. URLs are valid for one
hour.

Data Verification
=================

* **fMRI data**: the package checks each file's local size against the
  S3 size before re-fetching; ``download(...)`` is idempotent.
* **stimuli**: download is verified against a published
  ``sha256`` for both files (the manifest is served at
  https://laion-fmri.hebartlab.com/api/v1/manifest). On mismatch the
  ``.part`` file is removed and an error is raised.


Software Requirements
=====================

* Python 3.10+
* The ``laion_fmri`` package, installed from GitHub until the PyPI
  distribution is published:
  ``python -m pip install "laion-fmri @ git+https://github.com/ViCCo-Group/LAION-fMRI.git@main"``.
  It pulls in ``numpy``, ``h5py``, ``nibabel``, ``pandas``, ``awscli``,
  and ``Pillow``.
* Raw stimulus-image downloads require the Data Use Agreement flow
  through ``download_stimuli()``, ``laion-fmri download-stimuli``, or
  ``laion-fmri request-access``.


Citation
========

Until the dataset paper is available, cite the VSS 2026 conference
presentation:

   Zerbe, J., Roth, J., Mell, M. M., Herholz, P., Knapen, T., &
   Hebart, M. N. (2026). *LAION-fMRI: A densely sampled 7T-fMRI
   dataset providing broad coverage of natural image diversity*. Talk
   25.11, Scene Perception Talk Session, Vision Sciences Society
   Annual Meeting, May 16, 2026. `VSS abstract
   <https://www.visionsciences.org/talk-sessions?id=642>`__.

Also cite GLMsingle (Prince et al., 2022) if you use the provided
single-trial beta estimates.


Support
=======

For data access issues or questions:

* `Open an issue on GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`_
* For stimulus image takedown, see the contact at
  https://laion-fmri.hebartlab.com/takedown
* Check the :doc:`faq` for common questions

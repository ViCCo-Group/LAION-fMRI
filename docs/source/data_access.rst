===========
Data Access
===========

LAION-fMRI is hosted in an AWS S3 bucket sponsored by the AWS Open Data
program. The dataset has two release tracks with different licensing:

* The **fMRI data, derivatives, and metadata** are released openly under
  **CC0 1.0** and can be downloaded anonymously.
* The **stimulus images** come from third-party web sources and are
  gated by a short **Data Use Agreement**. Acceptance and access go
  through a project-controlled service at
  `laion-fmri.hebartlab.com <https://laion-fmri.hebartlab.com>`__.

The :doc:`laion_fmri_package/index` Python package handles both
download paths transparently. For a quick orientation see
:doc:`quickstart`; this page is the comprehensive reference.


Access Requirements
===================

CC0 fMRI data
-------------

No registration. The package shows the CC0 license once on the first
``download(...)`` call and writes a marker file so subsequent calls
don't re-prompt. Details: :doc:`laion_fmri_package/license`.

Gated stimulus images
---------------------

The stimulus images are subject to a Data Use Agreement that prohibits
redistribution, commercial use, and use for training general-purpose AI
models. You accept it by submitting a short form (terminal or web), at
which point the service issues a ``request_id`` and signs short-lived
S3 URLs for the stimulus archive on demand.

* Read the full terms: https://laion-fmri.hebartlab.com/terms
* Privacy notice: https://laion-fmri.hebartlab.com/privacy
* Takedown policy: https://laion-fmri.hebartlab.com/takedown

The form asks for your name, institutional email, institution, optional
PI/supervisor, and a short research-purpose description. No password,
no email verification, no admin queue — approval is automatic on
submission. Audit metadata is anonymised after one year of inactivity.
Full architectural detail is in :doc:`laion_fmri_package/stimulus_access`.


Download Methods
================

Python package (recommended)
----------------------------

The :mod:`laion_fmri` package handles both the public S3 mirror and the
gated stimulus service. Install via pip / uv:

.. code-block:: bash

   pip install laion_fmri

Common operations:

.. code-block:: python

   from laion_fmri.download import download, download_stimuli

   # fMRI for one subject
   download(subject="sub-01")

   # one session, parallel transfer
   download(subject="sub-01", ses="ses-04", n_jobs=4)

   # all subjects (whole-dataset mirror)
   download(subject="all")

   # gated stimulus archive — dataset-wide, subject-independent
   download_stimuli()

   # both at once
   download(subject="sub-01", include_stimuli=True)

CLI equivalents:

.. code-block:: bash

   laion-fmri config --data-dir ./laion_fmri_data
   laion-fmri download --subject sub-01
   laion-fmri download-stimuli
   laion-fmri request-access            # standalone DUA form, no download
   laion-fmri login --request-id lfm_   # paste an id from the web form
   laion-fmri logout

See :doc:`laion_fmri_package/download` and
:doc:`laion_fmri_package/stimulus_access` for full semantics.

Direct AWS CLI (fMRI only)
--------------------------

For the public CC0 portion, you can also use the AWS CLI directly —
the bucket is public and read-accessible without credentials:

.. code-block:: bash

   aws s3 sync --no-sign-request \
       s3://laion-fmri/derivatives/glmsingle-tedana/sub-01/ ./sub-01/

This skips the package's BIDS-entity filtering and idempotency checks,
but is useful if you want raw control over what's transferred.

The gated stimulus archive is **not** accessible this way — anonymous
``GET`` on ``s3://laion-fmri/stimuli/*`` returns 403. Use the package
or the web form.

Web form (no Python required)
-----------------------------

For browser users who'd rather not install the Python package, the same
DUA form is available at:

  https://laion-fmri.hebartlab.com/request

The confirmation page shows the presigned download URLs directly; fetch
them with ``curl`` / ``wget`` or by clicking. URLs are valid for one
hour. If you also want to wire the ``request_id`` into the loader on
your machine, run ``laion-fmri login --request-id lfm_…`` after.


Dataset Size
============

.. todo::

   Document:

   - Total dataset size
   - Size per subject (approximate)
   - Size of major components (raw, derivatives, stimuli)
   - Storage recommendations

For now: the stimulus archive is one HDF5 of ~3.2 GB plus a ~1.6 MB
metadata CSV.


Data Verification
=================

* **fMRI data**: the package checks each file's local size against the
  S3 size before re-fetching; ``download(...)`` is idempotent.
* **Stimulus archive**: download is verified against a published
  ``sha256`` for both files (the manifest is served at
  https://laion-fmri.hebartlab.com/api/v1/manifest). On mismatch the
  ``.part`` file is removed and an error is raised.


Software Requirements
=====================

* Python 3.10+
* The ``laion_fmri`` package (``pip install laion_fmri``) — pulls in
  ``numpy``, ``h5py``, ``nibabel``, ``pandas``, and the AWS CLI.
* Pillow is optional and only required for decoding stimulus images to
  :class:`PIL.Image` objects (raw JPEG bytes work without it).


Citation
========

.. todo::

   Add the full citation once the paper is published. Include BibTeX.


Support
=======

For data access issues or questions:

* `Open an issue on GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`_
* For stimulus access / takedown, see the contact at
  https://laion-fmri.hebartlab.com/takedown
* Check the :doc:`faq` for common questions

======================
Licenses and Artifacts
======================

LAION-fMRI separates public data from the raw stimulus image archive.

Public CC0 files
================

The fMRI data, derivatives, dataset metadata, and stimulus-derived
annotations are released under CC0 1.0 and can be downloaded
anonymously. The public stimulus-derived files are:

* ``task-images_metadata.csv``
* ``task-images_desc-captions.csv``
* ``task-images_desc-CLIP_embeddings.h5``
* ``task-images_desc-DINOv2_embeddings.h5``
* ``task-images_desc-PEcore_embeddings.h5``
* ``task-images_desc-SigLIP2_embeddings.h5``
* ``task-images_desc-segmentations.h5``
* ``task-images_desc-segmentations_metadata.csv``

The package shows the CC0 license once before the first public download
into a data directory:

.. code-block:: python

   from laion_fmri.download import accept_license

   accept_license()

Raw stimulus images
===================

The raw image archive, ``task-images_stimuli.h5``, comes from
third-party web sources and requires the LAION-fMRI Data Use Agreement.
Request access from the terminal:

.. code-block:: bash

   laion-fmri request-access
   laion-fmri download-stimuli

or use the browser form at https://laion-fmri.hebartlab.com/request.

See :doc:`access` for the full access flow.

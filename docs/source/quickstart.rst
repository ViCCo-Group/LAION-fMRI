==========
Quickstart
==========

Quick introduction to the LAION-fMRI dataset. For the full reference of every download path
and option, see :doc:`data_access`.

Install
=======

.. code-block:: bash

   pip install laion-fmri

Point the package at a local data directory (the place every download
will land):

.. code-block:: bash

   laion-fmri config --data-dir ./laion_fmri_data

Download one subject
====================

This pulls the GLMsingle single-trial betas, noise ceilings, ROI masks,
and per-session trial tables for ``sub-01``. The bucket is public, so
the first call asks you to accept the CC0 license; no AWS credentials
needed.

.. code-block:: bash

   laion-fmri download --subject sub-01

Re-running is safe — the downloader is idempotent and only fetches
files whose local size doesn't match the bucket. Pass ``--n-jobs 4``
for faster parallel transfers, or ``--ses ses-01`` to narrow to a
single session.

Load betas in Python
====================

.. code-block:: python

   from laion_fmri import load_subject

   sub = load_subject("sub-01")

   betas = sub.get_betas(session="ses-01")          # (n_trials, n_voxels)
   trials = sub.get_trial_info(session="ses-01")    # pandas DataFrame

The ``trials`` table has one row per beta volume; its ``label`` column
is the stimulus image filename and is the join key to the stimulus
metadata. Restrict by ROI in the same call:

.. code-block:: python

   betas_ffa = sub.get_betas(session="ses-01", roi="FFA1")
   betas_face = sub.get_betas(session="ses-01", roi="face")  # union of face ROIs
   betas_lo = sub.get_betas(session="ses-01", roi="all", nc_threshold=0.2)

The full accessor grammar — categories, mask combinations, surface
ROIs, streaming mode for memory-tight machines — is in
:doc:`laion_fmri_package/load`.

Get the stimulus images
=======================

Stimulus images require accepting a Data Use Agreement. The package
walks you through the form on first request and caches the resulting
access token for subsequent calls:

.. code-block:: bash

   laion-fmri download-stimuli

Then load them in Python:

.. code-block:: python

   from laion_fmri import load_stimuli

   stim = load_stimuli()
   stim.metadata.head()                                 # pandas DataFrame
   img = stim.image("shared_12rep_LAION_cluster_1003_i0.jpg")  # PIL.Image

Pretrained image embeddings (OpenCLIP, DINOv2, PE Core, SigLIP2) are
public and do not need the DUA:

.. code-block:: bash

   laion-fmri download-embeddings

.. code-block:: python

   from laion_fmri import load_embeddings
   emb = load_embeddings("CLIP")
   emb["CLIP"][0]                                       # (1024,) float16

Next Steps
==========

* :doc:`dataset_at_a_glance` — full dataset overview and "what files do I need"
* :doc:`glmsingle_betas` — details on the beta estimates and noise ceilings
* :doc:`stimulus_data` — stimulus images, metadata, and embeddings
* :doc:`train_test_splits` — predefined train/test partitions
* :doc:`laion_fmri_package/load` — full ``Subject`` API reference
* :doc:`faq` — common questions

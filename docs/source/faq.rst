===
FAQ
===

Frequently asked questions about the LAION-fMRI dataset. Answers stay
short on purpose — they point you to the doc page that goes deeper.

General
=======

.. dropdown:: What is the LAION-fMRI dataset?

   A deeply-sampled 7T fMRI dataset of brain responses to natural images.
   Five participants viewed over 25,000 unique images across about 165
   sessions, with multi-echo BOLD recorded at 1.8 mm isotropic resolution.
   The image set is drawn from the LAION-natural pool (a curated subset of
   LAION-5B, Roth & Hebart, 2025) plus shared images from NSD and THINGS+,
   and the release includes raw functional data, single-trial GLMsingle
   betas, retinotopy, functional localizers, and diffusion MRI. See
   :doc:`dataset_at_a_glance` for the full inventory.

.. dropdown:: How do I cite the dataset?

   The dataset paper is in preparation. A full citation (with BibTeX) and
   ready-to-use methods-section text will be added with the final
   release. See :doc:`example_methods_text` for the suggested
   acknowledgment text you can use today.

.. dropdown:: What license is the data released under?

   The fMRI data, derivatives, anatomical scans, and metadata are released
   under **CC0 1.0** — you can use them for any purpose, including
   commercial, without permission. The **stimulus images** are an
   exception: they come from third-party web sources and are gated by a
   short Data Use Agreement that forbids redistribution, commercial use,
   and training general-purpose AI models. Full terms:
   :doc:`data_access`.

.. dropdown:: Who collected this data?

   The dataset was collected by the Hebart Lab (ViCCo Group) at the
   Max Planck Institute for Human Cognitive and Brain Sciences in
   Leipzig, Germany, on a 7T MAGNETOM Terra.X scanner.

Data Access
===========

.. dropdown:: How do I download the dataset?

   Install the package from GitHub
   (``python -m pip install "laion-fmri @ git+https://github.com/ViCCo-Group/LAION-fMRI.git@main"``)
   and run ``mkdir -p <path>`` followed by
   ``laion-fmri config --data-dir <path>`` once, then
   ``laion-fmri download --subject sub-01`` to pull one participant. The
   data lives in an AWS Open Data S3 bucket and downloads anonymously —
   no AWS credentials required. See :doc:`quickstart` for a five-minute
   walkthrough, or :doc:`data_access` for every download path (Python,
   CLI, raw AWS CLI, web form).

.. dropdown:: What is the total size of the dataset?

   Stimulus-side sizes are known: the gated stimulus HDF5 is about
   3.2 GB, the four public embedding files are about 50 MB each, and
   the public object-segmentation masks are about 68 MB. Total raw +
   derivative sizes will be reported with the final release. For now
   download one subject and one session first to gauge what your machine
   can handle.

.. dropdown:: Can I download only the parts I need?

   Yes. Both the Python ``download(...)`` function and the
   ``laion-fmri download`` CLI accept BIDS-entity filters — narrow by
   subject, session, task, space, desc, stat, suffix, and extension. So
   you can grab a single session, only the noise-ceiling maps, only the
   ROI masks, etc. See :doc:`data_access` and
   :doc:`laion_fmri_package/download`.

.. dropdown:: Do I need to sign a Data Use Agreement?

   Only for the stimulus images. The fMRI data, derivatives, and metadata
   are CC0 and download anonymously. For the stimuli, the package walks
   you through a short web/CLI form once per machine; you can also submit
   the form in your browser at
   https://laion-fmri.hebartlab.com/request. See :doc:`data_access`.

Working with the Data
=====================

.. dropdown:: Which files do I need for encoding/decoding models?

   Single-trial beta estimates (``derivatives/glmsingle-tedana/``), the
   stimulus images and metadata (``stimuli/``), and the bundled train/test
   splits. ROI masks (``derivatives/rois/``) and pretrained image
   embeddings are optional but useful. The "What Files Do I Need?"
   section of :doc:`dataset_at_a_glance` lays it out by use case.

.. dropdown:: Which GLMsingle beta version should I use?

   Only the TYPED stage is shipped (``FITHRF_GLMDENOISE_RR`` — the full
   pipeline with HRF fitting, GLMdenoise, and fractional ridge), so the
   choice is made for you. Keep in mind that the ridge step shrinks
   magnitudes toward zero, so betas are reliable in a relative sense
   (good for encoding, decoding, RSA, contrasts) but should not be read
   as raw percent signal change — z-score within session before
   averaging when you need cross-voxel comparability. Details:
   :doc:`glmsingle_betas`.

.. dropdown:: How do beta indices map to stimulus IDs?

   Each session ships a per-trial TSV
   (``*_desc-SingletrialBetas_trials.tsv``) with one row per beta volume.
   The ``label`` column is the stimulus image filename and is the join
   key to the stimulus metadata. With the package this is
   ``sub.get_trial_info(session="ses-01")``; row :math:`i` of that table
   corresponds to volume :math:`i` of the 4D beta NIfTI. Details:
   :doc:`glmsingle_betas`.

.. dropdown:: What are the available train/test splits?

   The dataset ships predefined splits for all three methods of the
   re:vision generalization framework: ``tau`` (Method 1, balanced
   within-distribution 80/20), ``cluster_k5_0`` … ``cluster_k5_4``
   (Method 2, CLIP-cluster holdouts), and ``ood`` (Method 3, the 371
   held-out OOD images). Five seeded random 80/20 baselines
   (``random_0`` … ``random_4``) are also bundled. Each split is
   available for the shared pool and for every subject's full pool. Full
   reference and code examples: :doc:`train_test_splits`.

.. dropdown:: What coordinate spaces are the data provided in?

   GLMsingle single-trial betas, the noise-ceiling and R² maps, and the
   volumetric ROI masks are all in **T1w subject-native space** at
   1.778 mm isotropic. Surface ROIs are shipped on fsnative as
   ``.func.gii`` and FreeSurfer ``.label`` files. The full list of
   spaces and resolutions across all derivative streams will be added
   with the final release.

.. dropdown:: How do I extract betas from an ROI?

   Use ``sub.get_betas(session="ses-01", roi="FFA1")`` (or any ROI name
   / category like ``"face"``, or a list, or ``"all"``). The package
   loads the matching mask, applies it, and returns a
   ``(n_trials, n_voxels)`` array. ROI inputs also compose with
   ``mask=``, ``nc_threshold=``, and the ``streaming=True`` flag for
   memory-constrained environments. Full grammar:
   :doc:`laion_fmri_package/load`.

.. dropdown:: Are there shared stimuli across subjects?

   Yes — 1,492 images were shown to every subject. Of those, 881 are
   the 12-repeat set used for cross-subject noise-ceiling estimation,
   and 611 are a 4-repeat shared set. The remaining ~4,712 images per
   subject are subject-unique. The exact counts and how the repeats are
   scheduled are documented in :doc:`experimental_design`.

Acquisition & Preprocessing
============================

.. dropdown:: What MRI scanner and sequence were used?

   All data were acquired on a 7T MAGNETOM Terra.X (Siemens
   Healthineers) with an 8Tx/32Rx head coil (Nova Medical) at the MPI
   for Human Cognitive and Brain Sciences in Leipzig. Functional runs
   used a gradient-echo multi-band EPI sequence with three echoes
   (TE = 11.0 / 28.82 / 46.62 ms), TR = 1.9 s, 1.8 mm isotropic voxels,
   multiband factor 3. Full parameter tables (including the structural
   MEGRE and fieldmap protocols) are in :doc:`mri_acquisition`.

.. dropdown:: What preprocessing pipeline was applied?

   The functional data were preprocessed with NORDIC denoising followed
   by tedana optimal echo combination, and the resulting BOLD timeseries
   was fed to GLMsingle. The choice was based on a 2 × 3 variant
   comparison (NORDIC on/off × no tedana / optcom / ICA-denoised); the
   NORDIC + tedana ``optcom`` combination gave the best ROI-level noise
   ceilings while avoiding redundancy with GLMsingle's own GLMdenoise.
   Full step-by-step parameters will be added with the final release —
   see :doc:`preprocessing` for what's available today.

.. dropdown:: Is the raw (unprocessed) data available?

   Yes — raw BOLD, anatomical, fieldmap, and event files ship in
   standard BIDS layout alongside the derivatives, so you can rerun your
   own preprocessing if you prefer. Details: :doc:`fmri_data`.

.. dropdown:: What confound regressors are provided?

   The confound TSV columns will be documented with the final release.
   In the meantime, see :doc:`fmri_data` for what's currently shipped.

Quality Control
===============

.. dropdown:: Were any subjects or runs excluded?

   Exclusion criteria and the list of any dropped runs or sessions will
   be added with the final release. See :doc:`quality_control`.

.. dropdown:: What motion thresholds were used for exclusion?

   Motion thresholds and the associated framewise-displacement
   distributions will be added with the final release. See
   :doc:`quality_control`.

.. dropdown:: Where are the QC reports?

   Per-subject QC reports and their location in the bucket will be added
   with the final release. See :doc:`quality_control`.

Troubleshooting
===============

.. dropdown:: I get memory errors when loading the beta files

   A whole-brain session of betas is roughly 1 GB. Two easy reductions:
   pass an ``roi=`` filter (typically cuts voxel count by 1-2 orders of
   magnitude) and/or ``nc_threshold=``, or pass ``streaming=True`` to
   ``get_betas`` so the loader masks volume-by-volume instead of
   materialising the full 4D NIfTI in RAM. Memory-and-shape notes:
   :doc:`laion_fmri_package/load`.

.. dropdown:: The download is slow or keeps failing

   The package downloader is idempotent — re-running ``download(...)``
   only fetches files whose local size doesn't match S3, so interrupted
   transfers just resume. For faster pulls, pass ``n_jobs=4`` (or more)
   to run several AWS CLI copy workers in parallel. If a single file
   keeps stalling, the raw AWS CLI path (``aws s3 sync --no-sign-request
   s3://laion-fmri/...``) is sometimes the easiest fallback.


More Questions?
===============

If your question isn't answered here:

* `Open an issue on GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`_
* Check the detailed documentation pages listed in the sidebar

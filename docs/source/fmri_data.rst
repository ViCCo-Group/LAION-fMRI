=========
fMRI Data
=========

LAION-fMRI includes raw multi-echo BOLD data and preprocessed
optimally-combined BOLD timeseries. Most users will start from the
single-trial GLMsingle betas documented in :doc:`glmsingle_betas`, but
the functional data are available for users who want to inspect or
rerun the preprocessing.

For acquisition parameters, see :doc:`mri_acquisition`; for the
preprocessing pipeline, see :doc:`preprocessing`.

Raw Functional Data
===================

The scanner DICOMs were converted with ``heudiconv`` into BIDS-style
NIfTI files. Multi-echo BOLD and SBRef files live under ``func/``,
fieldmaps under ``fmap/``, and the MEGRE anatomical scan under
``anat/``.

A representative image-viewing run contains magnitude and phase BOLD
files for all three echoes, one SBRef per echo, JSON sidecars, and the
trial event file:

.. code-block:: text

   sub-01/ses-01/func/
   ├── sub-01_ses-01_task-images_run-01_echo-1_part-mag_bold.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-1_part-mag_bold.json
   ├── sub-01_ses-01_task-images_run-01_echo-1_part-phase_bold.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-1_part-phase_bold.json
   ├── sub-01_ses-01_task-images_run-01_echo-1_sbref.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-1_sbref.json
   ├── sub-01_ses-01_task-images_run-01_echo-2_part-mag_bold.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-2_part-mag_bold.json
   ├── sub-01_ses-01_task-images_run-01_echo-2_part-phase_bold.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-2_part-phase_bold.json
   ├── sub-01_ses-01_task-images_run-01_echo-2_sbref.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-2_sbref.json
   ├── sub-01_ses-01_task-images_run-01_echo-3_part-mag_bold.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-3_part-mag_bold.json
   ├── sub-01_ses-01_task-images_run-01_echo-3_part-phase_bold.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-3_part-phase_bold.json
   ├── sub-01_ses-01_task-images_run-01_echo-3_sbref.nii.gz
   ├── sub-01_ses-01_task-images_run-01_echo-3_sbref.json
   └── sub-01_ses-01_task-images_run-01_events.tsv

Fieldmaps are stored separately:

.. code-block:: text

   sub-01/ses-01/fmap/
   ├── sub-01_ses-01_run-01_magnitude1.nii.gz
   ├── sub-01_ses-01_run-01_magnitude1.json
   ├── sub-01_ses-01_run-01_magnitude2.nii.gz
   ├── sub-01_ses-01_run-01_magnitude2.json
   ├── sub-01_ses-01_run-01_phasediff.nii.gz
   └── sub-01_ses-01_run-01_phasediff.json

Preprocessed Functional Data
============================

The final preprocessed BOLD output used for downstream analysis is
stored under ``derivatives/tedana``. Each run is a single
T2*-weighted optimally-combined NIfTI in subject-native T1w space,
sampled on a 1.778 mm isotropic grid with TR = 1.0 s. The sidecar JSON
links the output back to the three echo BOLD files from which it was
derived.

.. code-block:: text

   derivatives/tedana/sub-01/ses-01/func/
   ├── sub-01_ses-01_task-images_run-01_space-T1w_desc-optcom_bold.nii.gz
   └── sub-01_ses-01_task-images_run-01_space-T1w_desc-optcom_bold.json

Most main image-viewing sessions contain 12 ``task-images`` runs.
Session ``ses-31`` is a mixed eyetracking session with fewer
image-viewing runs plus localizer/deepmreye runs. Sessions ``ses-32``
to ``ses-34`` are supplemental sessions and are not part of the
initial launch-release data.

Loading raw data
================

Raw BIDS files are reachable through the same package, either via
:func:`laion_fmri.download.download_raw` (raw only) or with
``include_raw=True`` on :func:`laion_fmri.download.download`
(raw on top of the derivative walk). ``Subject`` exposes three
accessors on top:

.. code-block:: python

   from laion_fmri import load_subject
   from laion_fmri.download import download_raw

   download_raw(subject="sub-01", ses="ses-01", run="01")

   sub = load_subject("sub-01")

   sub.has_raw()                                    # True
   sub.has_raw(session="ses-01")                    # True

   events = sub.get_events(session="ses-01")        # every run
   events_run1 = sub.get_events(session="ses-01",
                                run="01")           # one run

   bold = sub.get_raw_bold(session="ses-01",
                           run="01", echo="1")      # (n_vols, n_vox)
   sbref = sub.get_sbref(session="ses-01",
                         run="01", echo="1")        # (n_vox,)

:meth:`Subject.get_events` returns the raw BIDS events TSV(s) as a
pandas DataFrame. With ``run=None`` (default) it concatenates every
run in the session and adds a ``run`` column tagging each row.
:meth:`Subject.get_raw_bold` and :meth:`Subject.get_sbref` return
float32 arrays masked with the same brain mask used by
:meth:`Subject.get_betas` (default ``mask_source="anatomical"``).

Confounds and Behavioral Files
==============================

Richer confound documentation will be expanded in a later
documentation update. For the trial table that aligns directly
with the released GLMsingle beta volumes, see
:doc:`glmsingle_betas`. For raw BIDS ``events.tsv``, see the
"Loading raw data" section above.

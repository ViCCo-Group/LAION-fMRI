===============
MRI Acquisition
===============

This page documents the MRI acquisition parameters for all LAION-fMRI scans.
For the experimental design and task descriptions, see
:doc:`experimental_design`.

Scanner
=======

All MRI data were acquired at the Max Planck Institute for Human Cognitive
and Brain Sciences in Leipzig, Germany, on a 7T MAGNETOM Terra.X scanner
(Siemens Healthineers, syngo MR XA60) with a 7T 8Tx/32Rx head coil
(Nova Medical). Participants were scanned in custom-milled styrofoam
headcases to reduce head motion, and each subject's sessions were scheduled
within a fixed 2-hour time-of-day window throughout the ~1.5 year acquisition
period.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Manufacturer
     - Siemens Healthineers
   * - Model
     - SIEMENS MAGNETOM 7.0T W60 Numaris/X VA60A-0CT2
   * - Software
     - syngo MR XA60
   * - Field strength
     - 7T
   * - Head coil
     - 7T 8Tx/32Rx Head Coil (Nova Medical, Inc.)
   * - Site
     - Max Planck Institute for Human Cognitive and Brain Sciences,
       Leipzig, Germany

Functional MRI
==============

We chose a multi-echo EPI because it allows T2*-weighted optimal echo
combination (improving tSNR and BOLD sensitivity) and supports multi-echo
ICA denoising via tedana, which uses the TE-dependence of BOLD signal to
separate true neural signal from motion and physiological artifacts. For the
GLMsingle beta pipeline we work with the optimally-combined (not
tedana-denoised) echo to avoid interference with GLMsingle's own GLMdenoise.
The three echo times frame the expected gray matter T2* at 7T (~25-30 ms):
TE1 at 11 ms preserves signal in dropout regions, while TE2 and TE3 maximise
BOLD contrast in gray matter.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Sequence
     - gradient-echo multi-band EPI (CMRR sequence), 3 echoes, 2D
   * - TR
     - 1900 ms
   * - TE
     - TE1 = 11.0 ms, TE2 = 28.82 ms, TE3 = 46.62 ms
   * - Flip angle
     - 60°
   * - Voxel size
     - 1.8 mm isotropic
   * - Matrix size
     - 90 × 110 (base resolution 90, FOV phase 122.2 %)
   * - Number of slices
     - 72
   * - Slice orientation
     - transverse, tilted -10.4° towards coronal and +1.1° towards sagittal
       (oblique transverse, roughly aligned to AC-PC plane)
   * - Phase encoding direction
     - anterior to posterior (A >> P)
   * - Multiband factor
     - 3
   * - GRAPPA
     - PE acceleration factor 3, FLEET reference scan mode
   * - Partial Fourier
     - 6/8
   * - Fat suppression
     - yes (Fat Saturation, FA 110°)
   * - Bandwidth
     - 2058 Hz/pixel
   * - Echo spacing
     - 0.59 ms
   * - EPI factor
     - 110
   * - Volumes per run
     - 160 (sessions 1-5) or 163 (sessions 6-34)
   * - Acquisition time per run
     - 5:26 min (sessions 1-5) or 5:32 min (sessions 6-34)
   * - Dummy volumes discarded by scanner
     - 0

.. note::

   The scanner did not discard any volumes before saving, but a 12 second
   pre-task baseline (~7 volumes at TR = 1.9 s) is included at the start of
   each run during which no stimulus was shown, to allow signal stabilisation.

Structural MRI
==============

High-resolution T2* mapping (MEGRE) was recorded at 7T to improve
across-session alignment, but so far it has not been used for later
preprocessing. A separate T1w (MP2RAGE) at 3T Siemens Prisma was used for
structural alignment of the functional sessions and is described under
:doc:`retinotopy`.

MEGRE (T2*)
-----------

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - Sequence
     - 3D multi-echo gradient-echo (MEGRE), monopolar readout, 5 echoes
       (internal name "fl")
   * - TR
     - 27 ms
   * - TE
     - TE1 = 4.0, TE2 = 8.51, TE3 = 13.02, TE4 = 17.53, TE5 = 22.04 ms
   * - TI
     - not applicable (no inversion pulse)
   * - Flip angle
     - 12°
   * - Voxel size
     - 0.9 mm isotropic
   * - Matrix size
     - 180 × 220 (base resolution 180, FOV phase 122.2 %)
   * - Slices per slab
     - 144
   * - GRAPPA
     - PE 2 × 3D 2 (24 reference lines each)
   * - Phase partial Fourier
     - 7/8
   * - Slice partial Fourier
     - 7/8
   * - Bandwidth
     - 300 Hz/pixel (same for all 5 echoes)
   * - Distortion correction
     - 2D
   * - Acquisition time
     - 2:55 min (175 s)
   * - Inline T2* map
     - computed by scanner

Fieldmaps
=========

Dual-echo GRE fieldmaps were acquired repeatedly during each session to
correct for spatial distortions in the EPI data and to track B0 field drift
over time, which can be substantial at 7T.

.. list-table::
   :widths: 30 70
   :stub-columns: 1

   * - TR
     - 672 ms
   * - TE
     - TE1 = 5.0 ms, TE2 = 6.02 ms (ΔTE = 1.02 ms)
   * - Flip angle
     - 50°
   * - Voxel size
     - 1.8 mm isotropic
   * - Number of slices
     - 72
   * - FOV read
     - 160 mm
   * - FOV phase
     - 122.2 %
   * - Base resolution
     - 90
   * - Bandwidth
     - 291 Hz/pixel
   * - Phase partial Fourier
     - 7/8
   * - Distortion correction
     - 2D
   * - Acquisition time per fieldmap
     - 2:10 min (130 s)
   * - Number acquired per session
     - up to 4 (interleaved through the session to track B0 drift)

Retinotopy & Localizers
========================

.. todo::

   Document the acquisition parameters for retinotopy and localizer scans.
   If they used the same functional sequence as above, just state that.
   If any parameters differed, note what changed and why.

Diffusion MRI
=============

.. todo::

   If DWI data are included: narrative + parameter table (b-values,
   directions, resolution). If not included, remove this section.

   See also :doc:`diffusion`.

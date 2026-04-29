==================
License acceptance
==================

Two licenses apply:

* The **dataset license** (CC0 1.0) covers the brain and
  participant data.
* The **stimulus license** (closed, research-only) covers the
  stimulus images.

On the very first download the licenses are presented as
``Type "I AGREE"`` prompts; on acceptance, marker files are
written under ``{data_dir}/.laion_fmri/`` so the prompts don't
fire again.

Reviewing up front
==================

If you'd rather review and accept the licenses before any
``download(...)`` call, use the standalone helper:

.. code-block:: python

   from laion_fmri.download import accept_licenses

   accept_licenses(include_stimuli=True)

* Without ``include_stimuli``, only the dataset license is
  prompted.
* With ``include_stimuli=True``, both licenses are prompted in
  sequence.

Errors
======

* A declined dataset license raises ``LicenseNotAcceptedError``.
* A declined stimulus license raises ``RuntimeError``.

Both are the same exceptions ``download(...)`` raises
internally, so subsequent download calls behave identically
whether acceptance happened standalone or inside a download.

Dataset license (CC0 1.0)
=========================

The full text shown at the prompt:

.. code-block:: text

   === LAION-fMRI Dataset License (CC0 1.0) ===

   The brain imaging and participant data in the LAION-fMRI dataset are
   released under the Creative Commons Zero (CC0 1.0) Public Domain
   Dedication. You are free to copy, modify, distribute, and use the
   data for any purpose, including commercial, without asking permission.

   Full license text: https://creativecommons.org/publicdomain/zero/1.0/

   NOTE: Stimulus images are NOT covered by CC0. They are subject to a
   separate, restrictive license. You will be prompted to accept it if
   you choose to download stimuli.

Stimulus license
================

The full text shown at the prompt when ``include_stimuli=True``:

.. code-block:: text

   === LAION-fMRI Stimulus License ===

   The LAION-fMRI stimulus images are provided under a closed license.
   All rights are reserved by the original copyright holders.

   You may ONLY use these images for non-commercial academic research.
   All other uses are strictly prohibited. In particular, you may NOT:

     1. Share, redistribute, or make the images available to others.
     2. Use the images for any commercial purpose.
     3. Use the images to train, fine-tune, or evaluate commercial
        AI/ML models or services.
     4. Create derivative works from the images for any purpose
        other than non-commercial academic research.

   Full terms: https://laion-fmri.github.io/terms

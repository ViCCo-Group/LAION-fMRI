===============
Dataset license
===============

The brain imaging and derivatives of LAION-fMRI are released under
**CC0 1.0**. The stimulus images are not CC0; they're gated by a
separate Data Use Agreement enforced by the access service — see
:doc:`stimulus_access` for that flow.

CC0 acceptance prompt
=====================

On the very first ``download(...)`` against a new data directory you'll
see the CC0 license text and a ``Type "I AGREE"`` prompt:

.. code-block:: text

   === LAION-fMRI Dataset License (CC0 1.0) ===

   The brain imaging and participant data in the LAION-fMRI dataset are
   released under the Creative Commons Zero (CC0 1.0) Public Domain
   Dedication. You are free to copy, modify, distribute, and use the
   data for any purpose, including commercial, without asking permission.

   Full license text: https://creativecommons.org/publicdomain/zero/1.0/

   Type "I AGREE" to accept and continue with the download:

Accepting writes a marker file at
``{data_dir}/.laion_fmri/license_accepted`` so the prompt only appears
once per data directory.

Accepting up front
==================

To accept before any ``download(...)`` call:

.. code-block:: python

   from laion_fmri.download import accept_license
   accept_license()

The older ``accept_licenses(include_stimuli=True)`` signature still
works for back-compat, but ``include_stimuli=True`` is a no-op there —
stimulus terms are accepted via the access service, not via a local
prompt. See :doc:`stimulus_access`.

Errors
======

A declined CC0 license raises
:class:`laion_fmri._errors.LicenseNotAcceptedError`.

Stimulus images
===============

Different licensing applies — the stimulus images come from third-party
web sources and are gated behind a Data Use Agreement. Acceptance
happens via a short form (terminal or web). The full guide is on
:doc:`stimulus_access`.

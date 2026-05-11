================
Stimulus access
================

The fMRI data, derivatives, and metadata of LAION-fMRI are released
openly and need no special action — see :doc:`download`. The visual
stimulus images come from third-party web sources and are gated by a
short Data Use Agreement (DUA):
https://laion-fmri.hebartlab.com/terms.

How to download
===============

Run this once from a Python session:

.. code-block:: python

   import laion_fmri
   laion_fmri.download_stimuli()

…or from the shell:

.. code-block:: bash

   laion-fmri download-stimuli

The first time, you'll be prompted in the terminal for your name,
institutional email, institution, optional PI/supervisor, and a brief
description of your research purpose. You type ``yes`` to accept the
DUA and the download starts (~3 GB).

Running the command again later just re-downloads what's missing — no
form to re-fill.

Reading the images
==================

Once downloaded, read images out of the local archive with
:class:`laion_fmri.Stimuli`:

.. code-block:: python

   import laion_fmri

   stim = laion_fmri.Stimuli()
   stim.metadata.head()                          # pandas DataFrame, 25 052 rows
   stim["shared_12rep_LAION_cluster_1003_i0.jpg"]  # raw JPEG bytes
   stim.image(0)                                 # decoded PIL.Image (needs Pillow)

The metadata CSV columns are ``image_name``, ``dataset``,
``participant``, ``unique_or_shared``, ``n_reps``. Row ``i`` of the
DataFrame matches ``stim[i]``.

Together with fMRI in one call
==============================

Pass ``include_stimuli=True`` to the regular ``download()``:

.. code-block:: python

   from laion_fmri.download import download
   download(subject="sub-03", include_stimuli=True)

The fMRI part downloads first, then the stimulus archive.

In a browser, without Python
============================

If you'd rather not install the package, submit the same form in a
browser:

  https://laion-fmri.hebartlab.com/request

The confirmation page gives you direct download URLs (valid one hour)
that you can use with ``curl`` or click in your browser.

On a cluster
============

After downloading once on your laptop, copy the package's local cache
file to the cluster:

.. code-block:: bash

   rsync ~/.cache/laion-fmri/auth.json cluster:~/.cache/laion-fmri/

Then run the package on the cluster as usual — no form re-fill.

If something goes wrong
=======================

* **The DUA was updated since you accepted it.** The package will print
  a URL; open it, click *I accept*, and re-run the command.
* **The download was interrupted.** Just run the command again — it
  picks up where it left off.
* **Anything else.** Open an issue on
  `GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`__, or
  email ``martin.hebart@psychiat.med.uni-giessen.de`` for stimulus-access
  / takedown questions.

Privacy
=======

What the project records: your form submission and a log of which files
you've downloaded. No IP addresses, no email is ever sent. The full
privacy notice is at https://laion-fmri.hebartlab.com/privacy. Data
controller: **Prof. Martin Hebart**, Justus-Liebig-Universität Gießen.

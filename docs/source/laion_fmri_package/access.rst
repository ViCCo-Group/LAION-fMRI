=================
Licenses & access
=================

LAION-fMRI has two release tracks with different rules:

* The **fMRI data, derivatives, and metadata** are released under
  **CC0 1.0**. You can download them anonymously; we just ask you to
  acknowledge the licence once.
* The **stimulus images** come from third-party web sources and aren't
  CC0. We give them to you only after you accept a short **Data Use
  Agreement** (DUA): https://laion-fmri.hebartlab.com/terms.

Most of this page is about the DUA flow — the CC0 prompt is a single
``"I AGREE"``.

------------------------------------------------------------

The CC0 prompt
==============

The first time you run ``download(...)`` against a new data directory,
the package shows you the CC0 license and asks you to type ``"I AGREE"``:

.. code-block:: text

   === LAION-fMRI Dataset License (CC0 1.0) ===

   The brain imaging and participant data in the LAION-fMRI dataset are
   released under the Creative Commons Zero (CC0 1.0) Public Domain
   Dedication. You are free to copy, modify, distribute, and use the
   data for any purpose, including commercial, without asking permission.

   Full license text: https://creativecommons.org/publicdomain/zero/1.0/

   Type "I AGREE" to accept and continue with the download:

We write a small marker file at ``{data_dir}/.laion_fmri/license_accepted``
so you never see the prompt again on that data directory.

If you'd rather review the licence up front:

.. code-block:: python

   from laion_fmri.download import accept_license
   accept_license()

If you decline, the package raises
:class:`laion_fmri._errors.LicenseNotAcceptedError` and stops.

------------------------------------------------------------

The DUA flow (stimulus images)
==============================

The stimulus images come from third-party web sources — we don't own
them. To give them to you we ask you to accept a short Data Use
Agreement first. There's no login, no password, no email
verification. You fill in a short form once. From then on, the
``laion_fmri`` package quietly handles the rest.

How to download
---------------

From a Python session:

.. code-block:: python

   import laion_fmri
   laion_fmri.download_stimuli()

…or from the shell:

.. code-block:: bash

   laion-fmri download-stimuli

The first time, you'll be prompted in the terminal for your name,
institutional email, institution, optional PI/supervisor, and a brief
description of your research purpose. Type ``yes`` to accept the DUA
and the download starts (~3 GB).

Running the command again later just re-downloads what's missing — no
form to re-fill.

Reading the images
------------------

For the full API see :doc:`load`. The short version:

.. code-block:: python

   import laion_fmri
   stim = laion_fmri.load_stimuli()
   stim["shared_12rep_LAION_cluster_1003_i0.jpg"]
   stim.image(0)

Together with fMRI in one call
------------------------------

Pass ``include_stimuli=True`` to the regular ``download()`` — the fMRI
part runs first, the stimulus archive after:

.. code-block:: python

   from laion_fmri.download import download
   download(subject="sub-03", include_stimuli=True)

In a browser, without Python
----------------------------

If you'd rather not install the package, submit the same form in a
browser: https://laion-fmri.hebartlab.com/request. The confirmation
page gives you direct download URLs (valid one hour) that you can use
with ``curl`` or click in your browser.

On a cluster
------------

After downloading once on your laptop, copy the package's local cache
file to the cluster:

.. code-block:: bash

   rsync ~/.cache/laion-fmri/auth.json cluster:~/.cache/laion-fmri/

Then run the package on the cluster as usual — no form re-fill.

If something goes wrong
-----------------------

* **We've updated the DUA.** The package prints a URL; open it, click
  *I accept*, and re-run the command.
* **The download was interrupted.** Just run the command again — it
  picks up where it left off.
* **Anything else.** Open an issue on
  `GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`__. For
  stimulus access / takedown questions, see the contact at
  https://laion-fmri.hebartlab.com/takedown.

------------------------------------------------------------

Privacy
=======

**What we keep on the server.** Your form submission (name,
institutional email, institution, optional supervisor, research
purpose) and a record of which files we sent you and when.

**What we don't keep.** Your IP address or anything about your browser.

**What we never do.** Send you email — there's no email verification,
no newsletter, no automated notifications.

**What happens to your record over time.** After a year with no
downloads we automatically anonymise your form submission: name,
email, institution, supervisor and research purpose are dropped while
a minimal audit row (which files were sent, when) stays for governance.

The full privacy notice — including the data-controller contact — is
at https://laion-fmri.hebartlab.com/privacy.

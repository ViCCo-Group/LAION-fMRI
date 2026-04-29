=============================
Initialize the data directory
=============================

``dataset_initialize(path)`` records ``path`` as the local mirror
of the bucket. The choice is persisted in
``$XDG_CONFIG_HOME/laion_fmri/config.json`` (or
``~/.config/laion_fmri/config.json``), so subsequent sessions
pick it up automatically.

.. code-block:: python

   from laion_fmri.config import dataset_initialize, get_data_dir

   dataset_initialize("./laion_fmri_data")
   get_data_dir()        # → "./laion_fmri_data"

This step writes nothing to S3 and does not require AWS
credentials. It only sets up the local destination for future
``download(...)`` calls and makes ``Subject`` / ``Group``
loaders aware of where the data lives.

Requirements
============

* **The directory must already exist.** ``dataset_initialize``
  raises ``FileNotFoundError`` if the path is missing -- it
  doesn't create the directory for you, so a typo can't
  silently scatter dataset files in the wrong place. Create it
  yourself first (e.g. ``mkdir -p ./laion_fmri_data``).
* The path argument must be a string -- ``TypeError`` otherwise.

What gets created
=================

Inside the data directory, ``laion_fmri`` creates a hidden
``.laion_fmri/`` subdirectory used for state that is local to
the dataset:

* ``.laion_fmri/license_accepted`` -- marker file written when
  the dataset license is accepted (see :doc:`license`).
* ``.laion_fmri/stimuli_terms_accepted`` -- marker file written
  when the stimulus terms of use are accepted.

Nothing else lives there. The bucket mirror itself is laid out
under ``derivatives/``, ``stimuli/`` etc. directly in the data
directory once ``download(...)`` runs.

Switching data directories
==========================

Calling ``dataset_initialize`` again with a different path
overwrites the persisted choice and points all subsequent
loaders at the new location. The *old* directory is left on
disk untouched -- ``laion_fmri`` never deletes data for you.

.. code-block:: python

   dataset_initialize("./scratch_run")    # active until next call
   dataset_initialize("./project_run")    # now active; first dir untouched

If no data directory has been initialized yet,
``get_data_dir()`` raises ``DataDirNotSetError`` with a hint to
run ``dataset_initialize``.

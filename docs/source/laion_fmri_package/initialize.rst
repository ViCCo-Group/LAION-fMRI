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

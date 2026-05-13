==============
``laion_fmri``
==============

A data access package for downloading and loading the LAION-fMRI dataset.

.. code-block:: python

   from laion_fmri.config import dataset_initialize
   from laion_fmri.download import download
   from laion_fmri.subject import load_subject

   dataset_initialize("./laion_fmri_data")

   download(subject="sub-03", ses="ses-01", n_jobs=4)

   sub = load_subject("sub-03")
   betas = sub.get_betas(session="ses-01")     # (n_trials, n_voxels), float32

The same three workflow steps *configure*, *inspect*, and *download* are also exposed as a ``laion-fmri`` shell command:

.. code-block:: bash

   mkdir -p ./laion_fmri_data
   laion-fmri config   --data-dir ./laion_fmri_data
   laion-fmri info
   laion-fmri download --subject sub-03

The cards below walk through each step in detail.

.. grid:: 1 2 2 3
   :gutter: 2

   .. grid-item-card:: Initialize
      :link: initialize
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      Pick a local data directory and persist the choice across
      sessions.

      +++
      ``dataset_initialize`` · ``get_data_dir``

   .. grid-item-card:: Licenses & access
      :link: access
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      CC0 for the fMRI side, a short Data Use Agreement form for
      the stimulus images. The package handles both.

      +++
      ``accept_license`` · ``download_stimuli`` ·
      ``request_stimulus_access``

   .. grid-item-card:: Discover
      :link: discover
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      List subjects, ROIs, and bucket structure -- every query
      reads S3 directly, no local download needed.

      +++
      ``get_subjects`` · ``describe`` · ``inspect_bucket``

   .. grid-item-card:: Download
      :link: download
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      BIDS-entity filters, strict ``ses`` semantic with the
      ``"averages"`` keyword, idempotent re-runs, and ``n_jobs``
      parallelism.

      +++
      ``download(...)``

   .. grid-item-card:: Load
      :link: load
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      Single-trial betas, noise-ceiling maps, ROI masks,
      brain-space mapping, multi-subject groups, and PyTorch.

      +++
      ``Subject`` · ``Group``

   .. grid-item-card:: Examples gallery
      :link: /auto_examples/index
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      Five hands-on, narrated walkthroughs covering the full
      workflow.

      +++
      ``plot_01`` ... ``plot_05``

   .. grid-item-card:: API reference
      :link: api
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      Auto-generated reference for every public module, class,
      and function.

      +++
      ``brain`` · ``config`` · ``discovery`` · ``download`` ·
      ``group`` · ``io`` · ``stimuli`` · ``subject`` · ``torch_data``


.. toctree::
   :maxdepth: 1
   :hidden:

   initialize
   access
   discover
   download
   load
   api

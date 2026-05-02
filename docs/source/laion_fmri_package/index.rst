==============
``laion_fmri``
==============

A pure data downloader and wrangler for the LAION-fMRI dataset.
The package mirrors the bucket layout to your local disk via the
official AWS CLI, keeps every accessor as a one-to-one map onto a
single file in S3, and applies BIDS-entity filters so you only
fetch what you need.

A typical session looks like:

.. code-block:: python

   from laion_fmri.config import dataset_initialize
   from laion_fmri.download import download
   from laion_fmri.subject import load_subject

   dataset_initialize("./laion_fmri_data")

   download(subject="sub-03", ses="ses-01", n_jobs=4)

   sub = load_subject("sub-03")
   betas = sub.get_betas(session="ses-01")     # (n_trials, n_voxels), float32

The same three workflow steps -- *configure*, *inspect*,
*download* -- are also exposed as a ``laion-fmri`` shell
command, installed automatically by ``pip``/``uv``:

.. code-block:: bash

   laion-fmri config   --data-dir ./laion_fmri_data
   laion-fmri info
   laion-fmri download --subject sub-03

Loading still happens from Python; the CLI covers configure,
inspect, and download. See :doc:`download` for full
``laion-fmri download`` semantics.

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

   .. grid-item-card:: Licenses
      :link: license
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      Review and accept the dataset and stimulus licenses up
      front, or let ``download(...)`` prompt on first use.

      +++
      ``accept_licenses``

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

      Four hands-on, narrated walkthroughs covering the full
      workflow.

      +++
      ``plot_01`` … ``plot_04``

   .. grid-item-card:: API reference
      :link: api
      :link-type: doc
      :class-card: sd-border-0
      :shadow: sm

      Auto-generated reference for every public module, class,
      and function.

      +++
      ``brain`` · ``config`` · ``discovery`` · ``download`` ·
      ``group`` · ``io`` · ``subject`` · ``torch_data``


.. toctree::
   :maxdepth: 1
   :hidden:

   initialize
   license
   discover
   download
   load
   api

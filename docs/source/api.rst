=============
API Reference
=============

This page documents the top-level public Python API for
``laion_fmri``. For workflow examples, see :doc:`quickstart` and the
:doc:`auto_examples/index` gallery.

.. contents:: On this page
   :local:
   :depth: 2


Configuration
=============

.. autofunction:: laion_fmri.dataset_initialize

``laion_fmri.set_data_dir`` is an alias for
``laion_fmri.dataset_initialize``.

.. autofunction:: laion_fmri.get_data_dir


Loading Data
============

.. autofunction:: laion_fmri.load_subject

.. autofunction:: laion_fmri.load_subjects

.. autofunction:: laion_fmri.load_stimuli

.. autofunction:: laion_fmri.load_embeddings


Discovery
=========

.. autofunction:: laion_fmri.get_subjects

.. autofunction:: laion_fmri.get_rois

.. autofunction:: laion_fmri.describe


Downloads and Access
====================

.. autofunction:: laion_fmri.download_stimuli

.. autofunction:: laion_fmri.download_embeddings

.. autofunction:: laion_fmri.download_segmentations

.. autofunction:: laion_fmri.download_captions

.. autofunction:: laion_fmri.request_stimulus_access


Classes
=======

.. autoclass:: laion_fmri.Subject
   :members:

.. autoclass:: laion_fmri.Group
   :members:
   :special-members: __getitem__, __iter__, __len__

.. autoclass:: laion_fmri.Stimuli
   :members:
   :special-members: __getitem__, __len__, __iter__, __contains__

.. autoclass:: laion_fmri.Embeddings
   :members:
   :special-members: __getitem__, __len__, __contains__

.. autoclass:: laion_fmri.Captions
   :members:

.. autoclass:: laion_fmri.Segmentations
   :members:


Exceptions
==========

.. autoexception:: laion_fmri.DataDirNotSetError

.. autoexception:: laion_fmri.DataNotFoundError

.. autoexception:: laion_fmri.DataNotDownloadedError

.. autoexception:: laion_fmri.NoMatchingDataError

.. autoexception:: laion_fmri.StimuliNotDownloadedError

.. autoexception:: laion_fmri.SubjectNotFoundError

.. autoexception:: laion_fmri.LicenseNotAcceptedError


Utilities
=========

.. autofunction:: laion_fmri.resolve_subject_id


Train / Test Splits (``laion_fmri.splits``)
===========================================

The :mod:`laion_fmri.splits` subpackage bundles the predefined
train/test splits used by the re:vision generalization framework.
See :doc:`/train_test_splits` for the conceptual guide.

.. autofunction:: laion_fmri.splits.list_pools
   :no-index:

.. autofunction:: laion_fmri.splits.list_splits
   :no-index:

.. autofunction:: laion_fmri.splits.list_ood_types
   :no-index:

.. autofunction:: laion_fmri.splits.load_split
   :no-index:

.. autofunction:: laion_fmri.splits.load_all_splits
   :no-index:

.. autofunction:: laion_fmri.splits.get_train_test_ids
   :no-index:

.. autofunction:: laion_fmri.splits.get_split_masks
   :no-index:

.. autoclass:: laion_fmri.splits.Split
   :members:
   :no-index:

.. autoclass:: laion_fmri.splits.SplitVariant
   :members:
   :no-index:

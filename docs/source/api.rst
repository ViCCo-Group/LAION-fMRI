=============
API Reference
=============

This page documents the public Python API for the ``laion_fmri`` package.
For usage examples and workflows, see the :doc:`usage` guide.

.. contents:: On this page
   :local:
   :depth: 2


Top-level Functions
===================

Configuration
-------------

.. autofunction:: laion_fmri.set_data_dir

.. autofunction:: laion_fmri.get_data_dir

Loading Data
------------

.. autofunction:: laion_fmri.load_subject

.. autofunction:: laion_fmri.load_subjects

Discovery
---------

.. autofunction:: laion_fmri.get_subjects

.. autofunction:: laion_fmri.get_downloaded_subjects

.. autofunction:: laion_fmri.get_rois

.. autofunction:: laion_fmri.describe


Subject
=======

.. autoclass:: laion_fmri.Subject
   :members:


Group
=====

.. autoclass:: laion_fmri.Group
   :members:
   :special-members: __getitem__, __iter__, __len__


Exceptions
==========

.. autoexception:: laion_fmri.DataNotConfiguredError

.. autoexception:: laion_fmri.DataNotFoundError


Constants
=========

.. autodata:: laion_fmri.SUBJECTS

.. autodata:: laion_fmri.DEFAULT_CVE_THRESHOLD


Utilities
=========

.. autofunction:: laion_fmri.resolve_subject_id


Train / Test Splits (``laion_fmri.splits``)
===========================================

The :mod:`laion_fmri.splits` subpackage bundles the predefined
train/test splits used by the re:vision generalization framework.
See :doc:`/train_test_splits` for the conceptual guide.

.. autofunction:: laion_fmri.splits.list_pools

.. autofunction:: laion_fmri.splits.list_splits

.. autofunction:: laion_fmri.splits.list_ood_types

.. autofunction:: laion_fmri.splits.load_split

.. autofunction:: laion_fmri.splits.load_all_splits

.. autofunction:: laion_fmri.splits.get_train_test_ids

.. autofunction:: laion_fmri.splits.get_split_masks

.. autoclass:: laion_fmri.splits.Split
   :members:

.. autoclass:: laion_fmri.splits.SplitVariant
   :members:

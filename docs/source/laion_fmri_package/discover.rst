=============================
Discover what's in the bucket
=============================

The discovery functions don't depend on what's on your disk.
``get_subjects`` returns the fixed subject list of a dataset; the
others read the bucket directly. Run them right after
:doc:`initialization <initialize>` to confirm the bucket is
reachable and see what's available before committing to a
download.

.. code-block:: python

   from laion_fmri.discovery import (
       describe,
       get_rois,
       get_subjects,
       inspect_bucket,
   )

   get_subjects()                                # ['sub-01', ...], main experiment
   get_subjects("mapping")                       # adds 'sub-04', 'sub-08'
   get_rois("sub-01")                            # ['AFP1', 'EBA', ...]
   get_rois("sub-01", category="face")           # face-area ROIs only
   describe()                                    # human-readable summary
   inspect_bucket()                              # diagnostic listing

What each one does
==================

``get_subjects(dataset="main")``
   Lists the subjects of a dataset (:ref:`subject-sets`).
   ``"main"`` (default) is the main experiment: ``sub-01``,
   ``sub-03``, ``sub-05``, ``sub-06``, ``sub-07``. ``"mapping"`` is
   the precision-mapping dataset, which adds ``sub-04`` and
   ``sub-08``.

``get_rois(subject, category=None)``
   Lists ROI labels available for a subject. The bucket groups
   ROIs by category (``body``, ``character``, ``face``,
   ``laion``, ``laionstim``, ``motion``, ``object``, ``place``,
   ``retinotopy``); pass ``category=`` to restrict the listing.
   ROI labels are returned in BIDS-clean form. The bucket
   sometimes ships hyphenated label values (``label-FFA-1``,
   ``label-pSTS-faces``) that the package rewrites locally to
   ``FFA1`` / ``pSTSfaces`` so the on-disk mirror passes the
   BIDS validator.

``describe()``
   Prints a human-readable summary of bucket contents.

``inspect_bucket()``
   Verbose diagnostic listing, useful when something looks
   wrong (no subjects returned, unexpected layout, etc.).

Sample output
=============

.. code-block:: text

   LAION-fMRI Dataset
     Bucket:    s3://laion-fmri
     Subjects:  5 (sub-01, sub-03, sub-05, sub-06, sub-07)
     ROIs:      AFP1, AFP2, EBA, FBA, FFA1, ...

When something looks wrong, ``inspect_bucket()`` shows the
top-level layout plus a per-prefix subject count:

.. code-block:: text

   Bucket: s3://laion-fmri
   Top-level prefixes (1):
     derivatives/
   derivatives/glmsingle-tedana/: 5 entries, 5 sub-* entries
   derivatives/rois/: 6 entries, 6 sub-* entries

Empty-listing warnings
======================

If a subject has no ROIs on the bucket, ``get_rois()`` raises a
``UserWarning`` instead of returning an empty list silently, so a
missing upload is visible rather than mistaken for a configuration
error.

If you only want the result without the warning:

.. code-block:: python

   import warnings

   with warnings.catch_warnings():
       warnings.simplefilter("ignore", UserWarning)
       rois = get_rois("sub-03")

Once the bucket is fully populated and warnings stop firing,
this wrapper is no longer needed.

=============================
Discover what's in the bucket
=============================

All discovery functions read the bucket directly -- they don't
depend on what's on your disk. Run them right after
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

   get_subjects()             # ['sub-03', ...]
   get_rois("sub-03")         # ROI atlas names, when available
   describe()                 # human-readable summary
   inspect_bucket()           # diagnostic listing for troubleshooting

What each one does
==================

``get_subjects()``
   Lists all subjects exposed by the bucket (every ``sub-*``
   subdirectory under ``derivatives/glmsingle-tedana/`` or
   ``derivatives/atlases/``; the union of both is returned).

``get_rois(subject)``
   Lists ROI atlas names available for a subject.  ROI atlases
   are a forward-compatible feature: today the bucket exposes
   none, so this returns ``[]`` with a clear warning. When
   atlases are uploaded, the call lights up automatically.

``describe()``
   Prints a human-readable summary of bucket contents.

``inspect_bucket()``
   Verbose diagnostic listing -- useful when something looks
   wrong (no subjects returned, unexpected layout, etc.).

Sample output
=============

A populated bucket:

.. code-block:: text

   LAION-fMRI Dataset
     Bucket:    s3://laion-fmri
     Subjects:  3 (sub-01, sub-03, sub-05)
     ROIs:      hlvis, visual

A bucket that is reachable but partially populated (common
during the dev phase):

.. code-block:: text

   LAION-fMRI Dataset
     Bucket:    s3://laion-fmri
     Subjects:  1 (sub-03)

When something looks wrong, ``inspect_bucket()`` shows the
top-level layout plus a per-prefix subject count:

.. code-block:: text

   Bucket: s3://laion-fmri
   Top-level prefixes (1):
     derivatives/
   derivatives/glmsingle-tedana/: 1 entries, 1 sub-* entries
   derivatives/atlases/: 0 entries, 0 sub-* entries

Empty-listing warnings
======================

During the dev phase, individual derivative trees may not yet
be populated. ``get_subjects()`` and ``get_rois()`` raise a
``UserWarning`` instead of failing silently, so a partial
upload is visible rather than mistaken for a configuration
error.

If you only want the result without the warning:

.. code-block:: python

   import warnings

   with warnings.catch_warnings():
       warnings.simplefilter("ignore", UserWarning)
       subjects = get_subjects()

Once the bucket is fully populated and warnings stop firing,
this wrapper is no longer needed.

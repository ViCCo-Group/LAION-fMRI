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
   subdirectory under ``derivatives/glmsingle-tedana/``).

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

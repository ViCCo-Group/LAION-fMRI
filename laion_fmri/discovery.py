"""Discovery API backed entirely by the LAION-fMRI S3 bucket.

All queries about what is in the dataset read directly from the S3
bucket via the AWS CLI. Local filesystem state is never consulted.
"""

import warnings

from laion_fmri._bidsify import bidsify_local_key
from laion_fmri._paths import parse_roi_label
from laion_fmri._s3_engine import (
    list_common_prefixes,
    list_prefix_keys,
)
from laion_fmri._sources import LAION_FMRI_BUCKET

SUBJECT_PREFIXES = (
    "derivatives/glmsingle-tedana/",
    "derivatives/rois/",
    "derivatives/freesurfer/",
    "derivatives/anatomical/",
)


def get_subjects():
    """Return all subject BIDS IDs present in the S3 bucket.

    The bucket may be partially populated during development -- some
    derivative trees may exist before others. This function returns
    the union of subjects found under any known derivative prefix.

    Returns
    -------
    list[str]
        Sorted list of BIDS subject IDs (``sub-*``).
    """
    found = set()
    for prefix in SUBJECT_PREFIXES:
        for name in list_common_prefixes(LAION_FMRI_BUCKET, prefix):
            if name.startswith("sub-"):
                found.add(name)

    if not found:
        warnings.warn(
            f"No subjects found in s3://{LAION_FMRI_BUCKET}/ under "
            f"any of {SUBJECT_PREFIXES}. "
            "Check bucket layout and AWS credentials.",
            UserWarning,
            stacklevel=2,
        )

    return sorted(found)


def get_rois(subject=None, category=None):
    """Return ROI names available for a subject in the S3 bucket.

    The bucket layout is
    ``derivatives/rois/{subject}/{category}/...`` with three file
    types per ROI; only the volumetric ``.nii.gz`` files are used
    here as the source of truth (one per ROI per subject).

    Hyphenated label values (e.g. ``label-FFA-1``) are normalized
    to BIDS-clean form (``"FFA1"``) before being returned.

    Parameters
    ----------
    subject : str or None
        BIDS subject ID. If None, uses the first subject in the
        bucket.
    category : str or None
        Optional category filter (``"face"``, ``"place"``, ...).

    Returns
    -------
    list[str]
        Sorted bidsified ROI names.
    """
    if subject is None:
        subjects = get_subjects()
        if not subjects:
            return []
        subject = subjects[0]

    prefix = f"derivatives/rois/{subject}/"
    keys = list_prefix_keys(LAION_FMRI_BUCKET, prefix)

    rois = set()
    for key in keys:
        if not key.endswith("_mask.nii.gz"):
            continue
        if "_space-T1w_res-1pt8_" not in key:
            continue
        relative = key[len(prefix):]
        parts = relative.split("/")
        if len(parts) != 2:
            continue
        file_category, fname = parts
        if category is not None and file_category != category:
            continue
        roi = parse_roi_label(bidsify_local_key(fname), subject)
        if roi is None:
            continue
        rois.add(roi)

    if not rois:
        warnings.warn(
            f"No ROIs found at s3://{LAION_FMRI_BUCKET}/{prefix}. "
            "The subject may not have ROI atlases uploaded yet.",
            UserWarning,
            stacklevel=2,
        )

    return sorted(rois)


def describe():
    """Print a human-readable summary of the S3 bucket contents."""
    subjects = get_subjects()
    print("LAION-fMRI Dataset")
    print(f"  Bucket:    s3://{LAION_FMRI_BUCKET}")
    print(f"  Subjects:  {len(subjects)}", end="")
    if subjects:
        print(f" ({', '.join(subjects)})")
        rois = get_rois(subjects[0])
        if rois:
            print(f"  ROIs:      {', '.join(rois)}")
    else:
        print(" (none)")


def inspect_bucket():
    """Print a diagnostic listing of the bucket for troubleshooting.

    Lists immediate top-level prefixes and probes the expected
    subject prefixes, showing how many subject folders exist under
    each. Use this when discovery returns unexpected results.
    """
    print(f"Bucket: s3://{LAION_FMRI_BUCKET}")

    top = list_common_prefixes(LAION_FMRI_BUCKET, "")
    print(f"Top-level prefixes ({len(top)}):")
    for name in sorted(top):
        print(f"  {name}/")

    for prefix in SUBJECT_PREFIXES:
        names = list_common_prefixes(LAION_FMRI_BUCKET, prefix)
        subject_count = sum(1 for n in names if n.startswith("sub-"))
        print(
            f"{prefix}: {len(names)} entries, "
            f"{subject_count} sub-* entries"
        )

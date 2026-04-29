"""Discovery API backed entirely by the LAION-fMRI S3 bucket.

All queries about what is in the dataset read directly from the S3
bucket via the AWS CLI. Local filesystem state is never consulted.
"""

import warnings

from laion_fmri._s3_engine import (
    list_common_prefixes,
    list_prefix_keys,
)
from laion_fmri._sources import LAION_FMRI_BUCKET

SUBJECT_PREFIXES = (
    "derivatives/glmsingle-tedana/",
    "derivatives/atlases/",
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


def get_rois(subject=None):
    """Return ROI names available for a subject in the S3 bucket.

    Parameters
    ----------
    subject : str or None
        BIDS subject ID. If None, uses the first subject in the
        bucket.

    Returns
    -------
    list[str]
        Sorted ROI names (without the ``.nii.gz`` suffix).
    """
    if subject is None:
        subjects = get_subjects()
        if not subjects:
            return []
        subject = subjects[0]

    prefix = f"derivatives/atlases/{subject}/rois/"
    keys = list_prefix_keys(LAION_FMRI_BUCKET, prefix)
    rois = []
    for key in keys:
        name = key[len(prefix):]
        if name.endswith(".nii.gz") and "/" not in name:
            rois.append(name[: -len(".nii.gz")])

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

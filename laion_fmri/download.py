"""Download logic for the LAION-fMRI dataset."""

import sys

from laion_fmri._constants import (
    LICENSE_AGREEMENT_TEXT,
    TERMS_OF_USE_TEXT,
    resolve_subject_id,
)
from laion_fmri._errors import LicenseNotAcceptedError
from laion_fmri._laion_fmri_fetch import fetch_laion_fmri
from laion_fmri._paths import license_marker_path, tou_marker_path
from laion_fmri.config import get_data_dir
from laion_fmri.discovery import get_subjects


def _check_license_accepted(data_dir):
    """Check whether the dataset license has been accepted.

    Parameters
    ----------
    data_dir : str
        Path to the data directory.

    Returns
    -------
    bool
        True if the license marker file exists.
    """
    return license_marker_path(data_dir).exists()


def _write_license_marker(data_dir):
    """Write the license acceptance marker file.

    Parameters
    ----------
    data_dir : str
        Path to the data directory.
    """
    marker = license_marker_path(data_dir)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()


def _prompt_license():
    """Display the license agreement and prompt the user for acceptance.

    Returns
    -------
    bool
        True if the user typed "I AGREE".
    """
    sys.stdout.write(LICENSE_AGREEMENT_TEXT)
    sys.stdout.flush()
    response = input().strip()
    return response == "I AGREE"


def _check_tou_accepted(data_dir):
    """Check whether the terms of use have been accepted.

    Parameters
    ----------
    data_dir : str
        Path to the data directory.

    Returns
    -------
    bool
        True if the ToU marker file exists.
    """
    return tou_marker_path(data_dir).exists()


def _write_tou_marker(data_dir):
    """Write the terms-of-use acceptance marker file.

    Parameters
    ----------
    data_dir : str
        Path to the data directory.
    """
    marker = tou_marker_path(data_dir)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()


def _prompt_tou():
    """Display the terms of use and prompt the user for acceptance.

    Returns
    -------
    bool
        True if the user typed "I AGREE".
    """
    sys.stdout.write(TERMS_OF_USE_TEXT)
    sys.stdout.flush()
    response = input().strip()
    return response == "I AGREE"


def accept_licenses(include_stimuli=False):
    """Walk through the license-acceptance flow without downloading.

    Same prompts ``download()`` triggers internally on first use:

    * The dataset license (CC0 1.0) is always presented.
    * The stimulus license is presented when ``include_stimuli``
      is True.

    On acceptance the marker files are written so subsequent
    ``download(...)`` calls won't prompt again.

    Parameters
    ----------
    include_stimuli : bool
        If True, also prompt for the stimulus license.

    Raises
    ------
    LicenseNotAcceptedError
        If the dataset license is declined.
    RuntimeError
        If the stimulus license is declined when requested.
    """
    data_dir = get_data_dir()

    if not _check_license_accepted(data_dir):
        if not _prompt_license():
            raise LicenseNotAcceptedError(
                "Dataset license must be accepted before downloading."
            )
        _write_license_marker(data_dir)

    if include_stimuli and not _check_tou_accepted(data_dir):
        if not _prompt_tou():
            raise RuntimeError(
                "Terms of use must be accepted to download stimuli."
            )
        _write_tou_marker(data_dir)


def download(
    subject,
    ses=None,
    task=None,
    space=None,
    desc=None,
    stat=None,
    suffix=None,
    extension=None,
    include_stimuli=False,
    n_jobs=1,
):
    """Download dataset files for a subject, narrowed by BIDS entities.

    The download is **idempotent**: a file whose local size already
    matches the S3 size is skipped, so re-running after an
    interrupted transfer only fetches what's missing.

    Parameters
    ----------
    subject : int, str, or "all"
        Subject identifier (BIDS ID, integer index, or "all").
    ses, task, space, desc, stat : str or list[str], optional
        BIDS-entity filters. Each accepts a bare value
        (``ses="04"``) or the full BIDS token (``ses="ses-04"``).
        A list narrows to multiple values. Files that don't carry
        an entity are not excluded by a filter on it (so
        subject-level summaries survive a ``ses=`` filter).
    suffix : str or list[str], optional
        BIDS suffix filter (``"statmap"``, ``"events"``, ...).
    extension : str or list[str], optional
        File extension filter (``"nii.gz"``, ``"tsv"``, ...).
    include_stimuli : bool
        Whether to include stimulus images (requires ToU
        acceptance).
    n_jobs : int
        Number of parallel download workers (``aws s3 cp``
        subprocesses). ``1`` (default) is sequential.

    Raises
    ------
    SubjectNotFoundError
        If the subject identifier is invalid.
    LicenseNotAcceptedError
        If the dataset license is declined.
    """
    data_dir = get_data_dir()

    if subject != "all":
        resolve_subject_id(subject)

    if not _check_license_accepted(data_dir):
        accepted = _prompt_license()
        if not accepted:
            raise LicenseNotAcceptedError(
                "Dataset license must be accepted before downloading."
            )
        _write_license_marker(data_dir)

    if include_stimuli and not _check_tou_accepted(data_dir):
        accepted = _prompt_tou()
        if not accepted:
            raise RuntimeError(
                "Terms of use must be accepted to download stimuli."
            )
        _write_tou_marker(data_dir)

    if subject == "all":
        subjects = get_subjects()
    else:
        subjects = [resolve_subject_id(subject)]

    for sub_id in subjects:
        fetch_laion_fmri(
            data_dir,
            subject=sub_id,
            ses=ses,
            task=task,
            space=space,
            desc=desc,
            stat=stat,
            suffix=suffix,
            extension=extension,
            include_stimuli=include_stimuli,
            n_jobs=n_jobs,
        )
